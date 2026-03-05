"""
Deprecated script kept as a hard-stop guard.

The pipeline is now strict 128-d trained projection only.
All 768-d variants are forbidden.
"""

from __future__ import annotations


def main() -> None:
    raise SystemExit(
        "convert_lmdb_i8.py is disabled: 768-d variants are forbidden in this pipeline. "
        "Use 128_f16/128_f32 shards only."
    )


if __name__ == "__main__":
    main()
