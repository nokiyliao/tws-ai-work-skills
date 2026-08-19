#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
import os
import unittest
from pathlib import Path, PureWindowsPath
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
LAUNCHER_PATH = ROOT / "learner-setup/run_runtime_bootstrap.py"
POWERSHELL_PATH = ROOT / "learner-setup/Install-TwsAiRuntime.ps1"
PROMPT_PATH = ROOT / "learner-setup/INSTALL_PLUGINS_PROMPT.md"
WORKSPACE_SETUP_PATH = ROOT / "learner-setup/setup_workspace.py"


def load_launcher():
    spec = importlib.util.spec_from_file_location("tws_runtime_launcher_test", LAUNCHER_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


LAUNCHER = load_launcher()


class CrossPlatformLearnerSetupTest(unittest.TestCase):
    def test_default_codex_home_uses_current_user(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True), mock.patch.object(Path, "home", return_value=Path("/home/student")):
            self.assertEqual(Path("/home/student/.codex"), LAUNCHER.codex_home())

    def test_codex_home_override_is_supported(self) -> None:
        with mock.patch.dict(os.environ, {"CODEX_HOME": "C:/Users/student/CodexData"}, clear=True):
            self.assertEqual(Path("C:/Users/student/CodexData"), LAUNCHER.codex_home())

    def test_windows_bootstrap_path_has_no_macos_home(self) -> None:
        target = PureWindowsPath("C:/Users/student/.codex") / "skills" / "nokiy-deck-orchestrator" / "scripts" / "runtime_bootstrap.py"
        self.assertEqual("runtime_bootstrap.py", target.name)
        self.assertNotIn("/Users/nokiy", str(target))

    def test_workspace_setup_is_resolved_beside_launcher(self) -> None:
        self.assertEqual(WORKSPACE_SETUP_PATH, LAUNCHER.workspace_setup_path())

    def test_powershell_entrypoint_is_user_scoped_and_fail_closed(self) -> None:
        text = POWERSHELL_PATH.read_text(encoding="utf-8")
        self.assertIn("$env:CODEX_HOME", text)
        self.assertIn("Join-Path $HOME", text)
        self.assertIn("pip install --user", text)
        self.assertIn("runtime_bootstrap.py", text)
        self.assertIn("setup_workspace.py", text)
        self.assertIn("$PSScriptRoot", text)
        self.assertNotIn("/Users/nokiy", text)
        self.assertNotIn("Start-Process -Verb RunAs", text)

    def test_prompt_requires_platform_detection(self) -> None:
        text = PROMPT_PATH.read_text(encoding="utf-8")
        self.assertIn("自動辨識 macOS 或 Windows", text)
        self.assertIn("不得硬編碼其他作業系統的路徑或指令", text)
        self.assertIn("TWS_AI_Lab/AGENTS.md", text)
        self.assertIn("WORKSPACE_POLICY_CONFLICT", text)
        self.assertIn("不得寫入 home 根目錄或其他專案", text)


if __name__ == "__main__":
    unittest.main()
