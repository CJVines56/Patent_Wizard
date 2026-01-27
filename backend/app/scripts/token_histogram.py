"""
Generate a histogram of tokens per claim from Weaviate Claim objects.
Outputs a PNG chart with a mean line.
"""
from collections import Counter
from pathlib import Path
import re

import matplotlib.pyplot as plt
import requests


WEAVIATE_URL = "http://localhost:8080/v1/objects"
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

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(10, 6))
    plt.hist(counts, bins=40, color="#10B981", alpha=0.9, edgecolor="white")
    plt.axvline(mean_val, color="#EF4444", linewidth=2, linestyle="--", label=f"Mean = {mean_val:.1f}")
    plt.title("Tokens per Claim (Histogram)")
    plt.xlabel("Number of Tokens per Claim")
    plt.ylabel("Number of Claims")
    plt.legend()
    plt.tight_layout()
    plt.savefig(OUT_PATH, dpi=150)
    print(f"Wrote {OUT_PATH} (max_tokens={max_val})")


if __name__ == "__main__":
    main()

