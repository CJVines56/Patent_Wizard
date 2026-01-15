from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

# --- Configure your datasets here ---
# Each entry: name, total patents, mismatch CSV, skips CSV, optional date (YYYYMMDD or YYYY-MM-DD)
DATASETS = [
    {"name": "I20250401", "total": 6529, "mismatch": Path("metadata_mismatches.csv"), "skips": Path("metadata_mismatches_skips.csv"), "date": "2025-04-01"},
    {"name": "I20250429", "total": 5872, "mismatch": Path("metadata_mismatches2.csv"), "skips": Path("metadata_mismatches2_skips.csv"), "date": "2025-04-29"},
    {"name": "I20250527", "total": 8563, "mismatch": Path("metadata_mismatches3.csv"), "skips": Path("metadata_mismatches3_skips.csv"), "date": "2025-05-27"},
    {"name": "I20250701", "total": 7998, "mismatch": Path("metadata_mismatches4.csv"), "skips": Path("metadata_mismatches4_skips.csv"), "date": "2025-07-01"},
    {"name": "I20250729", "total": 7982, "mismatch": Path("metadata_mismatches5.csv"), "skips": Path("metadata_mismatches5_skips.csv"), "date": "2025-07-29"},
]

def _load_csv(path: Path, columns):
    if path.exists():
        return pd.read_csv(path)
    return pd.DataFrame(columns=columns)

def _format_date_label(cfg):
    import re
    if cfg.get("date"):
        s = str(cfg["date"])
        m = re.search(r"(\d{4})[-/]?(\d{2})[-/]?(\d{2})", s)
        if m:
            return f"{m.group(1)}/{m.group(2)}/{m.group(3)}"
    for source in [cfg.get("mismatch"), cfg.get("name")]:
        if not source:
            continue
        s = str(source)
        m = re.search(r"(20\d{2})(\d{2})(\d{2})", s)
        if m:
            return f"{m.group(1)}/{m.group(2)}/{m.group(3)}"
    return str(cfg.get("name", "run"))

summaries = []
for cfg in DATASETS:
    mismatches = _load_csv(cfg["mismatch"], ["doc_id", "field", "parsed", "api"])
    skips = _load_csv(cfg["skips"], ["doc_id", "reason"])
    cpc_ids = set(mismatches.loc[mismatches["field"] == "cpc", "doc_id"].dropna())
    title_ids = set(mismatches.loc[mismatches["field"] == "title", "doc_id"].dropna())
    skip_ids = set(skips.get("doc_id", []))
    error_ids = cpc_ids | title_ids | skip_ids
    success_count = max(int(cfg.get("total", 0)) - len(error_ids), 0)
    summaries.append({
        "name": cfg["name"],
        "label": _format_date_label(cfg),
        "success": success_count,
        "cpc_error": len(cpc_ids),
        "title_error": len(title_ids),
        "skips": len(skip_ids),
        "total": cfg.get("total", 0),
    })

pd.DataFrame(summaries)

if summaries:
    names = [s.get("label", s["name"]) for s in summaries]
    success = [s["success"] for s in summaries]
    cpc_err = [s["cpc_error"] for s in summaries]
    title_err = [s["title_error"] for s in summaries]
    skips = [s["skips"] for s in summaries]

    fig, ax = plt.subplots(figsize=(8, 4))
    width = 0.6
    ax.bar(names, success, width=width, label="Success", color="#4caf50", edgecolor="white", linewidth=0.6)
    ax.bar(names, cpc_err, width=width, bottom=success, label="CPC mismatch", color="#f44336", edgecolor="white", linewidth=0.6)
    ax.bar(names, title_err, width=width, bottom=[a+b for a,b in zip(success, cpc_err)], label="Title mismatch", color="#ff9800", edgecolor="white", linewidth=0.6)
    ax.bar(names, skips, width=width, bottom=[a+b+c for a,b,c in zip(success, cpc_err, title_err)], label="Skips", color="#9e9e9e", edgecolor="white", linewidth=0.6)
    ax.set_ylabel("# of patents in Dataset")
    ax.set_xlabel("Dataset release date")
    ax.set_title("Metadata Validation")
    ax.legend(framealpha=1.0, bbox_to_anchor=(0.5, -0.2), loc="upper center", ncols=4)
    # Grid and spine tweaks
    ax.set_axisbelow(True)
    ax.grid(True, axis="y", color="#e0e0e0", linestyle="-", linewidth=0.8)
    for spine in ['top', 'right', 'left']:
        ax.spines[spine].set_visible(False)
    plt.tight_layout()
    plt.savefig("plots.png", dpi=200)
    plt.show()
else:
    print("No summaries to plot. Check dataset config.")
