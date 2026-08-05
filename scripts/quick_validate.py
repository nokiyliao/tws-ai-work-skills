#!/usr/bin/env python3
"""Quick repository validation for TWS AI work skills.

Runs structure checks, py_compile on skill scripts, and the unit test suite.
Does not install system apps or touch files outside the repo.
"""

from __future__ import annotations

import compileall
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_SCRIPTS = [
    ROOT / "skills/nokiy-deck-orchestrator/scripts",
    ROOT / "skills/nokiy-presentation-generator/scripts",
    ROOT / "skills/codex-ppt/scripts",
]
REQUIRED = [
    ROOT / "skills/nokiy-deck-orchestrator/scripts/runtime_bootstrap.py",
    ROOT / "skills/nokiy-deck-orchestrator/scripts/preflight.py",
    ROOT / "skills/nokiy-deck-orchestrator/scripts/bootstrap_learner.py",
    ROOT / "skills/nokiy-deck-orchestrator/scripts/deck_pipeline_state.py",
    ROOT / "skills/nokiy-deck-orchestrator/scripts/validate_visual_plan.py",
    ROOT / "skills/nokiy-deck-orchestrator/runtime/requirements.lock",
    ROOT / "skills/nokiy-deck-orchestrator/runtime/requirements.txt",
    ROOT / "skills/nokiy-deck-orchestrator/runtime/pyproject.toml",
    ROOT / "tests/test_runtime_bootstrap.py",
    ROOT / "tests/test_learner_bootstrap.py",
    ROOT / "tests/test_skill_routing.py",
    ROOT / "tests/test_visual_plan.py",
    ROOT / "README.md",
    ROOT / "manifest.json",
]


def main() -> int:
    errors: list[str] = []
    for path in REQUIRED:
        if not path.is_file():
            errors.append(f"missing required file: {path.relative_to(ROOT)}")

    for directory in SKILL_SCRIPTS:
        if not directory.is_dir():
            continue
        ok = compileall.compile_dir(str(directory), quiet=1, force=True)
        if not ok:
            errors.append(f"py_compile failed under {directory.relative_to(ROOT)}")

    for path in (ROOT / "tests").glob("test_*.py"):
        if not compileall.compile_file(str(path), quiet=1, force=True):
            errors.append(f"py_compile failed: {path.relative_to(ROOT)}")

    loader = unittest.TestLoader()
    suite = loader.discover(str(ROOT / "tests"), pattern="test_*.py")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        errors.append(
            f"unittest failures={len(result.failures)} errors={len(result.errors)}"
        )

    with tempfile.TemporaryDirectory(prefix="tws-quick-rt-") as temp:
        rb = ROOT / "skills/nokiy-deck-orchestrator/scripts/runtime_bootstrap.py"
        proc = subprocess.run(
            [
                sys.executable,
                str(rb),
                "check",
                "--skip-remote",
                "--runtime-home",
                temp,
            ],
            capture_output=True,
            text=True,
            check=False,
        )
    try:
        payload = json.loads(proc.stdout)
        for key in ("status", "checks", "blockers", "mode", "runtime_home"):
            if key not in payload:
                errors.append(f"runtime_bootstrap JSON missing key: {key}")
    except json.JSONDecodeError:
        errors.append(
            f"runtime_bootstrap did not emit JSON: {proc.stdout[:200]!r} {proc.stderr[:200]!r}"
        )

    pf = ROOT / "skills/nokiy-deck-orchestrator/scripts/preflight.py"
    proc_pf = subprocess.run(
        [sys.executable, str(pf), "--workflow", "general", "--skip-runtime"],
        capture_output=True,
        text=True,
        check=False,
    )
    try:
        pf_payload = json.loads(proc_pf.stdout)
        for key in ("status", "checks", "failed", "blockers"):
            if key not in pf_payload:
                errors.append(f"preflight JSON missing key: {key}")
    except json.JSONDecodeError:
        errors.append(
            f"preflight did not emit JSON: {proc_pf.stdout[:200]!r} {proc_pf.stderr[:200]!r}"
        )

    report = {
        "status": "FAIL" if errors else "PASS",
        "errors": errors,
        "unittest": {
            "tests": result.testsRun,
            "failures": len(result.failures),
            "errors": len(result.errors),
            "skipped": len(result.skipped),
        },
    }
    print(json.dumps(report, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
