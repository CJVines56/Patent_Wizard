"""
Compact-copy LMDB shards to their approximate true size, then swap in place.

This keeps existing paths the same so the rest of the code does not change.
"""
from __future__ import annotations

import os
import shutil
from pathlib import Path

import lmdb

from backend.app.store import (
    LMDB_PATH_128_F16,
    LMDB_PATH_128_F32,
    LMDB_PATH_768_F16,
    LMDB_PATH_768_F32,
)


SHARDS = {
    "768_f32": LMDB_PATH_768_F32,
    "768_f16": LMDB_PATH_768_F16,
    "128_f32": LMDB_PATH_128_F32,
    "128_f16": LMDB_PATH_128_F16,
}


def _open_env(path: Path) -> lmdb.Environment:
    return lmdb.open(
        str(path),
        readonly=True,
        lock=False,
        readahead=False,
        max_dbs=1,
        subdir=True,
    )


def _used_bytes(path: Path) -> int:
    env = _open_env(path)
    try:
        info = env.info()
        stat = env.stat()
        # last_pgno is the last used page number; add 1 for page count.
        return int(info["last_pgno"] + 1) * int(stat["psize"])
    finally:
        env.close()


def _fmt_bytes(n: int) -> str:
    val = float(n)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if val < 1024.0:
            return f"{val:.1f}{unit}"
        val /= 1024.0
    return f"{val:.1f}PB"


def compact_in_place(path: Path):
    if not path.exists():
        print(f"[skip] missing {path}")
        return

    used = _used_bytes(path)
    print(f"[info] {path} used~{_fmt_bytes(used)}; compacting...")

    tmp_path = Path(str(path) + ".compact")
    bak_path = Path(str(path) + ".bak")

    if tmp_path.exists():
        shutil.rmtree(tmp_path, ignore_errors=True)
    if bak_path.exists():
        shutil.rmtree(bak_path, ignore_errors=True)
    tmp_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path.mkdir(parents=True, exist_ok=True)

    env = _open_env(path)
    try:
        # LMDB compact copy writes a minimized map to the target path.
        env.copy(str(tmp_path), compact=True)
    finally:
        env.close()

    # Swap directories: original -> .bak, compact -> original
    os.replace(str(path), str(bak_path))
    os.replace(str(tmp_path), str(path))

    # Cleanup backup after successful swap
    shutil.rmtree(bak_path, ignore_errors=True)
    print(f"[done] compacted {path}")


def main():
    for name, path in SHARDS.items():
        print(f"\n== {name} ==")
        compact_in_place(path)


if __name__ == "__main__":
    main()
