from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


# Allow direct script execution from repo root without installing as a package.
_ROOT = Path(__file__).resolve().parents[3]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from backend.app.services.cpc_scheme import describe_cpc_codes


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Describe CPC symbols from the CPC scheme ZIP.")
    parser.add_argument(
        "codes",
        nargs="+",
        help='One or more CPC symbols (example: "A61K 31/00" "G06F17/30").',
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    descriptions = describe_cpc_codes(args.codes)
    print(json.dumps(descriptions, indent=2))


if __name__ == "__main__":
    main()
