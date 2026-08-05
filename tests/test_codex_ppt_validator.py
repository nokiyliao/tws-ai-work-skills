#!/usr/bin/env python3

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "skills/codex-ppt/scripts/validate_visual_report.py"


class VisualReportValidatorTest(unittest.TestCase):
    def test_passes_complete_rendered_set(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            rendered = root / "rendered"
            rendered.mkdir()
            (rendered / "slide-01.png").write_bytes(b"png-fixture")
            report = root / "visual_qa.json"
            report.write_text(json.dumps({
                "schema_version": "codex_ppt_visual_qa_v1",
                "deck": "final.pptx",
                "sample_status": "pass",
                "slides": [{"slide": 1, "verdict": "PASS", "findings": [], "render": "rendered/slide-01.png"}],
                "repaired_slides": [],
                "deck_verdict": "PASS",
            }), encoding="utf-8")
            result = subprocess.run([sys.executable, str(VALIDATOR), str(report), "--rendered-dir", str(rendered)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_fails_missing_render_and_failed_slide(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            rendered = root / "rendered"
            rendered.mkdir()
            report = root / "visual_qa.json"
            report.write_text(json.dumps({
                "schema_version": "codex_ppt_visual_qa_v1",
                "deck": "final.pptx",
                "sample_status": "skipped",
                "sample_skip_reason": "approved revision reference",
                "slides": [{"slide": 1, "verdict": "FAIL", "findings": ["overlap"], "render": "rendered/slide-01.png"}],
                "repaired_slides": [],
                "deck_verdict": "FAIL",
            }), encoding="utf-8")
            result = subprocess.run([sys.executable, str(VALIDATOR), str(report), "--rendered-dir", str(rendered)], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("slide 1 is not PASS", result.stdout)


if __name__ == "__main__":
    unittest.main()
