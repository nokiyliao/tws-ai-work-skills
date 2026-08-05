#!/usr/bin/env python3
"""Zero-dependency verification for a materialized remote asset snapshot."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


def verify_materialized_selection(library: Path, manifest_path: Path) -> str:
    catalog_path = library / "catalog.json"
    catalog_bytes = catalog_path.read_bytes()
    catalog = json.loads(catalog_bytes)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    catalog_digest = hashlib.sha256(catalog_bytes).hexdigest()
    if manifest.get("schema_version") != "tws_asset_selection_v1":
        raise ValueError("unsupported selection manifest schema")
    if manifest.get("catalog_sha256") != catalog_digest:
        raise ValueError("selection manifest does not bind this catalog")
    by_id = {item.get("id"): item for item in catalog.get("assets", [])}
    selected = manifest.get("selected_assets")
    if not isinstance(selected, list) or not selected:
        raise ValueError("selection manifest has no selected assets")
    for item in selected:
        current = by_id.get(item.get("id"))
        if not current or any(item.get(key) != current.get(key) for key in ("file", "sha1", "evidence_level", "reuse_scope")):
            raise ValueError(f"selection/catalog mismatch: {item.get('id')}")
        relative = Path(current["file"])
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError(f"unsafe selected path: {relative}")
        asset = library / relative
        if hashlib.sha1(asset.read_bytes()).hexdigest() != current["sha1"]:
            raise ValueError(f"selected asset digest mismatch: {item.get('id')}")
    return f"{len(selected)} selected assets match catalog and digests"
