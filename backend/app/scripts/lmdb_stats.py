"""
Print LMDB file size and basic stats for ColBERT shards.
"""
import os
from pathlib import Path

import lmdb

BASE_DIR = Path(__file__).resolve().parents[2]
DEFAULT_DIR = BASE_DIR / "lmdb"

DEFAULT_PATHS = {
    "128_f32": Path(os.environ.get("LMDB_PATH_128_F32", DEFAULT_DIR / "colbert_128_f32.lmdb")),
    "128_f16": Path(os.environ.get("LMDB_PATH_128_F16", DEFAULT_DIR / "colbert_128_f16.lmdb")),
    "claim_payloads": Path(os.environ.get("LMDB_PATH_CLAIM_PAYLOAD", DEFAULT_DIR / "claim_payloads.lmdb")),
    "patent_metadata": Path(
        os.environ.get("LMDB_PATH_PATENT_METADATA", DEFAULT_DIR / "patent_metadata.lmdb")
    ),
}


def _open_env(path: Path) -> lmdb.Environment:
    return lmdb.open(
        str(path),
        readonly=True,
        lock=False,
        readahead=False,
        max_dbs=1,
    )


def _fmt_bytes(n: int) -> str:
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if n < 1024:
            return f"{n:.1f}{unit}"
        n /= 1024.0
    return f"{n:.1f}PB"


def main():
    for name, path in DEFAULT_PATHS.items():
        if not path.exists():
            print(f"[skip] {name}: missing {path}")
            continue
        size = path.stat().st_size
        env = _open_env(path)
        try:
            with env.begin(write=False) as txn:
                stat = txn.stat()
            info = env.info()
            stat = stat or {}
        finally:
            env.close()
        page_size = stat.get("psize") if isinstance(stat, dict) else None
        entries = stat.get("entries") if isinstance(stat, dict) else None
        print(
            f"{name}: file={_fmt_bytes(size)} entries={entries} "
            f"map_size={_fmt_bytes(info['map_size'])} page_size={page_size} last_pgno={info['last_pgno']}"
        )


if __name__ == "__main__":
    main()
