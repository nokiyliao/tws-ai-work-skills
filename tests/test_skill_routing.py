#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
import json
import re
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STATE_TOOL = ROOT / "skills/nokiy-deck-orchestrator/scripts/deck_pipeline_state.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


STATE = load_module("tws_deck_pipeline_state_test", STATE_TOOL)


def frontmatter_description(skill: str) -> str:
    text = (ROOT / "skills" / skill / "SKILL.md").read_text(encoding="utf-8")
    # All presentation-routing descriptions are intentionally single-line YAML.
    match = re.search(r"^description:\s*(.+)$", text, flags=re.MULTILINE)
    if not match:
        raise AssertionError(f"description missing for {skill}")
    return match.group(1).splitlines()[0]


def state_fixture() -> dict:
    return {
        "schema_version": 3,
        "routing": {
            "entry_skill": "nokiy-deck-orchestrator",
            "contract": "tws_deck_routing_v1",
        },
        "phases": {
            phase: {"status": "pending", "evidence": []}
            for phase in STATE.PHASES
        },
    }


class SkillMetadataRoutingTest(unittest.TestCase):
    def test_manifest_declares_one_presentation_entrypoint(self) -> None:
        manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
        routing = manifest["routing"]
        self.assertEqual(routing["presentationEntryPoint"], "skills/nokiy-deck-orchestrator")
        self.assertEqual(routing["stateContract"], "tws_deck_routing_v1")
        self.assertEqual(len(routing["internalPresentationPhases"]), 3)

    def test_only_orchestrator_claims_complete_presentation_requests(self) -> None:
        entry = frontmatter_description("nokiy-deck-orchestrator")
        self.assertIn("ONLY USER-FACING ENTRY POINT", entry)
        for skill in (
            "tws-customer-proposal-pipeline",
            "nokiy-presentation-generator",
            "codex-ppt",
        ):
            description = frontmatter_description(skill)
            self.assertIn("INTERNAL-ONLY", description, skill)
            self.assertIn("Do not use directly", description, skill)
            body = (ROOT / "skills" / skill / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn("## Invocation Boundary", body, skill)


class DelegationGuardTest(unittest.TestCase):
    def test_rejects_legacy_or_unrouted_state(self) -> None:
        state = state_fixture()
        state["schema_version"] = 2
        state["routing"] = {}
        errors = STATE.delegation_errors(state, "proposal")
        self.assertTrue(any("schema_version" in error for error in errors))
        self.assertTrue(any("entry_skill" in error for error in errors))

    def test_opens_only_when_phase_prerequisites_pass(self) -> None:
        state = state_fixture()
        self.assertTrue(STATE.delegation_errors(state, "proposal"))
        state["phases"]["source"]["status"] = "pass"
        state["phases"]["case_lock"]["status"] = "pass"
        self.assertEqual(STATE.delegation_errors(state, "proposal"), [])

        self.assertTrue(STATE.delegation_errors(state, "build"))
        for phase in ("copy", "asset_selection", "asset_verification", "sample"):
            state["phases"][phase]["status"] = "pass"
        self.assertEqual(STATE.delegation_errors(state, "build"), [])

    def test_closed_or_completed_phase_cannot_be_redelegated(self) -> None:
        state = state_fixture()
        state["phases"]["source"]["status"] = "pass"
        state["phases"]["case_lock"]["status"] = "pass"
        state["phases"]["proposal"]["status"] = "pass"
        errors = STATE.delegation_errors(state, "proposal")
        self.assertTrue(any("no new delegation" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
