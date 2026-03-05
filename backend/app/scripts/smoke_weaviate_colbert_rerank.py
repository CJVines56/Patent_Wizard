"""
Smoke test for strict 128-d ColBERT pipeline + Weaviate vector export rerank.

Checks:
1) embedding output token dim is exactly 128
2) sample claims can be inserted into Weaviate
3) vectors can be fetched back from Weaviate and used for reranking
"""

from __future__ import annotations

import argparse
import uuid

import numpy as np

from backend.app.embed import embed_chunks, model, tokenizer
from backend.app.scripts.retrieve_rerank import (
    fetch_colbert_vectors_from_weaviate,
    rerank_hits,
    retrieve_claims,
)
from backend.app.store import store_embeddings


def _build_smoke_claims(unique: str) -> list[dict]:
    doc_id = f"SMOKE-{unique}"
    return [
        {
            "doc_id": doc_id,
            "claim_id": f"{doc_id}-CLM-1",
            "claim_number": 1,
            "claim_type": "independent",
            "text": f"A widget using token smoke-key-{unique} for retrieval verification.",
            "filing_date": "2026-01-01",
            "classification": "G06F",
            "authors": ["Smoke Tester"],
            "title": "Smoke Projection Patent",
            "kind": "A1",
        },
        {
            "doc_id": doc_id,
            "claim_id": f"{doc_id}-CLM-2",
            "claim_number": 2,
            "claim_type": "dependent",
            "text": f"The widget of claim 1 wherein smoke-key-{unique} is repeated for ranking.",
            "filing_date": "2026-01-01",
            "classification": "G06F",
            "authors": ["Smoke Tester"],
            "title": "Smoke Projection Patent",
            "kind": "A1",
        },
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description="Smoke test: embed -> ingest -> Weaviate fetch -> rerank")
    parser.add_argument("--limit", type=int, default=50, help="Retrieval candidate limit.")
    args = parser.parse_args()

    unique = uuid.uuid4().hex[:8]
    claims = _build_smoke_claims(unique)
    query = f"smoke-key-{unique}"

    embedded = embed_chunks(claims, tokenizer, model)
    if not embedded:
        raise RuntimeError("Embedding returned no records.")
    token_matrix = np.asarray(embedded[0].get("colbert"))
    if token_matrix.ndim == 1:
        token_matrix = token_matrix.reshape(1, -1)
    if token_matrix.ndim != 2 or token_matrix.shape[1] != 128:
        raise ValueError(f"Expected embedded token vectors [T,128], got {token_matrix.shape}")

    store_embeddings(embedded)

    hits = retrieve_claims(query, limit=args.limit, shard="128_f16", retrieval_mode="vector")
    expected_claim_ids = {c["claim_id"] for c in claims}
    smoke_hits = [h for h in hits if h.claim_id in expected_claim_ids]
    if not smoke_hits:
        raise RuntimeError("Inserted smoke claims were not retrieved from Weaviate.")

    object_ids = [h.uuid for h in smoke_hits]
    if any(not oid for oid in object_ids):
        raise RuntimeError("Smoke retrieval hit missing Weaviate UUID.")
    vectors = fetch_colbert_vectors_from_weaviate(object_ids)
    for oid in object_ids:
        arr = vectors.get(oid)
        if arr is None:
            raise RuntimeError(f"Missing fetched vector for object_id={oid}")
        if arr.ndim != 2 or arr.shape[1] != 128:
            raise ValueError(f"Fetched Weaviate vectors must be [T,128], got {arr.shape}")

    reranked = rerank_hits(
        smoke_hits,
        query,
        shard="128_f16",
        rerank_k=len(smoke_hits),
        rerank_source="weaviate",
    )
    if not reranked or reranked[0].score is None:
        raise RuntimeError("Weaviate-based reranking did not produce scores.")

    print(
        "[smoke] success: embedded_128=1 inserted=1 fetched_vectors=1 reranked=1 "
        f"top_claim_id={reranked[0].claim_id} top_score={reranked[0].score:.6f}"
    )


if __name__ == "__main__":
    main()
