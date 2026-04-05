from __future__ import annotations

import argparse
import json
import os
import shutil
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import requests
from requests.adapters import HTTPAdapter

from backend.app.store import (
    _open_lmdb_env,
    _write_lmdb_claim_payloads,
    _write_lmdb_json_records,
    _write_lmdb_vectors,
)
from backend.app.vector_config import WEAVIATE_NAMED_VECTOR, assert_128_variant


WEAVIATE_OBJECTS = os.environ.get("WEAVIATE_OBJECTS", "http://localhost:8080/v1/objects").rstrip("/")
WEAVIATE_API_KEY = os.environ.get("WEAVIATE_API_KEY", "").strip()


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
    include_vector: bool,
    timeout_s: int,
) -> list[dict[str, Any]]:
    params = {
        "class": class_name,
        "limit": str(int(limit)),
    }
    if after:
        params["after"] = str(after)
    if include_vector:
        params["include"] = "vector"
    resp = sess.get(WEAVIATE_OBJECTS, params=params, timeout=timeout_s)
    if resp.status_code != 200:
        raise RuntimeError(
            f"Weaviate list objects failed for class={class_name}: {resp.status_code} {resp.text[:400]}"
        )
    payload = resp.json()
    return payload.get("objects", []) or []


def _coerce_token_matrix(value: Any, *, identity: str) -> np.ndarray:
    arr = np.asarray(value, dtype=np.float32)
    if arr.ndim == 1:
        arr = arr.reshape(1, -1)
    if arr.ndim != 2 or arr.shape[0] <= 0 or arr.shape[1] != 128:
        raise ValueError(f"Expected [T,128] vectors for {identity}, got shape={arr.shape}")
    return arr


def _extract_vector_from_object(obj: dict[str, Any]) -> np.ndarray | None:
    vectors = obj.get("vectors")
    oid = str(obj.get("id") or "").strip()
    if isinstance(vectors, dict) and WEAVIATE_NAMED_VECTOR in vectors:
        return _coerce_token_matrix(vectors[WEAVIATE_NAMED_VECTOR], identity=oid or "unknown")
    return None


def _fetch_vector_detail(sess: requests.Session, object_id: str, timeout_s: int) -> np.ndarray:
    url = f"{WEAVIATE_OBJECTS}/Claim/{object_id}"
    resp = sess.get(url, params={"include": "vector"}, timeout=timeout_s)
    if resp.status_code != 200:
        raise RuntimeError(f"Weaviate vector fetch failed for {object_id}: {resp.status_code} {resp.text[:400]}")
    payload = resp.json()
    vectors = payload.get("vectors")
    if not isinstance(vectors, dict) or WEAVIATE_NAMED_VECTOR not in vectors:
        raise ValueError(
            f"Weaviate object {object_id} missing named vector '{WEAVIATE_NAMED_VECTOR}'."
        )
    return _coerce_token_matrix(vectors[WEAVIATE_NAMED_VECTOR], identity=object_id)


def export_claim_vectors(
    *,
    output_root: Path,
    shard: str,
    page_size: int,
    timeout_s: int,
    overwrite: bool,
    export_patent_metadata: bool,
) -> dict[str, Any]:
    output_root.mkdir(parents=True, exist_ok=True)
    vector_lmdb_path = output_root / f"colbert_{shard}.lmdb"
    claim_payload_lmdb_path = output_root / "claim_payloads.lmdb"
    patent_metadata_lmdb_path = output_root / "patent_metadata.lmdb"
    manifest_path = output_root / "manifest.json"
    existing_outputs = [path for path in (vector_lmdb_path, claim_payload_lmdb_path, patent_metadata_lmdb_path) if path.exists()]
    if existing_outputs and not overwrite:
        raise FileExistsError(
            "Export target already exists. Pass --overwrite to replace it: "
            + ", ".join(str(path) for path in existing_outputs)
        )

    if overwrite:
        for path in (vector_lmdb_path, claim_payload_lmdb_path, patent_metadata_lmdb_path):
            shutil.rmtree(path, ignore_errors=True)
        if manifest_path.exists():
            manifest_path.unlink()

    sess = _build_session()
    vector_env = _open_lmdb_env(vector_lmdb_path)
    payload_env = _open_lmdb_env(claim_payload_lmdb_path)
    patent_env = _open_lmdb_env(patent_metadata_lmdb_path) if export_patent_metadata else None

    claim_count = 0
    doc_ids: set[str] = set()
    total_token_rows = 0
    fallback_vector_fetches = 0
    started = time.perf_counter()

    try:
        after: str | None = None
        while True:
            items = _fetch_objects_page(
                sess,
                class_name="Claim",
                limit=page_size,
                after=after,
                include_vector=True,
                timeout_s=timeout_s,
            )
            if not items:
                break
            vector_rows: list[tuple[str, list]] = []
            claim_payload_rows: list[tuple[str, dict]] = []
            for obj in items:
                oid = str(obj.get("id") or "").strip()
                props = obj.get("properties") or {}
                claim_id = str(props.get("claim_id") or "").strip()
                if not claim_id:
                    raise ValueError(f"Claim object {oid or '<unknown>'} is missing claim_id.")
                doc_id = str(props.get("doc_id") or "").strip()
                if doc_id:
                    doc_ids.add(doc_id)
                token_matrix = _extract_vector_from_object(obj)
                if token_matrix is None:
                    token_matrix = _fetch_vector_detail(sess, oid, timeout_s)
                    fallback_vector_fetches += 1
                vector_rows.append((claim_id, token_matrix))
                claim_payload_rows.append(
                    (
                        claim_id,
                        {
                            "text": str(props.get("text") or ""),
                            "doc_id": doc_id,
                            "claim_type": str(props.get("claim_type") or ""),
                            "claim_number": props.get("claim_number"),
                            "colbert": token_matrix,
                        },
                    )
                )
                claim_count += 1
                total_token_rows += int(token_matrix.shape[0])
            _write_lmdb_vectors(vector_env, vector_rows)
            _write_lmdb_claim_payloads(payload_env, claim_payload_rows)
            after = str(items[-1].get("id") or "").strip() or None
            print(
                f"[export] claims={claim_count} docs={len(doc_ids)} "
                f"token_rows={total_token_rows} after={after or '<done>'}"
            )

        patent_count = 0
        if patent_env is not None:
            after = None
            while True:
                items = _fetch_objects_page(
                    sess,
                    class_name="Patent",
                    limit=page_size,
                    after=after,
                    include_vector=False,
                    timeout_s=timeout_s,
                )
                if not items:
                    break
                patent_rows: list[tuple[str, dict]] = []
                for obj in items:
                    props = obj.get("properties") or {}
                    doc_id = str(props.get("doc_id") or "").strip()
                    if not doc_id:
                        continue
                    patent_rows.append((doc_id, props))
                    patent_count += 1
                if patent_rows:
                    _write_lmdb_json_records(patent_env, patent_rows)
                after = str(items[-1].get("id") or "").strip() or None
    finally:
        vector_env.close()
        payload_env.close()
        if patent_env is not None:
            patent_env.close()
        sess.close()

    manifest = {
        "schema_version": 1,
        "created_at": datetime.now().astimezone().isoformat(),
        "phase": "export_weaviate_colbert_to_lmdb",
        "scratch_only": True,
        "source": {
            "weaviate_objects": WEAVIATE_OBJECTS,
            "named_vector": WEAVIATE_NAMED_VECTOR,
        },
        "output_root": str(output_root.resolve()),
        "shard": shard,
        "claim_count": claim_count,
        "doc_count": len(doc_ids),
        "patent_count": patent_count if export_patent_metadata else 0,
        "total_token_rows": total_token_rows,
        "fallback_vector_fetches": fallback_vector_fetches,
        "lmdb_paths": {
            "vector_lmdb": str(vector_lmdb_path.resolve()),
            "claim_payload_lmdb": str(claim_payload_lmdb_path.resolve()),
            "patent_metadata_lmdb": str(patent_metadata_lmdb_path.resolve()) if export_patent_metadata else "",
        },
        "timing": {
            "elapsed_seconds": time.perf_counter() - started,
        },
        "note": (
            "This export is intended as a temporary home-PC rerank bundle. "
            "Delete it after reranking if you do not need to keep the scratch copy."
        ),
    }
    _json_dump(manifest_path, manifest)
    print(f"[export] Wrote manifest: {manifest_path}")
    print(f"[export] Wrote vector LMDB: {vector_lmdb_path}")
    print(f"[export] Wrote claim payload LMDB: {claim_payload_lmdb_path}")
    if export_patent_metadata:
        print(f"[export] Wrote patent metadata LMDB: {patent_metadata_lmdb_path}")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export Claim ColBERT vectors from Weaviate into a temporary LMDB bundle for home-PC reranking."
    )
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--shard", type=str, default="128_f16", choices=["128_f16", "128_f32"])
    parser.add_argument("--page-size", type=int, default=200)
    parser.add_argument("--timeout-s", type=int, default=60)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument(
        "--skip-patent-metadata",
        action="store_true",
        help="Skip exporting Patent collection metadata LMDB.",
    )
    args = parser.parse_args()

    shard = assert_128_variant(args.shard, context="export_weaviate_colbert_to_lmdb --shard")
    export_claim_vectors(
        output_root=Path(args.output_root).resolve(),
        shard=shard,
        page_size=int(args.page_size),
        timeout_s=int(args.timeout_s),
        overwrite=bool(args.overwrite),
        export_patent_metadata=not bool(args.skip_patent_metadata),
    )


if __name__ == "__main__":
    main()
