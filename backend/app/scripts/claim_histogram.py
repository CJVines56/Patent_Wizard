"""
Generate a histogram of claims per patent from Weaviate Claim objects.
Outputs a PNG chart with a mean line.
"""
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt
import requests


WEAVIATE_URL = "http://localhost:8080/v1/objects"
OUT_PATH = Path(__file__).resolve().parents[2] / "validation" / "claims_per_patent_hist.png"


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


def main():
    counts_by_doc = fetch_claim_counts()
    if not counts_by_doc:
        raise RuntimeError("No Claim objects found in Weaviate.")
    counts = list(counts_by_doc.values())
    mean_val = sum(counts) / len(counts)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(10, 6))
    hist_vals, bin_edges, _ = plt.hist(
        counts, bins=30, color="#3B82F6", alpha=0.85, edgecolor="white"
    )
    plt.axvline(mean_val, color="#EF4444", linewidth=2, linestyle="--", label=f"Mean = {mean_val:.2f}")
    if len(hist_vals) > 0:
        max_idx = int(hist_vals.argmax())
        max_count = int(hist_vals[max_idx])
        bin_left = bin_edges[max_idx]
        bin_right = bin_edges[max_idx + 1]
        bin_center = (bin_left + bin_right) / 2.0
        plt.annotate(
            f"Max bin: {max_count} patents\n~{bin_center:.1f} claims",
            xy=(bin_center, max_count),
            xytext=(bin_center + 5, max_count),
            arrowprops=dict(arrowstyle="->", color="#111827"),
            fontsize=9,
            color="#111827",
        )
    plt.title("Claims per Patent (Histogram)")
    plt.xlabel("Number of Claims per Patent")
    plt.ylabel("Number of Patents")
    plt.legend()
    plt.tight_layout()
    plt.savefig(OUT_PATH, dpi=150)
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
