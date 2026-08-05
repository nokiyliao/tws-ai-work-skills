#!/usr/bin/env python3
"""Fail-closed dependency check for the authoritative deck pipeline."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


HOME = Path.home()
SKILLS = HOME / ".codex" / "skills"
DEFAULT_TWS_LIBRARY = os.environ.get("TWS_ASSET_LIBRARY_PATH", "")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workflow", choices=("general", "tws-new-factory"), default="general")
    parser.add_argument("--asset-library", type=Path, help="local asset-library root; overrides TWS_ASSET_LIBRARY_PATH")
    args = parser.parse_args()

    required = ["humanizer-zh-tw", "nokiy-presentation-generator", "codex-ppt"]
    if args.workflow == "tws-new-factory":
        required.append("tws-customer-proposal-pipeline")

    checks = {
        f"skill:{name}": (SKILLS / name / "SKILL.md").is_file()
        for name in required
    }
    if args.workflow == "tws-new-factory":
        if os.environ.get("TWS_ASSET_LIBRARY_BASE_URL"):
            checks.update({
                "asset:remote-client": (Path(__file__).parent / "remote_asset_library.py").is_file(),
                "asset:remote-catalog-pin": bool(os.environ.get("TWS_ASSET_LIBRARY_CATALOG_SHA256")),
            })
        else:
            library = args.asset_library or (Path(DEFAULT_TWS_LIBRARY) if DEFAULT_TWS_LIBRARY else None)
            checks.update({
                "asset:library-configured": library is not None,
                "asset:catalog": bool(library and (library / "catalog.json").is_file()),
                "asset:selector": bool(library and (library / "select_assets.py").is_file()),
                "asset:verifier": bool(library and (library / "verify_assets.py").is_file()),
            })

    failed = sorted(name for name, ok in checks.items() if not ok)
    print(json.dumps({"status": "FAIL" if failed else "PASS", "checks": checks, "failed": failed}, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
