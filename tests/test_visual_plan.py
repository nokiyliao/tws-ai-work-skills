#!/usr/bin/env python3

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT / "skills/nokiy-deck-orchestrator/scripts/validate_visual_plan.py"
SPEC = importlib.util.spec_from_file_location("tws_visual_plan_test", VALIDATOR_PATH)
VALIDATOR = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = VALIDATOR
SPEC.loader.exec_module(VALIDATOR)


def fixture() -> tuple[dict, dict, dict]:
    digest = "a" * 64
    selected = {
        "id": "official-hero",
        "file": "assets/hero.png",
        "sha1": "b" * 40,
        "evidence_level": "official",
        "reuse_scope": "internal",
    }
    selection = {
        "schema_version": "tws_asset_selection_v1",
        "catalog_sha256": digest,
        "selected_assets": [selected],
    }
    receipt = {"status": "PASS", "catalog_sha256": digest, "selected": 1}
    plan = {
        "schema_version": "tws_deck_visual_plan_v1",
        "catalog_sha256": digest,
        "slides": [
            {
                "slide": 1,
                "role": "cover",
                "visual_type": "official_asset",
                "visual_purpose": "brand hero",
                "asset_ids": ["official-hero"],
                "hero": True,
            },
            {
                "slide": 2,
                "role": "capability",
                "visual_type": "editable_diagram",
                "visual_purpose": "capability map",
                "diagram_spec": {"nodes": ["A", "B"]},
            },
            {
                "slide": 3,
                "role": "process",
                "visual_type": "editable_diagram",
                "visual_purpose": "service flow",
                "diagram_spec": {"nodes": ["1", "2"]},
            },
        ],
    }
    return plan, selection, receipt


class VisualPlanContractTest(unittest.TestCase):
    def test_published_schema_matches_validator_contract(self) -> None:
        schema = json.loads((ROOT / "skills/nokiy-deck-orchestrator/references/tws-visual-plan.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(schema["properties"]["schema_version"]["const"], VALIDATOR.PLAN_SCHEMA)
        self.assertEqual(set(schema["properties"]["slides"]["items"]["properties"]["visual_type"]["enum"]), VALIDATOR.VISUAL_TYPES)

    def test_valid_plan_passes(self) -> None:
        plan, selection, receipt = fixture()
        errors, slides = VALIDATOR.validate_plan(plan, selection, receipt, 3)
        self.assertEqual(errors, [])
        self.assertEqual(len(slides), 3)

    def test_cover_and_slide_coverage_fail_closed(self) -> None:
        plan, selection, receipt = fixture()
        plan["slides"][0] = {
            "slide": 1,
            "role": "cover",
            "visual_type": "typography_only",
            "visual_purpose": "plain cover",
            "exception_reason": "quick draft",
            "hero": False,
        }
        plan["slides"].pop(1)
        errors, _slides = VALIDATOR.validate_plan(plan, selection, receipt, 3)
        joined = "\n".join(errors)
        self.assertIn("ordered slides", joined)
        self.assertIn("cover cannot be typography_only", joined)
        self.assertIn("cover must use", joined)

    def test_unselected_asset_and_failed_receipt_are_rejected(self) -> None:
        plan, selection, receipt = fixture()
        plan["slides"][0]["asset_ids"] = ["not-selected"]
        receipt["status"] = "FAIL"
        errors, _slides = VALIDATOR.validate_plan(plan, selection, receipt, 3)
        joined = "\n".join(errors)
        self.assertIn("receipt status must be PASS", joined)
        self.assertIn("not in the verified selection", joined)

    def test_built_deck_checks_asset_on_planned_slide(self) -> None:
        plan, selection, receipt = fixture()
        errors, slides = VALIDATOR.validate_plan(plan, selection, receipt, 3)
        self.assertEqual(errors, [])
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            image = root / "hero.png"
            image.write_bytes(b"fixture-image")
            pptx = root / "deck.pptx"
            slide_with_image = b'''<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><p:cSld><a:blip r:embed="rId1"/></p:cSld></p:sld>'''
            empty_slide = b'''<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"><p:cSld/></p:sld>'''
            rels = b'''<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="../media/image1.png"/></Relationships>'''
            with zipfile.ZipFile(pptx, "w") as package:
                package.writestr("ppt/slides/slide1.xml", slide_with_image)
                package.writestr("ppt/slides/_rels/slide1.xml.rels", rels)
                package.writestr("ppt/slides/slide2.xml", empty_slide)
                package.writestr("ppt/slides/slide3.xml", empty_slide)
                package.writestr("ppt/media/image1.png", image.read_bytes())
            registry = {
                "_registry_path": str(root / "registry.json"),
                "assets": [{
                    "asset_id": "official-hero",
                    "deck_asset_path": str(image),
                    "source_type": "official",
                    "role": "hero",
                    "slide": 1,
                    "sha1": hashlib.sha1(image.read_bytes()).hexdigest(),
                }],
            }
            self.assertEqual(VALIDATOR.validate_built_deck(slides, registry, pptx), [])
            registry["assets"][0]["slide"] = 2
            built_errors = VALIDATOR.validate_built_deck(slides, registry, pptx)
            self.assertTrue(any("absent from the registry" in error for error in built_errors))


if __name__ == "__main__":
    unittest.main()
