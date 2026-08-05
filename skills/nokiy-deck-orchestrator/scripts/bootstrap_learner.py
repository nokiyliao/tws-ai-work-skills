#!/usr/bin/env python3
"""Configure and verify the remote-only company learner environment."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen


DEFAULT_ENVIRONMENT = Path(__file__).resolve().parent.parent / "references" / "learner-environment.json"
DEFAULT_CONFIG = Path.home() / ".config" / "tws-ai" / "asset-service.json"
CLIENT_HEADERS = {"Accept": "application/json", "User-Agent": "TWSAssetClient/1.0"}


def load_environment(path: Path, base_url: str | None, catalog_sha256: str | None) -> tuple[str, str]:
    managed = {}
    if path.is_file():
        try:
            managed = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"managed learner environment is invalid: {path}") from exc
        if managed.get("schema_version") != "tws_ai_learner_environment_v1" or managed.get("access_mode") != "public":
            raise RuntimeError("managed learner environment has an unsupported contract")
    resolved_url = (base_url or managed.get("base_url", "")).rstrip("/")
    parsed = urlparse(resolved_url)
    if parsed.scheme != "https" or not parsed.netloc or parsed.path not in ("", "/") or parsed.query or parsed.fragment:
        raise RuntimeError("asset service must be a root HTTPS URL")
    digest = (catalog_sha256 or managed.get("catalog_sha256", "")).lower()
    if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
        raise RuntimeError("catalog SHA-256 pin is invalid")
    return resolved_url, digest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--environment", type=Path, default=DEFAULT_ENVIRONMENT,
                        help="managed non-secret learner environment bundled with the skill")
    parser.add_argument("--base-url", help="administrator override; learners should use the managed default")
    parser.add_argument("--catalog-sha256", help="administrator override; learners should use the managed default")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    args = parser.parse_args()
    try:
        base_url, digest = load_environment(args.environment, args.base_url, args.catalog_sha256)
        request = Request(f"{base_url}/v1/catalog", headers=CLIENT_HEADERS)
        with urlopen(request, timeout=30) as response:
            body = response.read()
            header_digest = response.headers.get("X-Catalog-Sha256", "")
        actual = hashlib.sha256(body).hexdigest()
        if actual != digest or header_digest != digest:
            raise RuntimeError("catalog digest does not match the managed pin")
        args.config.parent.mkdir(parents=True, exist_ok=True)
        args.config.write_text(json.dumps({"base_url": base_url, "catalog_sha256": digest, "access_mode": "public"}, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"status": "PASS", "config": str(args.config), "catalog_sha256": digest}))
        return 0
    except Exception as exc:
        print(f"FAIL_CLOSED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
