from pathlib import Path
import pandas as pd

# Configure your datasets: name (date), total patents, mismatch CSV, skips CSV
DATASETS = [
    {"name": "2025/04/01", "total": 6529, "mismatch": Path("metadata_mismatches.csv"), "skips": Path("metadata_mismatches_skips.csv")},
    {"name": "2025/04/29", "total": 5872, "mismatch": Path("metadata_mismatches2.csv"), "skips": Path("metadata_mismatches2_skips.csv")},
    {"name": "2025/05/27", "total": 8563, "mismatch": Path("metadata_mismatches3.csv"), "skips": Path("metadata_mismatches3_skips.csv")},
    {"name": "2025/07/01", "total": 7998, "mismatch": Path("metadata_mismatches4.csv"), "skips": Path("metadata_mismatches4_skips.csv")},
    {"name": "2025/07/29", "total": 7982, "mismatch": Path("metadata_mismatches5.csv"), "skips": Path("metadata_mismatches5_skips.csv")},
]


def _load_csv(path: Path, columns):
    if path.exists():
        return pd.read_csv(path)
    return pd.DataFrame(columns=columns)


def summarize_datasets():
    rows = []
    for cfg in DATASETS:
        mismatches = _load_csv(cfg["mismatch"], ["doc_id", "field", "parsed", "api"])
        skips = _load_csv(cfg["skips"], ["doc_id", "reason"])
        cpc_ids = set(mismatches.loc[mismatches["field"] == "cpc", "doc_id"].dropna())
        title_ids = set(mismatches.loc[mismatches["field"] == "title", "doc_id"].dropna())
        skip_ids = set(skips.get("doc_id", []))
        error_ids = cpc_ids | title_ids | skip_ids
        total = int(cfg.get("total", 0))
        success = max(total - len(error_ids), 0)
        rows.append({
            "Dataset": cfg["name"],
            "Success": int(success),
            "CPC Error": int(len(cpc_ids)),
            "Title Error": int(len(title_ids)),
            "Skips": int(len(skip_ids)),
            "Total": int(total),
        })
    df = pd.DataFrame(rows)
    # Add totals row
    total_sum = df["Total"].sum()
    totals = {
        "Dataset": "TOTAL",
        "Success": df["Success"].sum(),
        "CPC Error": df["CPC Error"].sum(),
        "Title Error": df["Title Error"].sum(),
        "Skips": df["Skips"].sum(),
        "Total": total_sum,
    }
    df = pd.concat([df, pd.DataFrame([totals])], ignore_index=True)
    # Percentage row
    pct = {
        "Dataset": "PERCENTAGE",
        "Success": round(totals["Success"] / total_sum * 100, 2) if total_sum else 0,
        "CPC Error": round(totals["CPC Error"] / total_sum * 100, 2) if total_sum else 0,
        "Title Error": round(totals["Title Error"] / total_sum * 100, 2) if total_sum else 0,
        "Skips": round(totals["Skips"] / total_sum * 100, 2) if total_sum else 0,
        "Total": 100.0 if total_sum else 0,
    }
    df = pd.concat([df, pd.DataFrame([pct])], ignore_index=True)
    return df


def main():
    df = summarize_datasets()
    out_path = Path("metadata_validation_summary.xlsx")
    df.to_excel(out_path, index=False)
    print(f"Wrote {out_path} with {len(df)-1} datasets + totals")
    print(df)


if __name__ == "__main__":
    main()
