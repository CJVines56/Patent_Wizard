from __future__ import annotations

import argparse
import gzip
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

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
    download_path: Path,
    dataset_product: str,
) -> list[str]:
    explicit = [part.strip() for part in str(dataset_ids_raw or "").split(",") if part.strip()]
    if explicit:
        return explicit
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


def _load_dataset_manifests(embeddings_roots: list[Path], dataset_ids: list[str]) -> list[dict[str, Any]]:
    manifests: list[dict[str, Any]] = []
    for dataset_id in dataset_ids:
        manifest_path = None
        selected_root = None
        for embeddings_root in embeddings_roots:
            candidate = embeddings_root / dataset_id / "manifest.json"
            if candidate.exists():
                manifest_path = candidate
                selected_root = embeddings_root
                break
        if manifest_path is None or selected_root is None:
            searched = ", ".join(str(root / dataset_id / "manifest.json") for root in embeddings_roots)
            raise FileNotFoundError(f"Missing dataset manifest for {dataset_id}. Searched: {searched}")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        storage_format = str(manifest.get("storage_format") or "jsonl.gz").strip().lower()
        if storage_format == "lmdb":
            storage_path = Path(manifest.get("dataset_lmdb_path") or selected_root / dataset_id / "embeddings.lmdb")
        else:
            storage_path = Path(manifest.get("embeddings_path") or selected_root / dataset_id / "embeddings.jsonl.gz")
        if not storage_path.exists():
            raise FileNotFoundError(f"Missing dataset embeddings file: {storage_path}")
        manifest["storage_format"] = storage_format
        manifest["storage_path"] = str(storage_path.resolve())
        manifest["manifest_path"] = str(manifest_path.resolve())
        manifest["embeddings_root"] = str(selected_root.resolve())
        manifests.append(manifest)
    return manifests


def _dataset_range(dataset_manifests: list[dict[str, Any]]) -> dict[str, Any]:
    dates = sorted(str(m.get("canonical_dataset_date") or "") for m in dataset_manifests)
    return {
        "dataset_ids": [str(m.get("canonical_dataset_id") or "") for m in dataset_manifests],
        "date_start": dates[0] if dates else "",
        "date_end": dates[-1] if dates else "",
    }


def upload_saved_embeddings(
    dataset_manifests: list[dict[str, Any]],
    *,
    batch_size: int,
    muvera_params: dict[str, Any] | None,
    pq_params: dict[str, Any] | None,
    write_cluster_lmdb: bool,
) -> dict[str, Any]:
    total_uploaded = 0
    dataset_counts: list[dict[str, Any]] = []
    for manifest in dataset_manifests:
        storage_path = Path(manifest["storage_path"])
        storage_format = str(manifest.get("storage_format") or "jsonl.gz").strip().lower()
        dataset_id = str(manifest["canonical_dataset_id"])
        count = 0
        buffer: list[dict[str, Any]] = []
        if storage_format == "lmdb":
            records = load_dataset_embeddings_from_lmdb(storage_path)
        else:
            records = _load_saved_records_from_file(storage_path)
        for record in records:
            buffer.append(record)
            if len(buffer) >= batch_size:
                store_embeddings(
                    buffer,
                    muvera_params=muvera_params,
                    pq_params=pq_params,
                    write_lmdb=write_cluster_lmdb,
                )
                count += len(buffer)
                total_uploaded += len(buffer)
                buffer.clear()
        if buffer:
            store_embeddings(
                buffer,
                muvera_params=muvera_params,
                pq_params=pq_params,
                write_lmdb=write_cluster_lmdb,
            )
            count += len(buffer)
            total_uploaded += len(buffer)
            buffer.clear()
        dataset_counts.append(
            {
                "canonical_dataset_id": dataset_id,
                "uploaded_records": count,
                "storage_format": storage_format,
                "storage_path": str(storage_path),
            }
        )
        print(f"[upload-only] Uploaded dataset {dataset_id}: {count} records")
    return {
        "total_uploaded_records": total_uploaded,
        "dataset_uploads": dataset_counts,
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
    parser.add_argument("--download-path", type=Path, default=DOWNLOAD_DIR)
    parser.add_argument("--dataset-product", type=str, default="PTGRDT")
    parser.add_argument("--upload-batch-size", type=int, default=256)
    parser.add_argument("--reset", action="store_true", help="Delete/recreate Patent and Claim before upload.")
    parser.add_argument(
        "--write-cluster-lmdb",
        action="store_true",
        help="Also write cluster-side LMDB side stores during upload. Default is off.",
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

    embeddings_roots = [Path(root).resolve() for root in args.embeddings_root]
    download_path = Path(args.download_path).resolve()
    dataset_ids = _resolve_dataset_ids(
        start_date=args.start_date,
        num_datasets=int(args.num_datasets),
        dataset_ids_raw=args.dataset_ids,
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

    print(
        f"[upload-only] embeddings_roots={','.join(str(root) for root in embeddings_roots)} "
        f"datasets={','.join(dataset_ids)} "
        f"reset={int(bool(args.reset))} batch_size={int(args.upload_batch_size)}"
    )
    print(
        f"[upload-only] muvera ksim={muvera_params['ksim']} dprojections={muvera_params['dprojections']} "
        f"repetitions={muvera_params['repetitions']} pq={int(bool(pq_params['enabled']))}"
    )

    started_at = datetime.now().astimezone().isoformat()
    start = time.perf_counter()
    deleted_collections: tuple[str, ...] = ()
    if args.reset:
        deleted_collections = reset_weaviate_state(muvera_params=muvera_params, pq_params=pq_params)

    upload_stats = upload_saved_embeddings(
        dataset_manifests,
        batch_size=int(args.upload_batch_size),
        muvera_params=muvera_params,
        pq_params=pq_params,
        write_cluster_lmdb=bool(args.write_cluster_lmdb),
    )
    elapsed = time.perf_counter() - start

    manifest = {
        "schema_version": 1,
        "phase": "upload_precomputed_to_weaviate",
        "timestamp": started_at,
        "embeddings_roots": [str(root) for root in embeddings_roots],
        "dataset": dataset_range,
        "parameters": {
            **muvera_params,
            "pq_enabled": bool(pq_params["enabled"]),
        },
        "pq": pq_params,
        "reset": {
            "requested": bool(args.reset),
            "collections_deleted": list(deleted_collections),
        },
        "cluster_lmdb": {
            "enabled": bool(args.write_cluster_lmdb),
        },
        "upload": upload_stats,
        "runtime": {
            "total_seconds": elapsed,
        },
    }

    if args.output_manifest is not None:
        manifest_path = Path(args.output_manifest).resolve()
    else:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        manifest_path = (DEFAULT_UPLOAD_RUNS_DIR / f"upload_{stamp}.json").resolve()
    _json_dump(manifest_path, manifest)
    print(f"[upload-only] Wrote manifest: {manifest_path}")
    print(f"[upload-only] Uploaded {upload_stats['total_uploaded_records']} total records in {elapsed:.1f}s")


if __name__ == "__main__":
    main()
