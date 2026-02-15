"""
Compact-copy LMDB shards to their approximate true size, then swap in place.

This keeps existing paths the same so the rest of the code does not change.
"""
from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path

import lmdb

from backend.app.store import (
    LMDB_SHARD_ROOT_768_F16,
    LMDB_PATH_128_F16,
    LMDB_PATH_128_F32,
    LMDB_PATH_768_F16,
    LMDB_PATH_768_F32,
    LMDB_PATH_768_I8,
)


SHARDS = {
    "768_f32": LMDB_PATH_768_F32,
    "768_f16": LMDB_PATH_768_F16,
    "768_i8": LMDB_PATH_768_I8,
    "128_f32": LMDB_PATH_128_F32,
    "128_f16": LMDB_PATH_128_F16,
}
UTIL_LMDB_FILENAME = "colbert_768_f16.lmdb"


def _util_shard_path(util_name: str) -> Path:
    return Path(LMDB_SHARD_ROOT_768_F16) / util_name.upper() / UTIL_LMDB_FILENAME


def _iter_util_shards() -> list[tuple[str, Path]]:
    root = Path(LMDB_SHARD_ROOT_768_F16)
    if not root.exists():
        return []
    out: list[tuple[str, Path]] = []
    for child in sorted(root.iterdir()):
        if not child.is_dir():
            continue
        if not child.name.upper().startswith("UTIL"):
            continue
        lmdb_path = child / UTIL_LMDB_FILENAME
        out.append((child.name.upper(), lmdb_path))
    return out


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
    parser = argparse.ArgumentParser(description="Compact LMDB shards in place.")
    parser.add_argument("--shard", type=str, default=None, choices=sorted(SHARDS.keys()))
    parser.add_argument("--all", action="store_true", help="Compact all shards.")
    parser.add_argument(
        "--util-shard",
        type=str,
        default=None,
        help="Compact one util shard (e.g., UTIL12401).",
    )
    parser.add_argument(
        "--util-all",
        action="store_true",
        help="Compact all util LMDB shards under LMDB_SHARD_ROOT_768_F16.",
    )
    args = parser.parse_args()

    if args.util_shard:
        util_name = str(args.util_shard).upper()
        print(f"\n== {util_name} ==")
        compact_in_place(_util_shard_path(util_name))
        return

    if args.util_all:
        util_shards = _iter_util_shards()
        if not util_shards:
            print(f"[skip] no util shards found under {Path(LMDB_SHARD_ROOT_768_F16)}")
            return
        for util_name, path in util_shards:
            print(f"\n== {util_name} ==")
            compact_in_place(path)
        return

    if args.shard:
        print(f"\n== {args.shard} ==")
        compact_in_place(SHARDS[args.shard])
        return

    if args.all or args.shard is None:
        for name, path in SHARDS.items():
            print(f"\n== {name} ==")
            compact_in_place(path)


if __name__ == "__main__":
    main()
