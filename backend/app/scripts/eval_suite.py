"""
Comprehensive ranking evaluation + visualization suite for qrels.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import statistics
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from backend.app.eval.metrics import (
    average_pr_curve,
    compute_query_metrics,
    cumulative_gain_curves,
    mean,
    positive_relevant_ids,
    relevance_heatmap_matrix,
)
from backend.app.eval.plots import (
    plot_dcg_curves,
    plot_hist_first_relevant_rank,
    plot_hist_metric,
    plot_pr_curve,
    plot_rank_shift,
    plot_recall_vs_k,
    plot_relevance_heatmap,
    plot_scatter_ndcg_vs_num_rel,
)


def _parse_int_list(raw: str, name: str) -> list[int]:
    out: list[int] = []
    for token in str(raw).split(","):
        token = token.strip()
        if not token:
            continue
        try:
            out.append(int(token))
        except ValueError as exc:
            raise ValueError(f"{name} must be a comma-separated integer list. Bad token: '{token}'") from exc
    if not out:
        raise ValueError(f"{name} cannot be empty.")
    if any(v <= 0 for v in out):
        raise ValueError(f"{name} values must all be > 0.")
    return sorted(set(out))


def _set_seeds(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    try:
        import torch

        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except Exception:
        pass


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def _sniff_delimiter(path: Path) -> str:
    if path.suffix.lower() == ".tsv":
        return "\t"
    sample = path.read_text(encoding="utf-8", errors="ignore")[:4096]
    if "\t" in sample and sample.count("\t") >= sample.count(","):
        return "\t"
    return ","


def _load_queries(path: Path) -> dict[str, str]:
    if not path.exists():
        raise FileNotFoundError(f"queries file not found: {path}")

    out: dict[str, str] = {}
    suffix = path.suffix.lower()

    if suffix == ".jsonl":
        rows = _read_jsonl(path)
        for idx, row in enumerate(rows, start=1):
            qid = str(
                row.get("query_id")
                or row.get("qid")
                or row.get("id")
                or row.get("query")
                or f"q{idx}"
            ).strip()
            text = str(row.get("query") or row.get("text") or row.get("q") or "").strip()
            if not text:
                raise ValueError(f"Query text missing for row {idx} in {path}")
            out[qid] = text
        return out

    delim = _sniff_delimiter(path)
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter=delim)
        if not reader.fieldnames:
            raise ValueError(f"Could not read query headers from {path}")
        fields = {str(x).strip().lower(): x for x in reader.fieldnames if x}

        qid_field = None
        for cand in ("query_id", "qid", "id"):
            if cand in fields:
                qid_field = fields[cand]
                break
        text_field = None
        for cand in ("query", "text", "q"):
            if cand in fields:
                text_field = fields[cand]
                break
        if text_field is None:
            raise ValueError(f"Could not find query text column in {path}. Expected one of: query,text,q")
        if qid_field is None:
            raise ValueError(f"Could not find query id column in {path}. Expected one of: query_id,qid,id")

        for row_num, row in enumerate(reader, start=2):
            qid = str(row.get(qid_field, "")).strip()
            text = str(row.get(text_field, "")).strip()
            if not qid:
                raise ValueError(f"Missing query id at {path}:{row_num}")
            if not text:
                raise ValueError(f"Missing query text at {path}:{row_num}")
            out[qid] = text
    return out


def _parse_rel(value: Any) -> int:
    if value is None:
        return 0
    raw = str(value).strip()
    if raw == "":
        return 0
    try:
        return int(float(raw))
    except ValueError as exc:
        raise ValueError(f"Could not parse relevance value '{value}'") from exc


def _infer_id_field_from_col(col: str) -> str:
    c = col.lower()
    if "claim" in c:
        return "claim_id"
    if "doc" in c:
        return "doc_id"
    if c in {"docno", "docid", "document_id", "target_id"}:
        return "doc_id"
    return c


def _load_qrels(path: Path) -> tuple[dict[str, dict[str, int]], str]:
    if not path.exists():
        raise FileNotFoundError(f"qrels file not found: {path}")

    suffix = path.suffix.lower()
    qrels: dict[str, dict[str, int]] = {}
    id_field: str | None = None

    def upsert(qid: str, tid: str, rel: int, inferred_id_field: str) -> None:
        nonlocal id_field
        qid = str(qid).strip()
        tid = str(tid).strip()
        if not qid or not tid:
            return
        if id_field is None:
            id_field = inferred_id_field
        elif id_field != inferred_id_field:
            raise ValueError(
                f"Mixed qrels id types are not supported. Saw '{id_field}' and '{inferred_id_field}'."
            )
        bucket = qrels.setdefault(qid, {})
        prev = bucket.get(tid, 0)
        bucket[tid] = max(prev, int(rel))

    if suffix == ".jsonl":
        rows = _read_jsonl(path)
        for idx, row in enumerate(rows, start=1):
            qid = str(row.get("query_id") or row.get("qid") or row.get("query") or "").strip()
            if not qid:
                raise ValueError(f"Missing query id/query text at {path}:{idx}")

            if "relevant_claim_ids" in row:
                ids = row.get("relevant_claim_ids") or []
                for tid in ids:
                    upsert(qid, str(tid), 1, "claim_id")
                continue
            if "relevant_doc_ids" in row:
                ids = row.get("relevant_doc_ids") or []
                for tid in ids:
                    upsert(qid, str(tid), 1, "doc_id")
                continue
            if "relevant_ids" in row:
                ids = row.get("relevant_ids") or []
                for tid in ids:
                    upsert(qid, str(tid), 1, "claim_id")
                continue

            tid = row.get("claim_id")
            inferred = "claim_id"
            if tid is None:
                tid = row.get("doc_id")
                inferred = "doc_id"
            if tid is None:
                raise ValueError(
                    f"Unsupported JSONL qrels row at {path}:{idx}. "
                    "Expected relevant_claim_ids/relevant_doc_ids/relevant_ids or claim_id/doc_id."
                )
            rel = _parse_rel(row.get("relevance", row.get("rel", 1)))
            upsert(qid, str(tid), rel, inferred)
    else:
        delim = _sniff_delimiter(path)
        with path.open("r", encoding="utf-8", newline="") as f:
            head = f.readline()
            f.seek(0)
            has_header = any(
                token in head.lower()
                for token in ("query_id", "qid", "claim_id", "doc_id", "relevance", "rel")
            )
            if has_header:
                reader = csv.DictReader(f, delimiter=delim)
                if not reader.fieldnames:
                    raise ValueError(f"Could not parse qrels header from {path}")
                fields = {str(x).strip().lower(): x for x in reader.fieldnames if x}

                qid_col = None
                for cand in ("query_id", "qid", "query"):
                    if cand in fields:
                        qid_col = fields[cand]
                        break
                if qid_col is None:
                    raise ValueError(f"Could not find qid column in {path}")

                tid_col = None
                for cand in ("claim_id", "doc_id", "docno", "docid", "document_id", "target_id"):
                    if cand in fields:
                        tid_col = fields[cand]
                        break
                if tid_col is None:
                    raise ValueError(f"Could not find doc/claim id column in {path}")
                inferred_id_field = _infer_id_field_from_col(tid_col)

                rel_col = None
                for cand in ("relevance", "rel", "label", "score", "grade", "judgment"):
                    if cand in fields:
                        rel_col = fields[cand]
                        break
                if rel_col is None:
                    raise ValueError(f"Could not find relevance column in {path}")

                for row in reader:
                    upsert(
                        str(row.get(qid_col, "")),
                        str(row.get(tid_col, "")),
                        _parse_rel(row.get(rel_col)),
                        inferred_id_field,
                    )
            else:
                reader = csv.reader(f, delimiter=delim if delim in {"\t", ","} else " ")
                for row_num, parts in enumerate(reader, start=1):
                    parts = [p for p in parts if str(p).strip()]
                    if not parts:
                        continue
                    if len(parts) >= 4:
                        qid, _, tid, rel = parts[0], parts[1], parts[2], parts[3]
                    elif len(parts) == 3:
                        qid, tid, rel = parts[0], parts[1], parts[2]
                    else:
                        raise ValueError(f"Could not parse qrels row at {path}:{row_num}: {parts}")
                    upsert(qid, tid, _parse_rel(rel), "doc_id")

    if not qrels:
        raise ValueError(f"No qrels rows loaded from {path}")
    if not id_field:
        raise ValueError(f"Could not infer qrels id field from {path}")
    return qrels, id_field


def _install_query_embedding_cache(cache_dir: Path | None):
    import backend.app.scripts.retrieve_rerank as rr

    original = rr._embed_query_tokens
    memory_cache: dict[tuple[str, str], np.ndarray] = {}
    cache_path = None
    if cache_dir is not None:
        cache_path = Path(cache_dir)
        cache_path.mkdir(parents=True, exist_ok=True)

    def cached_embed(query: str, shard: str) -> np.ndarray:
        key = (str(query), str(shard))
        cached = memory_cache.get(key)
        if cached is not None:
            return cached

        disk_path = None
        if cache_path is not None:
            digest = hashlib.sha1(f"{shard}\n{query}".encode("utf-8")).hexdigest()
            disk_path = cache_path / f"query_tokens_{digest}.npy"
            if disk_path.exists():
                arr = np.load(disk_path, allow_pickle=False)
                memory_cache[key] = arr
                return arr

        arr = np.asarray(original(query, shard))
        memory_cache[key] = arr
        if disk_path is not None:
            np.save(disk_path, arr, allow_pickle=False)
        return arr

    rr._embed_query_tokens = cached_embed
    return rr


@dataclass
class RunRecord:
    query_id: str
    target_id: str
    claim_id: str
    doc_id: str
    score: float
    rank: int = 0


def _extract_target_id(hit: Any, id_field: str) -> str:
    if id_field == "claim_id":
        return str(getattr(hit, "claim_id", "") or "").strip()
    if id_field == "doc_id":
        return str(getattr(hit, "doc_id", "") or "").strip()
    return str(getattr(hit, id_field, "") or "").strip()


def _hit_score_for_ranking(hit: Any, fallback_rank: int) -> float:
    score = getattr(hit, "score", None)
    if score is not None:
        return float(score)
    distance = getattr(hit, "distance", None)
    if distance is not None:
        return -float(distance)
    return -float(fallback_rank)


def _build_run_records(query_id: str, hits: list[Any], id_field: str) -> list[RunRecord]:
    by_target: dict[str, RunRecord] = {}
    for idx, h in enumerate(hits, start=1):
        target_id = _extract_target_id(h, id_field)
        if not target_id:
            continue
        claim_id = str(getattr(h, "claim_id", "") or "").strip()
        doc_id = str(getattr(h, "doc_id", "") or "").strip()
        score = _hit_score_for_ranking(h, idx)
        existing = by_target.get(target_id)
        if existing is None or score > existing.score:
            by_target[target_id] = RunRecord(
                query_id=query_id,
                target_id=target_id,
                claim_id=claim_id,
                doc_id=doc_id,
                score=score,
            )

    rows = list(by_target.values())
    rows.sort(key=lambda r: (-r.score, r.doc_id, r.target_id))
    for rank, rec in enumerate(rows, start=1):
        rec.rank = rank
    return rows


def _write_run_file(path: Path, runs_by_qid: dict[str, list[RunRecord]], tag: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        for qid in sorted(runs_by_qid):
            rows = runs_by_qid[qid]
            for rec in rows:
                f.write(
                    f"{qid}\tQ0\t{rec.target_id}\t{rec.rank}\t{rec.score:.8f}\t{tag}\n"
                )


def _mean_timing_ms(timing_rows: list[dict[str, float]]) -> tuple[float, float, float]:
    return (
        mean(r["retrieval_ms"] for r in timing_rows),
        mean(r["rerank_ms"] for r in timing_rows),
        mean(r["total_ms"] for r in timing_rows),
    )


def _best_row(rows: list[dict[str, Any]], *, metric: str, k: int) -> dict[str, Any] | None:
    candidates = [r for r in rows if int(r["k"]) == int(k)]
    if not candidates:
        return None
    return max(
        candidates,
        key=lambda r: (
            float(r.get(metric, 0.0)),
            float(r.get("recall@k", 0.0)),
            -float(r.get("mean_total_time_ms", 0.0)),
        ),
    )


def _summarize_rank_shift(points: list[tuple[int, int]]) -> dict[str, float]:
    if not points:
        return {"improved_pct": 0.0, "worsened_pct": 0.0, "unchanged_pct": 0.0, "n": 0.0}
    improved = sum(1 for before, after in points if after < before)
    worsened = sum(1 for before, after in points if after > before)
    unchanged = len(points) - improved - worsened
    n = float(len(points))
    return {
        "improved_pct": 100.0 * improved / n,
        "worsened_pct": 100.0 * worsened / n,
        "unchanged_pct": 100.0 * unchanged / n,
        "n": n,
    }


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _write_report(
    path: Path,
    *,
    args: argparse.Namespace,
    qid_total: int,
    qid_eval_count: int,
    qid_missing_qrels: list[str],
    qid_missing_queries: list[str],
    qid_zero_rel: list[str],
    summary_rows: list[dict[str, Any]],
    warnings: list[str],
    rank_shift_summary: dict[str, float],
) -> None:
    best_ndcg10 = _best_row(summary_rows, metric="ndcg@k", k=10)
    best_ndcg50 = _best_row(summary_rows, metric="ndcg@k", k=50)
    best_recall200 = _best_row(summary_rows, metric="recall@k", k=200)

    preferred_mode = "rerank" if any(r["mode"] == "rerank" for r in summary_rows) else "retrieve"
    balanced_k = int(args.balanced_k)
    balanced_candidates = [r for r in summary_rows if r["mode"] == preferred_mode and int(r["k"]) == balanced_k]

    latency_cap_ms = float(args.latency_cap_ms) if args.latency_cap_ms is not None else None
    if latency_cap_ms is None and balanced_candidates:
        totals = [float(r["mean_total_time_ms"]) for r in balanced_candidates]
        latency_cap_ms = 1.5 * float(statistics.median(totals))

    feasible = [
        r
        for r in balanced_candidates
        if float(r["recall@k"]) >= float(args.recall_threshold)
        and (latency_cap_ms is None or float(r["mean_total_time_ms"]) <= latency_cap_ms)
    ]
    if feasible:
        balanced = max(
            feasible,
            key=lambda r: (
                float(r["ndcg@k"]),
                float(r["recall@k"]),
                -float(r["mean_total_time_ms"]),
            ),
        )
    else:
        recall_ok = [r for r in balanced_candidates if float(r["recall@k"]) >= float(args.recall_threshold)]
        pool = recall_ok if recall_ok else balanced_candidates
        balanced = (
            max(
                pool,
                key=lambda r: (
                    float(r["ndcg@k"]),
                    float(r["recall@k"]),
                    -float(r["mean_total_time_ms"]),
                ),
            )
            if pool
            else None
        )

    bottleneck_msg = "Insufficient data."
    if balanced is not None:
        cand = float(balanced["candidate_hit_rate@limit"])
        rec = float(balanced["recall@k"])
        if cand < float(args.recall_threshold):
            bottleneck_msg = (
                f"Retrieval coverage bottleneck: candidate_hit_rate={cand:.4f} is below target "
                f"{float(args.recall_threshold):.4f}."
            )
        elif cand - rec > 0.20:
            bottleneck_msg = (
                f"Ordering bottleneck after candidate generation: candidate_hit_rate={cand:.4f} vs "
                f"recall@k={rec:.4f} (gap={cand - rec:.4f})."
            )
        else:
            bottleneck_msg = (
                f"Mixed/limited bottleneck: candidate_hit_rate={cand:.4f}, recall@k={rec:.4f}."
            )

    def fmt_row(row: dict[str, Any] | None) -> str:
        if row is None:
            return "_not available_"
        return (
            f"mode={row['mode']}, L={row['retrieval_limit']}, k={row['k']}, "
            f"precision@k={float(row['precision@k']):.4f}, recall@k={float(row['recall@k']):.4f}, "
            f"ndcg@k={float(row['ndcg@k']):.4f}, mrr@k={float(row['mrr@k']):.4f}, "
            f"candidate_hit_rate@limit={float(row['candidate_hit_rate@limit']):.4f}, "
            f"total_ms={float(row['mean_total_time_ms']):.2f}"
        )

    lines = [
        "# Evaluation Suite Report",
        "",
        "## Inputs",
        f"- queries: `{args.queries}`",
        f"- qrels: `{args.qrels}`",
        f"- mode: `{args.mode}`",
        f"- retrieval_mode: `{args.retrieval_mode}`",
        f"- hybrid_alpha: `{args.hybrid_alpha}`",
        f"- shard: `{args.shard}`",
        f"- rerank_source: `{args.rerank_source}`",
        f"- retrieval limits: `{args.retrieval_limit_list}`",
        f"- k list: `{args.k_list}`",
        "",
        "## Coverage Checks",
        f"- total queries loaded: **{qid_total}**",
        f"- queries evaluated (have qrels + positive relevance): **{qid_eval_count}**",
        f"- queries missing qrels: **{len(qid_missing_qrels)}**",
        f"- qrels missing query text: **{len(qid_missing_queries)}**",
        f"- queries with zero relevant docs (skipped for metrics): **{len(qid_zero_rel)}**",
        "",
        "## Best Configs",
        f"- best ndcg@10: {fmt_row(best_ndcg10)}",
        f"- best ndcg@50: {fmt_row(best_ndcg50)}",
        f"- best recall@200: {fmt_row(best_recall200)}",
        "",
        "## Balanced Config",
        f"- method: maximize `ndcg@{balanced_k}` subject to `recall@{balanced_k} >= {float(args.recall_threshold):.2f}` "
        + (f"and `mean_total_time_ms <= {latency_cap_ms:.2f}`" if latency_cap_ms is not None else ""),
        f"- selected: {fmt_row(balanced)}",
        "",
        "## Bottleneck Interpretation",
        f"- {bottleneck_msg}",
        "",
        "## Rank Shift (Relevant Docs Appearing in Either List)",
        f"- n points: {int(rank_shift_summary.get('n', 0.0))}",
        f"- improved: {rank_shift_summary.get('improved_pct', 0.0):.2f}%",
        f"- worsened: {rank_shift_summary.get('worsened_pct', 0.0):.2f}%",
        f"- unchanged: {rank_shift_summary.get('unchanged_pct', 0.0):.2f}%",
        "",
        "## Warnings",
    ]
    if warnings:
        lines.extend([f"- {w}" for w in warnings])
    else:
        lines.append("- none")
    lines.append("")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run qrels evaluation suite with sweeps + diagnostics plots.")
    parser.add_argument("--queries", type=Path, required=True)
    parser.add_argument("--qrels", type=Path, required=True)
    parser.add_argument("--mode", type=str, required=True, choices=["retrieve", "rerank", "both"])
    parser.add_argument("--retrieval-limit-list", type=str, default="100,200,400,800,1200,2000")
    parser.add_argument("--k-list", type=str, default="10,20,50,100,200")
    parser.add_argument(
        "--rerank-k",
        type=int,
        default=None,
        help="Rerank top-K candidates. Default: retrieval limit for each sweep point.",
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--shard", type=str, default="128_f16")
    parser.add_argument("--seed", type=int, default=13)
    parser.add_argument("--cache-dir", type=Path, default=None)
    parser.add_argument("--retrieval-mode", type=str, default="vector", choices=["vector", "bm25", "hybrid"])
    parser.add_argument("--hybrid-alpha", type=float, default=0.5)
    parser.add_argument("--rerank-source", type=str, default="weaviate", choices=["lmdb", "weaviate"])
    parser.add_argument("--diag-limit", type=int, default=None, help="Limit to use for detailed plots. Default=max L.")
    parser.add_argument("--diag-k", type=int, default=200, help="k used by per-query histogram/scatter dashboard.")
    parser.add_argument("--curve-kmax", type=int, default=200, help="Max k used for PR/DCG curves.")
    parser.add_argument("--heat-k", type=int, default=200, help="Heatmap rank width.")
    parser.add_argument("--balanced-k", type=int, default=50)
    parser.add_argument("--recall-threshold", type=float, default=0.70)
    parser.add_argument(
        "--latency-cap-ms",
        type=float,
        default=None,
        help="Optional latency cap for balanced config selection. Default: 1.5x median total time.",
    )
    args = parser.parse_args()

    if args.rerank_k is not None and args.rerank_k <= 0:
        raise SystemExit("--rerank-k must be > 0 when provided.")
    if not (0.0 <= float(args.hybrid_alpha) <= 1.0):
        raise SystemExit("--hybrid-alpha must be in [0, 1].")

    limits = _parse_int_list(args.retrieval_limit_list, "--retrieval-limit-list")
    ks = _parse_int_list(args.k_list, "--k-list")

    diag_limit = int(args.diag_limit) if args.diag_limit is not None else max(limits)
    if diag_limit not in limits:
        raise SystemExit(f"--diag-limit={diag_limit} must be one of retrieval limits: {limits}")
    diag_k = min(int(args.diag_k), diag_limit)
    kmax = min(int(args.curve_kmax), diag_limit)
    kheat = min(int(args.heat_k), diag_limit)

    _set_seeds(int(args.seed))
    rr = _install_query_embedding_cache(args.cache_dir)

    queries = _load_queries(args.queries)
    qrels, id_field = _load_qrels(args.qrels)
    if id_field not in {"claim_id", "doc_id"}:
        raise SystemExit(
            f"Unsupported qrels id field '{id_field}'. Expected claim_id or doc_id."
        )

    qids_queries = set(queries.keys())
    qids_qrels = set(qrels.keys())
    qid_missing_qrels = sorted(qids_queries - qids_qrels)
    qid_missing_queries = sorted(qids_qrels - qids_queries)
    qids_intersection = sorted(qids_queries & qids_qrels)
    if not qids_intersection:
        raise SystemExit("No overlapping query ids between queries and qrels.")

    qid_zero_rel = sorted(
        qid for qid in qids_intersection if not positive_relevant_ids(qrels[qid])
    )
    eval_qids = [qid for qid in qids_intersection if qid not in set(qid_zero_rel)]
    if not eval_qids:
        raise SystemExit("After filtering zero-relevance queries, no queries remain for evaluation.")

    warnings: list[str] = []
    if qid_missing_qrels:
        warnings.append(f"{len(qid_missing_qrels)} query ids from queries are missing in qrels.")
    if qid_missing_queries:
        warnings.append(f"{len(qid_missing_queries)} qrels query ids are missing in queries file.")
    if qid_zero_rel:
        warnings.append(f"{len(qid_zero_rel)} queries have zero relevant docs and were skipped for metrics.")

    output_dir = Path(args.output_dir)
    runs_dir = output_dir / "runs"
    plots_dir = output_dir / "plots"
    output_dir.mkdir(parents=True, exist_ok=True)
    runs_dir.mkdir(parents=True, exist_ok=True)
    plots_dir.mkdir(parents=True, exist_ok=True)

    run_modes = ["retrieve", "rerank"] if args.mode == "both" else [args.mode]
    need_rerank = "rerank" in run_modes

    summary_rows: list[dict[str, Any]] = []
    per_query_rows: list[dict[str, Any]] = []

    selected_runs_by_mode: dict[str, dict[str, list[str]]] = {}
    id_field_presence_checked = False

    for limit in limits:
        print(f"[sweep] retrieval_limit={limit}")
        retrieve_runs_qid: dict[str, list[RunRecord]] = {}
        rerank_runs_qid: dict[str, list[RunRecord]] = {}
        retrieve_times_qid: dict[str, dict[str, float]] = {}
        rerank_times_qid: dict[str, dict[str, float]] = {}

        effective_rerank_k = int(limit if args.rerank_k is None else min(int(args.rerank_k), int(limit)))

        for idx, qid in enumerate(eval_qids, start=1):
            query_text = queries[qid]
            print(f"[sweep] L={limit} q={idx}/{len(eval_qids)} mode=retrieve")

            t0 = time.perf_counter()
            hits = rr.retrieve_claims(
                query_text,
                limit=int(limit),
                shard=args.shard,
                retrieval_mode=args.retrieval_mode,
                hybrid_alpha=float(args.hybrid_alpha),
            )
            retrieval_ms = (time.perf_counter() - t0) * 1000.0
            retrieve_records = _build_run_records(qid, hits, id_field=id_field)
            retrieve_runs_qid[qid] = retrieve_records
            retrieve_times_qid[qid] = {
                "retrieval_ms": retrieval_ms,
                "rerank_ms": 0.0,
                "total_ms": retrieval_ms,
            }

            if not id_field_presence_checked:
                if id_field == "claim_id":
                    if not any((h.claim_id or "").strip() for h in hits):
                        raise RuntimeError(
                            "qrels uses claim_id but retrieval hits have empty claim_id values. "
                            "ID scheme mismatch; aborting."
                        )
                if id_field == "doc_id":
                    if not any((h.doc_id or "").strip() for h in hits):
                        raise RuntimeError(
                            "qrels uses doc_id but retrieval hits have empty doc_id values. "
                            "ID scheme mismatch; aborting."
                        )
                id_field_presence_checked = True

            if need_rerank:
                print(f"[sweep] L={limit} q={idx}/{len(eval_qids)} mode=rerank")
                query_tokens = rr._embed_query_tokens(query_text, args.shard)
                t1 = time.perf_counter()
                reranked_hits = rr.rerank_hits(
                    list(hits),
                    query_text,
                    shard=args.shard,
                    rerank_k=effective_rerank_k,
                    rerank_source=args.rerank_source,
                    query_tokens=query_tokens,
                )
                rerank_ms = (time.perf_counter() - t1) * 1000.0
                rerank_records = _build_run_records(qid, reranked_hits, id_field=id_field)
                rerank_runs_qid[qid] = rerank_records
                rerank_times_qid[qid] = {
                    "retrieval_ms": retrieval_ms,
                    "rerank_ms": rerank_ms,
                    "total_ms": retrieval_ms + rerank_ms,
                }

        _write_run_file(runs_dir / f"retrieve_L{limit}.run", retrieve_runs_qid, tag=f"retrieve_L{limit}")
        if need_rerank:
            _write_run_file(runs_dir / f"rerank_L{limit}.run", rerank_runs_qid, tag=f"rerank_L{limit}")

        retrieve_run_qids = {qid for qid, rows in retrieve_runs_qid.items() if rows}
        if len(retrieve_run_qids) != len(eval_qids):
            warnings.append(
                f"retrieve_L{limit}.run has {len(retrieve_run_qids)} queries with rows; expected {len(eval_qids)}."
            )
        if need_rerank:
            rerank_run_qids = {qid for qid, rows in rerank_runs_qid.items() if rows}
            if len(rerank_run_qids) != len(eval_qids):
                warnings.append(
                    f"rerank_L{limit}.run has {len(rerank_run_qids)} queries with rows; expected {len(eval_qids)}."
                )

        if limit == diag_limit:
            selected_runs_by_mode["retrieve"] = {
                qid: [r.target_id for r in rows] for qid, rows in retrieve_runs_qid.items()
            }
            if need_rerank:
                selected_runs_by_mode["rerank"] = {
                    qid: [r.target_id for r in rows] for qid, rows in rerank_runs_qid.items()
                }

        for k in ks:
            if k > limit:
                continue
            for mode in run_modes:
                runs = retrieve_runs_qid if mode == "retrieve" else rerank_runs_qid
                times = retrieve_times_qid if mode == "retrieve" else rerank_times_qid

                p_vals: list[float] = []
                r_vals: list[float] = []
                n_vals: list[float] = []
                m_vals: list[float] = []
                c_vals: list[float] = []
                timing_rows: list[dict[str, float]] = []

                for qid in eval_qids:
                    rel_map = qrels[qid]
                    ranked_ids = [r.target_id for r in runs.get(qid, [])]
                    candidate_ids = [r.target_id for r in retrieve_runs_qid.get(qid, [])]
                    qm = compute_query_metrics(
                        ranked_ids=ranked_ids,
                        rel_map=rel_map,
                        candidate_ids=candidate_ids,
                        k=int(k),
                    )
                    p_vals.append(qm.precision)
                    r_vals.append(qm.recall)
                    n_vals.append(qm.ndcg)
                    m_vals.append(qm.mrr)
                    c_vals.append(1.0 if qm.candidate_hit else 0.0)
                    trow = times[qid]
                    timing_rows.append(trow)

                    per_query_rows.append(
                        {
                            "mode": mode,
                            "retrieval_limit": int(limit),
                            "k": int(k),
                            "query_id": qid,
                            "num_relevant": int(qm.num_relevant),
                            "candidate_hit": bool(qm.candidate_hit),
                            "candidate_hit_count": int(qm.candidate_hit_count),
                            "first_relevant_rank": "" if qm.first_rel_rank is None else int(qm.first_rel_rank),
                            "precision@k": float(qm.precision),
                            "recall@k": float(qm.recall),
                            "ndcg@k": float(qm.ndcg),
                            "mrr@k": float(qm.mrr),
                            "retrieval_ms": float(trow["retrieval_ms"]),
                            "rerank_ms": float(trow["rerank_ms"]),
                            "total_ms": float(trow["total_ms"]),
                            "candidate_hit_rate@limit": 1.0 if qm.candidate_hit else 0.0,
                            "id_field": id_field,
                            "retrieval_mode": args.retrieval_mode,
                            "hybrid_alpha": float(args.hybrid_alpha),
                            "rerank_source": args.rerank_source,
                        }
                    )

                mean_retrieval_ms, mean_rerank_ms, mean_total_ms = _mean_timing_ms(timing_rows)
                summary_rows.append(
                    {
                        "mode": mode,
                        "retrieval_limit": int(limit),
                        "k": int(k),
                        "num_queries": len(eval_qids),
                        "precision@k": mean(p_vals),
                        "recall@k": mean(r_vals),
                        "ndcg@k": mean(n_vals),
                        "mrr@k": mean(m_vals),
                        "candidate_hit_rate@limit": mean(c_vals),
                        "mean_retrieval_time_ms": mean_retrieval_ms,
                        "mean_rerank_time_ms": mean_rerank_ms,
                        "mean_total_time_ms": mean_total_ms,
                        "rerank_k": int(effective_rerank_k),
                        "id_field": id_field,
                        "retrieval_mode": args.retrieval_mode,
                        "hybrid_alpha": float(args.hybrid_alpha),
                        "rerank_source": args.rerank_source,
                    }
                )

    for mode in run_modes:
        for k in ks:
            rows = [r for r in summary_rows if r["mode"] == mode and int(r["k"]) == int(k)]
            rows.sort(key=lambda r: int(r["retrieval_limit"]))
            recalls = [float(r["recall@k"]) for r in rows]
            limits_seq = [int(r["retrieval_limit"]) for r in rows]
            for i in range(1, len(recalls)):
                if recalls[i] + 1e-12 < recalls[i - 1]:
                    warnings.append(
                        f"Recall non-monotonic for mode={mode}, k={k}: "
                        f"L={limits_seq[i-1]}->{limits_seq[i]} gives {recalls[i-1]:.4f}->{recalls[i]:.4f}"
                    )

    summary_fieldnames = [
        "mode",
        "retrieval_limit",
        "k",
        "num_queries",
        "precision@k",
        "recall@k",
        "ndcg@k",
        "mrr@k",
        "candidate_hit_rate@limit",
        "mean_retrieval_time_ms",
        "mean_rerank_time_ms",
        "mean_total_time_ms",
        "rerank_k",
        "id_field",
        "retrieval_mode",
        "hybrid_alpha",
        "rerank_source",
    ]
    per_query_fieldnames = [
        "mode",
        "retrieval_limit",
        "k",
        "query_id",
        "num_relevant",
        "candidate_hit",
        "candidate_hit_count",
        "first_relevant_rank",
        "precision@k",
        "recall@k",
        "ndcg@k",
        "mrr@k",
        "retrieval_ms",
        "rerank_ms",
        "total_ms",
        "candidate_hit_rate@limit",
        "id_field",
        "retrieval_mode",
        "hybrid_alpha",
        "rerank_source",
    ]
    _write_csv(output_dir / "summary_metrics.csv", summary_rows, summary_fieldnames)
    _write_csv(output_dir / "per_query_metrics.csv", per_query_rows, per_query_fieldnames)

    diag_rows_by_mode = {
        mode: [
            row
            for row in per_query_rows
            if row["mode"] == mode
            and int(row["retrieval_limit"]) == int(diag_limit)
            and int(row["k"]) == int(diag_k)
        ]
        for mode in run_modes
    }

    first_rel_by_mode: dict[str, list[int]] = {}
    recall_by_mode: dict[str, list[float]] = {}
    mrr_by_mode: dict[str, list[float]] = {}
    scatter_by_mode: dict[str, list[tuple[int, float]]] = {}
    for mode in run_modes:
        rows = diag_rows_by_mode.get(mode, [])
        first_rel_by_mode[mode] = [
            int(r["first_relevant_rank"]) if str(r["first_relevant_rank"]).strip() else (diag_k + 1)
            for r in rows
        ]
        recall_by_mode[mode] = [float(r["recall@k"]) for r in rows]
        mrr_by_mode[mode] = [float(r["mrr@k"]) for r in rows]
        scatter_by_mode[mode] = [(int(r["num_relevant"]), float(r["ndcg@k"])) for r in rows]

    plot_hist_first_relevant_rank(
        first_rel_by_mode,
        k=diag_k,
        out_path=plots_dir / "hist_first_rel_rank.png",
    )
    plot_hist_metric(
        recall_by_mode,
        metric_label=f"recall@{diag_k}",
        out_path=plots_dir / "hist_recall_k.png",
    )
    plot_hist_metric(
        mrr_by_mode,
        metric_label=f"mrr@{diag_k}",
        out_path=plots_dir / "hist_mrr_k.png",
    )
    plot_scatter_ndcg_vs_num_rel(
        scatter_by_mode,
        out_path=plots_dir / "scatter_ndcg_vs_num_relevant.png",
        k=diag_k,
    )

    curves_by_mode: dict[str, dict[str, list[float]]] = {}
    gains_by_mode: dict[str, dict[str, list[float]]] = {}
    for mode in run_modes:
        runs = selected_runs_by_mode.get(mode, {})
        if not runs:
            continue
        curves_by_mode[mode] = average_pr_curve(runs, qrels, eval_qids, kmax)
        gains_by_mode[mode] = cumulative_gain_curves(runs, qrels, eval_qids, kmax)

    if curves_by_mode:
        plot_pr_curve(curves_by_mode, out_path=plots_dir / "pr_curve.png")
        plot_recall_vs_k(curves_by_mode, out_path=plots_dir / "recall_vs_k.png")
    if gains_by_mode:
        plot_dcg_curves(gains_by_mode, out_path=plots_dir / "dcg_curve.png")

    rank_shift_points: list[tuple[int, int]] = []
    if "retrieve" in selected_runs_by_mode and "rerank" in selected_runs_by_mode:
        for qid in eval_qids:
            rel_ids = positive_relevant_ids(qrels[qid])
            before = selected_runs_by_mode["retrieve"].get(qid, [])
            after = selected_runs_by_mode["rerank"].get(qid, [])
            before_rank = {doc_id: i for i, doc_id in enumerate(before[:kmax], start=1)}
            after_rank = {doc_id: i for i, doc_id in enumerate(after[:kmax], start=1)}
            missing_rank = kmax + 1
            for rid in rel_ids:
                b = before_rank.get(rid, missing_rank)
                a = after_rank.get(rid, missing_rank)
                if b <= kmax or a <= kmax:
                    rank_shift_points.append((b, a))
    plot_rank_shift(
        rank_shift_points,
        kmax=kmax,
        out_path=plots_dir / "rank_shift.png",
    )
    rank_shift_summary = _summarize_rank_shift(rank_shift_points)

    retrieve_matrix = relevance_heatmap_matrix(
        selected_runs_by_mode.get("retrieve", {}),
        qrels,
        eval_qids,
        kheat,
    )
    rerank_matrix = relevance_heatmap_matrix(
        selected_runs_by_mode.get("rerank", {}),
        qrels,
        eval_qids,
        kheat,
    )
    plot_relevance_heatmap(
        retrieve_matrix,
        out_path=plots_dir / "heatmap_retrieve.png",
        title=f"Relevant Distribution Heatmap - Retrieve (K={kheat})",
    )
    plot_relevance_heatmap(
        rerank_matrix,
        out_path=plots_dir / "heatmap_rerank.png",
        title=f"Relevant Distribution Heatmap - Rerank (K={kheat})",
    )

    _write_report(
        output_dir / "report.md",
        args=args,
        qid_total=len(queries),
        qid_eval_count=len(eval_qids),
        qid_missing_qrels=qid_missing_qrels,
        qid_missing_queries=qid_missing_queries,
        qid_zero_rel=qid_zero_rel,
        summary_rows=summary_rows,
        warnings=warnings,
        rank_shift_summary=rank_shift_summary,
    )

    print(f"[done] Wrote summary metrics: {output_dir / 'summary_metrics.csv'}")
    print(f"[done] Wrote per-query metrics: {output_dir / 'per_query_metrics.csv'}")
    print(f"[done] Wrote report: {output_dir / 'report.md'}")
    print(f"[done] Wrote plots under: {plots_dir}")
    print(f"[done] Wrote run files under: {runs_dir}")


if __name__ == "__main__":
    main()
