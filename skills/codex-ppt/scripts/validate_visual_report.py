#!/usr/bin/env python3
"""Validate final Codex-PPT visual QA evidence and rendered-slide coverage."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("--rendered-dir", type=Path, required=True)
    args = parser.parse_args()

    try:
        report = json.loads(args.report.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"FAIL: unreadable visual report: {exc}")
        return 1

    failures: list[str] = []
    if report.get("schema_version") != "codex_ppt_visual_qa_v1":
        failures.append("schema_version must be codex_ppt_visual_qa_v1")
    sample_status = report.get("sample_status")
    if sample_status not in {"pass", "skipped"}:
        failures.append("sample_status must be pass or skipped")
    if sample_status == "skipped" and not report.get("sample_skip_reason"):
        failures.append("skipped sample requires sample_skip_reason")

    slides = report.get("slides")
    if not isinstance(slides, list) or not slides:
        failures.append("slides must be a nonempty list")
        slides = []
    numbers = [row.get("slide") for row in slides if isinstance(row, dict)]
    if numbers != list(range(1, len(slides) + 1)):
        failures.append("slide numbers must be contiguous from 1")

    for row in slides:
        if not isinstance(row, dict):
            failures.append("every slide entry must be an object")
            continue
        number = row.get("slide")
        if row.get("verdict") != "PASS":
            failures.append(f"slide {number} is not PASS")
        render_name = row.get("render")
        if not isinstance(render_name, str) or not render_name:
            failures.append(f"slide {number} has no render path")
            continue
        render_path = args.report.parent / render_name
        try:
            render_path.resolve().relative_to(args.rendered_dir.resolve())
        except ValueError:
            failures.append(f"slide {number} render is outside rendered-dir")
            continue
        if not render_path.is_file() or render_path.stat().st_size == 0:
            failures.append(f"slide {number} render is missing or empty")

    if report.get("deck_verdict") != "PASS":
        failures.append("deck_verdict must be PASS")
    if failures:
        print("FAIL: " + "; ".join(failures))
        return 1
    print(f"PASS: {len(slides)} rendered slides have final visual approval")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
