from __future__ import annotations

import argparse
import json
import shutil
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from backend.app.embed import embed_chunks, model, tokenizer
from backend.app.services.download import bulk_dataset_download, output_file as DOWNLOAD_DIR
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


DEFAULT_SPEC_PATH = Path(__file__).resolve().parents[2] / "validation" / "selected_grant_issue_sets.json"


def _json_dump(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _normalize_target_doc_id(value: str | None) -> str | None:
    raw = "".join(ch for ch in str(value or "").strip().upper() if ch.isalnum())
    if raw.startswith("US") and len(raw) > 2:
        raw = raw[2:]
    if raw.isdigit():
        raw = str(int(raw))
    return raw or None


def _storage_dataset_id(target: dict[str, Any], *, include_full_issue: bool) -> str:
    base = str(target.get("dataset_id") or "").strip()
    if not base:
        raise ValueError("Selected target is missing dataset_id.")
    if include_full_issue:
        return f"{base}__full_issue"
    return base


def _expected_archive_ext(dataset_product: str) -> str:
    product_upper = str(dataset_product or "").strip().upper()
    return ".tar" if product_upper == "PTGRDT" else ".zip"


def _parse_set_ids(raw: str) -> set[str] | None:
    values = {part.strip() for part in str(raw or "").split(",") if part.strip()}
    return values or None


def _coerce_target_doc_ids(target: dict[str, Any]) -> list[str]:
    raw = target.get("doc_ids")
    if isinstance(raw, list):
        values = raw
    else:
        values = [target.get("doc_id")]
    doc_ids = [
        value
        for value in (_normalize_target_doc_id(item) for item in values)
        if value
    ]
    if not doc_ids:
        raise ValueError(f"Target {target.get('dataset_id') or '<unknown>'} is missing doc_ids.")
    return doc_ids


def _load_targets(spec_path: Path, *, set_ids: set[str] | None) -> tuple[str, list[dict[str, Any]]]:
    payload = json.loads(spec_path.read_text(encoding="utf-8"))
    dataset_product = str(payload.get("dataset_product") or "PTGRXML").strip().upper()
    targets: list[dict[str, Any]] = []
    for raw_target in payload.get("targets") or []:
        target = dict(raw_target)
        target["set_id"] = str(target.get("set_id") or "").strip()
        if set_ids and target["set_id"] not in set_ids:
            continue
        target["dataset_id"] = str(target.get("dataset_id") or "").strip()
        target["issue_date"] = str(target.get("issue_date") or "").strip()
        target["archive_stem"] = str(target.get("archive_stem") or "").strip()
        target["doc_ids"] = _coerce_target_doc_ids(target)
        target["dataset_product"] = str(target.get("dataset_product") or dataset_product).strip().upper()
        if not target["dataset_id"] or not target["issue_date"] or not target["archive_stem"]:
            raise ValueError(f"Malformed target in {spec_path}: {raw_target}")
        targets.append(target)
    if not targets:
        raise ValueError(f"No targets selected from spec {spec_path}.")
    return dataset_product, targets


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


def _build_target_manifest(
    *,
    status: str,
    target: dict[str, Any],
    storage_dataset_id: str,
    include_full_issue: bool,
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
    requested_doc_ids = list(target["doc_ids"])
    found_doc_ids = sorted(doc_id for doc_id in total_docs if doc_id)
    found_normalized = {
        value
        for value in (_normalize_target_doc_id(doc_id) for doc_id in found_doc_ids)
        if value
    }
    missing_doc_ids = [
        doc_id
        for doc_id in requested_doc_ids
        if _normalize_target_doc_id(doc_id) not in found_normalized
    ]
    return {
        "schema_version": 1,
        "status": status,
        "created_at": datetime.now().astimezone().isoformat(),
        "storage_format": "lmdb",
        "record_schema_version": 1,
        "canonical_dataset_id": storage_dataset_id,
        "source_dataset_id": target["dataset_id"],
        "canonical_dataset_date": target["issue_date"],
        "input_date": target["issue_date"],
        "dataset_product": target["dataset_product"],
        "expected_archive_name": f"{target['archive_stem']}{_expected_archive_ext(target['dataset_product'])}",
        "source_archive_stem": target["archive_stem"],
        "dataset_dir": str(dataset_dir.resolve()),
        "dataset_lmdb_path": str(embeddings_path.resolve()),
        "record_count": total_records,
        "doc_count": len(found_doc_ids),
        "named_vectors": sorted(vector_names),
        "fields_present": sorted(fieldnames),
        "selection": {
            "set_id": target["set_id"],
            "label": str(target.get("label") or ""),
            "note": str(target.get("note") or ""),
            "mode": "full_issue" if include_full_issue else "targeted_doc_ids",
            "requested_doc_ids": requested_doc_ids,
            "found_doc_ids": found_doc_ids,
            "missing_doc_ids": missing_doc_ids,
        },
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


def export_selected_target(
    *,
    target: dict[str, Any],
    output_root: Path,
    download_path: Path,
    batch_size: int,
    include_full_issue: bool,
    overwrite: bool,
    master_manifest_csv: Path | None,
) -> dict[str, Any]:
    dataset_id = _storage_dataset_id(target, include_full_issue=include_full_issue)
    dataset_dir = output_root / dataset_id
    embeddings_path = dataset_dir / "embeddings.lmdb"
    manifest_path = dataset_dir / "manifest.json"
    partial_manifest_path = dataset_dir / "manifest.partial.json"

    if not overwrite and embeddings_path.exists() and manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        print(f"[selected] Skipping existing dataset {dataset_id}: {embeddings_path}")
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
            f"[selected] Resuming partial dataset {dataset_id}: "
            f"existing_records={existing_records_at_start} existing_docs={len(total_docs)}"
        )

    lmdb_env = open_dataset_embeddings_lmdb(embeddings_path, readonly=False)
    try:
        _json_dump(
            partial_manifest_path,
            _build_target_manifest(
                status="in_progress",
                target=target,
                storage_dataset_id=dataset_id,
                include_full_issue=include_full_issue,
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
                    f"[selected] dataset={dataset_id} batch_records={len(batch)} "
                    f"skipped_existing={skipped} total_records={total_records}"
                )
                _json_dump(
                    partial_manifest_path,
                    _build_target_manifest(
                        status="in_progress",
                        target=target,
                        storage_dataset_id=dataset_id,
                        include_full_issue=include_full_issue,
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
                f"[selected] dataset={dataset_id} batch_records={len(pending)} "
                f"skipped_existing={skipped} total_records={total_records} "
                f"embed_s={embed_seconds:.1f} write_s={write_seconds:.1f}"
            )
            _json_dump(
                partial_manifest_path,
                _build_target_manifest(
                    status="in_progress",
                    target=target,
                    storage_dataset_id=dataset_id,
                    include_full_issue=include_full_issue,
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
            target["issue_date"],
            download_path,
            sample_k=0,
            use_manifest=False,
            dataset_product=target["dataset_product"],
            return_chunks=False,
            batch_size=int(batch_size),
            on_batch=on_batch,
            max_patents=0,
            master_manifest_csv=master_manifest_csv,
            archive_stem_override=target["archive_stem"],
            include_doc_ids=None if include_full_issue else target["doc_ids"],
        )
    finally:
        lmdb_env.close()

    elapsed = time.perf_counter() - start
    manifest = _build_target_manifest(
        status="complete",
        target=target,
        storage_dataset_id=dataset_id,
        include_full_issue=include_full_issue,
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
    missing_doc_ids = manifest["selection"]["missing_doc_ids"]
    if missing_doc_ids:
        print(f"[selected][warn] dataset={dataset_id} missing_doc_ids={','.join(missing_doc_ids)}")
    print(f"[selected] Wrote dataset {dataset_id} manifest: {manifest_path}")
    print(f"[selected] Wrote dataset {dataset_id} LMDB: {embeddings_path}")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Precompute embeddings for specific historical grant or application issues/doc IDs into per-dataset LMDB directories."
    )
    parser.add_argument("--spec-file", type=Path, default=DEFAULT_SPEC_PATH)
    parser.add_argument("--set-ids", type=str, default="")
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--download-path", type=Path, default=DOWNLOAD_DIR)
    parser.add_argument("--batch-size", type=int, default=512)
    parser.add_argument(
        "--include-full-issue",
        action="store_true",
        help="Embed the full issue archive for each selected target instead of filtering to the requested patent IDs.",
    )
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument(
        "--master-manifest-csv",
        type=Path,
        default=None,
        help="Optional existing download manifest CSV path to keep populated during precompute.",
    )
    args = parser.parse_args()

    spec_path = Path(args.spec_file).resolve()
    output_root = Path(args.output_root).resolve()
    download_path = Path(args.download_path).resolve()
    set_ids = _parse_set_ids(args.set_ids)

    dataset_product, targets = _load_targets(spec_path, set_ids=set_ids)
    print(
        f"[selected] spec={spec_path} output_root={output_root} "
        f"targets={len(targets)} dataset_product={dataset_product} "
        f"include_full_issue={int(bool(args.include_full_issue))}"
    )

    manifests: list[dict[str, Any]] = []
    overall_start = time.perf_counter()
    for target in targets:
        manifests.append(
            export_selected_target(
                target=target,
                output_root=output_root,
                download_path=download_path,
                batch_size=int(args.batch_size),
                include_full_issue=bool(args.include_full_issue),
                overwrite=bool(args.overwrite),
                master_manifest_csv=args.master_manifest_csv,
            )
        )

    run_manifest = {
        "schema_version": 1,
        "created_at": datetime.now().astimezone().isoformat(),
        "phase": "precompute_selected_patent_issues",
        "spec_file": str(spec_path),
        "set_ids": sorted(set_ids) if set_ids else [],
        "output_root": str(output_root),
        "download_path": str(download_path),
        "include_full_issue": bool(args.include_full_issue),
        "dataset_ids": [m["canonical_dataset_id"] for m in manifests],
        "issue_dates": [m["canonical_dataset_date"] for m in manifests],
        "missing_doc_ids": {
            m["canonical_dataset_id"]: list(m["selection"]["missing_doc_ids"])
            for m in manifests
            if m.get("selection", {}).get("missing_doc_ids")
        },
        "elapsed_seconds": time.perf_counter() - overall_start,
    }
    _json_dump(output_root / "run_manifest.json", run_manifest)
    print(f"[selected] Wrote run manifest: {output_root / 'run_manifest.json'}")


if __name__ == "__main__":
    main()
