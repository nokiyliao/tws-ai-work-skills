#!/usr/bin/env python3
"""OCR rendered slide images using macOS Vision or Tesseract.

The script is intentionally optional: `qa_check.py --ocr-rendered` calls it
only after slides have been rendered to PNG/JPG. It avoids third-party OCR
dependencies and returns machine-readable OCR text for prompt/watermark scans.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
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


def run_tesseract_ocr(images: list[Path], languages: str) -> list[dict]:
    binary = shutil.which("tesseract")
    if not binary:
        raise SystemExit("no OCR engine available; install Tesseract or use macOS with swiftc")
    rows = []
    for image in images:
        res = subprocess.run([binary, str(image), "stdout", "-l", languages], text=True, capture_output=True)
        rows.append({"path": str(image), "text": res.stdout, "error": "" if res.returncode == 0 else (res.stderr or "Tesseract failed").strip()})
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("target", type=Path, help="Rendered slide image or directory")
    parser.add_argument("--json", action="store_true", help="Emit JSON array")
    parser.add_argument("--engine", choices=("auto", "vision", "tesseract"), default="auto")
    parser.add_argument("--languages", default="eng+chi_tra", help="Tesseract language set")
    args = parser.parse_args()

    images = collect_images(args.target)
    if not images:
        rows = []
    elif args.engine == "vision" or (args.engine == "auto" and sys.platform == "darwin" and shutil.which("swiftc")):
        rows = run_swift_ocr(images)
    else:
        rows = run_tesseract_ocr(images, args.languages)
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
