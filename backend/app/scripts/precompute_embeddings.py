from __future__ import annotations

import argparse
import json
import shutil
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from backend.app.embed import embed_chunks, model, tokenizer
from backend.app.services.download import _dataset_file_base, bulk_dataset_download, output_file as DOWNLOAD_DIR
from backend.app.store import open_dataset_embeddings_lmdb, write_dataset_embeddings_batch
from backend.app.vector_config import (
    ENABLED_COLBERT_VARIANTS,
    PRIMARY_COLBERT_VARIANT,
    PROJECTION_MODE,
    PROJECTION_PATH,
    TOKEN_VECTOR_DIM,
    TOKEN_VECTOR_DTYPE,
)


def _build_weekly_dates(start_date: str, num_datasets: int) -> list[str]:
    anchor = datetime.strptime(start_date, "%Y-%m-%d")
    count = max(0, int(num_datasets))
    return [
        (anchor - timedelta(days=7 * idx)).strftime("%Y-%m-%d")
        for idx in range(count)
    ]


def _json_dump(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _dataset_context(input_date: str, *, download_path: Path, dataset_product: str) -> dict[str, str]:
    base, ext_hint, last_tuesday, product_upper = _dataset_file_base(
        input_date,
        download_path,
        dataset_product,
    )
    dataset_id = base.name
    return {
        "input_date": input_date,
        "canonical_dataset_id": dataset_id,
        "canonical_dataset_date": last_tuesday.strftime("%Y-%m-%d"),
        "dataset_product": product_upper,
        "expected_archive_name": f"{dataset_id}{ext_hint}",
    }


def export_dataset(
    *,
    input_date: str,
    output_root: Path,
    download_path: Path,
    dataset_product: str,
    batch_size: int,
    max_patents: int | None,
    overwrite: bool,
    master_manifest_csv: Path | None,
) -> dict[str, Any]:
    ctx = _dataset_context(
        input_date,
        download_path=download_path,
        dataset_product=dataset_product,
    )
    dataset_id = ctx["canonical_dataset_id"]
    dataset_dir = output_root / dataset_id
    embeddings_path = dataset_dir / "embeddings.lmdb"
    manifest_path = dataset_dir / "manifest.json"

    if not overwrite and embeddings_path.exists() and manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        print(f"[phase1] Skipping existing dataset {dataset_id}: {embeddings_path}")
        return manifest

    dataset_dir.mkdir(parents=True, exist_ok=True)
    if overwrite and embeddings_path.exists():
        shutil.rmtree(embeddings_path, ignore_errors=True)
    total_records = 0
    total_docs: set[str] = set()
    fieldnames: set[str] = set()
    vector_names: set[str] = set()
    start = time.perf_counter()

    lmdb_env = open_dataset_embeddings_lmdb(embeddings_path, readonly=False)
    try:
        def on_batch(batch: list[dict]) -> None:
            nonlocal total_records
            if not batch:
                return
            batch_start = time.perf_counter()
            embedded = embed_chunks(batch, tokenizer, model)
            embed_seconds = time.perf_counter() - batch_start
            write_start = time.perf_counter()
            batch_stats = write_dataset_embeddings_batch(
                lmdb_env,
                embedded,
                canonical_dataset_id=dataset_id,
            )
            write_seconds = time.perf_counter() - write_start
            total_records += int(batch_stats["record_count"])
            total_docs.update(batch_stats["doc_ids"])
            fieldnames.update(batch_stats["fieldnames"])
            vector_names.update(batch_stats["vector_names"])
            print(
                f"[phase1] dataset={dataset_id} batch_records={len(embedded)} "
                f"total_records={total_records} embed_s={embed_seconds:.1f} write_s={write_seconds:.1f}"
            )

        bulk_dataset_download(
            input_date,
            download_path,
            sample_k=0,
            use_manifest=False,
            dataset_product=dataset_product,
            return_chunks=False,
            batch_size=int(batch_size),
            on_batch=on_batch,
            max_patents=max_patents,
            master_manifest_csv=master_manifest_csv,
        )
    finally:
        lmdb_env.close()

    elapsed = time.perf_counter() - start
    manifest = {
        "schema_version": 1,
        "created_at": datetime.now().astimezone().isoformat(),
        "storage_format": "lmdb",
        "record_schema_version": 1,
        "canonical_dataset_id": dataset_id,
        "canonical_dataset_date": ctx["canonical_dataset_date"],
        "input_date": input_date,
        "dataset_product": ctx["dataset_product"],
        "expected_archive_name": ctx["expected_archive_name"],
        "dataset_dir": str(dataset_dir.resolve()),
        "dataset_lmdb_path": str(embeddings_path.resolve()),
        "record_count": total_records,
        "doc_count": len([doc for doc in total_docs if doc]),
        "named_vectors": sorted(vector_names),
        "fields_present": sorted(fieldnames),
        "embedding_config": {
            "token_vector_dim": TOKEN_VECTOR_DIM,
            "token_vector_dtype": TOKEN_VECTOR_DTYPE,
            "primary_colbert_variant": PRIMARY_COLBERT_VARIANT,
            "enabled_colbert_variants": sorted(ENABLED_COLBERT_VARIANTS),
            "projection_mode": PROJECTION_MODE,
            "projection_path": str(PROJECTION_PATH),
        },
        "timing": {
            "elapsed_seconds": elapsed,
        },
        "storage": {
            "layout": "per_dataset_lmdb",
            "record_payload": "npz(metadata_json,colbert)",
        },
    }
    _json_dump(manifest_path, manifest)
    print(f"[phase1] Wrote dataset {dataset_id} manifest: {manifest_path}")
    print(f"[phase1] Wrote dataset {dataset_id} LMDB: {embeddings_path}")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Precompute weekly patent embeddings into per-dataset LMDB directories."
    )
    parser.add_argument("--start-date", type=str, default="2025-09-02")
    parser.add_argument("--num-datasets", type=int, default=4)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--download-path", type=Path, default=DOWNLOAD_DIR)
    parser.add_argument("--dataset-product", type=str, default="PTGRDT")
    parser.add_argument("--batch-size", type=int, default=512)
    parser.add_argument("--max-patents", type=int, default=0, help="0 means no cap.")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument(
        "--master-manifest-csv",
        type=Path,
        default=None,
        help="Optional existing download manifest CSV path to keep populated during precompute.",
    )
    args = parser.parse_args()

    output_root = Path(args.output_root).resolve()
    download_path = Path(args.download_path).resolve()
    max_patents = None if int(args.max_patents) <= 0 else int(args.max_patents)
    dates = _build_weekly_dates(args.start_date, args.num_datasets)
    if not dates:
        raise SystemExit("--num-datasets must be >= 1.")

    print(
        f"[phase1] start_date={args.start_date} num_datasets={args.num_datasets} "
        f"output_root={output_root}"
    )
    manifests: list[dict[str, Any]] = []
    overall_start = time.perf_counter()
    for input_date in dates:
        manifests.append(
            export_dataset(
                input_date=input_date,
                output_root=output_root,
                download_path=download_path,
                dataset_product=args.dataset_product,
                batch_size=int(args.batch_size),
                max_patents=max_patents,
                overwrite=bool(args.overwrite),
                master_manifest_csv=args.master_manifest_csv,
            )
        )

    run_manifest = {
        "schema_version": 1,
        "created_at": datetime.now().astimezone().isoformat(),
        "phase": "precompute_embeddings",
        "start_date": args.start_date,
        "num_datasets": int(args.num_datasets),
        "output_root": str(output_root),
        "download_path": str(download_path),
        "dataset_ids": [m["canonical_dataset_id"] for m in manifests],
        "dataset_dates": [m["canonical_dataset_date"] for m in manifests],
        "elapsed_seconds": time.perf_counter() - overall_start,
    }
    _json_dump(output_root / "run_manifest.json", run_manifest)
    print(f"[phase1] Wrote run manifest: {output_root / 'run_manifest.json'}")


if __name__ == "__main__":
    main()
