"""
Minimal retrieval + ColBERT-style reranking utilities.

- Retrieve Claim candidates from Weaviate using a dense query vector.
- Load token vectors from an LMDB shard and rerank with MaxSim.
- Optionally evaluate simple IR metrics from query/qrels files.
- Provide a direct patent (doc_id) lookup helper.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import requests

from backend.app.embed import _get_token_projection, model, tokenizer
from backend.app.services.download import rich_to_plain
from backend.app.store import (
    LMDB_PATH_128_F16,
    LMDB_PATH_128_F32,
    LMDB_PATH_768_F16,
    LMDB_PATH_768_F32,
    load_colbert_from_lmdb,
)


WEAVIATE_GRAPHQL = os.environ.get("WEAVIATE_GRAPHQL", "http://localhost:8080/v1/graphql")
WEAVIATE_OBJECTS = os.environ.get("WEAVIATE_OBJECTS", "http://localhost:8080/v1/objects")


SHARD_TO_PATH = {
    "768_f32": LMDB_PATH_768_F32,
    "768_f16": LMDB_PATH_768_F16,
    "128_f32": LMDB_PATH_128_F32,
    "128_f16": LMDB_PATH_128_F16,
}


@dataclass
class ClaimHit:
    uuid: str
    claim_id: str
    doc_id: str
    claim_type: str
    text: str
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


def _embed_query_dense(query: str) -> np.ndarray:
    # Mean-pooled dense vector for Weaviate nearVector retrieval.
    import torch

    tokens = tokenizer(
        query,
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
    import torch
    import torch.nn.functional as F

    tokens = tokenizer(
        query,
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
    if shard.startswith("128_"):
        proj = _get_token_projection()
        if proj is None:
            raise RuntimeError("Token projection layer not initialized")
        masked = proj(masked)
        masked = F.normalize(masked, p=2, dim=1)
    dtype = torch.float16 if shard.endswith("f16") else torch.float32
    return masked.to(dtype).detach().cpu().numpy()


def retrieve_claims(query: str, limit: int = 200, shard: str = "768_f16") -> list[ClaimHit]:
    shard = shard.lower()
    if shard not in SHARD_TO_PATH:
        raise ValueError(f"Unknown shard '{shard}'. Choose from: {sorted(SHARD_TO_PATH)}")
    mv_vecs = _embed_query_tokens(query, shard).tolist()
    gql = (
        "{ Get { Claim("
        f"nearVector: {{vector: {mv_vecs}, targetVectors: [\"colbert\"]}}, limit: {int(limit)}"
        ") { claim_id doc_id claim_type text _additional { id distance } } } }"
    )
    data = _post_graphql(gql)
    items = data["Get"]["Claim"]
    hits: list[ClaimHit] = []
    for it in items:
        addl = it.get("_additional") or {}
        hits.append(
            ClaimHit(
                uuid=addl.get("id", ""),
                distance=addl.get("distance"),
                claim_id=it.get("claim_id", ""),
                doc_id=it.get("doc_id", ""),
                claim_type=it.get("claim_type", ""),
                text=rich_to_plain(it.get("text", "")),
            )
        )
    return hits


def _maxsim_score(query_tokens: np.ndarray, doc_tokens: np.ndarray) -> float:
    if doc_tokens.size == 0 or query_tokens.size == 0:
        return float("-inf")
    qt = query_tokens.astype(np.float32, copy=False)
    dt = doc_tokens.astype(np.float32, copy=False)
    sims = qt @ dt.T
    return float(np.max(sims, axis=1).sum())


def rerank_with_lmdb(hits: list[ClaimHit], query: str, shard: str, rerank_k: int = 100) -> list[ClaimHit]:
    shard = shard.lower()
    if shard not in SHARD_TO_PATH:
        raise ValueError(f"Unknown shard '{shard}'. Choose from: {sorted(SHARD_TO_PATH)}")
    lmdb_path = SHARD_TO_PATH[shard]
    q_tokens = _embed_query_tokens(query, shard)
    top = hits[: int(rerank_k)]
    rescored: list[ClaimHit] = []
    for h in top:
        doc_tokens = load_colbert_from_lmdb(lmdb_path, h.uuid)
        if doc_tokens is None:
            continue
        h.score = _maxsim_score(q_tokens, doc_tokens)
        rescored.append(h)
    rescored.sort(key=lambda x: (x.score if x.score is not None else float("-inf")), reverse=True)
    return rescored + hits[int(rerank_k) :]


def lookup_patent(doc_id: str, limit: int = 200) -> list[ClaimHit]:
    where = (
        "{path:[\"doc_id\"],operator:Equal,valueText:"
        f"\"{doc_id}\"}}"
    )
    gql = (
        "{ Get { Claim("
        f"where:{where}, limit:{int(limit)}"
        ") { claim_id doc_id claim_type text _additional { id } } } }"
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
                claim_type=it.get("claim_type", ""),
                text=rich_to_plain(it.get("text", "")),
            )
        )
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


def evaluate(
    queries_path: Path,
    qrels_path: Path,
    retrieve_shard: str,
    rerank_shard: str,
    limit: int,
    rerank_k: int,
    *,
    filter_missing_qrels: bool = True,
) -> dict:
    with queries_path.open("r", encoding="utf-8") as f:
        queries = [json.loads(line) for line in f if line.strip()]
    with qrels_path.open("r", encoding="utf-8") as f:
        qrels = {row["query"]: set(row.get("relevant_claim_ids", [])) for row in (json.loads(line) for line in f if line.strip())}

    metrics = {"precision@10": [], "recall@10": [], "ndcg@10": [], "mrr@10": []}
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
        queries = filtered
        total_q = len(queries)
        print(f"[eval] filtered {dropped} query(ies) with no relevant claims in index")
    for i, row in enumerate(queries, start=1):
        q = row.get("query", "")
        if not q:
            continue
        print(f"[eval] {i}/{total_q} retrieving + reranking")
        rel = qrels.get(q, set())
        hits = retrieve_claims(q, limit=limit, shard=retrieve_shard)
        ranked = rerank_with_lmdb(hits, q, shard=rerank_shard, rerank_k=rerank_k)
        ranked_ids = [h.claim_id for h in ranked]
        metrics["precision@10"].append(precision_at_k(ranked_ids, rel, 10))
        metrics["recall@10"].append(recall_at_k(ranked_ids, rel, 10))
        metrics["ndcg@10"].append(ndcg_at_k(ranked_ids, rel, 10))
        metrics["mrr@10"].append(mrr_at_k(ranked_ids, rel, 10))

    return {k: (sum(v) / len(v) if v else 0.0) for k, v in metrics.items()}


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
    parser.add_argument("--save-before-csv", type=Path, default=None, help="Save pre-rerank top-k to CSV.")
    parser.add_argument("--save-after-csv", type=Path, default=None, help="Save reranked top-k to CSV.")
    parser.add_argument("--save-k", type=int, default=10, help="How many rows to write to CSV outputs.")
    parser.add_argument(
        "--retrieve-shard",
        type=str,
        default=os.environ.get("WEAVIATE_SHARD", "768_f16"),
        choices=sorted(SHARD_TO_PATH.keys()),
        help="Which shard to use for Weaviate retrieval (must match index dimension).",
    )
    parser.add_argument(
        "--rerank-shard",
        type=str,
        default=os.environ.get("COLBERT_SHARD", "768_f16"),
        choices=sorted(SHARD_TO_PATH.keys()),
        help="Which ColBERT LMDB shard to use for reranking.",
    )
    parser.add_argument("--doc-id", type=str, default="", help="Lookup claims by patent doc_id.")
    parser.add_argument("--queries", type=Path, default=None, help="Path to JSONL queries for evaluation.")
    parser.add_argument("--qrels", type=Path, default=None, help="Path to JSONL qrels for evaluation.")
    parser.add_argument("--metrics-csv", type=Path, default=None, help="Write evaluation metrics to CSV.")
    parser.add_argument(
        "--filter-missing-qrels",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Drop queries whose relevant claim_ids are not present in Weaviate.",
    )
    args = parser.parse_args()

    if args.doc_id:
        hits = lookup_patent(args.doc_id)
        print(f"Found {len(hits)} claims for doc_id={args.doc_id}")
        _print_hits(hits, k=min(10, len(hits)))
        return

    if args.queries and args.qrels:
        scores = evaluate(
            args.queries,
            args.qrels,
            retrieve_shard=args.retrieve_shard,
            rerank_shard=args.rerank_shard,
            limit=args.limit,
            rerank_k=args.rerank_k,
            filter_missing_qrels=args.filter_missing_qrels,
        )
        print(json.dumps(scores, indent=2))
        if args.metrics_csv:
            args.metrics_csv.parent.mkdir(parents=True, exist_ok=True)
            with args.metrics_csv.open("w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["precision@10", "recall@10", "ndcg@10", "mrr@10"])
                writer.writerow(
                    [
                        scores.get("precision@10", 0.0),
                        scores.get("recall@10", 0.0),
                        scores.get("ndcg@10", 0.0),
                        scores.get("mrr@10", 0.0),
                    ]
                )
            print(f"Wrote metrics to {args.metrics_csv}")
        return

    if not args.query:
        raise SystemExit("Provide --query, or --doc-id, or (--queries and --qrels).")

    hits = retrieve_claims(args.query, limit=args.limit, shard=args.retrieve_shard)
    reranked = rerank_with_lmdb(hits, args.query, shard=args.rerank_shard, rerank_k=args.rerank_k)
    print(
        f"Retrieved {len(hits)} hits; reranked top {args.rerank_k} "
        f"using retrieve_shard={args.retrieve_shard} rerank_shard={args.rerank_shard}"
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
