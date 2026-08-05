#!/usr/bin/env python3
"""Render PPTX slides to PNG through PowerPoint COM or LibreOffice."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def export_pdf(pptx: Path, output: Path, engine: str) -> Path:
    output.mkdir(parents=True, exist_ok=True)
    if engine in {"auto", "powerpoint"} and sys.platform == "win32":
        try:
            import win32com.client  # type: ignore
            app = win32com.client.DispatchEx("PowerPoint.Application")
            deck = app.Presentations.Open(str(pptx.resolve()), WithWindow=False)
            pdf = output / f"{pptx.stem}.pdf"
            deck.SaveAs(str(pdf.resolve()), 32)
            deck.Close(); app.Quit()
            return pdf
        except Exception:
            if engine == "powerpoint":
                raise
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        raise RuntimeError("no renderer available; install LibreOffice or PowerPoint with pywin32")
    res = subprocess.run([soffice, "--headless", "--convert-to", "pdf", "--outdir", str(output), str(pptx)], capture_output=True, text=True)
    if res.returncode:
        raise RuntimeError(res.stderr or res.stdout or "LibreOffice export failed")
    return output / f"{pptx.stem}.pdf"


def rasterize(pdf: Path, output: Path, dpi: int) -> None:
    pdftoppm = shutil.which("pdftoppm")
    if pdftoppm:
        subprocess.run([pdftoppm, "-png", "-r", str(dpi), str(pdf), str(output / "slide")], check=True)
        return
    try:
        import fitz  # type: ignore
    except ImportError as exc:
        raise RuntimeError("install Poppler pdftoppm or PyMuPDF to rasterize PDF pages") from exc
    scale = dpi / 72
    with fitz.open(pdf) as doc:
        for index, page in enumerate(doc):
            page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False).save(output / f"slide-{index + 1:02d}.png")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pptx", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--engine", choices=("auto", "powerpoint", "libreoffice"), default="auto")
    parser.add_argument("--dpi", type=int, default=160)
    args = parser.parse_args()
    try:
        pdf = export_pdf(args.pptx, args.output, args.engine)
        rasterize(pdf, args.output, args.dpi)
        print(f"PASS: rendered slides to {args.output}")
        return 0
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
