import json
import os
from typing import Any, Dict, List, Optional

import numpy as np
import requests
from langchain.tools import tool

from backend.app.services.download import rich_to_plain
from backend.app.store import (
    LMDB_PATH_128_F16,
    LMDB_PATH_128_F32,
    load_claim_payloads_from_lmdb,
    load_colbert_from_lmdb,
    load_patent_metadata_batch_from_lmdb,
    resolve_lmdb_path,
)
from backend.app.vector_config import WEAVIATE_NAMED_VECTOR, assert_128_variant

WEAVIATE_GRAPHQL = os.environ.get("WEAVIATE_GRAPHQL", "http://localhost:8080/v1/graphql")
DEFAULT_LIMIT = int(os.environ.get("RETRIEVAL_K", "5"))
DEFAULT_CANDIDATE_LIMIT = int(os.environ.get("RETRIEVAL_CANDIDATES", str(max(DEFAULT_LIMIT, 400))))
RERANK_SHARD = assert_128_variant(
    os.environ.get("COLBERT_SHARD", "128_f16").lower(),
    context="orchestrator.RERANK_SHARD",
)
RETRIEVE_SHARD = assert_128_variant(
    os.environ.get("WEAVIATE_SHARD", RERANK_SHARD).lower(),
    context="orchestrator.RETRIEVE_SHARD",
)
RERANK_K = int(os.environ.get("RERANK_K", str(max(DEFAULT_LIMIT, 200))))
_retrieval_mode_env = os.environ.get("RETRIEVAL_MODE", os.environ.get("WEAVIATE_RETRIEVAL_MODE", "vector"))
RETRIEVAL_MODE = str(_retrieval_mode_env or "vector").strip().lower()
if RETRIEVAL_MODE not in {"vector", "bm25", "hybrid"}:
    raise ValueError(
        f"Invalid RETRIEVAL_MODE='{RETRIEVAL_MODE}'. Allowed: vector, bm25, hybrid."
    )
try:
    HYBRID_ALPHA = float(os.environ.get("HYBRID_ALPHA", os.environ.get("WEAVIATE_HYBRID_ALPHA", "0.5")))
except (TypeError, ValueError):
    HYBRID_ALPHA = 0.5
HYBRID_ALPHA = max(0.0, min(1.0, HYBRID_ALPHA))
FORCE_CLIENT_HYBRID = os.environ.get("FORCE_CLIENT_HYBRID", "1").strip() not in {
    "0",
    "false",
    "False",
    "no",
    "NO",
}

SHARD_TO_PATH = {
    "128_f16": LMDB_PATH_128_F16,
    "128_f32": LMDB_PATH_128_F32,
}


def _embed_query_colbert(query: str) -> List[List[float]]:
    from backend.app.embed import (
        embed_query_tokens_for_shard as shared_embed_query_tokens_for_shard,
        normalize_text_for_embedding,
    )

    query_text = normalize_text_for_embedding(query)
    vecs = np.asarray(
        shared_embed_query_tokens_for_shard(query_text, shard=RETRIEVE_SHARD, max_length=256),
        dtype=np.float32,
    )
    if vecs.ndim == 1:
        vecs = vecs.reshape(1, -1)
    return vecs.tolist()


def _embed_query_tokens_for_shard(query: str, shard: str) -> np.ndarray:
    from backend.app.embed import (
        embed_query_tokens_for_shard as shared_embed_query_tokens_for_shard,
        normalize_text_for_embedding,
    )

    shard = assert_128_variant(shard, context="orchestrator._embed_query_tokens_for_shard")
    if shard not in SHARD_TO_PATH:
        raise ValueError(f"Unknown shard '{shard}'. Choose from: {sorted(SHARD_TO_PATH)}")
    query_text = normalize_text_for_embedding(query)
    vecs = np.asarray(shared_embed_query_tokens_for_shard(query_text, shard=shard, max_length=256))
    if vecs.ndim == 1:
        vecs = vecs.reshape(1, -1)
    return vecs


def _post_graphql(query: str) -> Dict[str, Any]:
    resp = requests.post(WEAVIATE_GRAPHQL, json={"query": query}, timeout=60)
    resp.raise_for_status()
    payload = resp.json()
    if payload.get("errors"):
        raise RuntimeError(payload["errors"])
    return payload.get("data", {})


def _escape_text(value: str) -> str:
    return json.dumps(value)


def _extract_doc_id_filters(where_filter: Optional[Dict[str, Any]]) -> List[str]:
    if not where_filter:
        return []
    out: List[str] = []

    def walk(node: Any):
        if not isinstance(node, dict):
            return
        if "$and" in node and isinstance(node["$and"], list):
            for child in node["$and"]:
                walk(child)
            return
        if "$or" in node and isinstance(node["$or"], list):
            for child in node["$or"]:
                walk(child)
            return
        doc = node.get("doc_id")
        if isinstance(doc, str) and doc.strip():
            out.append(doc.strip())
            return
        if isinstance(doc, dict):
            for k, v in doc.items():
                if k in {"$regex", "$contains"} and isinstance(v, str) and v.strip():
                    out.append(v.strip())
                elif k == "$eq" and isinstance(v, str) and v.strip():
                    out.append(v.strip())

    walk(where_filter)
    dedup: List[str] = []
    seen = set()
    for item in out:
        if item not in seen:
            seen.add(item)
            dedup.append(item)
    return dedup


def _build_claim_where(doc_ids: List[str]) -> str:
    if not doc_ids:
        return ""
    operands = []
    for doc_id in doc_ids:
        pattern = f"*{doc_id}*"
        operands.append(
            "{path:[\"doc_id\"],operator:Like,valueText:%s}" % _escape_text(pattern)
        )
    return "where:{operator:Or,operands:[%s]}," % ",".join(operands)


def _build_retrieval_clause(query: str, mode: str, hybrid_alpha: float, query_vector: List[List[float]]) -> str:
    if mode == "bm25":
        return f"bm25:{{query:{_escape_text(query)}}},"
    if mode == "hybrid":
        alpha = max(0.0, min(1.0, float(hybrid_alpha)))
        # Avoid Weaviate edge-case instability on hybrid alpha=0 by using native BM25.
        if alpha <= 0.0:
            return f"bm25:{{query:{_escape_text(query)}}},"
        if alpha >= 1.0:
            return f'nearVector:{{vector:{json.dumps(query_vector)},targetVectors:["{WEAVIATE_NAMED_VECTOR}"]}},'
        return (
            "hybrid:{"
            f"query:{_escape_text(query)},"
            f"alpha:{alpha:.6f},"
            f"vector:{json.dumps(query_vector)},"
            f'targetVectors:["{WEAVIATE_NAMED_VECTOR}"]'
            "},"
        )
    return f'nearVector:{{vector:{json.dumps(query_vector)},targetVectors:["{WEAVIATE_NAMED_VECTOR}"]}},'


def _query_claim_rows(retrieval_clause: str, claim_where: str, limit: int) -> List[Dict[str, Any]]:
    gql = (
        "{ Get { Claim("
        f"{retrieval_clause}"
        f"{claim_where} limit: {int(limit)}"
        ") { claim_id doc_id _additional { id distance } } } }"
    )
    data = _post_graphql(gql)
    return data.get("Get", {}).get("Claim", []) or []


def _claim_row_key(hit: Dict[str, Any]) -> str:
    addl = hit.get("_additional") or {}
    return str(hit.get("claim_id") or addl.get("id") or hit.get("doc_id") or "")


def _fuse_hybrid_rows(
    vector_rows: List[Dict[str, Any]],
    bm25_rows: List[Dict[str, Any]],
    alpha: float,
    limit: int,
    *,
    rrf_k: int = 60,
) -> List[Dict[str, Any]]:
    alpha = max(0.0, min(1.0, float(alpha)))
    weights = {
        "vector": alpha,
        "bm25": 1.0 - alpha,
    }
    score_by_key: Dict[str, float] = {}
    row_by_key: Dict[str, Dict[str, Any]] = {}

    for source, rows in (("vector", vector_rows), ("bm25", bm25_rows)):
        w = weights[source]
        if w <= 0.0:
            continue
        for rank, row in enumerate(rows, start=1):
            key = _claim_row_key(row)
            if not key:
                continue
            if key not in row_by_key:
                row_by_key[key] = row
            else:
                existing_addl = row_by_key[key].get("_additional") or {}
                candidate_addl = row.get("_additional") or {}
                if existing_addl.get("distance") is None and candidate_addl.get("distance") is not None:
                    merged = dict(row_by_key[key])
                    merged["_additional"] = {
                        **existing_addl,
                        "distance": candidate_addl.get("distance"),
                    }
                    row_by_key[key] = merged
            score_by_key[key] = score_by_key.get(key, 0.0) + (w / float(rrf_k + rank))

    ranked_keys = sorted(score_by_key, key=lambda k: score_by_key[k], reverse=True)[: int(limit)]
    return [row_by_key[k] for k in ranked_keys]


def _retrieve_hybrid_client_fusion(
    query_text: str,
    claim_where: str,
    query_vector: List[List[float]],
    alpha: float,
    limit: int,
) -> List[Dict[str, Any]]:
    vec_clause = (
        f'nearVector:{{vector:{json.dumps(query_vector)},targetVectors:["{WEAVIATE_NAMED_VECTOR}"]}},'
    )
    bm25_clause = f"bm25:{{query:{_escape_text(query_text)}}},"
    vec_rows: List[Dict[str, Any]] = []
    bm25_rows: List[Dict[str, Any]] = []
    try:
        vec_rows = _query_claim_rows(vec_clause, claim_where, int(limit))
    except Exception as ve:
        print(f"[warn] hybrid nearVector leg failed: {ve}")
    try:
        bm25_rows = _query_claim_rows(bm25_clause, claim_where, int(limit))
    except Exception as be:
        print(f"[warn] hybrid bm25 leg failed: {be}")
    if not vec_rows and not bm25_rows:
        raise RuntimeError("both hybrid legs failed (nearVector and bm25)")
    return _fuse_hybrid_rows(vec_rows, bm25_rows, alpha, int(limit))


def _normalize_retrieval_mode(value: str | None) -> str:
    mode = str(value or RETRIEVAL_MODE).strip().lower()
    if mode not in {"vector", "bm25", "hybrid"}:
        raise ValueError(f"Unknown retrieval mode '{value}'. Choose from: vector, bm25, hybrid.")
    return mode


def _fetch_patent_metadata(doc_ids: List[str]) -> Dict[str, Dict[str, Any]]:
    return load_patent_metadata_batch_from_lmdb(doc_ids)


def _maxsim_score(query_tokens: np.ndarray, doc_tokens: np.ndarray) -> float:
    if query_tokens.size == 0 or doc_tokens.size == 0:
        return float("-inf")
    qt = query_tokens.astype(np.float32, copy=False)
    dt = doc_tokens.astype(np.float32, copy=False)
    if qt.ndim != 2 or dt.ndim != 2:
        return float("-inf")
    if qt.shape[1] != dt.shape[1]:
        return float("-inf")
    sims = qt @ dt.T
    return float(np.max(sims, axis=1).sum())


def _rerank_hits_with_lmdb(hits: List[Dict[str, Any]], query: str, shard: str, rerank_k: int) -> List[Dict[str, Any]]:
    shard = assert_128_variant(shard, context="orchestrator._rerank_hits_with_lmdb")
    if shard not in SHARD_TO_PATH:
        raise ValueError(f"Unknown shard '{shard}'. Choose from: {sorted(SHARD_TO_PATH)}")
    q_tokens = _embed_query_tokens_for_shard(query, shard)
    top = hits[: max(0, int(rerank_k))]
    scored = []
    for hit in top:
        addl = hit.get("_additional") or {}
        obj_id = addl.get("id")
        claim_id = hit.get("claim_id")
        doc_id = hit.get("doc_id")
        if not obj_id and not claim_id:
            continue
        lmdb_path = resolve_lmdb_path(shard, doc_id=doc_id)
        # Primary LMDB key is claim_id; keep UUID fallback for older ingests.
        lookup_keys = [k for k in [claim_id, obj_id] if k]
        doc_tokens = None
        for k in lookup_keys:
            doc_tokens = load_colbert_from_lmdb(lmdb_path, str(k))
            if doc_tokens is not None:
                break
        if doc_tokens is None:
            raise RuntimeError(f"Missing LMDB vectors for claim_id={claim_id} doc_id={doc_id}")
        arr = np.asarray(doc_tokens)
        if arr.ndim == 1:
            arr = arr.reshape(1, -1)
        if arr.ndim != 2 or arr.shape[1] != 128:
            raise ValueError(
                f"LMDB vectors must be [T,128] for claim_id={claim_id}; got shape={arr.shape}"
            )
        score = _maxsim_score(q_tokens, doc_tokens)
        if score == float("-inf"):
            raise RuntimeError(f"Invalid MaxSim score for claim_id={claim_id}")
        scored.append((score, hit))
    scored.sort(key=lambda x: x[0], reverse=True)
    reranked = [hit for _, hit in scored]
    used = {id(hit) for hit in reranked}
    for hit in top:
        if id(hit) not in used:
            reranked.append(hit)
    reranked.extend(hits[int(rerank_k):])
    return reranked


@tool(response_format="content")
def retrieve_context(
    query: str,
    where_filter: Optional[Dict[str, Any]] = None,
    retrieval_mode: Optional[str] = None,
    hybrid_alpha: Optional[float] = None,
):
    """Retrieve information to help answer a query, optionally using metadata filters.

    Args:
        query: Search terms to look for
        where_filter: Filter for database search
    """
    if not query or not query.strip():
        return {"query": query, "joined_text": "", "chunks": []}

    query_text = query.strip()
    effective_mode = _normalize_retrieval_mode(retrieval_mode)
    effective_alpha = HYBRID_ALPHA if hybrid_alpha is None else max(0.0, min(1.0, float(hybrid_alpha)))
    query_vector = _embed_query_colbert(query_text) if effective_mode in {"vector", "hybrid"} else []
    retrieval_clause = _build_retrieval_clause(query_text, effective_mode, effective_alpha, query_vector)
    doc_id_filters = _extract_doc_id_filters(where_filter)
    claim_where = _build_claim_where(doc_id_filters)
    if effective_mode == "hybrid" and 0.0 < effective_alpha < 1.0 and FORCE_CLIENT_HYBRID:
        hits = _retrieve_hybrid_client_fusion(
            query_text,
            claim_where,
            query_vector,
            effective_alpha,
            int(DEFAULT_CANDIDATE_LIMIT),
        )
    else:
        try:
            hits = _query_claim_rows(retrieval_clause, claim_where, int(DEFAULT_CANDIDATE_LIMIT))
        except Exception as e:
            if effective_mode != "hybrid" or effective_alpha <= 0.0 or effective_alpha >= 1.0:
                raise
            print(f"[warn] server-side hybrid failed; using client-side fusion fallback: {e}")
            hits = _retrieve_hybrid_client_fusion(
                query_text,
                claim_where,
                query_vector,
                effective_alpha,
                int(DEFAULT_CANDIDATE_LIMIT),
            )

    hits = _rerank_hits_with_lmdb(hits, query.strip(), RERANK_SHARD, RERANK_K)
    hits = hits[:DEFAULT_LIMIT]

    claim_payloads = load_claim_payloads_from_lmdb(
        [str(hit.get("claim_id", "")).strip() for hit in hits if str(hit.get("claim_id", "")).strip()]
    )

    unique_doc_ids = []
    seen_doc_ids = set()
    for hit in hits:
        claim_id = str(hit.get("claim_id", "")).strip()
        payload = claim_payloads.get(claim_id) or {}
        did = str(hit.get("doc_id", "") or payload.get("doc_id") or "").strip()
        if did and did not in seen_doc_ids:
            seen_doc_ids.add(did)
            unique_doc_ids.append(did)

    patent_meta = _fetch_patent_metadata(unique_doc_ids)

    chunks: List[Dict[str, Any]] = []
    for hit in hits:
        addl = hit.get("_additional") or {}
        claim_id = str(hit.get("claim_id", "")).strip()
        payload = claim_payloads.get(claim_id) or {}
        doc_id = str(hit.get("doc_id", "") or payload.get("doc_id") or "").strip()
        patent_row = patent_meta.get(doc_id, {})
        text = rich_to_plain(str(payload.get("text") or ""))
        snippet = text[:500]

        # Include SearchItem-compatible fields in metadata for API shaping.
        metadata = {
            "id": hit.get("claim_id") or addl.get("id", ""),
            "title": patent_row.get("title", ""),
            "snippet": snippet,
            "search_text": text,
            "doc_id": doc_id,
            "claim_id": claim_id,
            "claim_type": str(payload.get("claim_type") or ""),
            "distance": addl.get("distance"),
            "filing_date": patent_row.get("filing_date", ""),
            "classification": patent_row.get("classification", ""),
            "authors": patent_row.get("authors", []),
            "kind": patent_row.get("kind", ""),
        }
        chunks.append({"text": text, "metadata": metadata})

    joined_text = "\n\n".join(c["text"] for c in chunks if c.get("text"))
    return {
        "query": query,
        "query_vector": query_vector,
        "retrieval_mode": effective_mode,
        "hybrid_alpha": effective_alpha,
        "joined_text": joined_text,
        "chunks": chunks,
    }


retriever_tool = retrieve_context
