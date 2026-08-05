#!/usr/bin/env python3
"""Fetch and verify a TWS selection into a job-local asset mirror."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import sys
import subprocess
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urljoin, urlparse
from urllib.request import Request, urlopen


class RemoteAssetError(RuntimeError):
    pass


DEFAULT_CONFIG = Path.home() / ".config" / "tws-ai" / "asset-service.json"


def encoded_json(value: dict) -> str:
    return base64.urlsafe_b64encode(json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode()).decode().rstrip("=")


def sha1(data: bytes) -> str:
    return hashlib.sha1(data).hexdigest()


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_config(path: Path | None) -> dict:
    config = {}
    path = path or (DEFAULT_CONFIG if DEFAULT_CONFIG.is_file() else None)
    if path:
        try:
            config = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise RemoteAssetError(f"invalid asset-service config: {path}") from exc
    return {
        "base_url": os.environ.get("TWS_ASSET_LIBRARY_BASE_URL", config.get("base_url", "")),
        "catalog_sha256": os.environ.get("TWS_ASSET_LIBRARY_CATALOG_SHA256", config.get("catalog_sha256", "")),
        "access_mode": os.environ.get("TWS_ASSET_LIBRARY_ACCESS_MODE", config.get("access_mode", "public")),
    }


def checked_base_url(value: str, allow_http: bool) -> str:
    parsed = urlparse(value)
    if parsed.scheme not in ({"https", "http"} if allow_http else {"https"}) or not parsed.netloc or parsed.query or parsed.fragment:
        raise RemoteAssetError("asset-service base_url must be an HTTPS origin without query or fragment")
    return value.rstrip("/") + "/"


def fetch(base_url: str, path: str, headers: dict[str, str]) -> tuple[bytes, dict[str, str]]:
    request = Request(urljoin(base_url, path.lstrip("/")), headers=headers, method="GET")
    try:
        with urlopen(request, timeout=30) as response:
            if response.status != 200:
                raise RemoteAssetError(f"asset-service returned HTTP {response.status} for {path}")
            return response.read(), {name.lower(): value for name, value in response.headers.items()}
    except (HTTPError, URLError, TimeoutError) as exc:
        raise RemoteAssetError(f"asset-service request failed for {path}: {exc}") from exc


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--requirements", type=Path, required=True)
    parser.add_argument("--stage", type=Path, required=True, help="job-local directory receiving catalog, manifest, and selected assets")
    parser.add_argument("--config", type=Path, help="private administrator config; environment variables override it")
    parser.add_argument("--verifier", type=Path, help="optional additional local verify_assets.py")
    parser.add_argument("--limit", type=int, default=6)
    parser.add_argument("--allow-http", action="store_true", help="test-only: permit a loopback HTTP fixture")
    args = parser.parse_args()
    try:
        profile = json.loads(args.profile.read_text(encoding="utf-8"))
        requirements = json.loads(args.requirements.read_text(encoding="utf-8"))
        if not isinstance(profile, dict) or not isinstance(requirements, dict):
            raise RemoteAssetError("profile and requirements must be JSON objects")
        if not 1 <= args.limit <= 20:
            raise RemoteAssetError("limit must be between 1 and 20")
        config = load_config(args.config)
        base_url = checked_base_url(config["base_url"], args.allow_http)
        configured_catalog_digest = config["catalog_sha256"].lower()
        if len(configured_catalog_digest) != 64 or any(char not in "0123456789abcdef" for char in configured_catalog_digest):
            raise RemoteAssetError("a 64-character TWS_ASSET_LIBRARY_CATALOG_SHA256 pin is required")
        headers = {"Accept": "application/json", "User-Agent": "TWSAssetClient/1.0"}
        if config["access_mode"] != "public":
            raise RemoteAssetError("unsupported asset-service access mode")

        catalog, catalog_headers = fetch(base_url, "/v1/catalog", headers)
        catalog_digest = sha256(catalog)
        if catalog_headers.get("x-catalog-sha256") != catalog_digest:
            raise RemoteAssetError("catalog digest header is absent or does not match response bytes")
        if configured_catalog_digest != catalog_digest:
            raise RemoteAssetError("catalog digest does not match the configured pin")
        catalog_obj = json.loads(catalog)
        if not isinstance(catalog_obj.get("assets"), list):
            raise RemoteAssetError("remote catalog has no assets list")
        query = urlencode({"profile_b64": encoded_json(profile), "requirements_b64": encoded_json(requirements), "limit": args.limit})
        manifest_bytes, _manifest_headers = fetch(base_url, f"/v1/selection?{query}", headers)
        manifest = json.loads(manifest_bytes)
        if manifest.get("schema_version") != "tws_asset_selection_v1" or manifest.get("catalog_sha256") != catalog_digest:
            raise RemoteAssetError("selection manifest does not bind the downloaded catalog")

        stage = args.stage.resolve()
        if stage.exists():
            raise RemoteAssetError(f"stage already exists; refusing to replace: {stage}")
        stage.mkdir(parents=True)
        (stage / "catalog.json").write_bytes(catalog)
        (stage / "selection-manifest.json").write_bytes(manifest_bytes)
        catalog_by_id = {asset.get("id"): asset for asset in catalog_obj["assets"]}
        selected_assets = manifest.get("selected_assets")
        if not isinstance(selected_assets, list) or not selected_assets:
            raise RemoteAssetError("selection manifest has no selected_assets")
        for selected in selected_assets:
            current = catalog_by_id.get(selected.get("id"))
            if not current or any(selected.get(key) != current.get(key) for key in ("file", "sha1", "evidence_level", "reuse_scope")):
                raise RemoteAssetError(f"selection/catalog mismatch: {selected.get('id')}")
            relative = Path(current["file"])
            if relative.is_absolute() or ".." in relative.parts:
                raise RemoteAssetError(f"unsafe catalog path: {current['id']}")
            body, asset_headers = fetch(base_url, f"/v1/assets/{current['id']}", headers)
            if asset_headers.get("x-asset-id") != current["id"] or asset_headers.get("x-asset-sha1") != current["sha1"]:
                raise RemoteAssetError(f"asset identity header mismatch: {current['id']}")
            if sha1(body) != current["sha1"]:
                raise RemoteAssetError(f"digest mismatch: {current['id']}")
            target = stage / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(body)
        verifier_stdout = "built-in remote catalog/manifest/header/digest verification passed"
        verifier_stderr = ""
        verifier_returncode = 0
        if args.verifier:
            verified = subprocess.run([sys.executable, str(args.verifier), "--library", str(stage), "--selection", str(stage / "selection-manifest.json")], capture_output=True, text=True)
            verifier_stdout, verifier_stderr, verifier_returncode = verified.stdout, verified.stderr, verified.returncode
        receipt = {"status": "PASS" if verifier_returncode == 0 else "FAIL", "catalog_sha256": catalog_digest, "selected": len(selected_assets), "verifier_stdout": verifier_stdout, "verifier_stderr": verifier_stderr}
        (stage / "remote-verification-receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if verifier_returncode:
            raise RemoteAssetError(verifier_stderr or verifier_stdout or "asset verifier failed")
        print(json.dumps({"status": "PASS", "stage": str(stage), "catalog_sha256": catalog_digest, "selected": len(manifest.get("selected_assets", []))}))
        return 0
    except (OSError, ValueError, json.JSONDecodeError, RemoteAssetError) as exc:
        print(f"FAIL_CLOSED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
