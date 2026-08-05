#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP_PATH = ROOT / "skills/nokiy-deck-orchestrator/scripts/bootstrap_learner.py"
SPEC = importlib.util.spec_from_file_location("tws_learner_bootstrap", BOOTSTRAP_PATH)
BOOTSTRAP = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(BOOTSTRAP)


class LearnerBootstrapTest(unittest.TestCase):
    def test_loads_managed_remote_only_environment(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            environment = Path(temp) / "learner-environment.json"
            environment.write_text(json.dumps({
                "schema_version": "tws_ai_learner_environment_v1",
                "base_url": "https://assets.example.com",
                "catalog_sha256": "a" * 64,
                "access_mode": "public",
            }), encoding="utf-8")
            self.assertEqual(
                ("https://assets.example.com", "a" * 64),
                BOOTSTRAP.load_environment(environment, None, None),
            )

    def test_rejects_local_or_unpinned_environment(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            environment = Path(temp) / "learner-environment.json"
            environment.write_text(json.dumps({
                "schema_version": "tws_ai_learner_environment_v1",
                "base_url": "http://127.0.0.1:8792",
                "catalog_sha256": "not-a-pin",
                "access_mode": "public",
            }), encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "root HTTPS URL"):
                BOOTSTRAP.load_environment(environment, None, None)


if __name__ == "__main__":
    unittest.main()
