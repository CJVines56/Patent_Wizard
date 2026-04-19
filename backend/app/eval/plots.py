from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def _save(fig: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def plot_hist_first_relevant_rank(
    first_rel_ranks_by_mode: dict[str, list[int]],
    *,
    k: int,
    out_path: Path,
) -> None:
    fig, ax = plt.subplots(figsize=(10, 6))
    bins = np.arange(1, k + 3) - 0.5
    for mode, vals in first_rel_ranks_by_mode.items():
        if not vals:
            continue
        ax.hist(vals, bins=bins, alpha=0.45, label=mode)
    ax.set_title(f"First Relevant Rank Distribution (<= {k})")
    ax.set_xlabel("First relevant rank")
    ax.set_ylabel("Query count")
    if len(first_rel_ranks_by_mode) > 1:
        ax.legend()
    ax.grid(alpha=0.25, linestyle="--")
    _save(fig, out_path)


def plot_hist_metric(
    metric_by_mode: dict[str, list[float]],
    *,
    metric_label: str,
    out_path: Path,
) -> None:
    fig, ax = plt.subplots(figsize=(10, 6))
    bins = np.linspace(0.0, 1.0, 21)
    for mode, vals in metric_by_mode.items():
        if not vals:
            continue
        ax.hist(vals, bins=bins, alpha=0.45, label=mode)
    ax.set_title(f"{metric_label} Distribution")
    ax.set_xlabel(metric_label)
    ax.set_ylabel("Query count")
    if len(metric_by_mode) > 1:
        ax.legend()
    ax.grid(alpha=0.25, linestyle="--")
    _save(fig, out_path)


def plot_scatter_ndcg_vs_num_rel(
    points_by_mode: dict[str, list[tuple[int, float]]],
    *,
    out_path: Path,
    k: int,
) -> None:
    fig, ax = plt.subplots(figsize=(10, 6))
    for mode, pts in points_by_mode.items():
        if not pts:
            continue
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        ax.scatter(xs, ys, alpha=0.6, s=20, label=mode)
    ax.set_title(f"nDCG@{k} vs Number of Relevant Docs (|R|)")
    ax.set_xlabel("|R|")
    ax.set_ylabel(f"nDCG@{k}")
    if len(points_by_mode) > 1:
        ax.legend()
    ax.grid(alpha=0.25, linestyle="--")
    _save(fig, out_path)


def plot_pr_curve(
    curves_by_mode: dict[str, dict[str, list[float]]],
    *,
    out_path: Path,
) -> None:
    fig, ax = plt.subplots(figsize=(8, 7))
    for mode, curve in curves_by_mode.items():
        recall = curve.get("recall", [])
        precision = curve.get("precision", [])
        if not recall or not precision:
            continue
        ax.plot(recall, precision, linewidth=2, label=mode)
    ax.set_title("Precision-Recall Curve (Average Across Queries)")
    ax.set_xlabel("Recall")
    ax.set_ylabel("Precision")
    ax.set_xlim(0.0, 1.0)
    ax.set_ylim(0.0, 1.0)
    ax.grid(alpha=0.25, linestyle="--")
    if len(curves_by_mode) > 1:
        ax.legend()
    _save(fig, out_path)


def plot_recall_vs_k(
    curves_by_mode: dict[str, dict[str, list[float]]],
    *,
    out_path: Path,
) -> None:
    fig, ax = plt.subplots(figsize=(10, 6))
    for mode, curve in curves_by_mode.items():
        ks = curve.get("k", [])
        recall = curve.get("recall", [])
        if not ks or not recall:
            continue
        ax.plot(ks, recall, linewidth=2, label=mode)
    ax.set_title("Recall vs Rank Cutoff (k)")
    ax.set_xlabel("k")
    ax.set_ylabel("Recall@k")
    ax.set_ylim(0.0, 1.0)
    ax.grid(alpha=0.25, linestyle="--")
    if len(curves_by_mode) > 1:
        ax.legend()
    _save(fig, out_path)


def plot_dcg_curves(
    gain_by_mode: dict[str, dict[str, list[float]]],
    *,
    out_path: Path,
) -> None:
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10), sharex=True)
    for mode, curve in gain_by_mode.items():
        ks = curve.get("k", [])
        dcg = curve.get("dcg", [])
        ndcg = curve.get("ndcg", [])
        if ks and dcg:
            ax1.plot(ks, dcg, linewidth=2, label=mode)
        if ks and ndcg:
            ax2.plot(ks, ndcg, linewidth=2, label=mode)

    ax1.set_title("Mean DCG Accumulation vs Rank")
    ax1.set_ylabel("DCG@r")
    ax1.grid(alpha=0.25, linestyle="--")
    if len(gain_by_mode) > 1:
        ax1.legend()

    ax2.set_title("Mean nDCG Accumulation vs Rank")
    ax2.set_xlabel("rank r")
    ax2.set_ylabel("nDCG@r")
    ax2.set_ylim(0.0, 1.0)
    ax2.grid(alpha=0.25, linestyle="--")
    if len(gain_by_mode) > 1:
        ax2.legend()
    _save(fig, out_path)


def plot_rank_shift(
    points: list[tuple[int, int]],
    *,
    kmax: int,
    out_path: Path,
) -> None:
    fig, ax = plt.subplots(figsize=(8, 8))
    if points:
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        ax.scatter(xs, ys, s=18, alpha=0.45)
    ax.plot([1, kmax + 1], [1, kmax + 1], linestyle="--", linewidth=2, color="black")
    ax.set_title("Rank Shift (Retrieve vs Rerank) for Relevant Docs")
    ax.set_xlabel("Retrieve rank (x)")
    ax.set_ylabel("Rerank rank (y)")
    ax.set_xlim(1, kmax + 1)
    ax.set_ylim(1, kmax + 1)
    ax.grid(alpha=0.25, linestyle="--")
    _save(fig, out_path)


def plot_relevance_heatmap(
    matrix: np.ndarray,
    *,
    out_path: Path,
    title: str,
) -> None:
    fig, ax = plt.subplots(figsize=(12, 6))
    if matrix.size == 0:
        ax.text(0.5, 0.5, "No data", ha="center", va="center")
        ax.set_axis_off()
        _save(fig, out_path)
        return

    im = ax.imshow(matrix, aspect="auto", interpolation="nearest", cmap="Greys")
    ax.set_title(title)
    ax.set_xlabel("Rank position")
    ax.set_ylabel("Query index")
    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label("Relevant hit (1=yes, 0=no)")
    _save(fig, out_path)

