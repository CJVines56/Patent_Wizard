"""
Convert an existing 768_f16 LMDB shard to 768_i8 without re-ingesting.
Quantizes per-token with a symmetric scale (max abs / 127) and stores int8 + scale.
"""
from __future__ import annotations

import io
import os
from pathlib import Path

import lmdb
import numpy as np

from backend.app.store import (
    LMDB_MAP_GROW_GB,
    LMDB_MAP_SIZE,
    LMDB_PATH_768_F16,
    LMDB_PATH_768_I8,
    _deserialize_colbert,
)


def _open_env(path: Path, *, readonly: bool = False) -> lmdb.Environment:
    path.parent.mkdir(parents=True, exist_ok=True)
    return lmdb.open(
        str(path),
        map_size=LMDB_MAP_SIZE,
        subdir=True,
        create=not readonly,
        lock=not readonly,
        readonly=readonly,
        readahead=False,
        max_dbs=1,
    )


def _serialize_i8(data: np.ndarray, scale: np.ndarray) -> bytes:
    buffer = io.BytesIO()
    np.savez(buffer, data=data, scale=scale)
    return buffer.getvalue()


def _quantize_i8(vectors: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    # vectors: [tokens, dim] float16/float32
    max_abs = np.max(np.abs(vectors), axis=1, keepdims=True)
    scale = max_abs / 127.0
    scale[scale == 0] = 1.0
    q = np.clip(np.round(vectors / scale), -127, 127).astype(np.int8)
    return q, scale.astype(np.float32)


def convert(src_path: Path, dst_path: Path, *, log_every: int = 1000) -> None:
    src_env = _open_env(src_path, readonly=True)
    dst_env = _open_env(dst_path, readonly=False)
    total = 0
    try:
        with src_env.begin(write=False) as src_txn:
            cursor = src_txn.cursor()
            while True:
                batch = []
                for _ in range(1000):
                    if not cursor.next():
                        break
                    key, payload = cursor.item()
                    vectors = _deserialize_colbert(payload)
                    q, scale = _quantize_i8(vectors)
                    batch.append((key, _serialize_i8(q, scale)))
                if not batch:
                    break
                while True:
                    try:
                        with dst_env.begin(write=True) as dst_txn:
                            for key, payload in batch:
                                dst_txn.put(key, payload)
                        break
                    except lmdb.MapFullError:
                        current = dst_env.info()["map_size"]
                        grow = LMDB_MAP_GROW_GB * 1024**3
                        dst_env.set_mapsize(current + grow)
                        print(f"[lmdb] MapFullError: increased map size to {current + grow:,} bytes")
                total += len(batch)
                if total % log_every == 0:
                    print(f"[convert] wrote {total} vectors")
    finally:
        src_env.close()
        dst_env.close()
    print(f"[done] wrote {total} vectors to {dst_path}")


def main():
    src = Path(os.environ.get("LMDB_PATH_768_F16", LMDB_PATH_768_F16))
    dst = Path(os.environ.get("LMDB_PATH_768_I8", LMDB_PATH_768_I8))
    if not src.exists():
        raise SystemExit(f"Source LMDB not found: {src}")
    convert(src, dst)


if __name__ == "__main__":
    main()
