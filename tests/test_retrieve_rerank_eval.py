import csv
import json

import numpy as np
import pytest

from backend.app.scripts import retrieve_rerank as rr


def _write_jsonl(path, rows):
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")


def _read_csv_rows(path):
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def test_extract_relevant_doc_ids_normalizes_claim_level_qrels():
    row = {
        "query": "example",
        "relevant_claim_ids": ["PAT-100-CLM-1", "PAT-100-CLM-2", "PAT-200-CLM-7"],
    }

    assert rr._extract_relevant_doc_ids(row) == {"PAT-100", "PAT-200"}
    assert rr._extract_relevant_doc_ids({"doc_id": "PAT-300", "relevance": 1}) == {"PAT-300"}
    assert rr._extract_relevant_doc_ids({"claim_id": "PAT-400-CLM-3", "rel": 1}) == {"PAT-400"}


def test_evaluate_uses_patent_level_matching_for_claim_qrels(tmp_path, monkeypatch):
    queries_path = tmp_path / "queries.jsonl"
    qrels_path = tmp_path / "qrels.jsonl"
    per_query_csv = tmp_path / "per_query.csv"
    per_query_topk_csv = tmp_path / "per_query_topk.csv"

    _write_jsonl(queries_path, [{"query": "query one"}])
    _write_jsonl(
        qrels_path,
        [{"query": "query one", "relevant_claim_ids": ["PAT-A-CLM-1", "PAT-A-CLM-9"]}],
    )

    hits = [
        rr.ClaimHit(uuid="u-b1", claim_id="PAT-B-CLM-1", doc_id="PAT-B", text="b1", score=0.9),
        rr.ClaimHit(uuid="u-a9", claim_id="PAT-A-CLM-9", doc_id="PAT-A", text="a9", score=0.8),
        rr.ClaimHit(uuid="u-a10", claim_id="PAT-A-CLM-10", doc_id="PAT-A", text="a10", score=0.7),
        rr.ClaimHit(uuid="u-c1", claim_id="PAT-C-CLM-1", doc_id="PAT-C", text="c1", score=0.6),
    ]

    monkeypatch.setattr(rr, "retrieve_claims", lambda *args, **kwargs: list(hits))
    monkeypatch.setattr(rr, "rerank_hits", lambda hits, *args, **kwargs: list(hits))
    monkeypatch.setattr(rr, "_embed_query_tokens", lambda *args, **kwargs: np.zeros((1, 128), dtype=np.float32))
    monkeypatch.setattr(
        rr,
        "fetch_colbert_vectors_from_weaviate",
        lambda object_ids: {oid: np.ones((1, 128), dtype=np.float32) for oid in object_ids},
    )

    scores = rr.evaluate(
        queries_path,
        qrels_path,
        retrieve_shard="128_f16",
        rerank_shard="128_f16",
        limit=5,
        rerank_k=5,
        rerank_source="weaviate",
        per_query_csv=per_query_csv,
        per_query_topk_csv=per_query_topk_csv,
        per_query_topk=3,
    )

    assert scores["candidate_hit@5"] == 1.0
    assert scores["recall@10"] == 1.0
    assert scores["mrr@10"] == pytest.approx(0.5)
    assert scores["precision@10"] == pytest.approx(1.0 / 3.0)

    per_query_rows = _read_csv_rows(per_query_csv)
    assert len(per_query_rows) == 1
    assert per_query_rows[0]["relevant_doc_1"] == "PAT-A"
    assert per_query_rows[0]["candidate_hits_count"] == "1"
    assert per_query_rows[0]["candidate_first_relevant_rank"] == "2"
    assert per_query_rows[0]["reranked_hit_at_10"] == "True"
    assert per_query_rows[0]["retrieved_top2_doc_id"] == "PAT-A"
    assert per_query_rows[0]["retrieved_top2_is_relevant"] == "True"

    topk_rows = _read_csv_rows(per_query_topk_csv)
    assert len(topk_rows) == 3
    assert topk_rows[0]["relevant_doc_ids"] == "PAT-A"
    assert topk_rows[1]["doc_id"] == "PAT-A"
    assert topk_rows[1]["candidate_rank"] == "2"
    assert topk_rows[1]["is_relevant"] == "True"


def _hit(
    claim_id: str,
    *,
    doc_id: str | None = None,
    distance: float | None = None,
    retrieval_score: float | None = None,
) -> rr.ClaimHit:
    return rr.ClaimHit(
        uuid=f"uuid-{claim_id}",
        claim_id=claim_id,
        doc_id=doc_id or claim_id.split("-CLM-")[0],
        distance=distance,
        retrieval_score=retrieval_score,
        text=claim_id,
    )


def test_relative_score_fusion_blends_overlap_and_single_leg_candidates():
    vector_hits = [
        _hit("PAT-A-CLM-1", distance=0.1),
        _hit("PAT-B-CLM-1", distance=0.4),
        _hit("PAT-C-CLM-1", distance=0.2),
    ]
    bm25_hits = [
        _hit("PAT-A-CLM-1", retrieval_score=12.0),
        _hit("PAT-D-CLM-1", retrieval_score=15.0),
        _hit("PAT-B-CLM-1", retrieval_score=9.0),
    ]

    fused = rr._fuse_hybrid_hits_relative_score(vector_hits, bm25_hits, alpha=0.5, limit=10)

    assert [hit.claim_id for hit in fused] == [
        "PAT-A-CLM-1",
        "PAT-D-CLM-1",
        "PAT-C-CLM-1",
        "PAT-B-CLM-1",
    ]

    fused_by_claim = {hit.claim_id: hit for hit in fused}
    assert fused_by_claim["PAT-A-CLM-1"].hybrid_source == "both"
    assert fused_by_claim["PAT-D-CLM-1"].hybrid_source == "bm25_only"
    assert fused_by_claim["PAT-C-CLM-1"].hybrid_source == "vector_only"
    assert fused_by_claim["PAT-A-CLM-1"].vector_score_raw == pytest.approx(-0.1)
    assert fused_by_claim["PAT-A-CLM-1"].bm25_score_raw == pytest.approx(12.0)
    assert fused_by_claim["PAT-A-CLM-1"].vector_score_norm == pytest.approx(1.0)
    assert fused_by_claim["PAT-A-CLM-1"].bm25_score_norm == pytest.approx(0.5)
    assert fused_by_claim["PAT-A-CLM-1"].hybrid_fused_score == pytest.approx(0.75)
    assert fused_by_claim["PAT-D-CLM-1"].hybrid_fused_score == pytest.approx(0.5)
    assert fused_by_claim["PAT-C-CLM-1"].hybrid_fused_score == pytest.approx(1.0 / 3.0)
    assert fused_by_claim["PAT-B-CLM-1"].hybrid_fused_score == pytest.approx(0.0)


def test_relative_score_fusion_zeroes_constant_score_leg():
    vector_hits = [
        _hit("PAT-A-CLM-1", distance=0.2),
        _hit("PAT-B-CLM-1", distance=0.2),
    ]
    bm25_hits = [
        _hit("PAT-A-CLM-1", retrieval_score=10.0),
        _hit("PAT-B-CLM-1", retrieval_score=5.0),
    ]

    fused = rr._fuse_hybrid_hits_relative_score(vector_hits, bm25_hits, alpha=0.9, limit=10)
    fused_by_claim = {hit.claim_id: hit for hit in fused}

    assert [hit.claim_id for hit in fused] == ["PAT-A-CLM-1", "PAT-B-CLM-1"]
    assert fused_by_claim["PAT-A-CLM-1"].vector_score_norm == pytest.approx(0.0)
    assert fused_by_claim["PAT-B-CLM-1"].vector_score_norm == pytest.approx(0.0)
    assert fused_by_claim["PAT-A-CLM-1"].bm25_score_norm == pytest.approx(1.0)
    assert fused_by_claim["PAT-B-CLM-1"].bm25_score_norm == pytest.approx(0.0)
    assert fused_by_claim["PAT-A-CLM-1"].hybrid_fused_score == pytest.approx(0.1)
    assert fused_by_claim["PAT-B-CLM-1"].hybrid_fused_score == pytest.approx(0.0)


def test_rrf_fusion_method_remains_available_for_comparison():
    vector_hits = [
        _hit("PAT-A-CLM-1", distance=0.1),
        _hit("PAT-B-CLM-1", distance=0.2),
    ]
    bm25_hits = [
        _hit("PAT-A-CLM-1", retrieval_score=10.0),
        _hit("PAT-C-CLM-1", retrieval_score=9.0),
    ]

    fused = rr._fuse_hybrid_hits(vector_hits, bm25_hits, alpha=0.5, limit=10, fusion_method="rrf")

    assert fused[0].claim_id == "PAT-A-CLM-1"
    assert fused[0].hybrid_source == "both"
    assert fused[0].hybrid_fused_score is not None
