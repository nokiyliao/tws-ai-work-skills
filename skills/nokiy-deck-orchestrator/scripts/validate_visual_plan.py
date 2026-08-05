#!/usr/bin/env python3
"""Fail-closed validator for TWS per-slide visual plans and built decks."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import posixpath
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


PLAN_SCHEMA = "tws_deck_visual_plan_v1"
SELECTION_SCHEMA = "tws_asset_selection_v1"
ASSET_VISUALS = {"official_asset", "concept_asset"}
IMAGE_VISUALS = ASSET_VISUALS | {"generated_concept"}
VISUAL_TYPES = IMAGE_VISUALS | {
    "editable_diagram",
    "data_visual",
    "typography_only",
}
SHA1_RE = re.compile(r"^[0-9a-f]{40}$", re.IGNORECASE)
REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
DRAWING_REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


def load_object(path: Path, label: str) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{label} must be a JSON object")
    return data


def normalized_slides(item: dict) -> set[int]:
    value = item.get("slides", item.get("slide", []))
    if isinstance(value, int):
        value = [value]
    if not isinstance(value, list) or not all(isinstance(number, int) and number > 0 for number in value):
        return set()
    return set(value)


def validate_plan(plan: dict, selection: dict, receipt: dict, expect_slides: int) -> tuple[list[str], list[dict]]:
    errors: list[str] = []
    if plan.get("schema_version") != PLAN_SCHEMA:
        errors.append(f"visual plan schema_version must be {PLAN_SCHEMA}")
    if selection.get("schema_version") != SELECTION_SCHEMA:
        errors.append(f"selection schema_version must be {SELECTION_SCHEMA}")
    catalog_digest = str(selection.get("catalog_sha256", "")).lower()
    if receipt.get("status") != "PASS":
        errors.append("asset verification receipt status must be PASS")
    if not catalog_digest or receipt.get("catalog_sha256") != catalog_digest:
        errors.append("asset verification receipt does not bind the selection catalog digest")
    if plan.get("catalog_sha256") != catalog_digest:
        errors.append("visual plan does not bind the selection catalog digest")

    selected = selection.get("selected_assets")
    if not isinstance(selected, list) or not selected:
        errors.append("selection manifest has no selected_assets")
        selected = []
    selected_by_id = {
        str(item.get("id")): item
        for item in selected
        if isinstance(item, dict) and str(item.get("id", "")).strip()
    }

    slides = plan.get("slides")
    if not isinstance(slides, list):
        errors.append("visual plan slides must be an array")
        return errors, []
    numbers = [item.get("slide") for item in slides if isinstance(item, dict)]
    expected_numbers = list(range(1, expect_slides + 1))
    if numbers != expected_numbers:
        errors.append(f"visual plan must contain ordered slides 1..{expect_slides} exactly once")

    typography_count = 0
    image_count = 0
    for index, item in enumerate(slides, 1):
        if not isinstance(item, dict):
            errors.append(f"slide entry {index} must be an object")
            continue
        slide = item.get("slide", index)
        visual_type = item.get("visual_type")
        for key in ("role", "visual_purpose"):
            if not str(item.get(key, "")).strip():
                errors.append(f"slide {slide}: {key} is required")
        if visual_type not in VISUAL_TYPES:
            errors.append(f"slide {slide}: invalid visual_type {visual_type!r}")
            continue
        if visual_type in IMAGE_VISUALS:
            image_count += 1
        if visual_type in ASSET_VISUALS:
            asset_ids = item.get("asset_ids")
            if not isinstance(asset_ids, list) or not asset_ids:
                errors.append(f"slide {slide}: {visual_type} requires asset_ids")
                continue
            for asset_id in asset_ids:
                selected_asset = selected_by_id.get(str(asset_id))
                if not selected_asset:
                    errors.append(f"slide {slide}: asset {asset_id!r} is not in the verified selection")
                    continue
                evidence = str(selected_asset.get("evidence_level", "")).lower()
                if visual_type == "official_asset" and evidence not in {"official", "customer_only"}:
                    errors.append(f"slide {slide}: asset {asset_id!r} is not official evidence")
                if visual_type == "concept_asset" and evidence not in {"concept", "customer_only"}:
                    errors.append(f"slide {slide}: asset {asset_id!r} is not concept evidence")
        elif visual_type == "generated_concept":
            if not str(item.get("generation_prompt", "")).strip():
                errors.append(f"slide {slide}: generated_concept requires generation_prompt")
        elif visual_type == "editable_diagram":
            if not item.get("diagram_spec"):
                errors.append(f"slide {slide}: editable_diagram requires diagram_spec")
        elif visual_type == "data_visual":
            if not str(item.get("source_ref", "")).strip():
                errors.append(f"slide {slide}: data_visual requires source_ref")
        elif visual_type == "typography_only":
            typography_count += 1
            if slide == 1:
                errors.append("slide 1 cover cannot be typography_only")
            if not str(item.get("exception_reason", "")).strip():
                errors.append(f"slide {slide}: typography_only requires exception_reason")
        if slide == 1 and visual_type not in IMAGE_VISUALS:
            errors.append("slide 1 cover must use an official, concept, or generated hero visual")
        if slide == 1 and item.get("hero") is not True:
            errors.append("slide 1 cover must declare hero=true")

    if typography_count > math.floor(expect_slides * 0.20):
        errors.append("typography_only exceeds 20 percent of the deck")
    required_images = max(1, math.ceil(expect_slides / 3))
    if image_count < required_images:
        errors.append(f"visual plan requires at least {required_images} image-bearing slides")
    return errors, slides


def slide_media_sha1(pptx: Path) -> dict[int, set[str]]:
    result: dict[int, set[str]] = {}
    with zipfile.ZipFile(pptx) as package:
        for member in package.namelist():
            match = re.fullmatch(r"ppt/slides/slide(\d+)\.xml", member)
            if not match:
                continue
            slide_number = int(match.group(1))
            rels_name = f"ppt/slides/_rels/slide{slide_number}.xml.rels"
            relationships: dict[str, str] = {}
            if rels_name in package.namelist():
                rel_root = ET.fromstring(package.read(rels_name))
                for rel in rel_root.findall(f"{{{REL_NS}}}Relationship"):
                    relationships[str(rel.get("Id"))] = str(rel.get("Target"))
            slide_root = ET.fromstring(package.read(member))
            digests: set[str] = set()
            for node in slide_root.iter():
                embed = node.get(f"{{{DRAWING_REL_NS}}}embed")
                target = relationships.get(str(embed), "")
                if not target:
                    continue
                normalized = posixpath.normpath(posixpath.join("ppt/slides", target))
                if normalized.startswith("ppt/media/") and normalized in package.namelist():
                    digests.add(hashlib.sha1(package.read(normalized)).hexdigest())
            result[slide_number] = digests
    return result


def validate_built_deck(plan_slides: list[dict], registry: dict, pptx: Path) -> list[str]:
    errors: list[str] = []
    assets = registry.get("assets")
    if not isinstance(assets, list) or not assets:
        return ["asset registry must contain a non-empty assets array"]
    media_by_slide = slide_media_sha1(pptx)
    records: list[dict] = []
    for index, item in enumerate(assets, 1):
        if not isinstance(item, dict):
            errors.append(f"registry item {index} must be an object")
            continue
        path_value = str(item.get("deck_asset_path", "")).strip()
        path = Path(path_value)
        if not path.is_absolute():
            path = Path(registry.get("_registry_path", ".")).parent / path
        try:
            actual_sha1 = hashlib.sha1(path.read_bytes()).hexdigest()
        except OSError as exc:
            errors.append(f"registry item {index} cannot read {path_value}: {exc}")
            continue
        declared = str(item.get("sha1", "")).lower()
        if declared and (not SHA1_RE.fullmatch(declared) or declared != actual_sha1):
            errors.append(f"registry item {index} sha1 does not match {path_value}")
        record = dict(item, _sha1=actual_sha1, _slides=normalized_slides(item))
        if not record["_slides"]:
            errors.append(f"registry item {index} requires slide or slides provenance")
        records.append(record)

    for item in plan_slides:
        slide = item.get("slide")
        visual_type = item.get("visual_type")
        candidates: list[dict] = []
        if visual_type in ASSET_VISUALS:
            planned_ids = {str(value) for value in item.get("asset_ids", [])}
            for asset_id in planned_ids:
                matched = [record for record in records if str(record.get("asset_id", "")) == asset_id and slide in record["_slides"]]
                if not matched:
                    errors.append(f"slide {slide}: planned asset {asset_id!r} is absent from the registry for this slide")
                candidates.extend(matched)
        elif visual_type == "generated_concept":
            prompt = str(item.get("generation_prompt", "")).strip()
            candidates = [
                record for record in records
                if str(record.get("source_type", "")).lower() == "generated"
                and slide in record["_slides"]
                and str(record.get("prompt", "")).strip() == prompt
            ]
            if not candidates:
                errors.append(f"slide {slide}: generated concept is absent from the registry or prompt does not match")
        for record in candidates:
            if record["_sha1"] not in media_by_slide.get(slide, set()):
                errors.append(f"slide {slide}: registered visual {record.get('deck_asset_path')} is not embedded on the planned slide")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--selection-manifest", type=Path, required=True)
    parser.add_argument("--verification-receipt", type=Path, required=True)
    parser.add_argument("--expect-slides", type=int, required=True)
    parser.add_argument("--asset-registry", type=Path)
    parser.add_argument("--pptx", type=Path)
    args = parser.parse_args()
    errors: list[str] = []
    try:
        plan = load_object(args.plan, "visual plan")
        selection = load_object(args.selection_manifest, "selection manifest")
        receipt = load_object(args.verification_receipt, "verification receipt")
        plan_errors, slides = validate_plan(plan, selection, receipt, args.expect_slides)
        errors.extend(plan_errors)
        if bool(args.asset_registry) != bool(args.pptx):
            errors.append("--asset-registry and --pptx must be supplied together")
        elif args.asset_registry and args.pptx and not plan_errors:
            registry = load_object(args.asset_registry, "asset registry")
            registry["_registry_path"] = str(args.asset_registry.resolve())
            errors.extend(validate_built_deck(slides, registry, args.pptx))
    except (OSError, ValueError, json.JSONDecodeError, zipfile.BadZipFile, ET.ParseError) as exc:
        errors.append(str(exc))
    payload = {
        "status": "FAIL" if errors else "PASS",
        "schema_version": PLAN_SCHEMA,
        "slides": args.expect_slides,
        "built_deck_checked": bool(args.asset_registry and args.pptx),
        "errors": errors,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
