#!/usr/bin/env python3
"""Platform-neutral launcher for the installed TWS AI runtime bootstrap.

This file contains no credentials and does not modify Codex configuration. It
only locates the installed authoritative skill under the current user's home
directory, verifies the minimum Python version, and delegates to that skill's
runtime bootstrap.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


MIN_PYTHON = (3, 10)


def codex_home() -> Path:
    configured = os.environ.get("CODEX_HOME", "").strip()
    return Path(configured).expanduser() if configured else Path.home() / ".codex"


def bootstrap_path(home: Path | None = None) -> Path:
    root = home if home is not None else codex_home()
    return root / "skills" / "nokiy-deck-orchestrator" / "scripts" / "runtime_bootstrap.py"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("install", "check"), nargs="?", default="install")
    parser.add_argument("--skip-remote", action="store_true", help="developer test only")
    args = parser.parse_args()

    if sys.version_info[:2] < MIN_PYTHON:
        print(json.dumps({
            "status": "FAIL",
            "blocker": "PYTHON_VERSION",
            "detail": f"Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]} or newer is required",
            "platform": sys.platform,
        }, ensure_ascii=False))
        return 2

    target = bootstrap_path()
    if not target.is_file():
        print(json.dumps({
            "status": "FAIL",
            "blocker": "SKILL_NOT_INSTALLED",
            "detail": str(target),
            "platform": sys.platform,
        }, ensure_ascii=False))
        return 3

    command = [sys.executable, str(target), args.mode]
    if args.skip_remote:
        command.append("--skip-remote")
    completed = subprocess.run(command, check=False)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
