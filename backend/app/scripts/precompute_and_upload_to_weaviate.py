from __future__ import annotations

import argparse
from concurrent.futures import Future, ThreadPoolExecutor
import json
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from backend.app.scripts.precompute_embeddings import _build_weekly_dates, export_dataset
from backend.app.scripts.upload_precomputed_to_weaviate import (
    upload_saved_embeddings,
)
from backend.app.services.download import _dataset_file_base, output_file as DOWNLOAD_DIR
from backend.app.store import (
    WEAVIATE_MUVERA_DPROJECTIONS,
    WEAVIATE_MUVERA_KSIM,
    WEAVIATE_MUVERA_REPETITIONS,
    WEAVIATE_PQ_BIT_COMPRESSION,
    WEAVIATE_PQ_CENTROIDS,
    WEAVIATE_PQ_ENABLED,
    WEAVIATE_PQ_SEGMENTS,
    WEAVIATE_PQ_TRAINING_LIMIT,
    reset_weaviate_state,
)


DEFAULT_PRECOMPUTE_ROOT = Path(__file__).resolve().parents[2] / "validation" / "precomputed_pipeline"
DEFAULT_PIPELINE_RUNS_DIR = Path(__file__).resolve().parents[2] / "validation" / "pipeline_runs"


def _parse_bool(value: str) -> bool:
    normalized = str(value or "").strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise argparse.ArgumentTypeError(f"invalid boolean value: {value}")


def _json_dump(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _load_json_if_exists(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {}
    except Exception:
        return {}


def _resolve_input_dates(start_date: str, num_datasets: int, dataset_ids_raw: str) -> list[str]:
    explicit = [part.strip() for part in str(dataset_ids_raw or "").split(",") if part.strip()]
    if explicit:
        dates: list[str] = []
        for dataset_id in explicit:
            if not re.fullmatch(r"I\d{8}", dataset_id):
                raise SystemExit(
                    "--dataset-ids currently supports weekly issue IDs like I20250902 only."
                )
            dates.append(f"{dataset_id[1:5]}-{dataset_id[5:7]}-{dataset_id[7:9]}")
        return dates
    dates = _build_weekly_dates(start_date, num_datasets)
    if not dates:
        raise SystemExit("--num-datasets must be >= 1.")
    return dates


def _expected_dataset_ids(
    input_dates: list[str],
    *,
    download_path: Path,
    dataset_product: str,
) -> list[str]:
    out: list[str] = []
    for input_date in input_dates:
        base, _, _, _ = _dataset_file_base(input_date, download_path, dataset_product)
        out.append(base.name)
    return out


def _default_manifest_path(
    *,
    dataset_ids: list[str],
    muvera_params: dict[str, Any],
    pq_params: dict[str, Any],
) -> Path:
    first = dataset_ids[0] if dataset_ids else "none"
    last = dataset_ids[-1] if dataset_ids else "none"
    name = (
        f"pipeline_{first}_{last}_n{len(dataset_ids)}"
        f"_k{muvera_params['ksim']}_d{muvera_params['dprojections']}_r{muvera_params['repetitions']}"
        f"_pq{int(bool(pq_params['enabled']))}.json"
    )
    return (DEFAULT_PIPELINE_RUNS_DIR / name).resolve()


def _load_existing_complete_manifest(output_root: Path, dataset_id: str) -> dict[str, Any] | None:
    manifest_path = output_root / dataset_id / "manifest.json"
    if not manifest_path.exists():
        return None
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if not isinstance(payload, dict):
        return None
    if str(payload.get("canonical_dataset_id") or "").strip() != dataset_id:
        return None
    if str(payload.get("status") or "").strip().lower() != "complete":
        return None
    return payload


def _hydrate_dataset_manifest(manifest: dict[str, Any], *, output_root: Path) -> dict[str, Any]:
    dataset_id = str(manifest.get("canonical_dataset_id") or "").strip()
    if not dataset_id:
        raise ValueError("Dataset manifest missing canonical_dataset_id")

    dataset_dir = output_root / dataset_id
    manifest_path = Path(
        str(manifest.get("manifest_path") or (dataset_dir / "manifest.json"))
    ).resolve()
    storage_format = str(manifest.get("storage_format") or "lmdb").strip().lower()

    candidates: list[Path] = []
    if storage_format == "lmdb":
        raw_path = str(
            manifest.get("storage_path")
            or manifest.get("dataset_lmdb_path")
            or ""
        ).strip()
        if raw_path:
            candidates.append(Path(raw_path))
        candidates.append(dataset_dir / "embeddings.lmdb")
        candidates.append(manifest_path.parent / "embeddings.lmdb")
    else:
        raw_path = str(
            manifest.get("storage_path")
            or manifest.get("embeddings_path")
            or ""
        ).strip()
        if raw_path:
            candidates.append(Path(raw_path))
        candidates.append(dataset_dir / "embeddings.jsonl.gz")
        candidates.append(manifest_path.parent / "embeddings.jsonl.gz")

    storage_path = next((path.resolve() for path in candidates if path.exists()), None)
    if storage_path is None:
        joined = ", ".join(str(path) for path in candidates)
        raise FileNotFoundError(f"Missing embeddings payload for {dataset_id}. Tried: {joined}")

    hydrated = dict(manifest)
    hydrated["storage_format"] = storage_format
    hydrated["storage_path"] = str(storage_path)
    hydrated["manifest_path"] = str(manifest_path)
    hydrated["embeddings_root"] = str(output_root.resolve())
    return hydrated


def _planned_dataset_range(dataset_ids: list[str], input_dates: list[str]) -> dict[str, Any]:
    dates = sorted(str(value or "").strip() for value in input_dates if str(value or "").strip())
    return {
        "dataset_ids": list(dataset_ids),
        "date_start": dates[0] if dates else "",
        "date_end": dates[-1] if dates else "",
    }


def _precompute_summary(dataset_manifests: list[dict[str, Any]]) -> dict[str, Any]:
    datasets: list[dict[str, Any]] = []
    total_records = 0
    total_docs = 0
    for manifest in dataset_manifests:
        record_count = int(manifest.get("record_count") or 0)
        doc_count = int(manifest.get("doc_count") or 0)
        total_records += record_count
        total_docs += doc_count
        datasets.append(
            {
                "canonical_dataset_id": str(manifest.get("canonical_dataset_id") or ""),
                "canonical_dataset_date": str(manifest.get("canonical_dataset_date") or ""),
                "input_date": str(manifest.get("input_date") or ""),
                "dataset_product": str(manifest.get("dataset_product") or ""),
                "record_count": record_count,
                "doc_count": doc_count,
                "status": str(manifest.get("status") or ""),
                "storage_path": str(manifest.get("storage_path") or ""),
                "manifest_path": str(manifest.get("manifest_path") or ""),
                "resume": manifest.get("resume") or {},
            }
        )
    return {
        "total_record_count": total_records,
        "total_doc_count": total_docs,
        "datasets": datasets,
    }


def _build_run_manifest(
    *,
    started_at: str,
    completed: bool,
    output_root: Path,
    download_path: Path,
    dataset_range: dict[str, Any],
    dataset_product: str,
    precompute_batch_size: int,
    upload_batch_size: int,
    max_patents: int | None,
    overwrite: bool,
    muvera_params: dict[str, Any],
    pq_params: dict[str, Any],
    reset_requested: bool,
    deleted_collections: tuple[str, ...],
    write_cluster_lmdb: bool,
    skip_existing: bool,
    dataset_manifests: list[dict[str, Any]],
    upload_stats: dict[str, Any],
    pipeline_state: dict[str, Any],
    precompute_seconds: float,
    upload_seconds: float,
    total_seconds: float,
    last_error: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = {
        "schema_version": 2,
        "phase": "precompute_and_upload_to_weaviate",
        "timestamp": started_at,
        "updated_at": datetime.now().astimezone().isoformat(),
        "completed": bool(completed),
        "output_root": str(output_root),
        "download_path": str(download_path),
        "dataset": dataset_range,
        "parameters": {
            "dataset_product": dataset_product,
            "precompute_batch_size": int(precompute_batch_size),
            "upload_batch_size": int(upload_batch_size),
            "max_patents": None if max_patents is None else int(max_patents),
            "overwrite": bool(overwrite),
            "skip_existing": bool(skip_existing),
            "ksim": muvera_params["ksim"],
            "dprojections": muvera_params["dprojections"],
            "repetitions": muvera_params["repetitions"],
            "pq_enabled": bool(pq_params["enabled"]),
        },
        "pq": pq_params,
        "reset": {
            "requested": bool(reset_requested),
            "collections_deleted": list(deleted_collections),
        },
        "cluster_lmdb": {
            "enabled": bool(write_cluster_lmdb),
        },
        "pipeline": pipeline_state,
        "precompute": _precompute_summary(dataset_manifests),
        "upload": upload_stats,
        "runtime": {
            "precompute_seconds": precompute_seconds,
            "upload_seconds": upload_seconds,
            "total_seconds": total_seconds,
        },
    }
    if last_error:
        payload["last_error"] = last_error
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Precompute weekly patent embeddings to LMDB and upload them to Weaviate "
            "with dataset-level pipelining in one resumable run."
        )
    )
    parser.add_argument("--start-date", type=str, default="2025-09-02")
    parser.add_argument("--num-datasets", type=int, default=4)
    parser.add_argument(
        "--dataset-ids",
        type=str,
        default="",
        help="Optional comma-separated weekly dataset IDs like I20250902,I20250826.",
    )
    parser.add_argument("--output-root", type=Path, default=DEFAULT_PRECOMPUTE_ROOT)
    parser.add_argument("--download-path", type=Path, default=DOWNLOAD_DIR)
    parser.add_argument("--dataset-product", type=str, default="PTGRDT")
    parser.add_argument("--precompute-batch-size", type=int, default=512)
    parser.add_argument("--upload-batch-size", type=int, default=256)
    parser.add_argument("--max-patents", type=int, default=0, help="0 means no cap.")
    parser.add_argument("--overwrite", action="store_true", help="Rebuild local LMDBs even if they already exist.")
    parser.add_argument("--reset", action="store_true", help="Delete/recreate Patent and Claim before upload.")
    parser.add_argument(
        "--write-cluster-lmdb",
        action="store_true",
        help="Also write cluster-side LMDB side stores during upload. Default is off.",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Check Weaviate for existing UUIDs and skip duplicates during upload.",
    )
    parser.add_argument(
        "--master-manifest-csv",
        type=Path,
        default=None,
        help="Optional existing download manifest CSV path to keep populated during precompute.",
    )
    parser.add_argument("--ksim", type=int, default=WEAVIATE_MUVERA_KSIM)
    parser.add_argument("--dprojections", type=int, default=WEAVIATE_MUVERA_DPROJECTIONS)
    parser.add_argument("--repetitions", type=int, default=WEAVIATE_MUVERA_REPETITIONS)
    parser.add_argument("--pq-enabled", type=_parse_bool, default=WEAVIATE_PQ_ENABLED)
    parser.add_argument("--pq-centroids", type=int, default=WEAVIATE_PQ_CENTROIDS)
    parser.add_argument("--pq-segments", type=int, default=WEAVIATE_PQ_SEGMENTS)
    parser.add_argument("--pq-training-limit", type=int, default=WEAVIATE_PQ_TRAINING_LIMIT)
    parser.add_argument("--pq-bit-compression", type=_parse_bool, default=WEAVIATE_PQ_BIT_COMPRESSION)
    parser.add_argument("--output-manifest", type=Path, default=None)
    args = parser.parse_args()

    output_root = Path(args.output_root).resolve()
    download_path = Path(args.download_path).resolve()
    max_patents = None if int(args.max_patents) <= 0 else int(args.max_patents)
    input_dates = _resolve_input_dates(args.start_date, int(args.num_datasets), args.dataset_ids)
    expected_dataset_ids = _expected_dataset_ids(
        input_dates,
        download_path=download_path,
        dataset_product=args.dataset_product,
    )

    muvera_params = {
        "ksim": args.ksim,
        "dprojections": args.dprojections,
        "repetitions": args.repetitions,
    }
    pq_params = {
        "enabled": bool(args.pq_enabled),
        "centroids": int(args.pq_centroids),
        "segments": int(args.pq_segments),
        "training_limit": int(args.pq_training_limit),
        "bit_compression": bool(args.pq_bit_compression),
    }

    if args.output_manifest is not None:
        manifest_path = Path(args.output_manifest).resolve()
    else:
        manifest_path = _default_manifest_path(
            dataset_ids=expected_dataset_ids,
            muvera_params=muvera_params,
            pq_params=pq_params,
        )

    existing_manifest = _load_json_if_exists(manifest_path)
    existing_dataset_uploads = {
        str(item.get("canonical_dataset_id") or ""): item
        for item in (existing_manifest.get("upload", {}).get("dataset_uploads", []) or [])
        if str(item.get("canonical_dataset_id") or "").strip() in set(expected_dataset_ids)
    }
    started_at = str(existing_manifest.get("timestamp") or datetime.now().astimezone().isoformat())
    dataset_range = _planned_dataset_range(expected_dataset_ids, input_dates)

    print(
        f"[pipeline] output_root={output_root} datasets={','.join(expected_dataset_ids)} "
        f"precompute_batch={int(args.precompute_batch_size)} upload_batch={int(args.upload_batch_size)} "
        f"mode=dataset_pipelined"
    )

    overall_start = time.perf_counter()
    precompute_seconds = 0.0
    upload_seconds = 0.0
    local_manifests_by_id: dict[str, dict[str, Any]] = {}
    upload_results_by_id: dict[str, dict[str, Any]] = {} if args.reset else dict(existing_dataset_uploads)
    active_precompute_dataset_id = ""
    active_upload_dataset_id = ""
    pending_upload_dataset_id = ""
    precompute_work: list[tuple[str, str]] = []
    upload_backlog_ids: list[str] = []

    deleted_collections: tuple[str, ...] = ()
    if args.reset:
        deleted_collections = reset_weaviate_state(muvera_params=muvera_params, pq_params=pq_params)

    def _ordered_dataset_manifests() -> list[dict[str, Any]]:
        return [
            local_manifests_by_id[dataset_id]
            for dataset_id in expected_dataset_ids
            if dataset_id in local_manifests_by_id
        ]

    def _ordered_dataset_uploads() -> list[dict[str, Any]]:
        return [
            upload_results_by_id[dataset_id]
            for dataset_id in expected_dataset_ids
            if dataset_id in upload_results_by_id
        ]

    def _current_upload_stats() -> dict[str, Any]:
        dataset_uploads = _ordered_dataset_uploads()
        total_uploaded = sum(
            int(item.get("uploaded_records", 0))
            for item in dataset_uploads
            if str(item.get("status") or "").strip().lower() == "completed"
        )
        return {
            "total_uploaded_records": total_uploaded,
            "dataset_uploads": dataset_uploads,
        }

    def _dataset_needs_upload(dataset_id: str) -> bool:
        prior_upload = upload_results_by_id.get(dataset_id)
        return not (
            prior_upload
            and str(prior_upload.get("status") or "").strip().lower() == "completed"
        )

    def _write_progress(
        *,
        completed: bool,
        last_error: dict[str, Any] | None = None,
    ) -> None:
        payload = _build_run_manifest(
            started_at=started_at,
            completed=completed,
            output_root=output_root,
            download_path=download_path,
            dataset_range=dataset_range,
            dataset_product=args.dataset_product,
            precompute_batch_size=int(args.precompute_batch_size),
            upload_batch_size=int(args.upload_batch_size),
            max_patents=max_patents,
            overwrite=bool(args.overwrite),
            muvera_params=muvera_params,
            pq_params=pq_params,
            reset_requested=bool(args.reset),
            deleted_collections=deleted_collections,
            write_cluster_lmdb=bool(args.write_cluster_lmdb),
            skip_existing=bool(args.skip_existing),
            dataset_manifests=_ordered_dataset_manifests(),
            upload_stats=_current_upload_stats(),
            pipeline_state={
                "mode": "dataset_pipelined",
                "active_precompute_dataset_id": active_precompute_dataset_id,
                "active_upload_dataset_id": active_upload_dataset_id,
                "pending_upload_dataset_id": pending_upload_dataset_id,
                "precomputed_dataset_ids": [
                    dataset_id for dataset_id in expected_dataset_ids if dataset_id in local_manifests_by_id
                ],
                "uploaded_dataset_ids": [
                    dataset_id for dataset_id in expected_dataset_ids if dataset_id in upload_results_by_id
                ],
            },
            precompute_seconds=precompute_seconds,
            upload_seconds=upload_seconds,
            total_seconds=time.perf_counter() - overall_start,
            last_error=last_error,
        )
        _json_dump(manifest_path, payload)

    def _upload_single_dataset(dataset_manifest: dict[str, Any]) -> tuple[dict[str, Any], float]:
        dataset_id = str(dataset_manifest.get("canonical_dataset_id") or "").strip()
        prior = existing_dataset_uploads.get(dataset_id)
        if prior and str(prior.get("status") or "").strip().lower() == "completed" and not args.reset:
            print(
                f"[pipeline] Reusing completed upload for {dataset_id}: "
                f"{int(prior.get('uploaded_records', 0))} records"
            )
            return dict(prior), 0.0

        upload_start = time.perf_counter()
        result = upload_saved_embeddings(
            [dataset_manifest],
            batch_size=int(args.upload_batch_size),
            muvera_params=muvera_params,
            pq_params=pq_params,
            write_cluster_lmdb=bool(args.write_cluster_lmdb),
            skip_existing=bool(args.skip_existing),
            completed_dataset_uploads={},
            progress_callback=None,
        )
        dataset_uploads = list(result.get("dataset_uploads") or [])
        if not dataset_uploads:
            raise RuntimeError(f"Upload finished without dataset stats for {dataset_id}")
        return dict(dataset_uploads[0]), time.perf_counter() - upload_start

    def _fill_pending_upload() -> dict[str, Any] | None:
        nonlocal pending_upload_dataset_id
        while upload_backlog_ids:
            dataset_id = upload_backlog_ids.pop(0)
            if not _dataset_needs_upload(dataset_id):
                continue
            dataset_manifest = local_manifests_by_id.get(dataset_id)
            if dataset_manifest is None:
                continue
            pending_upload_dataset_id = dataset_id
            return dataset_manifest
        pending_upload_dataset_id = ""
        return None

    for input_date, dataset_id in zip(input_dates, expected_dataset_ids):
        existing_local_manifest = None if args.overwrite else _load_existing_complete_manifest(output_root, dataset_id)
        if existing_local_manifest is not None:
            local_manifests_by_id[dataset_id] = _hydrate_dataset_manifest(
                existing_local_manifest,
                output_root=output_root,
            )
            if _dataset_needs_upload(dataset_id):
                upload_backlog_ids.append(dataset_id)
            continue
        precompute_work.append((input_date, dataset_id))

    if upload_backlog_ids:
        print(
            f"[pipeline] Found {len(upload_backlog_ids)} precomputed dataset(s) awaiting upload: "
            f"{','.join(upload_backlog_ids)}"
        )
    if precompute_work:
        print(
            f"[pipeline] Remaining datasets to precompute: "
            f"{','.join(dataset_id for _, dataset_id in precompute_work)}"
        )

    _write_progress(completed=False)

    try:
        pending_upload_manifest = _fill_pending_upload()
        upload_future: Future[tuple[dict[str, Any], float]] | None = None

        with ThreadPoolExecutor(max_workers=1) as executor:
            for input_date, expected_dataset_id in precompute_work:
                if pending_upload_manifest is not None:
                    pending_upload_dataset_id = str(
                        pending_upload_manifest.get("canonical_dataset_id") or ""
                    ).strip()
                    active_upload_dataset_id = pending_upload_dataset_id
                    upload_future = executor.submit(_upload_single_dataset, dict(pending_upload_manifest))
                    pending_upload_manifest = None
                    pending_upload_dataset_id = ""
                    _write_progress(completed=False)

                active_precompute_dataset_id = expected_dataset_id
                _write_progress(completed=False)
                precompute_start = time.perf_counter()
                dataset_manifest = export_dataset(
                    input_date=input_date,
                    output_root=output_root,
                    download_path=download_path,
                    dataset_product=args.dataset_product,
                    batch_size=int(args.precompute_batch_size),
                    max_patents=max_patents,
                    overwrite=bool(args.overwrite),
                    master_manifest_csv=args.master_manifest_csv,
                )
                dataset_manifest = _hydrate_dataset_manifest(
                    dataset_manifest,
                    output_root=output_root,
                )
                precompute_seconds += time.perf_counter() - precompute_start
                dataset_id = str(dataset_manifest.get("canonical_dataset_id") or expected_dataset_id).strip()
                local_manifests_by_id[dataset_id] = dataset_manifest
                active_precompute_dataset_id = ""
                _write_progress(completed=False)

                if upload_future is not None:
                    upload_item, upload_elapsed = upload_future.result()
                    upload_seconds += upload_elapsed
                    upload_results_by_id[str(upload_item.get("canonical_dataset_id") or dataset_id)] = upload_item
                    active_upload_dataset_id = ""
                    upload_future = None
                    _write_progress(completed=False)

                if _dataset_needs_upload(dataset_id):
                    upload_backlog_ids.append(dataset_id)
                pending_upload_manifest = _fill_pending_upload()
                if pending_upload_manifest is not None:
                    _write_progress(completed=False)

            while pending_upload_manifest is not None:
                active_upload_dataset_id = str(
                    pending_upload_manifest.get("canonical_dataset_id") or ""
                ).strip()
                pending_upload_dataset_id = ""
                _write_progress(completed=False)
                upload_item, upload_elapsed = _upload_single_dataset(pending_upload_manifest)
                upload_seconds += upload_elapsed
                upload_results_by_id[str(upload_item.get("canonical_dataset_id") or "")] = upload_item
                active_upload_dataset_id = ""
                pending_upload_manifest = _fill_pending_upload()
                _write_progress(completed=False)
    except Exception as exc:
        _write_progress(
            completed=False,
            last_error={
                "type": type(exc).__name__,
                "message": str(exc),
            },
        )
        raise

    _write_progress(completed=True)
    print(f"[pipeline] Wrote manifest: {manifest_path}")
    print(
        f"[pipeline] Completed {len(_ordered_dataset_manifests())} dataset(s): "
        f"{int(_current_upload_stats().get('total_uploaded_records', 0))} uploaded records"
    )


if __name__ == "__main__":
    main()
