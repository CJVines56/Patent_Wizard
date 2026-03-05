"""
Minimal retrieval + ColBERT-style reranking utilities.

- Retrieve Claim candidates from Weaviate using vector, BM25, or hybrid retrieval.
- Rerank with token vectors from LMDB or vectors fetched from Weaviate.
- Optionally evaluate simple IR metrics from query/qrels files.
- Provide a direct patent (doc_id) lookup helper.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import requests

from backend.app.embed import embed_query_tokens_for_shard, model, normalize_text_for_embedding, tokenizer
from backend.app.services.download import rich_to_plain
from backend.app.store import (
    LMDB_PATH_128_F16,
    LMDB_PATH_128_F32,
    load_claim_payloads_from_lmdb,
    load_colbert_from_lmdb,
    resolve_lmdb_path,
)
from backend.app.vector_config import (
    WEAVIATE_NAMED_VECTOR,
    assert_128_variant,
)


WEAVIATE_GRAPHQL = os.environ.get("WEAVIATE_GRAPHQL", "http://localhost:8080/v1/graphql")
WEAVIATE_OBJECTS = os.environ.get("WEAVIATE_OBJECTS", "http://localhost:8080/v1/objects")


SHARD_TO_PATH = {
    "128_f32": LMDB_PATH_128_F32,
    "128_f16": LMDB_PATH_128_F16,
}
VALID_RETRIEVAL_MODES = ("vector", "bm25", "hybrid")
VALID_RERANK_SOURCES = ("lmdb", "weaviate")


def _normalize_retrieval_mode(value: str | None) -> str:
    mode = str(value or "vector").strip().lower()
    if mode not in VALID_RETRIEVAL_MODES:
        raise ValueError(f"Unknown retrieval mode '{value}'. Choose from: {list(VALID_RETRIEVAL_MODES)}")
    return mode


def _safe_float(value: str | None, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _clamp_hybrid_alpha(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _normalize_rerank_source(value: str | None) -> str:
    source = str(value or DEFAULT_RERANK_SOURCE).strip().lower()
    if source not in VALID_RERANK_SOURCES:
        raise ValueError(f"Unknown rerank source '{value}'. Choose from: {list(VALID_RERANK_SOURCES)}")
    return source


DEFAULT_RETRIEVAL_MODE = _normalize_retrieval_mode(
    os.environ.get("RETRIEVAL_MODE", os.environ.get("WEAVIATE_RETRIEVAL_MODE", "vector"))
)
DEFAULT_HYBRID_ALPHA = _clamp_hybrid_alpha(
    _safe_float(os.environ.get("HYBRID_ALPHA", os.environ.get("WEAVIATE_HYBRID_ALPHA", "0.5")), 0.5)
)
FORCE_CLIENT_HYBRID = os.environ.get("FORCE_CLIENT_HYBRID", "1").strip() not in {
    "0",
    "false",
    "False",
    "no",
    "NO",
}
DEFAULT_RERANK_SOURCE = os.environ.get("RERANK_SOURCE", "lmdb").strip().lower()
if DEFAULT_RERANK_SOURCE not in VALID_RERANK_SOURCES:
    raise ValueError(
        f"Invalid RERANK_SOURCE='{DEFAULT_RERANK_SOURCE}'. Allowed: {list(VALID_RERANK_SOURCES)}"
    )
DEBUG_COMPARE_SAMPLE_N = int(os.environ.get("DEBUG_VECTOR_COMPARE_N", "10"))


@dataclass
class ClaimHit:
    uuid: str
    claim_id: str
    doc_id: str
    claim_type: str = ""
    text: str = ""
    distance: float | None = None
    score: float | None = None


def _post_graphql(query: str) -> dict:
    resp = requests.post(WEAVIATE_GRAPHQL, json={"query": query}, timeout=60)
    if resp.status_code != 200:
        print("STATUS:", resp.status_code)
        print("RESPONSE:", resp.text)
    resp.raise_for_status()
    payload = resp.json()
    if payload.get("errors"):
        raise RuntimeError(payload["errors"])
    return payload["data"]


def _hydrate_claim_hits_from_lmdb(hits: list[ClaimHit]) -> None:
    claim_ids = [h.claim_id for h in hits if h.claim_id]
    if not claim_ids:
        return
    payload_map = load_claim_payloads_from_lmdb(claim_ids)
    for h in hits:
        payload = payload_map.get(h.claim_id)
        if not payload:
            continue
        if not h.doc_id:
            h.doc_id = str(payload.get("doc_id") or "")
        if not h.claim_type:
            h.claim_type = str(payload.get("claim_type") or "")
        h.text = rich_to_plain(str(payload.get("text") or ""))


def _embed_query_dense(query: str) -> np.ndarray:
    # Mean-pooled dense vector for Weaviate nearVector retrieval.
    import torch

    query_text = normalize_text_for_embedding(query)
    tokens = tokenizer(
        query_text,
        return_tensors="pt",
        truncation=True,
        padding="max_length",
        max_length=256,
    )
    tokens = {k: v.to(model.device) for k, v in tokens.items()}
    model.eval()
    with torch.no_grad():
        outputs = model(**tokens)
    token_embeddings = outputs.last_hidden_state.squeeze(0)
    attn_mask = tokens["attention_mask"].squeeze(0).bool()
    masked = token_embeddings[attn_mask]
    if masked.numel() == 0:
        masked = token_embeddings[:1]
    dense = masked.mean(dim=0, keepdim=True).detach().cpu().numpy().astype("float32")
    return dense[0]


def _embed_query_tokens(query: str, shard: str) -> np.ndarray:
    """
    Token-level query embeddings matching the LMDB shard dimensionality.
    """
    shard = assert_128_variant(shard, context="retrieve_rerank._embed_query_tokens")
    variants = embed_query_tokens_for_shard(query, shard=shard, max_length=256)
    arr = np.asarray(variants)
    if arr.ndim == 1:
        arr = arr.reshape(1, -1)
    if arr.ndim != 2 or arr.shape[1] != 128:
        raise ValueError(f"Query token vectors must be [T,128], got {arr.shape}.")
    return arr


def _build_claim_retrieval_args(
    query: str,
    limit: int,
    *,
    shard: str,
    retrieval_mode: str,
    hybrid_alpha: float,
) -> str:
    mode = _normalize_retrieval_mode(retrieval_mode)
    if mode == "bm25":
        return f"bm25: {{query: {json.dumps(query)}}}, limit: {int(limit)}"
    if mode == "hybrid":
        alpha = _clamp_hybrid_alpha(hybrid_alpha)
        # Avoid Weaviate edge-case instability on hybrid alpha=0 by using native BM25.
        if alpha <= 0.0:
            return f"bm25: {{query: {json.dumps(query)}}}, limit: {int(limit)}"
        mv_vecs = _embed_query_tokens(query, shard).tolist()
        if alpha >= 1.0:
            return (
                f'nearVector: {{vector: {mv_vecs}, targetVectors: ["{WEAVIATE_NAMED_VECTOR}"]}}, '
                f"limit: {int(limit)}"
            )
        return (
            "hybrid: {"
            f"query: {json.dumps(query)}, "
            f"alpha: {alpha:.6f}, "
            f"vector: {mv_vecs}, "
            f'targetVectors: ["{WEAVIATE_NAMED_VECTOR}"]'
            f"}}, limit: {int(limit)}"
        )
    mv_vecs = _embed_query_tokens(query, shard).tolist()
    return (
        f'nearVector: {{vector: {mv_vecs}, targetVectors: ["{WEAVIATE_NAMED_VECTOR}"]}}, '
        f"limit: {int(limit)}"
    )


def _query_claim_rows(retrieval_args: str) -> list[dict]:
    gql = (
        "{ Get { Claim("
        f"{retrieval_args}"
        ") { claim_id doc_id _additional { id distance } } } }"
    )
    data = _post_graphql(gql)
    return data.get("Get", {}).get("Claim", []) or []


def fetch_colbert_vectors_from_weaviate(object_ids: list[str]) -> dict[str, np.ndarray]:
    """
    Fetch token-level ColBERT vectors from Weaviate object REST API.
    Endpoint used: GET /v1/objects/Claim/{uuid}?include=vector
    """
    ids = [str(oid).strip() for oid in object_ids if str(oid).strip()]
    if not ids:
        return {}
    sess = requests.Session()
    out: dict[str, np.ndarray] = {}
    for oid in ids:
        url = f"{WEAVIATE_OBJECTS}/Claim/{oid}"
        resp = sess.get(url, params={"include": "vector"}, timeout=60)
        if resp.status_code != 200:
            raise RuntimeError(f"Weaviate vector fetch failed for {oid}: {resp.status_code} {resp.text[:300]}")
        payload = resp.json()
        vectors = payload.get("vectors")
        if not isinstance(vectors, dict):
            raise ValueError(
                f"Weaviate object {oid} missing named vectors map; expected dict with key '{WEAVIATE_NAMED_VECTOR}'."
            )
        if WEAVIATE_NAMED_VECTOR not in vectors:
            raise ValueError(
                f"Weaviate object {oid} missing named vector '{WEAVIATE_NAMED_VECTOR}'. "
                f"Available keys={sorted(vectors.keys())}"
            )
        token_matrix = np.asarray(vectors[WEAVIATE_NAMED_VECTOR], dtype=np.float32)
        if token_matrix.ndim == 1:
            token_matrix = token_matrix.reshape(1, -1)
        if token_matrix.ndim != 2 or token_matrix.shape[0] <= 0:
            raise ValueError(f"Weaviate vector for {oid} is empty or malformed: shape={token_matrix.shape}")
        if token_matrix.shape[1] != 128:
            raise ValueError(
                f"Weaviate vector for {oid} must be 128-d, got shape={token_matrix.shape}."
            )
        out[oid] = token_matrix

    missing = [oid for oid in ids if oid not in out]
    if missing:
        raise RuntimeError(f"Failed to fetch vectors for object ids: {missing}")
    return out


def _rows_to_hits(items: list[dict]) -> list[ClaimHit]:
    hits: list[ClaimHit] = []
    for it in items:
        addl = it.get("_additional") or {}
        hits.append(
            ClaimHit(
                uuid=addl.get("id", ""),
                distance=addl.get("distance"),
                claim_id=it.get("claim_id", ""),
                doc_id=it.get("doc_id", ""),
            )
        )
    return hits


def _claim_key(hit: ClaimHit) -> str:
    return str(hit.claim_id or hit.uuid or hit.doc_id or "")


def _fuse_hybrid_hits(
    vector_hits: list[ClaimHit],
    bm25_hits: list[ClaimHit],
    alpha: float,
    limit: int,
    *,
    rrf_k: int = 60,
) -> list[ClaimHit]:
    alpha = _clamp_hybrid_alpha(alpha)
    weights = {
        "vector": alpha,
        "bm25": 1.0 - alpha,
    }
    score_by_key: dict[str, float] = {}
    hit_by_key: dict[str, ClaimHit] = {}

    for source, hits in (("vector", vector_hits), ("bm25", bm25_hits)):
        w = weights[source]
        if w <= 0.0:
            continue
        for rank, hit in enumerate(hits, start=1):
            key = _claim_key(hit)
            if not key:
                continue
            if key not in hit_by_key:
                hit_by_key[key] = hit
            elif hit_by_key[key].distance is None and hit.distance is not None:
                hit_by_key[key].distance = hit.distance
            score_by_key[key] = score_by_key.get(key, 0.0) + (w / float(rrf_k + rank))

    ranked_keys = sorted(score_by_key, key=lambda k: score_by_key[k], reverse=True)[: int(limit)]
    return [hit_by_key[k] for k in ranked_keys]


def _retrieve_hybrid_client_fusion(
    query: str,
    limit: int,
    shard: str,
    alpha: float,
) -> list[ClaimHit]:
    bm25_args = f"bm25: {{query: {json.dumps(query)}}}, limit: {int(limit)}"
    vec_args = (
        f'nearVector: {{vector: {_embed_query_tokens(query, shard).tolist()}, '
        f'targetVectors: ["{WEAVIATE_NAMED_VECTOR}"]}}, limit: {int(limit)}'
    )
    vector_items: list[dict] = []
    bm25_items: list[dict] = []
    try:
        vector_items = _query_claim_rows(vec_args)
    except Exception as ve:
        print(f"[warn] hybrid nearVector leg failed: {ve}")
    try:
        bm25_items = _query_claim_rows(bm25_args)
    except Exception as be:
        print(f"[warn] hybrid bm25 leg failed: {be}")
    if not vector_items and not bm25_items:
        raise RuntimeError("both hybrid legs failed (nearVector and bm25)")
    return _fuse_hybrid_hits(
        _rows_to_hits(vector_items),
        _rows_to_hits(bm25_items),
        alpha,
        int(limit),
    )


def retrieve_claims(
    query: str,
    limit: int = 200,
    shard: str = "128_f16",
    *,
    retrieval_mode: str = DEFAULT_RETRIEVAL_MODE,
    hybrid_alpha: float = DEFAULT_HYBRID_ALPHA,
) -> list[ClaimHit]:
    shard = assert_128_variant(shard, context="retrieve_claims")
    mode = _normalize_retrieval_mode(retrieval_mode)
    if mode in {"vector", "hybrid"} and shard not in SHARD_TO_PATH:
        raise ValueError(f"Unknown shard '{shard}'. Choose from: {sorted(SHARD_TO_PATH)}")
    alpha = _clamp_hybrid_alpha(hybrid_alpha)
    retrieval_args = _build_claim_retrieval_args(
        query,
        limit,
        shard=shard,
        retrieval_mode=mode,
        hybrid_alpha=alpha,
    )

    if mode == "hybrid" and 0.0 < alpha < 1.0 and FORCE_CLIENT_HYBRID:
        hits = _retrieve_hybrid_client_fusion(query, int(limit), shard, alpha)
        _hydrate_claim_hits_from_lmdb(hits)
        return hits

    try:
        hits = _rows_to_hits(_query_claim_rows(retrieval_args))
    except Exception as e:
        if mode != "hybrid" or alpha <= 0.0 or alpha >= 1.0:
            raise
        print(f"[warn] server-side hybrid failed; using client-side fusion fallback: {e}")
        hits = _retrieve_hybrid_client_fusion(query, int(limit), shard, alpha)

    _hydrate_claim_hits_from_lmdb(hits)
    return hits


def _maxsim_score(query_tokens: np.ndarray, doc_tokens: np.ndarray) -> float:
    if doc_tokens.size == 0 or query_tokens.size == 0:
        return float("-inf")
    qt = query_tokens.astype(np.float32, copy=False)
    dt = doc_tokens.astype(np.float32, copy=False)
    sims = qt @ dt.T
    return float(np.max(sims, axis=1).sum())


def _fmt_score(value: float | None) -> str:
    return "" if value is None else f"{value:.6f}"


def rerank_with_lmdb(
    hits: list[ClaimHit],
    query: str,
    shard: str,
    rerank_k: int = 100,
    query_tokens: np.ndarray | None = None,
) -> list[ClaimHit]:
    shard = assert_128_variant(shard, context="rerank_with_lmdb")
    q_tokens = query_tokens if query_tokens is not None else _embed_query_tokens(query, shard)
    top = hits[: int(rerank_k)]
    rescored: list[ClaimHit] = []
    for h in top:
        lmdb_path = resolve_lmdb_path(shard, doc_id=h.doc_id or None)
        doc_tokens = load_colbert_from_lmdb(lmdb_path, h.claim_id)
        if doc_tokens is None:
            raise RuntimeError(f"Missing LMDB vectors for claim_id={h.claim_id} at {lmdb_path}")
        if np.asarray(doc_tokens).ndim != 2 or np.asarray(doc_tokens).shape[1] != 128:
            raise ValueError(
                f"LMDB vectors for claim_id={h.claim_id} must be [T,128], got {np.asarray(doc_tokens).shape}"
            )
        h.score = _maxsim_score(q_tokens, doc_tokens)
        rescored.append(h)
    rescored.sort(key=lambda x: (x.score if x.score is not None else float("-inf")), reverse=True)
    return rescored + hits[int(rerank_k) :]


def rerank_with_weaviate(
    hits: list[ClaimHit],
    query: str,
    shard: str,
    rerank_k: int = 100,
    query_tokens: np.ndarray | None = None,
) -> list[ClaimHit]:
    shard = assert_128_variant(shard, context="rerank_with_weaviate")
    q_tokens = query_tokens if query_tokens is not None else _embed_query_tokens(query, shard)
    top = hits[: int(rerank_k)]
    object_ids = [h.uuid for h in top]
    if any(not oid for oid in object_ids):
        raise ValueError("All rerank candidates must include Weaviate object UUID for rerank_source=weaviate.")
    vectors_by_object_id = fetch_colbert_vectors_from_weaviate(object_ids)
    rescored: list[ClaimHit] = []
    for h in top:
        doc_tokens = vectors_by_object_id.get(h.uuid)
        if doc_tokens is None:
            raise RuntimeError(f"Missing Weaviate vectors for object id={h.uuid}")
        if doc_tokens.ndim != 2 or doc_tokens.shape[1] != 128:
            raise ValueError(f"Weaviate vectors for object id={h.uuid} must be [T,128], got {doc_tokens.shape}")
        h.score = _maxsim_score(q_tokens, doc_tokens)
        rescored.append(h)
    rescored.sort(key=lambda x: (x.score if x.score is not None else float("-inf")), reverse=True)
    return rescored + hits[int(rerank_k) :]


def rerank_hits(
    hits: list[ClaimHit],
    query: str,
    shard: str,
    rerank_k: int = 100,
    *,
    rerank_source: str = DEFAULT_RERANK_SOURCE,
    query_tokens: np.ndarray | None = None,
) -> list[ClaimHit]:
    source = _normalize_rerank_source(rerank_source)
    if source == "lmdb":
        return rerank_with_lmdb(hits, query, shard=shard, rerank_k=rerank_k, query_tokens=query_tokens)
    return rerank_with_weaviate(hits, query, shard=shard, rerank_k=rerank_k, query_tokens=query_tokens)


def debug_compare_lmdb_vs_weaviate_vectors(
    hits: list[ClaimHit],
    shard: str,
    sample_n: int,
    *,
    max_abs_tol: float = 0.05,
) -> dict[str, float]:
    shard = assert_128_variant(shard, context="debug_compare_lmdb_vs_weaviate_vectors")
    sample_pool = [h for h in hits if h.uuid and h.claim_id]
    if not sample_pool:
        raise ValueError("No candidates with both uuid and claim_id available for vector comparison.")
    n = min(int(sample_n), len(sample_pool))
    sampled = random.sample(sample_pool, n)
    obj_ids = [h.uuid for h in sampled]
    weaviate_vecs = fetch_colbert_vectors_from_weaviate(obj_ids)
    diffs: list[float] = []
    for h in sampled:
        lmdb_path = resolve_lmdb_path(shard, doc_id=h.doc_id or None)
        lmdb_vec = load_colbert_from_lmdb(lmdb_path, h.claim_id)
        if lmdb_vec is None:
            raise RuntimeError(f"LMDB vector missing for claim_id={h.claim_id}")
        wv_vec = weaviate_vecs.get(h.uuid)
        if wv_vec is None:
            raise RuntimeError(f"Weaviate vector missing for object_id={h.uuid}")
        lmdb_arr = np.asarray(lmdb_vec, dtype=np.float32)
        if lmdb_arr.ndim == 1:
            lmdb_arr = lmdb_arr.reshape(1, -1)
        if lmdb_arr.shape != wv_vec.shape:
            raise ValueError(
                f"Shape mismatch claim_id={h.claim_id}: lmdb={lmdb_arr.shape} weaviate={wv_vec.shape}"
            )
        max_abs = float(np.max(np.abs(lmdb_arr - wv_vec)))
        diffs.append(max_abs)
    stats = {
        "n": float(n),
        "max_abs_min": float(np.min(diffs)),
        "max_abs_mean": float(np.mean(diffs)),
        "max_abs_p95": float(np.percentile(diffs, 95)),
        "max_abs_max": float(np.max(diffs)),
    }
    print(
        "[debug-compare] n={n} max_abs(min/mean/p95/max)="
        "{minv:.6f}/{meanv:.6f}/{p95:.6f}/{maxv:.6f}".format(
            n=int(stats["n"]),
            minv=stats["max_abs_min"],
            meanv=stats["max_abs_mean"],
            p95=stats["max_abs_p95"],
            maxv=stats["max_abs_max"],
        )
    )
    if stats["max_abs_max"] > float(max_abs_tol):
        raise ValueError(
            f"LMDB vs Weaviate vector mismatch too large: max_abs={stats['max_abs_max']:.6f} > {max_abs_tol}"
        )
    return stats


def lookup_patent(doc_id: str, limit: int = 200) -> list[ClaimHit]:
    where = (
        "{path:[\"doc_id\"],operator:Equal,valueText:"
        f"\"{doc_id}\"}}"
    )
    gql = (
        "{ Get { Claim("
        f"where:{where}, limit:{int(limit)}"
        ") { claim_id doc_id _additional { id } } } }"
    )
    data = _post_graphql(gql)
    items = data["Get"]["Claim"]
    hits: list[ClaimHit] = []
    for it in items:
        addl = it.get("_additional") or {}
        hits.append(
            ClaimHit(
                uuid=addl.get("id", ""),
                claim_id=it.get("claim_id", ""),
                doc_id=it.get("doc_id", ""),
            )
        )
    _hydrate_claim_hits_from_lmdb(hits)
    return hits


def _claim_id_exists(claim_id: str) -> bool:
    where = (
        "{path:[\"claim_id\"],operator:Equal,valueText:"
        f"\"{claim_id}\"}}"
    )
    gql = (
        "{ Get { Claim("
        f"where:{where}, limit:1"
        ") { claim_id } } }"
    )
    data = _post_graphql(gql)
    return bool(data.get("Get", {}).get("Claim"))


def precision_at_k(ranked_ids: list[str], relevant: set[str], k: int) -> float:
    if k <= 0:
        return 0.0
    top = ranked_ids[:k]
    if not top:
        return 0.0
    hits = sum(1 for rid in top if rid in relevant)
    return hits / float(len(top))


def recall_at_k(ranked_ids: list[str], relevant: set[str], k: int) -> float:
    if not relevant:
        return 0.0
    top = ranked_ids[:k]
    hits = sum(1 for rid in top if rid in relevant)
    return hits / float(len(relevant))


def ndcg_at_k(ranked_ids: list[str], relevant: set[str], k: int) -> float:
    def dcg(ids: Iterable[str]) -> float:
        total = 0.0
        for i, rid in enumerate(ids, start=1):
            rel = 1.0 if rid in relevant else 0.0
            if rel > 0:
                total += rel / math.log2(i + 1.0)
        return total

    top = ranked_ids[:k]
    if not top:
        return 0.0
    ideal = [1.0] * min(len(relevant), k)
    idcg = sum(rel / math.log2(i + 1.0) for i, rel in enumerate(ideal, start=1))
    if idcg == 0:
        return 0.0
    return dcg(top) / idcg


def mrr_at_k(ranked_ids: list[str], relevant: set[str], k: int) -> float:
    for i, rid in enumerate(ranked_ids[:k], start=1):
        if rid in relevant:
            return 1.0 / float(i)
    return 0.0


def _first_relevant_rank(ranked_ids: list[str], relevant: set[str]) -> int | None:
    for i, rid in enumerate(ranked_ids, start=1):
        if rid in relevant:
            return i
    return None


def _write_per_query_csv(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    relevant_claim_cols = [f"relevant_claim_{i}" for i in range(1, 11)]
    relevant_claim_maxsim_cols = [f"relevant_claim_{i}_maxsim" for i in range(1, 11)]
    reranked_claim_id_cols = [f"reranked_top{i}_claim_id" for i in range(1, 11)]
    reranked_claim_maxsim_cols = [f"reranked_top{i}_maxsim" for i in range(1, 11)]
    reranked_claim_text_cols = [f"reranked_top{i}_claim_text" for i in range(1, 11)]
    reranked_claim_rel_cols = [f"reranked_top{i}_is_relevant" for i in range(1, 11)]
    fieldnames = [
        "status",
        "query",
        "num_relevant",
        "relevant_claim_extra_count",
        *relevant_claim_cols,
        *relevant_claim_maxsim_cols,
        "candidate_k",
        "rerank_k",
        "candidate_hit",
        "candidate_hits_count",
        "candidate_first_relevant_rank",
        "candidate_relevant_ranks",
        "reranked_hit_at_10",
        "reranked_hits_at_10",
        "reranked_first_relevant_rank",
        "reranked_relevant_ranks_at_10",
        "precision@10",
        "recall@10",
        "ndcg@10",
        "mrr@10",
        *reranked_claim_id_cols,
        *reranked_claim_maxsim_cols,
        *reranked_claim_rel_cols,
        *reranked_claim_text_cols,
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _write_per_query_topk_csv(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "status",
        "query",
        "num_relevant",
        "relevant_claim_ids",
        "candidate_k",
        "rerank_k",
        "rank",
        "claim_id",
        "doc_id",
        "claim_type",
        "score",
        "distance",
        "is_relevant",
        "text",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def evaluate(
    queries_path: Path,
    qrels_path: Path,
    retrieve_shard: str,
    rerank_shard: str,
    limit: int,
    rerank_k: int,
    *,
    retrieval_mode: str = DEFAULT_RETRIEVAL_MODE,
    hybrid_alpha: float = DEFAULT_HYBRID_ALPHA,
    rerank_source: str = DEFAULT_RERANK_SOURCE,
    debug_compare_vectors: bool = False,
    debug_compare_n: int = DEBUG_COMPARE_SAMPLE_N,
    debug_compare_max_abs_tol: float = 0.05,
    filter_missing_qrels: bool = True,
    per_query_csv: Path | None = None,
    per_query_topk_csv: Path | None = None,
) -> dict:
    retrieval_mode = _normalize_retrieval_mode(retrieval_mode)
    hybrid_alpha = _clamp_hybrid_alpha(hybrid_alpha)
    rerank_source = _normalize_rerank_source(rerank_source)
    rerank_shard = assert_128_variant(rerank_shard, context="evaluate.rerank_shard")
    retrieve_shard = assert_128_variant(retrieve_shard, context="evaluate.retrieve_shard")
    with queries_path.open("r", encoding="utf-8") as f:
        queries = [json.loads(line) for line in f if line.strip()]
    with qrels_path.open("r", encoding="utf-8") as f:
        qrels = {row["query"]: set(row.get("relevant_claim_ids", [])) for row in (json.loads(line) for line in f if line.strip())}

    candidate_hit_metric = f"candidate_hit@{int(limit)}"
    metrics = {
        "precision@10": [],
        "recall@10": [],
        "ndcg@10": [],
        "mrr@10": [],
        candidate_hit_metric: [],
    }
    per_query_rows: list[dict] = []
    per_query_topk_rows: list[dict] = []
    total_q = len(queries)
    if filter_missing_qrels:
        cache: dict[str, bool] = {}
        filtered = []
        dropped = 0
        for row in queries:
            q = row.get("query", "")
            rel = qrels.get(q, set())
            keep = False
            for claim_id in rel:
                if claim_id not in cache:
                    cache[claim_id] = _claim_id_exists(claim_id)
                if cache[claim_id]:
                    keep = True
                    break
            if keep:
                filtered.append(row)
            else:
                dropped += 1
                if per_query_csv is not None:
                    sorted_rel = sorted(rel)
                    row_out = {
                        "status": "filtered_missing_qrels",
                        "query": q,
                        "num_relevant": len(rel),
                        "relevant_claim_extra_count": max(0, len(sorted_rel) - 10),
                        "candidate_k": int(limit),
                        "rerank_k": int(rerank_k),
                        "candidate_hit": False,
                        "candidate_hits_count": 0,
                        "candidate_first_relevant_rank": "",
                        "candidate_relevant_ranks": "",
                        "reranked_hit_at_10": False,
                        "reranked_hits_at_10": 0,
                        "reranked_first_relevant_rank": "",
                        "reranked_relevant_ranks_at_10": "",
                        "precision@10": 0.0,
                        "recall@10": 0.0,
                        "ndcg@10": 0.0,
                        "mrr@10": 0.0,
                    }
                    for idx in range(1, 11):
                        row_out[f"relevant_claim_{idx}"] = sorted_rel[idx - 1] if idx <= len(sorted_rel) else ""
                        row_out[f"relevant_claim_{idx}_maxsim"] = ""
                        row_out[f"reranked_top{idx}_claim_id"] = ""
                        row_out[f"reranked_top{idx}_maxsim"] = ""
                        row_out[f"reranked_top{idx}_is_relevant"] = False
                        row_out[f"reranked_top{idx}_claim_text"] = ""
                    per_query_rows.append(row_out)
                if per_query_topk_csv is not None:
                    for rank in range(1, 11):
                        sorted_rel = sorted(rel)
                        per_query_topk_rows.append(
                            {
                                "status": "filtered_missing_qrels",
                                "query": q,
                                "num_relevant": len(rel),
                                "relevant_claim_ids": "|".join(sorted(rel)),
                                "candidate_k": int(limit),
                                "rerank_k": int(rerank_k),
                                "rank": rank,
                                "claim_id": "",
                                "doc_id": "",
                                "claim_type": "",
                                "score": "",
                                "distance": "",
                                "is_relevant": False,
                                "text": "",
                            }
                        )
        queries = filtered
        total_q = len(queries)
        print(f"[eval] filtered {dropped} query(ies) with no relevant claims in index")
    for i, row in enumerate(queries, start=1):
        q = row.get("query", "")
        if not q:
            continue
        print(f"[eval] {i}/{total_q} retrieving + reranking")
        rel = qrels.get(q, set())
        hits = retrieve_claims(
            q,
            limit=limit,
            shard=retrieve_shard,
            retrieval_mode=retrieval_mode,
            hybrid_alpha=hybrid_alpha,
        )
        candidate_ids = [h.claim_id for h in hits]
        candidate_ranks = [idx for idx, cid in enumerate(candidate_ids, start=1) if cid in rel]
        candidate_hit = bool(candidate_ranks)
        q_tokens = _embed_query_tokens(q, rerank_shard)
        claim_id_to_uuid = {h.claim_id: h.uuid for h in hits if h.claim_id and h.uuid}
        weaviate_vec_cache: dict[str, np.ndarray] = {}
        maxsim_cache: dict[str, float | None] = {}

        def _claim_maxsim(claim_id: str) -> float | None:
            if not claim_id:
                return None
            cached = maxsim_cache.get(claim_id)
            if cached is not None or claim_id in maxsim_cache:
                return cached
            if rerank_source == "weaviate":
                obj_id = claim_id_to_uuid.get(claim_id)
                if not obj_id:
                    maxsim_cache[claim_id] = None
                    return None
                if obj_id not in weaviate_vec_cache:
                    fetched = fetch_colbert_vectors_from_weaviate([obj_id])
                    weaviate_vec_cache.update(fetched)
                doc_tokens = weaviate_vec_cache.get(obj_id)
                if doc_tokens is None:
                    raise RuntimeError(
                        f"Missing Weaviate vectors for object_id={obj_id} claim_id={claim_id}"
                    )
            else:
                lmdb_path = resolve_lmdb_path(rerank_shard)
                doc_tokens = load_colbert_from_lmdb(lmdb_path, claim_id)
                if doc_tokens is None:
                    maxsim_cache[claim_id] = None
                    return None
            arr = np.asarray(doc_tokens)
            if arr.ndim == 1:
                arr = arr.reshape(1, -1)
            if arr.ndim != 2 or arr.shape[1] != 128:
                raise ValueError(f"MaxSim vectors must be [T,128], got shape={arr.shape} for claim_id={claim_id}")
            score = _maxsim_score(q_tokens, doc_tokens)
            maxsim_cache[claim_id] = score
            return score

        ranked = rerank_hits(
            hits,
            q,
            shard=rerank_shard,
            rerank_k=rerank_k,
            rerank_source=rerank_source,
            query_tokens=q_tokens,
        )
        if debug_compare_vectors and rerank_source == "weaviate":
            debug_compare_lmdb_vs_weaviate_vectors(
                ranked[: max(1, rerank_k)],
                rerank_shard,
                sample_n=debug_compare_n,
                max_abs_tol=debug_compare_max_abs_tol,
            )
        ranked_ids = [h.claim_id for h in ranked]
        p10 = precision_at_k(ranked_ids, rel, 10)
        r10 = recall_at_k(ranked_ids, rel, 10)
        n10 = ndcg_at_k(ranked_ids, rel, 10)
        m10 = mrr_at_k(ranked_ids, rel, 10)
        metrics["precision@10"].append(p10)
        metrics["recall@10"].append(r10)
        metrics["ndcg@10"].append(n10)
        metrics["mrr@10"].append(m10)
        metrics[candidate_hit_metric].append(1.0 if candidate_hit else 0.0)

        if per_query_csv is not None:
            sorted_rel = sorted(rel)
            reranked_top10 = ranked[:10]
            reranked_top10_ids = [h.claim_id for h in reranked_top10]
            reranked_top10_relevant = [cid for cid in reranked_top10_ids if cid in rel]
            reranked_top10_ranks = [idx for idx, cid in enumerate(reranked_top10_ids, start=1) if cid in rel]
            row_out = {
                "status": "evaluated",
                "query": q,
                "num_relevant": len(rel),
                "relevant_claim_extra_count": max(0, len(sorted_rel) - 10),
                "candidate_k": int(limit),
                "rerank_k": int(rerank_k),
                "candidate_hit": candidate_hit,
                "candidate_hits_count": len(candidate_ranks),
                "candidate_first_relevant_rank": candidate_ranks[0] if candidate_ranks else "",
                "candidate_relevant_ranks": "|".join(str(r) for r in candidate_ranks),
                "reranked_hit_at_10": bool(reranked_top10_relevant),
                "reranked_hits_at_10": len(reranked_top10_relevant),
                "reranked_first_relevant_rank": _first_relevant_rank(ranked_ids, rel) or "",
                "reranked_relevant_ranks_at_10": "|".join(str(r) for r in reranked_top10_ranks),
                "precision@10": p10,
                "recall@10": r10,
                "ndcg@10": n10,
                "mrr@10": m10,
            }
            for idx in range(1, 11):
                row_out[f"relevant_claim_{idx}"] = sorted_rel[idx - 1] if idx <= len(sorted_rel) else ""
                rel_claim = sorted_rel[idx - 1] if idx <= len(sorted_rel) else ""
                row_out[f"relevant_claim_{idx}_maxsim"] = _fmt_score(_claim_maxsim(rel_claim))
                if idx <= len(reranked_top10):
                    hit = reranked_top10[idx - 1]
                    row_out[f"reranked_top{idx}_claim_id"] = hit.claim_id
                    hit_score = hit.score if hit.score is not None else _claim_maxsim(hit.claim_id)
                    row_out[f"reranked_top{idx}_maxsim"] = _fmt_score(hit_score)
                    row_out[f"reranked_top{idx}_is_relevant"] = hit.claim_id in rel
                    row_out[f"reranked_top{idx}_claim_text"] = hit.text
                else:
                    row_out[f"reranked_top{idx}_claim_id"] = ""
                    row_out[f"reranked_top{idx}_maxsim"] = ""
                    row_out[f"reranked_top{idx}_is_relevant"] = False
                    row_out[f"reranked_top{idx}_claim_text"] = ""
            per_query_rows.append(row_out)
        if per_query_topk_csv is not None:
            sorted_rel = "|".join(sorted(rel))
            top10_hits = ranked[:10]
            for rank, h in enumerate(top10_hits, start=1):
                per_query_topk_rows.append(
                    {
                        "status": "evaluated",
                        "query": q,
                        "num_relevant": len(rel),
                        "relevant_claim_ids": sorted_rel,
                        "candidate_k": int(limit),
                        "rerank_k": int(rerank_k),
                        "rank": rank,
                        "claim_id": h.claim_id,
                        "doc_id": h.doc_id,
                        "claim_type": h.claim_type,
                        "score": _fmt_score(h.score if h.score is not None else _claim_maxsim(h.claim_id)),
                        "distance": "" if h.distance is None else f"{h.distance:.6f}",
                        "is_relevant": h.claim_id in rel,
                        "text": h.text,
                    }
                )
            if len(top10_hits) < 10:
                for rank in range(len(top10_hits) + 1, 11):
                    per_query_topk_rows.append(
                        {
                            "status": "evaluated",
                            "query": q,
                            "num_relevant": len(rel),
                            "relevant_claim_ids": sorted_rel,
                            "candidate_k": int(limit),
                            "rerank_k": int(rerank_k),
                            "rank": rank,
                            "claim_id": "",
                            "doc_id": "",
                            "claim_type": "",
                            "score": "",
                            "distance": "",
                            "is_relevant": False,
                            "text": "",
                        }
                    )

    if per_query_csv is not None:
        _write_per_query_csv(per_query_rows, per_query_csv)
        print(f"Wrote per-query diagnostics to {per_query_csv}")
    if per_query_topk_csv is not None:
        _write_per_query_topk_csv(per_query_topk_rows, per_query_topk_csv)
        print(f"Wrote per-query top-10 reranked claims to {per_query_topk_csv}")

    return {k: (sum(v) / len(v) if v else 0.0) for k, v in metrics.items()}


def evaluate_sweep(
    queries_path: Path,
    qrels_path: Path,
    retrieve_shard: str,
    rerank_shards: list[str],
    limit: int,
    rerank_k: int,
    *,
    retrieval_mode: str = DEFAULT_RETRIEVAL_MODE,
    hybrid_alpha: float = DEFAULT_HYBRID_ALPHA,
    rerank_source: str = DEFAULT_RERANK_SOURCE,
    filter_missing_qrels: bool = True,
) -> list[dict]:
    results: list[dict] = []
    for shard in rerank_shards:
        scores = evaluate(
            queries_path,
            qrels_path,
            retrieve_shard=retrieve_shard,
            rerank_shard=shard,
            limit=limit,
            rerank_k=rerank_k,
            retrieval_mode=retrieval_mode,
            hybrid_alpha=hybrid_alpha,
            rerank_source=rerank_source,
            filter_missing_qrels=filter_missing_qrels,
        )
        row = {"rerank_shard": shard, **scores}
        results.append(row)
    return results


def _print_hits(hits: list[ClaimHit], k: int = 10):
    for i, h in enumerate(hits[:k], start=1):
        score = f"{h.score:.3f}" if h.score is not None else "-"
        dist = f"{h.distance:.4f}" if h.distance is not None else "-"
        print(f"{i:02d} score={score} dist={dist} claim_id={h.claim_id} doc_id={h.doc_id} type={h.claim_type}")
        print(f"    {h.text[:200]}")


def _write_hits_csv(hits: list[ClaimHit], path: Path, k: int = 10):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["rank", "score", "distance", "claim_id", "doc_id", "claim_type", "text"])
        for i, h in enumerate(hits[:k], start=1):
            writer.writerow(
                [
                    i,
                    "" if h.score is None else f"{h.score:.6f}",
                    "" if h.distance is None else f"{h.distance:.6f}",
                    h.claim_id,
                    h.doc_id,
                    h.claim_type,
                    h.text,
                ]
            )


def main():
    parser = argparse.ArgumentParser(description="Retrieve + rerank claims with shard selection.")
    parser.add_argument("--query", type=str, default="", help="Query text for retrieval.")
    parser.add_argument("--limit", type=int, default=200, help="Initial retrieval limit.")
    parser.add_argument("--rerank-k", type=int, default=100, help="How many initial hits to rerank.")
    parser.add_argument(
        "--retrieval-mode",
        type=str,
        default=DEFAULT_RETRIEVAL_MODE,
        choices=list(VALID_RETRIEVAL_MODES),
        help="First-stage retrieval mode in Weaviate.",
    )
    parser.add_argument(
        "--hybrid-alpha",
        type=float,
        default=DEFAULT_HYBRID_ALPHA,
        help="Hybrid interpolation weight (0=bm25 only, 1=vector only).",
    )
    parser.add_argument("--save-before-csv", type=Path, default=None, help="Save pre-rerank top-k to CSV.")
    parser.add_argument("--save-after-csv", type=Path, default=None, help="Save reranked top-k to CSV.")
    parser.add_argument("--save-k", type=int, default=10, help="How many rows to write to CSV outputs.")
    parser.add_argument(
        "--retrieve-shard",
        type=str,
        default=os.environ.get("WEAVIATE_SHARD", "128_f16"),
        choices=sorted(SHARD_TO_PATH.keys()),
        help="Which shard to use for Weaviate retrieval (must match index dimension).",
    )
    parser.add_argument(
        "--rerank-shard",
        type=str,
        default=os.environ.get("COLBERT_SHARD", "128_f16"),
        choices=sorted(SHARD_TO_PATH.keys()),
        help="Which ColBERT shard to use for reranking.",
    )
    parser.add_argument(
        "--rerank-source",
        type=str,
        default=DEFAULT_RERANK_SOURCE,
        choices=list(VALID_RERANK_SOURCES),
        help="Source for token vectors during reranking.",
    )
    parser.add_argument(
        "--debug-compare-vectors",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="When rerank-source=weaviate, compare fetched vectors against LMDB vectors.",
    )
    parser.add_argument(
        "--debug-compare-n",
        type=int,
        default=DEBUG_COMPARE_SAMPLE_N,
        help="Sample size for LMDB vs Weaviate vector comparison.",
    )
    parser.add_argument(
        "--debug-compare-max-abs-tol",
        type=float,
        default=0.05,
        help="Max allowed absolute difference for LMDB vs Weaviate debug comparison.",
    )
    parser.add_argument("--doc-id", type=str, default="", help="Lookup claims by patent doc_id.")
    parser.add_argument("--queries", type=Path, default=None, help="Path to JSONL queries for evaluation.")
    parser.add_argument("--qrels", type=Path, default=None, help="Path to JSONL qrels for evaluation.")
    parser.add_argument("--metrics-csv", type=Path, default=None, help="Write evaluation metrics to CSV.")
    parser.add_argument(
        "--per-query-csv",
        type=Path,
        default=None,
        help="Write per-query diagnostics CSV (coverage, relevant ranks, and top-10 IDs).",
    )
    parser.add_argument(
        "--per-query-top10-csv",
        type=Path,
        default=None,
        help="Write one row per query per reranked rank (1-10) with claim metadata.",
    )
    parser.add_argument(
        "--sweep-rerank-shards",
        action="store_true",
        help="Run evaluation once per rerank shard and write a CSV.",
    )
    parser.add_argument(
        "--sweep-csv",
        type=Path,
        default=None,
        help="Output CSV path for sweep results (required with --sweep-rerank-shards).",
    )
    parser.add_argument(
        "--filter-missing-qrels",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Drop queries whose relevant claim_ids are not present in Weaviate.",
    )
    args = parser.parse_args()
    args.hybrid_alpha = _clamp_hybrid_alpha(args.hybrid_alpha)
    args.rerank_source = _normalize_rerank_source(args.rerank_source)
    args.retrieve_shard = assert_128_variant(args.retrieve_shard, context="main.retrieve_shard")
    args.rerank_shard = assert_128_variant(args.rerank_shard, context="main.rerank_shard")

    if args.doc_id:
        hits = lookup_patent(args.doc_id)
        print(f"Found {len(hits)} claims for doc_id={args.doc_id}")
        _print_hits(hits, k=min(10, len(hits)))
        return

    if args.queries and args.qrels:
        candidate_hit_metric = f"candidate_hit@{int(args.limit)}"
        if args.sweep_rerank_shards:
            if not args.sweep_csv:
                raise SystemExit("Provide --sweep-csv when using --sweep-rerank-shards.")
            if args.per_query_csv:
                raise SystemExit("--per-query-csv is not supported with --sweep-rerank-shards.")
            if args.per_query_top10_csv:
                raise SystemExit("--per-query-top10-csv is not supported with --sweep-rerank-shards.")
            rerank_shards = sorted(SHARD_TO_PATH.keys())
            results = evaluate_sweep(
                args.queries,
                args.qrels,
                retrieve_shard=args.retrieve_shard,
                rerank_shards=rerank_shards,
                limit=args.limit,
                rerank_k=args.rerank_k,
                retrieval_mode=args.retrieval_mode,
                hybrid_alpha=args.hybrid_alpha,
                rerank_source=args.rerank_source,
                filter_missing_qrels=args.filter_missing_qrels,
            )
            args.sweep_csv.parent.mkdir(parents=True, exist_ok=True)
            with args.sweep_csv.open("w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(
                    [
                        "rerank_shard",
                        "precision@10",
                        "recall@10",
                        "ndcg@10",
                        "mrr@10",
                        candidate_hit_metric,
                    ]
                )
                for row in results:
                    writer.writerow(
                        [
                            row.get("rerank_shard"),
                            row.get("precision@10", 0.0),
                            row.get("recall@10", 0.0),
                            row.get("ndcg@10", 0.0),
                            row.get("mrr@10", 0.0),
                            row.get(candidate_hit_metric, 0.0),
                        ]
                    )
            print(f"Wrote sweep results to {args.sweep_csv}")
        else:
            scores = evaluate(
                args.queries,
                args.qrels,
                retrieve_shard=args.retrieve_shard,
                rerank_shard=args.rerank_shard,
                limit=args.limit,
                rerank_k=args.rerank_k,
                retrieval_mode=args.retrieval_mode,
                hybrid_alpha=args.hybrid_alpha,
                rerank_source=args.rerank_source,
                debug_compare_vectors=args.debug_compare_vectors,
                debug_compare_n=args.debug_compare_n,
                debug_compare_max_abs_tol=args.debug_compare_max_abs_tol,
                filter_missing_qrels=args.filter_missing_qrels,
                per_query_csv=args.per_query_csv,
                per_query_topk_csv=args.per_query_top10_csv,
            )
            print(json.dumps(scores, indent=2))
            if args.metrics_csv:
                args.metrics_csv.parent.mkdir(parents=True, exist_ok=True)
                with args.metrics_csv.open("w", encoding="utf-8", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(["precision@10", "recall@10", "ndcg@10", "mrr@10", candidate_hit_metric])
                    writer.writerow(
                        [
                            scores.get("precision@10", 0.0),
                            scores.get("recall@10", 0.0),
                            scores.get("ndcg@10", 0.0),
                            scores.get("mrr@10", 0.0),
                            scores.get(candidate_hit_metric, 0.0),
                        ]
                    )
                print(f"Wrote metrics to {args.metrics_csv}")
        return

    if not args.query:
        raise SystemExit("Provide --query, or --doc-id, or (--queries and --qrels).")

    hits = retrieve_claims(
        args.query,
        limit=args.limit,
        shard=args.retrieve_shard,
        retrieval_mode=args.retrieval_mode,
        hybrid_alpha=args.hybrid_alpha,
    )
    reranked = rerank_hits(
        hits,
        args.query,
        shard=args.rerank_shard,
        rerank_k=args.rerank_k,
        rerank_source=args.rerank_source,
    )
    if args.debug_compare_vectors and args.rerank_source == "weaviate":
        debug_compare_lmdb_vs_weaviate_vectors(
            reranked[: max(1, args.rerank_k)],
            args.rerank_shard,
            sample_n=args.debug_compare_n,
            max_abs_tol=args.debug_compare_max_abs_tol,
        )
    print(
        f"Retrieved {len(hits)} hits; reranked top {args.rerank_k} "
        f"using mode={args.retrieval_mode} alpha={args.hybrid_alpha:.3f} "
        f"retrieve_shard={args.retrieve_shard} rerank_shard={args.rerank_shard} "
        f"rerank_source={args.rerank_source}"
    )
    _print_hits(reranked, k=10)
    if args.save_before_csv:
        _write_hits_csv(hits, args.save_before_csv, k=max(1, args.save_k))
        print(f"Saved pre-rerank results to {args.save_before_csv}")
    if args.save_after_csv:
        _write_hits_csv(reranked, args.save_after_csv, k=max(1, args.save_k))
        print(f"Saved reranked results to {args.save_after_csv}")


if __name__ == "__main__":
    main()
