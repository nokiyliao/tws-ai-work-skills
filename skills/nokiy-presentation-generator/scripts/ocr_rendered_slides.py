#!/usr/bin/env python3
"""OCR rendered slide images using macOS Vision via Swift.

The script is intentionally optional: `qa_check.py --ocr-rendered` calls it
only after slides have been rendered to PNG/JPG. It avoids third-party OCR
dependencies and returns machine-readable OCR text for prompt/watermark scans.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}
SCRIPT_DIR = Path(__file__).resolve().parent
SWIFT_SOURCE = SCRIPT_DIR / "vision_ocr.swift"
CACHE_DIR = Path.home() / ".cache" / "tws-presentation-generator"
CACHE_BIN = CACHE_DIR / "vision_ocr"


def collect_images(target: Path) -> list[Path]:
    if target.is_dir():
        return sorted(p for p in target.iterdir() if p.suffix.lower() in IMAGE_EXTS)
    return [target] if target.suffix.lower() in IMAGE_EXTS else []


def compiled_ocr_binary() -> Path:
    swiftc = shutil.which("swiftc")
    if not swiftc:
        raise SystemExit("swiftc is not available; cannot compile macOS Vision OCR helper")
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    needs_build = (
        not CACHE_BIN.exists()
        or CACHE_BIN.stat().st_mtime < SWIFT_SOURCE.stat().st_mtime
    )
    if needs_build:
        res = subprocess.run([swiftc, str(SWIFT_SOURCE), "-o", str(CACHE_BIN)], text=True, capture_output=True)
        if res.returncode != 0:
            raise SystemExit((res.stderr or res.stdout or "swiftc failed").strip())
    return CACHE_BIN


def run_swift_ocr(images: list[Path]) -> list[dict]:
    binary = compiled_ocr_binary()
    res = subprocess.run([str(binary), *map(str, images)], text=True, capture_output=True)
    if res.returncode != 0:
        raise SystemExit((res.stderr or res.stdout or "Swift Vision OCR failed").strip())
    return json.loads(res.stdout or "[]")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("target", type=Path, help="Rendered slide image or directory")
    parser.add_argument("--json", action="store_true", help="Emit JSON array")
    args = parser.parse_args()

    images = collect_images(args.target)
    rows = run_swift_ocr(images) if images else []
    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    else:
        for row in rows:
            print(f"## {row.get('path')}")
            if row.get("error"):
                print(f"ERROR: {row['error']}")
            else:
                print(row.get("text", ""))


if __name__ == "__main__":
    main()
