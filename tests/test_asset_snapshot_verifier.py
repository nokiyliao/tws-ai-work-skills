#!/usr/bin/env python3

from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERIFIER_PATH = ROOT / "skills/nokiy-presentation-generator/scripts/asset_snapshot.py"
SPEC = importlib.util.spec_from_file_location("tws_asset_snapshot", VERIFIER_PATH)
VERIFIER = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(VERIFIER)


class AssetSnapshotVerifierTest(unittest.TestCase):
    def test_verifies_materialized_remote_snapshot_and_fails_on_tamper(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            asset = root / "assets" / "sample.png"
            asset.parent.mkdir()
            asset.write_bytes(b"verified-asset")
            item = {
                "id": "sample",
                "file": "assets/sample.png",
                "sha1": hashlib.sha1(asset.read_bytes()).hexdigest(),
                "evidence_level": "official",
                "reuse_scope": "internal",
            }
            catalog_bytes = (json.dumps({"assets": [item]}, separators=(",", ":")) + "\n").encode()
            (root / "catalog.json").write_bytes(catalog_bytes)
            manifest = root / "selection-manifest.json"
            manifest.write_text(json.dumps({
                "schema_version": "tws_asset_selection_v1",
                "catalog_sha256": hashlib.sha256(catalog_bytes).hexdigest(),
                "selected_assets": [item],
            }), encoding="utf-8")

            self.assertIn("1 selected assets", VERIFIER.verify_materialized_selection(root, manifest))
            asset.write_bytes(b"tampered")
            with self.assertRaisesRegex(ValueError, "digest mismatch"):
                VERIFIER.verify_materialized_selection(root, manifest)


if __name__ == "__main__":
    unittest.main()
