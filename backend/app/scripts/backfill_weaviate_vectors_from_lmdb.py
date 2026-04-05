"""
Backfill Weaviate Claim vectors from existing LMDB ColBERT token vectors.

This avoids full re-ingest when Claim objects already exist but were indexed with
mean-pooled vectors instead of token-level multi-vectors.
"""
from __future__ import annotations

import argparse
import csv
import io
import os
from pathlib import Path
import threading
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait

import lmdb
import numpy as np
import requests
from requests.adapters import HTTPAdapter

from backend.app.store import LMDB_VARIANT_PATHS, resolve_lmdb_path
from backend.app.vector_config import assert_128_variant


WEAVIATE_OBJECTS = os.environ.get("WEAVIATE_OBJECTS", "http://localhost:8080/v1/objects")
WEAVIATE_GRAPHQL = os.environ.get("WEAVIATE_GRAPHQL", "http://localhost:8080/v1/graphql")
_TLS = threading.local()


def _build_session(pool_maxsize: int = 64) -> requests.Session:
    s = requests.Session()
    adapter = HTTPAdapter(pool_connections=pool_maxsize, pool_maxsize=pool_maxsize)
    s.mount("http://", adapter)
    s.mount("https://", adapter)
    return s


def _get_worker_session() -> requests.Session:
    sess = getattr(_TLS, "session", None)
    if sess is None:
        sess = _build_session()
        _TLS.session = sess
    return sess


def _deserialize_colbert(payload: bytes) -> np.ndarray:
    buffer = io.BytesIO(payload)
    obj = np.load(buffer, allow_pickle=False)
    if isinstance(obj, np.lib.npyio.NpzFile):
        data = obj["data"]
        scale = obj["scale"]
        obj.close()
        return data.astype(np.float32) * scale
    return obj


class LmdbReader:
    def __init__(self):
        self._env_by_path: dict[Path, lmdb.Environment] = {}

    def close(self):
        for env in self._env_by_path.values():
            env.close()
        self._env_by_path.clear()

    def _get_env(self, path: Path) -> lmdb.Environment:
        env = self._env_by_path.get(path)
        if env is None:
            env = lmdb.open(
                str(path),
                readonly=True,
                lock=False,
                readahead=False,
                create=False,
                subdir=True,
                max_dbs=1,
            )
            self._env_by_path[path] = env
        return env

    def get_vectors(self, path: Path, claim_id: str) -> np.ndarray | None:
        if not path.exists():
            return None
        env = self._get_env(path)
        with env.begin(write=False) as txn:
            payload = txn.get(claim_id.encode("utf-8"))
        if payload is None:
            return None
        return _deserialize_colbert(payload)


def _iter_claim_rows(page_size: int, timeout_s: int, start_after: str = ""):
    """
    Iterate Claim rows using GraphQL cursor pagination and only fetch needed fields.
    This is much lighter than /v1/objects, which returns full properties (including text).
    """
    after = start_after or None
    sess = _build_session()
    while True:
        after_clause = f', after:"{after}"' if after else ""
        query = (
            "{ Get { Claim("
            f"limit:{int(page_size)}{after_clause}"
            ') { claim_id doc_id _additional { id } } } }'
        )
        resp = sess.post(WEAVIATE_GRAPHQL, json={"query": query}, timeout=timeout_s)
        resp.raise_for_status()
        payload = resp.json()
        if payload.get("errors"):
            raise RuntimeError(payload["errors"])
        rows = payload.get("data", {}).get("Get", {}).get("Claim", []) or []
        if not rows:
            return
        for row in rows:
            yield row
        after = (rows[-1].get("_additional") or {}).get("id")


def _to_weaviate_multivector(vectors: np.ndarray | list) -> list[list[float]]:
    arr = np.asarray(vectors)
    if arr.ndim == 1:
        arr = arr.reshape(1, -1)
    if arr.ndim != 2 or arr.shape[0] <= 0 or arr.shape[1] != 128:
        raise ValueError(f"Expected [T,128] vectors for backfill, got shape={arr.shape}")
    return arr.astype(np.float32, copy=False).tolist()


def _patch_claim_vector(uuid: str, vectors: list[list[float]], timeout_s: int):
    sess = _get_worker_session()
    payload = {
        "class": "Claim",
        "vectors": {
            "colbert": vectors,
        },
    }
    resp = sess.patch(f"{WEAVIATE_OBJECTS}/Claim/{uuid}", json=payload, timeout=timeout_s)
    if resp.status_code != 204:
        raise RuntimeError(f"PATCH failed ({resp.status_code}): {resp.text[:400]}")


def main():
    parser = argparse.ArgumentParser(description="Backfill Weaviate Claim vectors from LMDB ColBERT vectors.")
    parser.add_argument(
        "--shard",
        type=str,
        default=os.environ.get("WEAVIATE_SHARD", "128_f16"),
        choices=sorted(LMDB_VARIANT_PATHS.keys()),
        help="LMDB shard variant to read from.",
    )
    parser.add_argument("--batch-size", type=int, default=128, help="Weaviate object page size.")
    parser.add_argument("--max-claims", type=int, default=0, help="Optional cap for testing; 0 means all.")
    parser.add_argument("--timeout-s", type=int, default=60, help="HTTP timeout seconds.")
    parser.add_argument("--progress-every", type=int, default=100, help="Print progress every N claims.")
    parser.add_argument("--start-after", type=str, default="", help="Resume after this UUID cursor.")
    parser.add_argument("--patch-workers", type=int, default=16, help="Concurrent PATCH workers (apply mode).")
    parser.add_argument("--dry-run", action="store_true", help="Do not patch Weaviate; only report.")
    parser.add_argument("--strict", action="store_true", help="Stop on first patch/load error.")
    parser.add_argument("--report-csv", type=Path, default=None, help="Optional per-claim status CSV.")
    args = parser.parse_args()
    args.shard = assert_128_variant(args.shard, context="backfill_weaviate_vectors_from_lmdb --shard")

    if args.report_csv:
        args.report_csv.parent.mkdir(parents=True, exist_ok=True)
        csv_f = args.report_csv.open("w", encoding="utf-8", newline="")
        writer = csv.DictWriter(
            csv_f,
            fieldnames=[
                "uuid",
                "claim_id",
                "doc_id",
                "lmdb_path",
                "tokens",
                "dim",
                "status",
                "message",
            ],
        )
        writer.writeheader()
    else:
        csv_f = None
        writer = None

    counts = {
        "seen": 0,
        "updated": 0,
        "missing_claim_id": 0,
        "missing_lmdb": 0,
        "invalid_vectors": 0,
        "errors": 0,
    }

    reader = LmdbReader()
    try:
        patch_executor = None
        if not args.dry_run and args.patch_workers > 1:
            patch_executor = ThreadPoolExecutor(max_workers=int(args.patch_workers))
        pending: list[tuple[object, dict]] = []
        max_pending = max(1, int(args.patch_workers) * 4)

        def _write_row(row: dict):
            if writer is not None:
                writer.writerow(row)

        def _flush_pending(force: bool = False):
            nonlocal pending
            if not pending:
                return
            if force:
                done = pending
                pending = []
            else:
                done_set, _ = wait(
                    [fut for fut, _ in pending],
                    return_when=FIRST_COMPLETED,
                )
                keep: list[tuple[object, dict]] = []
                done: list[tuple[object, dict]] = []
                for fut, row in pending:
                    if fut in done_set:
                        done.append((fut, row))
                    else:
                        keep.append((fut, row))
                pending = keep

            for fut, row in done:
                try:
                    fut.result()
                    counts["updated"] += 1
                    row["status"] = "updated"
                except Exception as e:
                    counts["errors"] += 1
                    row["status"] = "error"
                    row["message"] = str(e)
                    if args.strict:
                        _write_row(row)
                        raise
                _write_row(row)

        for obj in _iter_claim_rows(args.batch_size, args.timeout_s, start_after=args.start_after):
            if args.max_claims and counts["seen"] >= args.max_claims:
                break
            counts["seen"] += 1

            addl = obj.get("_additional") or {}
            uuid = str(addl.get("id") or "")
            claim_id = str(obj.get("claim_id") or "").strip()
            doc_id = str(obj.get("doc_id") or "").strip()
            lmdb_path = ""
            status = "updated"
            message = ""
            token_count = 0
            dim = 0

            try:
                if not claim_id:
                    counts["missing_claim_id"] += 1
                    status = "skip_missing_claim_id"
                    message = "claim_id missing on object"
                else:
                    preferred_path = resolve_lmdb_path(args.shard, doc_id=doc_id or None, dataset_shard=None)
                    lmdb_path = str(preferred_path)
                    vecs = reader.get_vectors(preferred_path, claim_id)
                    if vecs is None:
                        counts["missing_lmdb"] += 1
                        status = "skip_missing_lmdb"
                        message = "claim_id not found in LMDB"
                    else:
                        matrix = _to_weaviate_multivector(vecs)
                        if not matrix:
                            counts["invalid_vectors"] += 1
                            status = "skip_invalid_vectors"
                            message = "vector matrix is empty or malformed"
                        else:
                            token_count = len(matrix)
                            dim = len(matrix[0]) if matrix else 0
                            if not args.dry_run:
                                if patch_executor is not None:
                                    fut = patch_executor.submit(
                                        _patch_claim_vector,
                                        uuid,
                                        matrix,
                                        args.timeout_s,
                                    )
                                    pending.append(
                                        (
                                            fut,
                                            {
                                                "uuid": uuid,
                                                "claim_id": claim_id,
                                                "doc_id": doc_id,
                                                "lmdb_path": lmdb_path,
                                                "tokens": token_count,
                                                "dim": dim,
                                                "status": "pending_patch",
                                                "message": "",
                                            },
                                        )
                                    )
                                    if len(pending) >= max_pending:
                                        _flush_pending(force=False)
                                else:
                                    _patch_claim_vector(uuid, matrix, timeout_s=args.timeout_s)
                                    counts["updated"] += 1
                            else:
                                counts["updated"] += 1
            except Exception as e:
                counts["errors"] += 1
                status = "error"
                message = str(e)
                if args.strict:
                    raise

            if args.dry_run or patch_executor is None or status != "updated":
                _write_row(
                    {
                        "uuid": uuid,
                        "claim_id": claim_id,
                        "doc_id": doc_id,
                        "lmdb_path": lmdb_path,
                        "tokens": token_count,
                        "dim": dim,
                        "status": status,
                        "message": message,
                    }
                )

            if args.progress_every > 0 and (
                counts["seen"] == 1 or counts["seen"] % args.progress_every == 0
            ):
                in_flight = len(pending) if patch_executor is not None else 0
                print(
                    f"[backfill] seen={counts['seen']} updated={counts['updated']} "
                    f"in_flight={in_flight} missing_lmdb={counts['missing_lmdb']} "
                    f"errors={counts['errors']}"
                )
        _flush_pending(force=True)
    finally:
        try:
            if "patch_executor" in locals() and patch_executor is not None:
                patch_executor.shutdown(wait=True)
        except Exception:
            pass
        reader.close()
        if csv_f is not None:
            csv_f.close()

    mode = "dry-run" if args.dry_run else "apply"
    print(
        f"[backfill] done mode={mode} seen={counts['seen']} updated={counts['updated']} "
        f"missing_claim_id={counts['missing_claim_id']} missing_lmdb={counts['missing_lmdb']} "
        f"invalid_vectors={counts['invalid_vectors']} errors={counts['errors']}"
    )
    if args.report_csv:
        print(f"[backfill] wrote report: {args.report_csv}")


if __name__ == "__main__":
    main()
