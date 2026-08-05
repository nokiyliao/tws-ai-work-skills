#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP_PATH = ROOT / "skills/nokiy-deck-orchestrator/scripts/runtime_bootstrap.py"
PREFLIGHT_PATH = ROOT / "skills/nokiy-deck-orchestrator/scripts/preflight.py"
RUNTIME_DIR = ROOT / "skills/nokiy-deck-orchestrator/runtime"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


RB = load_module("tws_runtime_bootstrap_test", BOOTSTRAP_PATH)
PF = load_module("tws_preflight_test", PREFLIGHT_PATH)


class RuntimeDiscoveryTest(unittest.TestCase):
    def test_platform_and_python_gates(self) -> None:
        self.assertEqual(RB.detect_platform("Darwin")["family"], "macos")
        self.assertEqual(RB.detect_platform("Windows")["family"], "windows")
        self.assertFalse(RB.detect_platform("Plan9")["ok"])
        self.assertTrue(RB.detect_python((3, 11, 0))["ok"])
        self.assertEqual(RB.detect_python((3, 9, 0))["blocker"], RB.BLOCKER_PYTHON)

    def test_tool_discovery_fail_closed_and_ready(self) -> None:
        missing_renderer = RB.detect_renderer(platform_name="macos", which_fn=lambda *_: None)
        self.assertEqual(missing_renderer["blocker"], RB.BLOCKER_RENDERER)
        renderer = RB.detect_renderer(
            platform_name="macos",
            which_fn=lambda name, *_: "/usr/bin/soffice" if name == "soffice" else None,
        )
        self.assertTrue(renderer["ok"])

        missing_ocr = RB.detect_ocr(
            platform_name="windows",
            which_fn=lambda *_: None,
            import_probe=lambda *_: False,
        )
        self.assertEqual(missing_ocr["blocker"], RB.BLOCKER_OCR)
        ocr = RB.detect_ocr(
            platform_name="windows",
            which_fn=lambda name, *_: "C:/tesseract.exe" if name == "tesseract" else None,
        )
        self.assertTrue(ocr["primary"].startswith("tesseract"))
        portable_ocr = RB.detect_ocr(
            python_exe=Path("C:/runtime/python.exe"),
            platform_name="windows",
            which_fn=lambda *_: None,
            import_probe=lambda module, _python: module in {"rapidocr", "onnxruntime"},
        )
        self.assertEqual(portable_ocr["primary"], "rapidocr-onnxruntime")
        self.assertFalse(portable_ocr["admin_or_gui_required"])

        missing_rasterizer = RB.detect_rasterizer(
            python_exe=None,
            which_fn=lambda *_: None,
            import_probe=lambda *_: False,
        )
        self.assertEqual(missing_rasterizer["blocker"], RB.BLOCKER_RASTERIZER)
        rasterizer = RB.detect_rasterizer(
            python_exe=Path("/tmp/python"),
            which_fn=lambda *_: None,
            import_probe=lambda module, _python: module == "fitz",
        )
        self.assertEqual(rasterizer["primary"], "pymupdf")

    def test_runtime_path_is_portable(self) -> None:
        root = Path("runtime-fixture")
        paths = RB.runtime_paths(root)
        self.assertEqual(paths["root"], root)
        self.assertNotIn("/Users/nokiy", str(paths["python"]))

    def test_uv_skips_broken_path_alias_and_uses_real_user_binary(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            real_uv = Path(temp) / "uv.exe"
            real_uv.write_bytes(b"fixture")

            def fake_version(command, **_kwargs):
                if command[0] == "C:/broken/uv.exe":
                    raise OSError("broken alias")
                return "uv 0.12.0\n"

            with mock.patch.object(RB.subprocess, "check_output", side_effect=fake_version):
                result = RB.detect_uv(
                    which_fn=lambda *_: "C:/broken/uv.exe",
                    candidate_paths=[real_uv],
                )
        self.assertTrue(result["ok"])
        self.assertEqual(result["path"], str(real_uv))


class RuntimeBehaviorTest(unittest.TestCase):
    def test_check_fails_closed_without_isolated_runtime(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            report = RB.run_check(Path(temp), skip_remote=True)
        self.assertEqual(report["status"], "FAIL")
        self.assertIn(RB.BLOCKER_VENV, {item["blocker"] for item in report["blockers"]})
        json.dumps(report)

    def test_uv_is_required_for_managed_install(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            paths = RB.runtime_paths(Path(temp))
            result = RB.ensure_venv(paths, uv_path=None)
        self.assertEqual(result["blocker"], RB.BLOCKER_UV)

    def test_smoke_render_invokes_real_renderer_script(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            workdir = Path(temp)
            pptx = workdir / "smoke.pptx"
            pptx.write_bytes(b"fixture")

            def fake_run(command, **_kwargs):
                output = Path(command[command.index("--output") + 1])
                output.mkdir(parents=True)
                (output / "slide-01.png").write_bytes(b"x" * 200)
                return subprocess.CompletedProcess(command, 0, "PASS", "")

            with mock.patch.object(RB.subprocess, "run", side_effect=fake_run) as invoked:
                result = RB.smoke_render(Path(sys.executable), workdir, pptx)
        self.assertTrue(result["ok"])
        self.assertIn("render_slides.py", str(invoked.call_args.args[0][1]))

    def test_vision_smoke_executes_ocr_helper(self) -> None:
        payload = json.dumps([{"path": "slide.png", "text": "TWS AI", "error": ""}])
        completed = subprocess.CompletedProcess([], 0, payload, "")
        with mock.patch.object(RB.subprocess, "run", return_value=completed) as invoked:
            result = RB.smoke_ocr(
                Path("slide.png"),
                {"ok": True, "primary": "vision_swift", "engines": ["macos-vision"]},
            )
        self.assertTrue(result["ok"])
        self.assertIn("ocr_rendered_slides.py", str(invoked.call_args.args[0][1]))

    def test_locked_dependencies_are_pinned_and_portable(self) -> None:
        text = (RUNTIME_DIR / "requirements.lock").read_text(encoding="utf-8")
        for package in ("python-pptx==", "pillow==", "pymupdf==", "rapidocr==", "onnxruntime==", "pywin32=="):
            self.assertIn(package, text)
        self.assertIn("sys_platform", text)
        self.assertNotIn("/Users/", text)

    def test_rapidocr_smoke_uses_isolated_python(self) -> None:
        completed = subprocess.CompletedProcess([], 0, '{"texts": ["TWS AI runtime smoke"]}\n', "")
        with mock.patch.object(RB.subprocess, "run", return_value=completed) as invoked:
            result = RB.smoke_ocr(
                Path("slide.png"),
                {
                    "ok": True,
                    "primary": "rapidocr-onnxruntime",
                    "engines": ["rapidocr-onnxruntime"],
                    "python": "C:/Users/student/.codex/runtimes/tws-ai/venv/Scripts/python.exe",
                },
            )
        self.assertTrue(result["ok"])
        self.assertEqual(invoked.call_args.args[0][0], "C:/Users/student/.codex/runtimes/tws-ai/venv/Scripts/python.exe")


class PreflightTest(unittest.TestCase):
    def test_runtime_contract_is_machine_readable(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            detail = PF.runtime_checks(Path(temp))
        for key in ("runtime", "imports", "renderer", "rasterizer", "ocr", "platform", "uv", "python_host"):
            self.assertIn(key, detail)
            self.assertIn("ok", detail[key])
        flattened = PF.flatten_runtime_bools(detail)
        self.assertIn("runtime:renderer", flattened)
        self.assertIn("runtime:ocr", flattened)
        self.assertFalse(flattened["runtime:home"])
        json.dumps(detail)


if __name__ == "__main__":
    unittest.main()
