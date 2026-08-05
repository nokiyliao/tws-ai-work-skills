#!/usr/bin/env python3
"""Fail-closed dependency check for the authoritative deck pipeline.

Checks installed skills, remote/local asset configuration, and the isolated
TWS AI runtime (imports, renderer, PDF rasterizer, OCR). Emits machine-readable
JSON. Missing system Office/LibreOffice/Tesseract tools are typed blockers.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
from pathlib import Path
from typing import Any


HOME = Path.home()
SKILLS = Path(os.environ.get("CODEX_HOME", HOME / ".codex")) / "skills"
DEFAULT_TWS_LIBRARY = os.environ.get("TWS_ASSET_LIBRARY_PATH", "")
DEFAULT_REMOTE_CONFIG = HOME / ".config" / "tws-ai" / "asset-service.json"
SCRIPT_DIR = Path(__file__).resolve().parent


def _load_runtime_bootstrap():
    path = SCRIPT_DIR / "runtime_bootstrap.py"
    name = "tws_runtime_bootstrap"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load runtime bootstrap from {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def remote_configured() -> tuple[bool, bool]:
    base_url = os.environ.get("TWS_ASSET_LIBRARY_BASE_URL", "")
    catalog_pin = os.environ.get("TWS_ASSET_LIBRARY_CATALOG_SHA256", "")
    if DEFAULT_REMOTE_CONFIG.is_file():
        try:
            config = json.loads(DEFAULT_REMOTE_CONFIG.read_text(encoding="utf-8"))
            base_url = base_url or config.get("base_url", "")
            catalog_pin = catalog_pin or config.get("catalog_sha256", "")
        except (OSError, json.JSONDecodeError):
            pass
    return bool(base_url), len(catalog_pin) == 64


def _as_map(value: Any) -> dict[str, Any]:
    if value is None:
        return {"ok": False}
    if isinstance(value, dict):
        out = dict(value)
        out["ok"] = bool(out.get("ok"))
        out["admin_or_gui"] = bool(out.get("admin_or_gui") or out.get("admin_or_gui_required"))
        return out
    if hasattr(value, "ok"):
        data = getattr(value, "data", None) or {}
        out = {
            "ok": bool(value.ok),
            "detail": getattr(value, "detail", None),
            "blocker": getattr(value, "blocker", None),
        }
        out.update(data)
        out["admin_or_gui"] = bool(data.get("admin_or_gui_required") or out.get("admin_or_gui"))
        return out
    return {"ok": bool(value), "detail": str(value)}


def runtime_checks(runtime_home_path: Path | None = None) -> dict[str, Any]:
    """Probe isolated runtime and system tools; return structured detail map."""
    rb = _load_runtime_bootstrap()
    home = rb.runtime_home(runtime_home_path)
    paths = rb.runtime_paths(home)
    python_exe = paths["python"] if paths["python"].is_file() else None
    runtime = _as_map(rb.detect_runtime(home))
    imports = _as_map(rb.detect_imports(python_exe))
    return {
        "runtime": runtime,
        "runtime_home": str(paths.get("home") or paths.get("root") or home),
        "runtime_python": str(paths["python"]) if paths["python"].is_file() else None,
        "venv_present": paths["python"].is_file(),
        "imports": imports,
        "renderer": _as_map(rb.detect_renderer(win32com_available=(imports.get("modules") or {}).get("win32com"))),
        "rasterizer": _as_map(rb.detect_rasterizer(python_exe=python_exe)),
        "ocr": _as_map(rb.detect_ocr(python_exe)),
        "platform": _as_map(rb.detect_platform()),
        "uv": _as_map(rb.detect_uv()),
        "python_host": _as_map(rb.detect_python()),
        "python": _as_map(rb.detect_python()),
    }


def flatten_runtime_bools(runtime: dict[str, Any]) -> dict[str, bool]:
    """Convert runtime_checks() detail into flat boolean preflight keys."""
    checks: dict[str, bool] = {
        "runtime:venv": bool(runtime.get("venv_present")),
        "runtime:home": bool((runtime.get("runtime") or {}).get("ok")),
        "runtime:platform": bool((runtime.get("platform") or {}).get("ok")),
        "runtime:python_host": bool((runtime.get("python_host") or runtime.get("python") or {}).get("ok")),
        "runtime:imports": bool((runtime.get("imports") or {}).get("ok")),
        "runtime:renderer": bool((runtime.get("renderer") or {}).get("ok")),
        "runtime:rasterizer": bool((runtime.get("rasterizer") or {}).get("ok")),
        "runtime:ocr": bool((runtime.get("ocr") or {}).get("ok")),
    }
    modules = (runtime.get("imports") or {}).get("modules") or {}
    for name, ok in modules.items():
        checks[f"import:{name}"] = bool(ok)
    return checks


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workflow", choices=("general", "tws-new-factory"), default="general")
    parser.add_argument(
        "--asset-mode",
        choices=("remote", "local"),
        default="remote",
        help="company learners use remote; local is administrator maintenance only",
    )
    parser.add_argument("--asset-library", type=Path, help="local asset-library root; overrides TWS_ASSET_LIBRARY_PATH")
    parser.add_argument(
        "--runtime-home",
        type=Path,
        default=None,
        help="override isolated runtime root (default: ~/.codex/runtimes/tws-ai)",
    )
    parser.add_argument(
        "--skip-runtime",
        action="store_true",
        help="legacy skill/asset checks only (not for company learner production)",
    )
    parser.add_argument("--json", action="store_true", default=True, help="emit machine-readable JSON (default)")
    args = parser.parse_args(argv)

    required = ["humanizer-zh-tw", "nokiy-presentation-generator", "codex-ppt"]
    if args.workflow == "tws-new-factory":
        required.append("tws-customer-proposal-pipeline")

    checks: dict[str, bool] = {
        f"skill:{name}": (SKILLS / name / "SKILL.md").is_file()
        for name in required
    }
    details: dict[str, Any] = {"skills_root": str(SKILLS)}

    if args.workflow == "tws-new-factory":
        if args.asset_mode == "remote":
            has_base_url, has_catalog_pin = remote_configured()
            checks.update(
                {
                    "asset:remote-base-url": has_base_url,
                    "asset:remote-client": (SCRIPT_DIR / "remote_asset_library.py").is_file(),
                    "asset:remote-catalog-pin": has_catalog_pin,
                }
            )
            details["asset_mode"] = "remote"
        else:
            library = args.asset_library or (Path(DEFAULT_TWS_LIBRARY) if DEFAULT_TWS_LIBRARY else None)
            checks.update(
                {
                    "asset:library-configured": library is not None,
                    "asset:catalog": bool(library and (library / "catalog.json").is_file()),
                    "asset:selector": bool(library and (library / "select_assets.py").is_file()),
                    "asset:verifier": bool(library and (library / "verify_assets.py").is_file()),
                }
            )
            details["asset_mode"] = "local"
            details["asset_library"] = str(library) if library else None

    runtime_detail: dict[str, Any] | None = None
    runtime_blockers: list[dict[str, Any]] = []
    if not args.skip_runtime:
        try:
            runtime_detail = runtime_checks(args.runtime_home)
            checks.update(flatten_runtime_bools(runtime_detail))
            for key in ("imports", "renderer", "rasterizer", "ocr", "platform", "python_host", "runtime"):
                node = runtime_detail.get(key) or {}
                if node.get("ok") is False and node.get("blocker"):
                    runtime_blockers.append(
                        {
                            "check": key,
                            "blocker": node.get("blocker"),
                            "detail": node.get("detail"),
                            "admin_or_gui": bool(node.get("admin_or_gui")),
                        }
                    )
            if not runtime_detail.get("venv_present"):
                runtime_blockers.append(
                    {
                        "check": "venv",
                        "blocker": "RUNTIME_VENV",
                        "detail": f"missing isolated runtime at {runtime_detail.get('runtime_home')}",
                        "admin_or_gui": False,
                    }
                )
        except Exception as exc:  # fail closed
            checks["runtime:bootstrap-load"] = False
            runtime_blockers.append(
                {
                    "check": "runtime_bootstrap",
                    "blocker": "RUNTIME_BOOTSTRAP",
                    "detail": str(exc),
                    "admin_or_gui": False,
                }
            )
            runtime_detail = {"error": str(exc)}

    failed = sorted(name for name, ok in checks.items() if not ok)
    status = "FAIL" if failed else "PASS"
    report = {
        "status": status,
        "workflow": args.workflow,
        "asset_mode": args.asset_mode,
        "checks": checks,
        "failed": failed,
        "runtime": runtime_detail,
        "blockers": runtime_blockers,
        "details": details,
    }
    print(json.dumps(report, indent=2, ensure_ascii=True))
    if status != "PASS":
        admin = [b for b in runtime_blockers if b.get("admin_or_gui")]
        if admin:
            print(
                "FAIL_CLOSED: system tools require admin/GUI install: "
                + ", ".join(str(b["blocker"]) for b in admin),
                file=sys.stderr,
            )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
