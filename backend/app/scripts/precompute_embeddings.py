from __future__ import annotations

import argparse
import json
import re
import shutil
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from backend.app.embed import embed_chunks, model, tokenizer
from backend.app.services.download import (
    _dataset_file_base,
    _delete_dataset_archives,
    bulk_dataset_download,
    output_file as DOWNLOAD_DIR,
)
from backend.app.store import (
    dataset_embedding_entry_count,
    filter_new_dataset_embedding_records,
    load_dataset_embeddings_from_lmdb,
    open_dataset_embeddings_lmdb,
    write_dataset_embeddings_batch,
)
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


def _normalize_issue_identifiers(values: list[str], *, source_label: str) -> list[str]:
    dates: list[str] = []
    for raw_value in values:
        value = str(raw_value or "").strip()
        if not value:
            continue
        if re.fullmatch(r"I\d{8}", value):
            dates.append(f"{value[1:5]}-{value[5:7]}-{value[7:9]}")
            continue
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            dates.append(value)
            continue
        raise SystemExit(
            f"{source_label} currently supports weekly issue IDs like I20250902 "
            f"or ISO dates like 2025-09-02 only. Got: {value}"
        )
    return dates


def _load_dataset_identifiers_from_file(path: Path, *, key: str | None) -> list[str]:
    raw_text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        payload = json.loads(raw_text)
        if isinstance(payload, list):
            return [str(item or "").strip() for item in payload if str(item or "").strip()]
        if isinstance(payload, dict):
            candidate_key = str(key or "").strip()
            if candidate_key:
                selected = payload.get(candidate_key)
                if not isinstance(selected, list):
                    raise SystemExit(
                        f"--dataset-ids-key '{candidate_key}' was not found as a list in {path}."
                    )
                return [str(item or "").strip() for item in selected if str(item or "").strip()]
            for fallback_key in ("dataset_ids", "missing_dataset_ids", "missing_complete_dataset_ids"):
                selected = payload.get(fallback_key)
                if isinstance(selected, list):
                    return [str(item or "").strip() for item in selected if str(item or "").strip()]
            list_keys = [
                str(name)
                for name, value in payload.items()
                if isinstance(name, str) and isinstance(value, list)
            ]
            if len(list_keys) == 1:
                selected = payload[list_keys[0]]
                return [str(item or "").strip() for item in selected if str(item or "").strip()]
            raise SystemExit(
                f"{path} contains multiple list fields. Pass --dataset-ids-key to choose one."
            )
        raise SystemExit(f"Unsupported JSON structure in {path}. Expected list or object.")
    tokens: list[str] = []
    for line in raw_text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        for part in stripped.split(","):
            token = part.strip()
            if token:
                tokens.append(token)
    return tokens


def _resolve_input_dates(
    start_date: str,
    num_datasets: int,
    dataset_ids_raw: str,
    dataset_ids_file: Path | None,
    dataset_ids_key: str | None,
) -> list[str]:
    explicit = [part.strip() for part in str(dataset_ids_raw or "").split(",") if part.strip()]
    if explicit:
        return _normalize_issue_identifiers(explicit, source_label="--dataset-ids")
    if dataset_ids_file is not None:
        identifiers = _load_dataset_identifiers_from_file(Path(dataset_ids_file).resolve(), key=dataset_ids_key)
        resolved = _normalize_issue_identifiers(
            identifiers,
            source_label="--dataset-ids-file",
        )
        if not resolved:
            raise SystemExit(f"--dataset-ids-file {dataset_ids_file} did not yield any dataset identifiers.")
        return resolved
    dates = _build_weekly_dates(start_date, num_datasets)
    if not dates:
        raise SystemExit("--num-datasets must be >= 1.")
    return dates


def _summarize_existing_dataset(embeddings_path: Path) -> dict[str, Any]:
    summary = {
        "record_count": 0,
        "doc_ids": set(),
        "fieldnames": set(),
        "vector_names": set(),
    }
    if not embeddings_path.exists():
        return summary
    for record in load_dataset_embeddings_from_lmdb(embeddings_path):
        summary["record_count"] += 1
        doc_id = str(record.get("doc_id") or "").strip()
        if doc_id:
            summary["doc_ids"].add(doc_id)
        summary["fieldnames"].update(record.keys())
        summary["vector_names"].update((record.get("weaviate_named_vectors") or {"colbert": None}).keys())
    return summary


def _build_dataset_manifest(
    *,
    status: str,
    ctx: dict[str, str],
    input_date: str,
    dataset_dir: Path,
    embeddings_path: Path,
    total_records: int,
    total_docs: set[str],
    fieldnames: set[str],
    vector_names: set[str],
    elapsed_seconds: float,
    existing_records_at_start: int,
    skipped_existing_records: int,
    resumed_from_partial: bool,
    batches_embedded: int,
    batches_skipped_existing: int,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "status": status,
        "created_at": datetime.now().astimezone().isoformat(),
        "storage_format": "lmdb",
        "record_schema_version": 1,
        "canonical_dataset_id": ctx["canonical_dataset_id"],
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
            "elapsed_seconds": elapsed_seconds,
        },
        "storage": {
            "layout": "per_dataset_lmdb",
            "record_payload": "npz(metadata_json,colbert)",
        },
        "resume": {
            "resumed_from_partial": resumed_from_partial,
            "existing_records_at_start": existing_records_at_start,
            "skipped_existing_records": skipped_existing_records,
            "batches_embedded": batches_embedded,
            "batches_skipped_existing": batches_skipped_existing,
        },
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
    delete_archive_after_embed: bool,
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
    partial_manifest_path = dataset_dir / "manifest.partial.json"

    if not overwrite and embeddings_path.exists() and manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        print(f"[phase1] Skipping existing dataset {dataset_id}: {embeddings_path}")
        return manifest

    dataset_dir.mkdir(parents=True, exist_ok=True)
    if overwrite and embeddings_path.exists():
        shutil.rmtree(embeddings_path, ignore_errors=True)
    if overwrite:
        for stale in (manifest_path, partial_manifest_path):
            if stale.exists():
                stale.unlink()
    total_records = 0
    total_docs: set[str] = set()
    fieldnames: set[str] = set()
    vector_names: set[str] = set()
    start = time.perf_counter()
    existing_records_at_start = 0
    skipped_existing_records = 0
    resumed_from_partial = False
    batches_embedded = 0
    batches_skipped_existing = 0

    if not overwrite and embeddings_path.exists() and not manifest_path.exists():
        existing_summary = _summarize_existing_dataset(embeddings_path)
        existing_records_at_start = int(existing_summary["record_count"])
        total_records = existing_records_at_start
        total_docs.update(existing_summary["doc_ids"])
        fieldnames.update(existing_summary["fieldnames"])
        vector_names.update(existing_summary["vector_names"])
        resumed_from_partial = existing_records_at_start > 0
        print(
            f"[phase1] Resuming partial dataset {dataset_id}: "
            f"existing_records={existing_records_at_start} existing_docs={len(total_docs)}"
        )

    lmdb_env = open_dataset_embeddings_lmdb(embeddings_path, readonly=False)
    try:
        _json_dump(
            partial_manifest_path,
            _build_dataset_manifest(
                status="in_progress",
                ctx=ctx,
                input_date=input_date,
                dataset_dir=dataset_dir,
                embeddings_path=embeddings_path,
                total_records=total_records,
                total_docs=total_docs,
                fieldnames=fieldnames,
                vector_names=vector_names,
                elapsed_seconds=time.perf_counter() - start,
                existing_records_at_start=existing_records_at_start,
                skipped_existing_records=skipped_existing_records,
                resumed_from_partial=resumed_from_partial,
                batches_embedded=batches_embedded,
                batches_skipped_existing=batches_skipped_existing,
            ),
        )

        def on_batch(batch: list[dict]) -> None:
            nonlocal total_records, skipped_existing_records, batches_embedded, batches_skipped_existing
            if not batch:
                return
            pending, skipped = filter_new_dataset_embedding_records(lmdb_env, batch)
            skipped_existing_records += skipped
            if not pending:
                batches_skipped_existing += 1
                print(
                    f"[phase1] dataset={dataset_id} batch_records={len(batch)} "
                    f"skipped_existing={skipped} total_records={total_records}"
                )
                _json_dump(
                    partial_manifest_path,
                    _build_dataset_manifest(
                        status="in_progress",
                        ctx=ctx,
                        input_date=input_date,
                        dataset_dir=dataset_dir,
                        embeddings_path=embeddings_path,
                        total_records=total_records,
                        total_docs=total_docs,
                        fieldnames=fieldnames,
                        vector_names=vector_names,
                        elapsed_seconds=time.perf_counter() - start,
                        existing_records_at_start=existing_records_at_start,
                        skipped_existing_records=skipped_existing_records,
                        resumed_from_partial=resumed_from_partial,
                        batches_embedded=batches_embedded,
                        batches_skipped_existing=batches_skipped_existing,
                    ),
                )
                return
            batch_start = time.perf_counter()
            embedded = embed_chunks(pending, tokenizer, model)
            embed_seconds = time.perf_counter() - batch_start
            write_start = time.perf_counter()
            batch_stats = write_dataset_embeddings_batch(
                lmdb_env,
                embedded,
                canonical_dataset_id=dataset_id,
            )
            write_seconds = time.perf_counter() - write_start
            current_entries = dataset_embedding_entry_count(lmdb_env)
            if current_entries < total_records + int(batch_stats["record_count"]):
                raise RuntimeError(
                    f"Dataset LMDB entry count moved backwards for {dataset_id}: "
                    f"entries={current_entries} expected_at_least={total_records + int(batch_stats['record_count'])}"
                )
            total_records += int(batch_stats["record_count"])
            total_docs.update(batch_stats["doc_ids"])
            fieldnames.update(batch_stats["fieldnames"])
            vector_names.update(batch_stats["vector_names"])
            batches_embedded += 1
            print(
                f"[phase1] dataset={dataset_id} batch_records={len(pending)} "
                f"skipped_existing={skipped} total_records={total_records} "
                f"embed_s={embed_seconds:.1f} write_s={write_seconds:.1f}"
            )
            _json_dump(
                partial_manifest_path,
                _build_dataset_manifest(
                    status="in_progress",
                    ctx=ctx,
                    input_date=input_date,
                    dataset_dir=dataset_dir,
                    embeddings_path=embeddings_path,
                    total_records=total_records,
                    total_docs=total_docs,
                    fieldnames=fieldnames,
                    vector_names=vector_names,
                    elapsed_seconds=time.perf_counter() - start,
                    existing_records_at_start=existing_records_at_start,
                    skipped_existing_records=skipped_existing_records,
                    resumed_from_partial=resumed_from_partial,
                    batches_embedded=batches_embedded,
                    batches_skipped_existing=batches_skipped_existing,
                ),
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
    manifest = _build_dataset_manifest(
        status="complete",
        ctx=ctx,
        input_date=input_date,
        dataset_dir=dataset_dir,
        embeddings_path=embeddings_path,
        total_records=total_records,
        total_docs=total_docs,
        fieldnames=fieldnames,
        vector_names=vector_names,
        elapsed_seconds=elapsed,
        existing_records_at_start=existing_records_at_start,
        skipped_existing_records=skipped_existing_records,
        resumed_from_partial=resumed_from_partial,
        batches_embedded=batches_embedded,
        batches_skipped_existing=batches_skipped_existing,
    )
    _json_dump(manifest_path, manifest)
    if partial_manifest_path.exists():
        partial_manifest_path.unlink()
    if delete_archive_after_embed:
        _delete_dataset_archives(input_date, download_path, dataset_product)
        print(f"[phase1] Deleted downloaded archive for {dataset_id}")
    print(f"[phase1] Wrote dataset {dataset_id} manifest: {manifest_path}")
    print(f"[phase1] Wrote dataset {dataset_id} LMDB: {embeddings_path}")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Precompute weekly patent embeddings into per-dataset LMDB directories."
    )
    parser.add_argument("--start-date", type=str, default="2025-09-02")
    parser.add_argument("--num-datasets", type=int, default=4)
    parser.add_argument(
        "--dataset-ids",
        type=str,
        default="",
        help="Optional comma-separated weekly dataset IDs like I20250902,I20250826.",
    )
    parser.add_argument(
        "--dataset-ids-file",
        type=Path,
        default=None,
        help=(
            "Optional path to a JSON or text file containing weekly issue IDs or dates. "
            "Use --dataset-ids-key when the JSON file contains multiple dataset lists."
        ),
    )
    parser.add_argument(
        "--dataset-ids-key",
        type=str,
        default="",
        help="Optional JSON key to read from --dataset-ids-file.",
    )
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--download-path", type=Path, default=DOWNLOAD_DIR)
    parser.add_argument("--dataset-product", type=str, default="PTGRDT")
    parser.add_argument("--batch-size", type=int, default=512)
    parser.add_argument("--max-patents", type=int, default=0, help="0 means no cap.")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument(
        "--delete-archive-after-embed",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Delete the downloaded USPTO archive after a dataset finishes embedding successfully.",
    )
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
    dates = _resolve_input_dates(
        args.start_date,
        int(args.num_datasets),
        args.dataset_ids,
        args.dataset_ids_file,
        args.dataset_ids_key,
    )

    print(
        f"[phase1] output_root={output_root} dataset_count={len(dates)} "
        f"datasets={','.join(dates[:20])}" + (",..." if len(dates) > 20 else "")
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
                delete_archive_after_embed=bool(args.delete_archive_after_embed),
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
