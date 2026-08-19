#!/usr/bin/env python3
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "plugins.manifest.json"
EXPECTED_COUNT = 13
EXPECTED_EXCLUDED_COUNT = 8


def main() -> int:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    plugins = data.get("plugins", [])
    excluded = data.get("excluded", [])
    ids = [item.get("id") for item in plugins]
    excluded_ids = [item.get("id") for item in excluded]

    errors = []
    if len(plugins) != EXPECTED_COUNT:
        errors.append(f"expected {EXPECTED_COUNT} plugins, found {len(plugins)}")
    if len(excluded) != EXPECTED_EXCLUDED_COUNT:
        errors.append(
            f"expected {EXPECTED_EXCLUDED_COUNT} exclusions, found {len(excluded)}"
        )
    if len(ids) != len(set(ids)):
        errors.append("duplicate plugin id")
    if set(ids) & set(excluded_ids):
        errors.append("an excluded plugin also appears in the install list")
    for item in plugins:
        for field in ("id", "name", "channel", "observedVersion", "requiresAuth"):
            if field not in item:
                errors.append(f"{item.get('id', '<unknown>')} missing {field}")

    if errors:
        print("FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"PASS: {len(plugins)} plugins; {len(excluded)} plugins excluded")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
