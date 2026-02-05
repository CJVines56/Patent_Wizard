"""
Generate a histogram of claims per patent from Weaviate Claim objects.
Outputs a PNG chart with a mean line.
"""
from collections import Counter
from pathlib import Path
import csv
import os

import matplotlib.pyplot as plt
import requests


WEAVIATE_URL = "http://localhost:8080/v1/objects"
OUT_PATH = Path(__file__).resolve().parents[2] / "validation" / "claims_per_patent_hist.png"
OUTLIERS_PATH = Path(__file__).resolve().parents[2] / "validation" / "claims_per_patent_outliers.csv"


def fetch_claim_counts(limit: int = 500) -> Counter:
    counter = Counter()
    next_after = None
    while True:
        params = {"class": "Claim", "limit": str(limit)}
        if next_after:
            params["after"] = next_after
        resp = requests.get(WEAVIATE_URL, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        items = data.get("objects", []) or []
        if not items:
            break
        for obj in items:
            props = obj.get("properties", {}) or {}
            doc_id = props.get("doc_id")
            if doc_id:
                counter[doc_id] += 1
        next_after = items[-1].get("id")
    return counter


def _percentile(values: list[int], pct: float) -> float:
    if not values:
        return 0.0
    vals = sorted(values)
    k = (len(vals) - 1) * (pct / 100.0)
    f = int(k)
    c = min(f + 1, len(vals) - 1)
    if f == c:
        return float(vals[f])
    return vals[f] + (vals[c] - vals[f]) * (k - f)


def _format_percentiles(counts: list[int]) -> dict[str, float]:
    return {
        "p50": _percentile(counts, 50.0),
        "p90": _percentile(counts, 90.0),
        "p95": _percentile(counts, 95.0),
        "p99": _percentile(counts, 99.0),
    }


def _write_outliers(counts_by_doc: Counter, outliers: list[tuple[str, int]]):
    OUTLIERS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTLIERS_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["doc_id", "claim_count"])
        for doc_id, count in outliers:
            writer.writerow([doc_id, count])
    print(f"Wrote {OUTLIERS_PATH}")


def main():
    counts_by_doc = fetch_claim_counts()
    if not counts_by_doc:
        raise RuntimeError("No Claim objects found in Weaviate.")
    counts = list(counts_by_doc.values())
    mean_val = sum(counts) / len(counts)
    percentiles = _format_percentiles(counts)

    trunc_val = int(os.environ.get("CLAIM_HIST_TRUNC_VALUE", "60"))
    truncated = [c for c in counts if c <= trunc_val]
    outliers = sorted(
        ((doc_id, cnt) for doc_id, cnt in counts_by_doc.items() if cnt > trunc_val),
        key=lambda x: x[1],
        reverse=True,
    )

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(10, 6))
    hist_vals, bin_edges, _ = plt.hist(
        truncated, bins=30, color="#3B82F6", alpha=0.85, edgecolor="white"
    )
    ax.axvline(mean_val, color="#EF4444", linewidth=2, linestyle="--", label=f"Mean = {mean_val:.2f}")
    if len(hist_vals) > 0:
        max_idx = int(hist_vals.argmax())
        max_count = int(hist_vals[max_idx])
        bin_left = bin_edges[max_idx]
        bin_right = bin_edges[max_idx + 1]
        bin_center = (bin_left + bin_right) / 2.0
        ax.annotate(
            f"Max bin: {max_count} patents\n~{bin_center:.1f} claims",
            xy=(bin_center, max_count),
            xytext=(bin_center + 5, max_count),
            arrowprops=dict(arrowstyle="->", color="#111827"),
            fontsize=9,
            color="#111827",
        )
    ax.set_title(f"Claims per Patent (Histogram, ≤ {trunc_val})")
    ax.set_xlabel("Number of Claims per Patent")
    ax.set_ylabel("Number of Patents")
    ax.legend(loc="upper left")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # Tail zoom inset (45+ claims per patent)
    tail_min = 45
    tail = [c for c in counts if c >= tail_min]
    if tail and len(tail) >= 5:
        axins = ax.inset_axes([0.582, 0.52, 0.38, 0.38])
        axins.hist(tail, bins=20, color="#1D4ED8", alpha=0.9, edgecolor="white")
        axins.set_title(f"Tail (≥ {tail_min})", fontsize=9)
        axins.tick_params(labelsize=8)
        axins.spines["top"].set_visible(False)
        axins.spines["right"].set_visible(False)
        try:
            from mpl_toolkits.axes_grid1.inset_locator import mark_inset
            _, con1, con2 = mark_inset(ax, axins, loc1=3, loc2=2, fc="none", ec="#111827")
            con2.set_visible(False)
        except Exception:
            pass

    ax.text(
        0.02,
        0.92,
        f"p50={percentiles['p50']:.0f}  p90={percentiles['p90']:.0f}\n"
        f"p95={percentiles['p95']:.0f}  p99={percentiles['p99']:.0f}",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=9,
        bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor="#D1D5DB"),
    )

    fig.tight_layout()
    fig.savefig(OUT_PATH, dpi=150)
    print(f"Wrote {OUT_PATH}")
    print(f"[info] truncation value={trunc_val}; outliers={len(outliers)}")
    if outliers:
        _write_outliers(counts_by_doc, outliers[:50])


if __name__ == "__main__":
    main()
