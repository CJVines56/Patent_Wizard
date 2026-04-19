from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable

import numpy as np


def positive_relevant_ids(rel_map: dict[str, int | float]) -> set[str]:
    return {doc_id for doc_id, rel in rel_map.items() if float(rel) > 0.0}


def precision_at_k(ranked_ids: list[str], relevant_ids: set[str], k: int) -> float:
    """precision@k = (# relevant in top k) / k"""
    if k <= 0:
        return 0.0
    top = ranked_ids[:k]
    hits = sum(1 for rid in top if rid in relevant_ids)
    return float(hits) / float(k)


def recall_at_k(ranked_ids: list[str], relevant_ids: set[str], k: int) -> float:
    if not relevant_ids:
        return 0.0
    top = ranked_ids[:k]
    hits = sum(1 for rid in top if rid in relevant_ids)
    return float(hits) / float(len(relevant_ids))


def mrr_at_k(ranked_ids: list[str], relevant_ids: set[str], k: int) -> float:
    for rank, rid in enumerate(ranked_ids[:k], start=1):
        if rid in relevant_ids:
            return 1.0 / float(rank)
    return 0.0


def first_relevant_rank(ranked_ids: list[str], relevant_ids: set[str], *, k: int | None = None) -> int | None:
    scan = ranked_ids if k is None else ranked_ids[:k]
    for rank, rid in enumerate(scan, start=1):
        if rid in relevant_ids:
            return rank
    return None


def dcg_at_k(ranked_ids: list[str], rel_map: dict[str, int | float], k: int) -> float:
    """
    dcg@k = sum((2^rel - 1) / log2(rank + 1))
    """
    total = 0.0
    for rank, rid in enumerate(ranked_ids[:k], start=1):
        rel = float(rel_map.get(rid, 0.0))
        if rel <= 0.0:
            continue
        total += (2.0 ** rel - 1.0) / math.log2(rank + 1.0)
    return total


def idcg_at_k(rel_map: dict[str, int | float], k: int) -> float:
    ideal = sorted((float(v) for v in rel_map.values() if float(v) > 0.0), reverse=True)
    total = 0.0
    for rank, rel in enumerate(ideal[:k], start=1):
        total += (2.0 ** rel - 1.0) / math.log2(rank + 1.0)
    return total


def ndcg_at_k(ranked_ids: list[str], rel_map: dict[str, int | float], k: int) -> float:
    i = idcg_at_k(rel_map, k)
    if i <= 0.0:
        return 0.0
    return dcg_at_k(ranked_ids, rel_map, k) / i


def candidate_hit(candidate_ids: list[str], rel_map: dict[str, int | float]) -> bool:
    rel_ids = positive_relevant_ids(rel_map)
    return any(cid in rel_ids for cid in candidate_ids)


@dataclass(frozen=True)
class QueryMetrics:
    precision: float
    recall: float
    ndcg: float
    mrr: float
    first_rel_rank: int | None
    num_relevant: int
    candidate_hit: bool
    candidate_hit_count: int


def compute_query_metrics(
    ranked_ids: list[str],
    rel_map: dict[str, int | float],
    candidate_ids: list[str],
    k: int,
) -> QueryMetrics:
    rel_ids = positive_relevant_ids(rel_map)
    first_rank = first_relevant_rank(ranked_ids, rel_ids, k=k)
    cand_hits = [cid for cid in candidate_ids if cid in rel_ids]
    return QueryMetrics(
        precision=precision_at_k(ranked_ids, rel_ids, k),
        recall=recall_at_k(ranked_ids, rel_ids, k),
        ndcg=ndcg_at_k(ranked_ids, rel_map, k),
        mrr=mrr_at_k(ranked_ids, rel_ids, k),
        first_rel_rank=first_rank,
        num_relevant=len(rel_ids),
        candidate_hit=bool(cand_hits),
        candidate_hit_count=len(cand_hits),
    )


def mean(values: Iterable[float]) -> float:
    vals = list(values)
    if not vals:
        return 0.0
    return float(sum(vals) / len(vals))


def average_pr_curve(
    runs_by_qid: dict[str, list[str]],
    qrels_by_qid: dict[str, dict[str, int | float]],
    qids: list[str],
    kmax: int,
) -> dict[str, list[float]]:
    ks = range(1, kmax + 1)
    p_vals: list[float] = []
    r_vals: list[float] = []
    for k in ks:
        ps = []
        rs = []
        for qid in qids:
            rel_ids = positive_relevant_ids(qrels_by_qid[qid])
            if not rel_ids:
                continue
            ranked = runs_by_qid.get(qid, [])
            ps.append(precision_at_k(ranked, rel_ids, k))
            rs.append(recall_at_k(ranked, rel_ids, k))
        p_vals.append(mean(ps))
        r_vals.append(mean(rs))
    return {"k": list(ks), "precision": p_vals, "recall": r_vals}


def cumulative_gain_curves(
    runs_by_qid: dict[str, list[str]],
    qrels_by_qid: dict[str, dict[str, int | float]],
    qids: list[str],
    kmax: int,
) -> dict[str, list[float]]:
    ks = range(1, kmax + 1)
    dcg_curve: list[float] = []
    ndcg_curve: list[float] = []
    for k in ks:
        dcgs = []
        ndcgs = []
        for qid in qids:
            rel_map = qrels_by_qid[qid]
            if not positive_relevant_ids(rel_map):
                continue
            ranked = runs_by_qid.get(qid, [])
            dcgs.append(dcg_at_k(ranked, rel_map, k))
            ndcgs.append(ndcg_at_k(ranked, rel_map, k))
        dcg_curve.append(mean(dcgs))
        ndcg_curve.append(mean(ndcgs))
    return {"k": list(ks), "dcg": dcg_curve, "ndcg": ndcg_curve}


def relevance_heatmap_matrix(
    runs_by_qid: dict[str, list[str]],
    qrels_by_qid: dict[str, dict[str, int | float]],
    qids: list[str],
    kheat: int,
) -> np.ndarray:
    rows: list[np.ndarray] = []
    for qid in qids:
        rel_ids = positive_relevant_ids(qrels_by_qid[qid])
        ranked = runs_by_qid.get(qid, [])
        row = np.zeros(kheat, dtype=np.float32)
        for i, rid in enumerate(ranked[:kheat], start=1):
            if rid in rel_ids:
                row[i - 1] = 1.0
        rows.append(row)
    if not rows:
        return np.zeros((0, kheat), dtype=np.float32)
    return np.stack(rows, axis=0)

