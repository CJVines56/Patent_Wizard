#!/usr/bin/env python3
"""
Utility to convert any TIFF figure payloads in sample_chunks.jsonl to PNG.
Run this if you already generated sample chunks but need browser-friendly
base64 images without re-running the entire download pipeline.
"""

from __future__ import annotations

import argparse
import base64
import io
import json
import sys
from pathlib import Path

from PIL import Image

TIFF_MEDIA_TYPES = {"image/tiff", "image/x-tiff"}
TIFF_EXTS = (".tif", ".tiff")


def _needs_conversion(img: dict) -> bool:
    media_type = (img.get("media_type") or "").lower()
    filename = (img.get("file") or "").lower()
    return media_type in TIFF_MEDIA_TYPES or filename.endswith(TIFF_EXTS)


def _convert_payload(img: dict) -> bool:
    if not _needs_conversion(img):
        return False
    b64 = img.get("data_b64")
    if not b64:
        return False
    try:
        raw = base64.b64decode(b64)
    except Exception:
        return False
    try:
        with Image.open(io.BytesIO(raw)) as pil_img:
            if pil_img.mode not in ("RGB", "RGBA"):
                pil_img = pil_img.convert("RGBA")
            buf = io.BytesIO()
            pil_img.save(buf, format="PNG")
            png_bytes = buf.getvalue()
    except Exception:
        return False
    img["data_b64"] = base64.b64encode(png_bytes).decode("ascii")
    img["media_type"] = "image/png"
    fname = img.get("file")
    if fname:
        img["file"] = f"{Path(fname).stem}.png"
    return True


def convert_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(path)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    print('[convert_fig_images] Converting file:', path)
    total_chunks = 0
    total_figs = 0
    converted = 0
    with path.open("r", encoding="utf-8") as src, tmp_path.open("w", encoding="utf-8") as dst:
        for line in src:
            line = line.rstrip("\n")
            if not line:
                dst.write("\n")
                continue
            total_chunks += 1
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                dst.write(line + "\n")
                continue
            imgs = obj.get("fig_images") or []
            for img in imgs:
                total_figs += 1
                if _convert_payload(img):
                    converted += 1
                    print(f'[convert_fig_images] Converted figure {total_figs}')
            dst.write(json.dumps(obj, ensure_ascii=False) + "\n")
    tmp_path.replace(path)
    print(
        f"[convert_fig_images] chunks={total_chunks} figures={total_figs} converted={converted} "
        f"({path})"
    )


def main(argv: list[str] | None = None) -> int:
    print("[convert_fig_images] Starting conversion...")
    parser = argparse.ArgumentParser(description="Convert TIFF figure payloads in sample_chunks.jsonl to PNG")
    default_path = Path(__file__).resolve().parents[1] / "db" / "sample_chunks.jsonl"
    print(f"[convert_fig_images] Default path: {default_path}")
    parser.add_argument(
        "path",
        nargs="?",
        default=str(default_path),
        help=f"Path to sample_chunks.jsonl (default: {default_path})",
    )
    args = parser.parse_args(argv)
    print(f"[convert_fig_images] Converting file: {args.path}")
    convert_file(Path(args.path))
    print("[convert_fig_images] Conversion complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
