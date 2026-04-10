from __future__ import annotations

import argparse
import io
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import lmdb
import numpy as np
import requests
from requests.adapters import HTTPAdapter


WEAVIATE_OBJECTS = os.environ.get("WEAVIATE_OBJECTS", "http://localhost:8080/v1/objects").rstrip("/")
WEAVIATE_API_KEY = os.environ.get("WEAVIATE_API_KEY", "").strip()
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parents[2] / "validation" / "cluster_manifests"


def _json_dump(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _build_session(pool_maxsize: int = 32) -> requests.Session:
    sess = requests.Session()
    adapter = HTTPAdapter(pool_connections=pool_maxsize, pool_maxsize=pool_maxsize)
    sess.mount("http://", adapter)
    sess.mount("https://", adapter)
    if WEAVIATE_API_KEY:
        sess.headers.update({"Authorization": f"Bearer {WEAVIATE_API_KEY}"})
    return sess


def _fetch_objects_page(
    sess: requests.Session,
    *,
    class_name: str,
    limit: int,
    after: str | None,
    timeout_s: int,
) -> list[dict[str, Any]]:
    params = {
        "class": class_name,
        "limit": str(int(limit)),
    }
    if after:
        params["after"] = str(after)
    resp = sess.get(WEAVIATE_OBJECTS, params=params, timeout=timeout_s)
    if resp.status_code != 200:
        raise RuntimeError(
            f"Weaviate list objects failed for class={class_name}: {resp.status_code} {resp.text[:400]}"
        )
    payload = resp.json()
    return payload.get("objects", []) or []


def _iter_cluster_patent_doc_ids(page_size: int, timeout_s: int):
    sess = _build_session()
    try:
        after: str | None = None
        while True:
            items = _fetch_objects_page(
                sess,
                class_name="Patent",
                limit=page_size,
                after=after,
                timeout_s=timeout_s,
            )
            if not items:
                break
            for obj in items:
                props = obj.get("properties") or {}
                doc_id = str(props.get("doc_id") or "").strip()
                if doc_id:
                    yield doc_id
            after = str(items[-1].get("id") or "").strip() or None
    finally:
        sess.close()


def _iter_dataset_manifests(roots: list[Path]):
    seen: set[Path] = set()
    for root in roots:
        for manifest_path in sorted(root.rglob("manifest.json")):
            resolved = manifest_path.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            try:
                payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            except Exception:
                continue
            dataset_id = str(payload.get("canonical_dataset_id") or "").strip()
            if not dataset_id:
                continue
            yield manifest_path, payload


def _resolve_storage_path(manifest_path: Path, payload: dict[str, Any]) -> Path | None:
    raw_candidates = [
        str(payload.get("dataset_lmdb_path") or "").strip(),
        str(payload.get("storage_path") or "").strip(),
    ]
    candidates = [Path(raw) for raw in raw_candidates if raw]
    candidates.append(manifest_path.parent / "embeddings.lmdb")
    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()
    return None


def _default_output_path() -> Path:
    ts = datetime.now().astimezone().strftime("%Y%m%d_%H%M%S")
    return (DEFAULT_OUTPUT_DIR / f"inferred_cluster_datasets_{ts}.json").resolve()


def _np_scalar_to_str(value) -> str:
    if isinstance(value, np.ndarray):
        if value.shape == ():
            return str(value.item())
        if value.size == 0:
            return ""
        return str(value.reshape(-1)[0])
    return str(value)


def _iter_unique_doc_ids_from_dataset_lmdb(path: Path):
    env = lmdb.open(
        str(path),
        readonly=True,
        lock=False,
        readahead=False,
        create=False,
        subdir=True,
        max_dbs=1,
    )
    seen: set[str] = set()
    try:
        with env.begin(write=False) as txn:
            cursor = txn.cursor()
            for _, payload in cursor:
                if payload is None:
                    continue
                buffer = io.BytesIO(payload)
                obj = np.load(buffer, allow_pickle=False)
                try:
                    metadata_raw = ""
                    if "metadata" in obj:
                        metadata_raw = _np_scalar_to_str(obj["metadata"])
                    metadata = json.loads(metadata_raw) if metadata_raw else {}
                    if not isinstance(metadata, dict):
                        metadata = {}
                    doc_id = str(metadata.get("doc_id") or "").strip()
                    if not doc_id and "doc_id" in obj:
                        doc_id = _np_scalar_to_str(obj["doc_id"]).strip()
                    if doc_id and doc_id not in seen:
                        seen.add(doc_id)
                        yield doc_id
                finally:
                    if isinstance(obj, np.lib.npyio.NpzFile):
                        obj.close()
    finally:
        env.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Infer which local datasets are present on the current Weaviate cluster by "
            "matching cluster Patent doc_ids against local per-dataset LMDB embeddings."
        )
    )
    parser.add_argument(
        "--embeddings-root",
        type=Path,
        nargs="+",
        required=True,
        help="One or more roots containing per-dataset manifest.json + embeddings.lmdb directories.",
    )
    parser.add_argument("--page-size", type=int, default=500)
    parser.add_argument("--timeout-s", type=int, default=60)
    parser.add_argument("--output-manifest", type=Path, default=None)
    args = parser.parse_args()

    roots = [Path(root).resolve() for root in args.embeddings_root]
    output_manifest = (
        Path(args.output_manifest).resolve() if args.output_manifest is not None else _default_output_path()
    )

    started = time.perf_counter()
    print(f"[infer] Fetching Patent doc_ids from {WEAVIATE_OBJECTS}")
    cluster_doc_ids: set[str] = set()
    fetched = 0
    for doc_id in _iter_cluster_patent_doc_ids(int(args.page_size), int(args.timeout_s)):
        fetched += 1
        cluster_doc_ids.add(doc_id)
        if fetched % 5000 == 0:
            print(f"[infer] fetched_patents={fetched} unique_doc_ids={len(cluster_doc_ids)}")

    print(f"[infer] Cluster unique Patent doc_ids: {len(cluster_doc_ids)}")

    dataset_summaries: list[dict[str, Any]] = []
    matched_by_cluster_doc: dict[str, list[str]] = {}

    for manifest_path, payload in _iter_dataset_manifests(roots):
        dataset_id = str(payload.get("canonical_dataset_id") or "").strip()
        storage_path = _resolve_storage_path(manifest_path, payload)
        if storage_path is None:
            print(f"[infer][warn] Skipping {dataset_id}: no embeddings storage found")
            continue

        local_doc_ids: set[str] = set()
        matched_doc_count = 0
        for doc_id in _iter_unique_doc_ids_from_dataset_lmdb(storage_path):
            local_doc_ids.add(doc_id)
            if doc_id not in cluster_doc_ids:
                continue
            matched_doc_count += 1
            matched_by_cluster_doc.setdefault(doc_id, []).append(dataset_id)

        coverage = (matched_doc_count / len(local_doc_ids)) if local_doc_ids else 0.0
        dataset_summaries.append(
            {
                "canonical_dataset_id": dataset_id,
                "canonical_dataset_date": str(payload.get("canonical_dataset_date") or ""),
                "dataset_product": str(payload.get("dataset_product") or ""),
                "local_doc_count": len(local_doc_ids),
                "matched_cluster_doc_count": matched_doc_count,
                "coverage_ratio": round(coverage, 6),
                "manifest_path": str(manifest_path.resolve()),
                "storage_path": str(storage_path),
            }
        )
        print(
            f"[infer] dataset={dataset_id} matched_docs={matched_doc_count}/{len(local_doc_ids)}"
        )

    ambiguous_docs = {
        doc_id: dataset_ids
        for doc_id, dataset_ids in matched_by_cluster_doc.items()
        if len(dataset_ids) > 1
    }
    matched_docs = len(matched_by_cluster_doc)
    unmatched_count = max(0, len(cluster_doc_ids) - matched_docs)

    dataset_summaries.sort(
        key=lambda row: (
            -int(row.get("matched_cluster_doc_count") or 0),
            str(row.get("canonical_dataset_id") or ""),
        )
    )

    manifest = {
        "schema_version": 1,
        "phase": "infer_cluster_datasets_from_local_embeddings",
        "created_at": datetime.now().astimezone().isoformat(),
        "weaviate_objects_endpoint": WEAVIATE_OBJECTS,
        "embeddings_roots": [str(root) for root in roots],
        "cluster": {
            "unique_patent_doc_ids": len(cluster_doc_ids),
            "matched_patent_doc_ids": matched_docs,
            "unmatched_patent_doc_ids": unmatched_count,
            "ambiguous_patent_doc_ids": len(ambiguous_docs),
        },
        "datasets": dataset_summaries,
        "ambiguous_doc_id_samples": [
            {
                "doc_id": doc_id,
                "datasets": dataset_ids,
            }
            for doc_id, dataset_ids in sorted(ambiguous_docs.items())[:100]
        ],
        "runtime": {
            "total_seconds": time.perf_counter() - started,
        },
    }
    _json_dump(output_manifest, manifest)
    print(f"[infer] Wrote manifest: {output_manifest}")


if __name__ == "__main__":
    main()
