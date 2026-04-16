from __future__ import annotations

import argparse
from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
import gzip
import json
import re
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from backend.app.services.download import _dataset_file_base, output_file as DOWNLOAD_DIR
from backend.app.store import (
    WEAVIATE_CLAIM_SHARD_COUNT,
    WEAVIATE_MUVERA_DPROJECTIONS,
    WEAVIATE_MUVERA_KSIM,
    WEAVIATE_MUVERA_REPETITIONS,
    WEAVIATE_PATENT_SHARD_COUNT,
    WEAVIATE_PQ_BIT_COMPRESSION,
    WEAVIATE_PQ_CENTROIDS,
    WEAVIATE_PQ_ENABLED,
    WEAVIATE_PQ_SEGMENTS,
    WEAVIATE_PQ_TRAINING_LIMIT,
    load_dataset_embeddings_from_lmdb,
    reset_weaviate_state,
    store_embeddings,
)


DEFAULT_UPLOAD_RUNS_DIR = Path(__file__).resolve().parents[2] / "validation" / "upload_runs"


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


def _default_manifest_path(
    output_dir: Path,
    *,
    dataset_ids: list[str],
    muvera_params: dict[str, Any],
    pq_params: dict[str, Any],
) -> Path:
    first = dataset_ids[0] if dataset_ids else "none"
    last = dataset_ids[-1] if dataset_ids else "none"
    name = (
        f"upload_{first}_{last}_n{len(dataset_ids)}"
        f"_k{muvera_params['ksim']}_d{muvera_params['dprojections']}_r{muvera_params['repetitions']}"
        f"_pq{int(bool(pq_params['enabled']))}.json"
    )
    return (output_dir / name).resolve()


def _load_json_if_exists(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {}
    except Exception:
        return {}


def _normalize_dataset_identifier(
    value: str,
    *,
    download_path: Path,
    dataset_product: str,
    source_label: str,
) -> str:
    token = str(value or "").strip()
    if not token:
        raise SystemExit(f"{source_label} contained an empty dataset identifier.")
    if re.fullmatch(r"I\d{8}", token):
        return token
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", token):
        base, _, _, _ = _dataset_file_base(token, download_path, dataset_product)
        return base.name
    raise SystemExit(
        f"{source_label} currently supports weekly dataset IDs like I20250902 "
        f"or ISO dates like 2025-09-02 only. Got: {token}"
    )


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


def _build_upload_manifest(
    *,
    started_at: str,
    completed: bool,
    embeddings_roots: list[Path],
    dataset_range: dict[str, Any],
    muvera_params: dict[str, Any],
    pq_params: dict[str, Any],
    upload_batch_size: int,
    upload_workers: int,
    reset_requested: bool,
    deleted_collections: tuple[str, ...],
    write_cluster_lmdb: bool,
    skip_existing: bool,
    patent_shard_count: int,
    claim_shard_count: int,
    upload_stats: dict[str, Any],
    elapsed_seconds: float,
    last_error: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = {
        "schema_version": 2,
        "phase": "upload_precomputed_to_weaviate",
        "timestamp": started_at,
        "updated_at": datetime.now().astimezone().isoformat(),
        "completed": bool(completed),
        "embeddings_roots": [str(root) for root in embeddings_roots],
        "dataset": dataset_range,
        "parameters": {
            **muvera_params,
            "pq_enabled": bool(pq_params["enabled"]),
            "upload_batch_size": int(upload_batch_size),
            "upload_workers": int(upload_workers),
            "skip_existing": bool(skip_existing),
            "patent_shards": int(patent_shard_count),
            "claim_shards": int(claim_shard_count),
        },
        "pq": pq_params,
        "reset": {
            "requested": bool(reset_requested),
            "collections_deleted": list(deleted_collections),
        },
        "cluster_lmdb": {
            "enabled": bool(write_cluster_lmdb),
        },
        "upload": upload_stats,
        "runtime": {
            "total_seconds": elapsed_seconds,
        },
    }
    if last_error:
        payload["last_error"] = last_error
    return payload


def _build_weekly_dates(start_date: str, num_datasets: int) -> list[str]:
    anchor = datetime.strptime(start_date, "%Y-%m-%d")
    count = max(0, int(num_datasets))
    return [
        (anchor - timedelta(days=7 * idx)).strftime("%Y-%m-%d")
        for idx in range(count)
    ]


def _resolve_dataset_ids(
    *,
    start_date: str,
    num_datasets: int,
    dataset_ids_raw: str,
    dataset_ids_file: Path | None,
    dataset_ids_key: str | None,
    download_path: Path,
    dataset_product: str,
) -> list[str]:
    explicit = [part.strip() for part in str(dataset_ids_raw or "").split(",") if part.strip()]
    if explicit:
        return [
            _normalize_dataset_identifier(
                part,
                download_path=download_path,
                dataset_product=dataset_product,
                source_label="--dataset-ids",
            )
            for part in explicit
        ]
    if dataset_ids_file is not None:
        identifiers = _load_dataset_identifiers_from_file(
            Path(dataset_ids_file).resolve(),
            key=dataset_ids_key,
        )
        resolved = [
            _normalize_dataset_identifier(
                part,
                download_path=download_path,
                dataset_product=dataset_product,
                source_label="--dataset-ids-file",
            )
            for part in identifiers
        ]
        if not resolved:
            raise SystemExit(f"--dataset-ids-file {dataset_ids_file} did not yield any dataset identifiers.")
        return resolved
    dataset_ids: list[str] = []
    for input_date in _build_weekly_dates(start_date, num_datasets):
        base, _, _, _ = _dataset_file_base(input_date, download_path, dataset_product)
        dataset_ids.append(base.name)
    return dataset_ids


def _load_saved_records_from_file(path: Path):
    opener = gzip.open if path.suffix == ".gz" else Path.open
    if opener is gzip.open:
        handle = opener(path, "rt", encoding="utf-8")
    else:
        handle = opener(path, "r", encoding="utf-8")
    with handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def _find_dataset_manifest(embeddings_root: Path, dataset_id: str) -> Path | None:
    direct = embeddings_root / dataset_id / "manifest.json"
    if direct.exists():
        return direct
    matches = sorted(p for p in embeddings_root.rglob("manifest.json") if p.parent.name == dataset_id)
    if not matches:
        return None
    if len(matches) > 1:
        joined = ", ".join(str(path) for path in matches)
        raise FileNotFoundError(
            f"Ambiguous dataset manifest for {dataset_id} under {embeddings_root}. Matches: {joined}"
        )
    return matches[0]


def _resolve_storage_path(
    manifest: dict[str, Any],
    *,
    storage_format: str,
    manifest_path: Path,
    selected_root: Path,
    dataset_id: str,
) -> Path:
    candidates: list[Path] = []
    if storage_format == "lmdb":
        raw = str(manifest.get("dataset_lmdb_path") or "").strip()
        if raw:
            candidates.append(Path(raw))
        candidates.append(manifest_path.parent / "embeddings.lmdb")
        candidates.append(selected_root / dataset_id / "embeddings.lmdb")
    else:
        raw = str(manifest.get("embeddings_path") or "").strip()
        if raw:
            candidates.append(Path(raw))
        candidates.append(manifest_path.parent / "embeddings.jsonl.gz")
        candidates.append(selected_root / dataset_id / "embeddings.jsonl.gz")
    for candidate in candidates:
        if candidate.exists():
            return candidate
    joined = ", ".join(str(path) for path in candidates)
    raise FileNotFoundError(f"Missing dataset embeddings file for {dataset_id}. Tried: {joined}")


def _load_dataset_manifests(embeddings_roots: list[Path], dataset_ids: list[str]) -> list[dict[str, Any]]:
    manifests: list[dict[str, Any]] = []
    for dataset_id in dataset_ids:
        manifest_path = None
        selected_root = None
        for embeddings_root in embeddings_roots:
            candidate = _find_dataset_manifest(embeddings_root, dataset_id)
            if candidate is not None and candidate.exists():
                manifest_path = candidate
                selected_root = embeddings_root
                break
        if manifest_path is None or selected_root is None:
            searched = ", ".join(str(root) for root in embeddings_roots)
            raise FileNotFoundError(f"Missing dataset manifest for {dataset_id}. Searched: {searched}")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        storage_format = str(manifest.get("storage_format") or "jsonl.gz").strip().lower()
        storage_path = _resolve_storage_path(
            manifest,
            storage_format=storage_format,
            manifest_path=manifest_path,
            selected_root=selected_root,
            dataset_id=dataset_id,
        )
        manifest["storage_format"] = storage_format
        manifest["storage_path"] = str(storage_path.resolve())
        manifest["manifest_path"] = str(manifest_path.resolve())
        manifest["embeddings_root"] = str(selected_root.resolve())
        manifests.append(manifest)
    return manifests


def _discover_complete_dataset_manifests(embeddings_roots: list[Path]) -> list[dict[str, Any]]:
    manifests_by_id: dict[str, dict[str, Any]] = {}
    for embeddings_root in embeddings_roots:
        for manifest_path in sorted(embeddings_root.rglob("manifest.json")):
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            except Exception:
                continue
            if not isinstance(manifest, dict):
                continue
            if str(manifest.get("status") or "").strip().lower() != "complete":
                continue
            dataset_id = str(manifest.get("canonical_dataset_id") or "").strip()
            if not dataset_id or dataset_id in manifests_by_id:
                continue
            storage_format = str(manifest.get("storage_format") or "jsonl.gz").strip().lower()
            storage_path = _resolve_storage_path(
                manifest,
                storage_format=storage_format,
                manifest_path=manifest_path,
                selected_root=embeddings_root,
                dataset_id=dataset_id,
            )
            hydrated = dict(manifest)
            hydrated["storage_format"] = storage_format
            hydrated["storage_path"] = str(storage_path.resolve())
            hydrated["manifest_path"] = str(manifest_path.resolve())
            hydrated["embeddings_root"] = str(embeddings_root.resolve())
            manifests_by_id[dataset_id] = hydrated
    return sorted(
        manifests_by_id.values(),
        key=lambda item: (
            str(item.get("canonical_dataset_date") or ""),
            str(item.get("canonical_dataset_id") or ""),
        ),
    )


def _dataset_range(dataset_manifests: list[dict[str, Any]]) -> dict[str, Any]:
    dates = sorted(
        str(m.get("canonical_dataset_date") or "").strip()
        for m in dataset_manifests
        if str(m.get("canonical_dataset_date") or "").strip()
    )
    return {
        "dataset_ids": [
            str(m.get("canonical_dataset_id") or "").strip()
            for m in dataset_manifests
            if str(m.get("canonical_dataset_id") or "").strip()
        ],
        "date_start": dates[0] if dates else "",
        "date_end": dates[-1] if dates else "",
    }


def _upload_single_saved_dataset(
    manifest: dict[str, Any],
    *,
    batch_size: int,
    muvera_params: dict[str, Any] | None,
    pq_params: dict[str, Any] | None,
    write_cluster_lmdb: bool,
    skip_existing: bool,
    patent_shard_count: int,
    claim_shard_count: int,
) -> dict[str, Any]:
    storage_path = Path(manifest["storage_path"])
    storage_format = str(manifest.get("storage_format") or "jsonl.gz").strip().lower()
    dataset_id = str(manifest["canonical_dataset_id"])
    count = 0
    skipped_existing = 0
    buffer: list[dict[str, Any]] = []
    if storage_format == "lmdb":
        records = load_dataset_embeddings_from_lmdb(storage_path)
    else:
        records = _load_saved_records_from_file(storage_path)
    for record in records:
        buffer.append(record)
        if len(buffer) >= batch_size:
            result = store_embeddings(
                buffer,
                muvera_params=muvera_params,
                pq_params=pq_params,
                write_lmdb=write_cluster_lmdb,
                skip_existing=skip_existing,
                patent_shard_count=patent_shard_count,
                claim_shard_count=claim_shard_count,
            )
            inserted = int((result or {}).get("claims_inserted", len(buffer)))
            skipped_existing += int((result or {}).get("claims_skipped_existing", 0))
            count += inserted
            buffer.clear()
    if buffer:
        result = store_embeddings(
            buffer,
            muvera_params=muvera_params,
            pq_params=pq_params,
            write_lmdb=write_cluster_lmdb,
            skip_existing=skip_existing,
            patent_shard_count=patent_shard_count,
            claim_shard_count=claim_shard_count,
        )
        inserted = int((result or {}).get("claims_inserted", len(buffer)))
        skipped_existing += int((result or {}).get("claims_skipped_existing", 0))
        count += inserted
        buffer.clear()
    return {
        "canonical_dataset_id": dataset_id,
        "uploaded_records": count,
        "skipped_existing_records": skipped_existing,
        "storage_format": storage_format,
        "storage_path": str(storage_path),
        "status": "completed",
    }


def upload_saved_embeddings(
    dataset_manifests: list[dict[str, Any]],
    *,
    batch_size: int,
    muvera_params: dict[str, Any] | None,
    pq_params: dict[str, Any] | None,
    write_cluster_lmdb: bool,
    skip_existing: bool,
    completed_dataset_uploads: dict[str, dict[str, Any]] | None = None,
    upload_workers: int = 1,
    patent_shard_count: int = WEAVIATE_PATENT_SHARD_COUNT,
    claim_shard_count: int = WEAVIATE_CLAIM_SHARD_COUNT,
    progress_callback=None,
) -> dict[str, Any]:
    completed_dataset_uploads = completed_dataset_uploads or {}
    dataset_order = [str(manifest.get("canonical_dataset_id") or "") for manifest in dataset_manifests]
    if len(dataset_order) != len(set(dataset_order)):
        raise ValueError("dataset_manifests contains duplicate canonical_dataset_id values.")
    total_uploaded = sum(
        int(item.get("uploaded_records", 0))
        for item in completed_dataset_uploads.values()
        if str(item.get("status") or "").strip().lower() == "completed"
    )
    dataset_counts_by_id: dict[str, dict[str, Any]] = {}
    pending_manifests: list[dict[str, Any]] = []

    def _ordered_dataset_counts() -> list[dict[str, Any]]:
        return [
            dataset_counts_by_id[dataset_id]
            for dataset_id in dataset_order
            if dataset_id in dataset_counts_by_id
        ]

    for manifest in dataset_manifests:
        dataset_id = str(manifest["canonical_dataset_id"])
        prior = completed_dataset_uploads.get(dataset_id)
        if prior and str(prior.get("status") or "").strip().lower() == "completed":
            dataset_counts_by_id[dataset_id] = dict(prior)
            print(
                f"[upload-only] Reusing completed dataset {dataset_id}: "
                f"{int(prior.get('uploaded_records', 0))} records"
            )
            if progress_callback is not None:
                progress_callback(_ordered_dataset_counts(), total_uploaded)
            continue
        pending_manifests.append(manifest)

    if int(upload_workers) <= 1:
        for manifest in pending_manifests:
            dataset_item = _upload_single_saved_dataset(
                manifest,
                batch_size=batch_size,
                muvera_params=muvera_params,
                pq_params=pq_params,
                write_cluster_lmdb=write_cluster_lmdb,
                skip_existing=skip_existing,
                patent_shard_count=patent_shard_count,
                claim_shard_count=claim_shard_count,
            )
            dataset_id = str(dataset_item["canonical_dataset_id"])
            dataset_counts_by_id[dataset_id] = dataset_item
            total_uploaded += int(dataset_item.get("uploaded_records", 0))
            print(
                f"[upload-only] Uploaded dataset {dataset_id}: "
                f"{int(dataset_item.get('uploaded_records', 0))} records"
                + (
                    f" (skipped_existing={int(dataset_item.get('skipped_existing_records', 0))})"
                    if int(dataset_item.get("skipped_existing_records", 0))
                    else ""
                )
            )
            if progress_callback is not None:
                progress_callback(_ordered_dataset_counts(), total_uploaded)
    else:
        first_error: Exception | None = None
        queue = list(pending_manifests)
        running: dict[Future[dict[str, Any]], str] = {}

        with ThreadPoolExecutor(max_workers=max(1, int(upload_workers))) as executor:
            while queue and len(running) < int(upload_workers):
                manifest = queue.pop(0)
                dataset_id = str(manifest["canonical_dataset_id"])
                running[
                    executor.submit(
                        _upload_single_saved_dataset,
                        manifest,
                        batch_size=batch_size,
                        muvera_params=muvera_params,
                        pq_params=pq_params,
                        write_cluster_lmdb=write_cluster_lmdb,
                        skip_existing=skip_existing,
                        patent_shard_count=patent_shard_count,
                        claim_shard_count=claim_shard_count,
                    )
                ] = dataset_id

            while running:
                done, _ = wait(tuple(running.keys()), return_when=FIRST_COMPLETED)
                for future in done:
                    dataset_id = running.pop(future)
                    try:
                        dataset_item = future.result()
                    except Exception as exc:
                        if first_error is None:
                            first_error = exc
                        continue

                    dataset_counts_by_id[dataset_id] = dataset_item
                    total_uploaded += int(dataset_item.get("uploaded_records", 0))
                    print(
                        f"[upload-only] Uploaded dataset {dataset_id}: "
                        f"{int(dataset_item.get('uploaded_records', 0))} records"
                        + (
                            f" (skipped_existing={int(dataset_item.get('skipped_existing_records', 0))})"
                            if int(dataset_item.get("skipped_existing_records", 0))
                            else ""
                        )
                    )
                    if progress_callback is not None:
                        progress_callback(_ordered_dataset_counts(), total_uploaded)

                if first_error is not None:
                    continue

                while queue and len(running) < int(upload_workers):
                    manifest = queue.pop(0)
                    dataset_id = str(manifest["canonical_dataset_id"])
                    running[
                        executor.submit(
                            _upload_single_saved_dataset,
                            manifest,
                            batch_size=batch_size,
                            muvera_params=muvera_params,
                            pq_params=pq_params,
                            write_cluster_lmdb=write_cluster_lmdb,
                            skip_existing=skip_existing,
                            patent_shard_count=patent_shard_count,
                            claim_shard_count=claim_shard_count,
                        )
                    ] = dataset_id

        if first_error is not None:
            raise first_error

    return {
        "total_uploaded_records": total_uploaded,
        "dataset_uploads": _ordered_dataset_counts(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Upload precomputed dataset embeddings to Weaviate without running the qrels sweep."
    )
    parser.add_argument(
        "--embeddings-root",
        type=Path,
        nargs="+",
        required=True,
        help="One or more roots containing per-dataset manifest.json + embeddings.lmdb directories.",
    )
    parser.add_argument("--start-date", type=str, default="2025-09-02")
    parser.add_argument("--num-datasets", type=int, default=4)
    parser.add_argument("--dataset-ids", type=str, default="")
    parser.add_argument(
        "--dataset-ids-file",
        type=Path,
        default=None,
        help=(
            "Optional path to a JSON or text file containing dataset IDs or ISO dates. "
            "Use --dataset-ids-key when the JSON file contains multiple dataset lists."
        ),
    )
    parser.add_argument(
        "--dataset-ids-key",
        type=str,
        default="",
        help="Optional JSON key to read from --dataset-ids-file.",
    )
    parser.add_argument(
        "--all-complete-datasets",
        action="store_true",
        help="Ignore date-range selection and upload every complete dataset manifest found under --embeddings-root.",
    )
    parser.add_argument("--download-path", type=Path, default=DOWNLOAD_DIR)
    parser.add_argument("--dataset-product", type=str, default="PTGRDT")
    parser.add_argument("--upload-batch-size", type=int, default=256)
    parser.add_argument(
        "--upload-workers",
        type=int,
        default=1,
        help="Dataset-level upload workers. Each worker uploads one dataset at a time.",
    )
    parser.add_argument("--reset", action="store_true", help="Delete/recreate Patent and Claim before upload.")
    parser.add_argument(
        "--write-cluster-lmdb",
        action="store_true",
        help="Also write cluster-side LMDB side stores during upload. Default is off.",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Before insert, query Weaviate for existing claim/patent UUIDs and skip duplicates. Use this to resume after interrupted uploads.",
    )
    parser.add_argument("--ksim", type=int, default=WEAVIATE_MUVERA_KSIM)
    parser.add_argument("--dprojections", type=int, default=WEAVIATE_MUVERA_DPROJECTIONS)
    parser.add_argument("--repetitions", type=int, default=WEAVIATE_MUVERA_REPETITIONS)
    parser.add_argument("--pq-enabled", type=_parse_bool, default=WEAVIATE_PQ_ENABLED)
    parser.add_argument("--pq-centroids", type=int, default=WEAVIATE_PQ_CENTROIDS)
    parser.add_argument("--pq-segments", type=int, default=WEAVIATE_PQ_SEGMENTS)
    parser.add_argument("--pq-training-limit", type=int, default=WEAVIATE_PQ_TRAINING_LIMIT)
    parser.add_argument("--pq-bit-compression", type=_parse_bool, default=WEAVIATE_PQ_BIT_COMPRESSION)
    parser.add_argument(
        "--patent-shards",
        type=int,
        default=WEAVIATE_PATENT_SHARD_COUNT,
        help="Desired shard count when Patent is created during --reset or lazy collection creation.",
    )
    parser.add_argument(
        "--claim-shards",
        type=int,
        default=WEAVIATE_CLAIM_SHARD_COUNT,
        help="Desired shard count when Claim is created during --reset or lazy collection creation.",
    )
    parser.add_argument("--output-manifest", type=Path, default=None)
    args = parser.parse_args()

    embeddings_roots = [Path(root).resolve() for root in args.embeddings_root]
    download_path = Path(args.download_path).resolve()
    if int(args.upload_workers) < 1:
        raise SystemExit("--upload-workers must be >= 1.")
    if int(args.patent_shards) < 1 or int(args.claim_shards) < 1:
        raise SystemExit("--patent-shards and --claim-shards must be >= 1.")
    if int(args.upload_workers) > 1 and bool(args.write_cluster_lmdb):
        print(
            "[warn] Parallel dataset uploads with --write-cluster-lmdb enabled can contend on local LMDB side stores."
        )

    if args.all_complete_datasets:
        dataset_manifests = _discover_complete_dataset_manifests(embeddings_roots)
        if not dataset_manifests:
            searched = ", ".join(str(root) for root in embeddings_roots)
            raise SystemExit(f"No complete dataset manifests found under: {searched}")
        dataset_ids = [str(item.get("canonical_dataset_id") or "") for item in dataset_manifests]
    else:
        dataset_ids = _resolve_dataset_ids(
            start_date=args.start_date,
            num_datasets=int(args.num_datasets),
            dataset_ids_raw=args.dataset_ids,
            dataset_ids_file=args.dataset_ids_file,
            dataset_ids_key=args.dataset_ids_key,
            download_path=download_path,
            dataset_product=args.dataset_product,
        )
        dataset_manifests = _load_dataset_manifests(embeddings_roots, dataset_ids)
    dataset_range = _dataset_range(dataset_manifests)

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
    dataset_display = ",".join(dataset_ids[:20])
    if len(dataset_ids) > 20:
        dataset_display += ",..."

    print(
        f"[upload-only] embeddings_roots={','.join(str(root) for root in embeddings_roots)} "
        f"dataset_count={len(dataset_ids)} datasets={dataset_display} "
        f"reset={int(bool(args.reset))} batch_size={int(args.upload_batch_size)} "
        f"workers={int(args.upload_workers)} patent_shards={int(args.patent_shards)} "
        f"claim_shards={int(args.claim_shards)}"
    )
    print(
        f"[upload-only] muvera ksim={muvera_params['ksim']} dprojections={muvera_params['dprojections']} "
        f"repetitions={muvera_params['repetitions']} pq={int(bool(pq_params['enabled']))}"
    )

    if args.output_manifest is not None:
        manifest_path = Path(args.output_manifest).resolve()
    else:
        manifest_path = _default_manifest_path(
            DEFAULT_UPLOAD_RUNS_DIR,
            dataset_ids=dataset_ids,
            muvera_params=muvera_params,
            pq_params=pq_params,
        )

    existing_manifest = _load_json_if_exists(manifest_path)
    selected_dataset_ids = set(dataset_ids)
    existing_dataset_uploads = {
        str(item.get("canonical_dataset_id") or ""): item
        for item in (existing_manifest.get("upload", {}).get("dataset_uploads", []) or [])
        if str(item.get("canonical_dataset_id") or "").strip() in selected_dataset_ids
    }

    started_at = str(existing_manifest.get("timestamp") or datetime.now().astimezone().isoformat())
    start = time.perf_counter()
    deleted_collections: tuple[str, ...] = ()
    if args.reset:
        deleted_collections = reset_weaviate_state(
            muvera_params=muvera_params,
            pq_params=pq_params,
            patent_shard_count=int(args.patent_shards),
            claim_shard_count=int(args.claim_shards),
        )

    def _write_progress(dataset_counts: list[dict[str, Any]], total_uploaded: int, *, completed: bool = False) -> None:
        payload = _build_upload_manifest(
            started_at=started_at,
            completed=completed,
            embeddings_roots=embeddings_roots,
            dataset_range=dataset_range,
            muvera_params=muvera_params,
            pq_params=pq_params,
            upload_batch_size=int(args.upload_batch_size),
            upload_workers=int(args.upload_workers),
            reset_requested=bool(args.reset),
            deleted_collections=deleted_collections,
            write_cluster_lmdb=bool(args.write_cluster_lmdb),
            skip_existing=bool(args.skip_existing),
            patent_shard_count=int(args.patent_shards),
            claim_shard_count=int(args.claim_shards),
            upload_stats={
                "total_uploaded_records": total_uploaded,
                "dataset_uploads": dataset_counts,
            },
            elapsed_seconds=time.perf_counter() - start,
        )
        _json_dump(manifest_path, payload)

    if existing_dataset_uploads and not args.reset:
        reused = [
            dataset_id
            for dataset_id in dataset_ids
            if str(existing_dataset_uploads.get(dataset_id, {}).get("status") or "").strip().lower() == "completed"
        ]
        if reused:
            print(f"[upload-only] Reusing completed datasets from prior manifest: {','.join(reused)}")

    try:
        upload_stats = upload_saved_embeddings(
            dataset_manifests,
            batch_size=int(args.upload_batch_size),
            muvera_params=muvera_params,
            pq_params=pq_params,
            write_cluster_lmdb=bool(args.write_cluster_lmdb),
            skip_existing=bool(args.skip_existing),
            completed_dataset_uploads=existing_dataset_uploads if not args.reset else {},
            upload_workers=int(args.upload_workers),
            patent_shard_count=int(args.patent_shards),
            claim_shard_count=int(args.claim_shards),
            progress_callback=lambda dataset_counts, total_uploaded: _write_progress(
                dataset_counts,
                total_uploaded,
                completed=False,
            ),
        )
    except Exception as exc:
        prior = _load_json_if_exists(manifest_path)
        dataset_uploads = prior.get("upload", {}).get("dataset_uploads", []) if prior else []
        total_uploaded = int(prior.get("upload", {}).get("total_uploaded_records", 0)) if prior else 0
        failure_manifest = _build_upload_manifest(
            started_at=started_at,
            completed=False,
            embeddings_roots=embeddings_roots,
            dataset_range=dataset_range,
            muvera_params=muvera_params,
            pq_params=pq_params,
            upload_batch_size=int(args.upload_batch_size),
            upload_workers=int(args.upload_workers),
            reset_requested=bool(args.reset),
            deleted_collections=deleted_collections,
            write_cluster_lmdb=bool(args.write_cluster_lmdb),
            skip_existing=bool(args.skip_existing),
            patent_shard_count=int(args.patent_shards),
            claim_shard_count=int(args.claim_shards),
            upload_stats={
                "total_uploaded_records": total_uploaded,
                "dataset_uploads": dataset_uploads,
            },
            elapsed_seconds=time.perf_counter() - start,
            last_error={
                "type": type(exc).__name__,
                "message": str(exc),
            },
        )
        _json_dump(manifest_path, failure_manifest)
        raise

    elapsed = time.perf_counter() - start

    manifest = _build_upload_manifest(
        started_at=started_at,
        completed=True,
        embeddings_roots=embeddings_roots,
        dataset_range=dataset_range,
        muvera_params=muvera_params,
        pq_params=pq_params,
        upload_batch_size=int(args.upload_batch_size),
        upload_workers=int(args.upload_workers),
        reset_requested=bool(args.reset),
        deleted_collections=deleted_collections,
        write_cluster_lmdb=bool(args.write_cluster_lmdb),
        skip_existing=bool(args.skip_existing),
        patent_shard_count=int(args.patent_shards),
        claim_shard_count=int(args.claim_shards),
        upload_stats=upload_stats,
        elapsed_seconds=elapsed,
    )
    _json_dump(manifest_path, manifest)
    print(f"[upload-only] Wrote manifest: {manifest_path}")
    print(f"[upload-only] Uploaded {upload_stats['total_uploaded_records']} total records in {elapsed:.1f}s")


if __name__ == "__main__":
    main()
