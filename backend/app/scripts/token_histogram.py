"""
Generate a histogram of tokens per claim from Weaviate Claim objects.
Outputs a PNG chart with a mean line.
"""
from collections import Counter
from pathlib import Path
import os
import re

import matplotlib.pyplot as plt
import requests


WEAVIATE_URL = "http://localhost:8081/v1/objects"
OUT_PATH = Path(__file__).resolve().parents[2] / "validation" / "tokens_per_claim_hist.png"


def _token_count(text: str) -> int:
    return len(re.findall(r"[A-Za-z0-9]+", text or ""))


def fetch_token_counts(limit: int = 500) -> list[int]:
    counts: list[int] = []
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
            text = props.get("text") or ""
            counts.append(_token_count(text))
        next_after = items[-1].get("id")
    return counts


def main():
    counts = fetch_token_counts()
    if not counts:
        raise RuntimeError("No Claim objects found in Weaviate.")
    mean_val = sum(counts) / len(counts)
    max_val = max(counts)
    split_limit = int(os.environ.get("SPLIT_TOKEN_LIMIT", "350"))
    over_limit = sum(1 for c in counts if c > split_limit)
    over_pct = (over_limit / len(counts)) * 100.0 if counts else 0.0

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.hist(counts, bins=40, color="#10B981", alpha=0.9, edgecolor="white")
    ax.axvline(mean_val, color="#EF4444", linewidth=2, linestyle="--", label=f"Mean = {mean_val:.1f}")
    ax.set_title("Tokens per Claim (Histogram)")
    ax.set_xlabel("Number of Tokens per Claim")
    ax.set_ylabel("Number of Claims")
    ax.legend()
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    ax.text(
        0.98,
        0.95,
        f"Over split limit ({split_limit}): {over_limit} / {len(counts)}\n({over_pct:.2f}% chunked)",
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=9,
        bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor="#D1D5DB"),
    )

    fig.tight_layout()
    fig.savefig(OUT_PATH, dpi=150)
    print(f"Wrote {OUT_PATH} (max_tokens={max_val})")


if __name__ == "__main__":
    main()
