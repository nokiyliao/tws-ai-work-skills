#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SETUP_PATH = ROOT / "learner-setup/setup_workspace.py"
MANIFEST_PATH = ROOT / "learner-setup/workspace.manifest.json"
POLICY_PATH = ROOT / "learner-setup/AGENTS.md"
ROOT_MANIFEST_PATH = ROOT / "manifest.json"


def load_setup():
    spec = importlib.util.spec_from_file_location("tws_workspace_setup_test", SETUP_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


SETUP = load_setup()


class LearnerWorkspaceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.workspace = Path(self.temporary.name) / "TWS_AI_Lab"
        self.manifest = SETUP.load_manifest(MANIFEST_PATH)
        _, self.policy_content = SETUP.resolve_policy_source(MANIFEST_PATH, self.manifest, None)

    def test_published_policy_matches_manifest_digest(self) -> None:
        self.assertEqual(self.manifest["policy"]["sha256"], SETUP.sha256_file(POLICY_PATH))
        self.assertEqual("preserve-and-fail", self.manifest["conflictPolicy"])
        self.assertEqual("desktop", self.manifest["workspaceLocation"])
        self.assertNotIn("courseDirectories", self.manifest)

    def test_default_workspace_uses_current_macos_desktop(self) -> None:
        self.assertEqual(
            Path("/Users/student/Desktop/TWS_AI_Lab"),
            SETUP.default_workspace(
                self.manifest,
                home=Path("/Users/student"),
                platform="darwin",
            ),
        )

    def test_default_workspace_uses_redirected_windows_known_folder(self) -> None:
        desktop = Path("C:/Users/student/OneDrive/Desktop")
        with mock.patch.object(SETUP, "windows_desktop_directory", return_value=desktop):
            self.assertEqual(
                desktop / "TWS_AI_Lab",
                SETUP.default_workspace(self.manifest, platform="win32"),
            )

    def test_install_creates_only_policy_and_receipt(self) -> None:
        result = SETUP.install_workspace(self.workspace, self.manifest, self.policy_content)

        self.assertEqual("PASS", result["status"])
        self.assertEqual("installed", result["action"])
        self.assertEqual(self.policy_content, (self.workspace / "AGENTS.md").read_bytes())
        receipt = json.loads((self.workspace / self.manifest["receipt"]).read_text(encoding="utf-8"))
        self.assertEqual(SETUP.expected_receipt(self.manifest), receipt)
        self.assertEqual("desktop", receipt["workspaceLocation"])
        self.assertEqual({"AGENTS.md", self.manifest["receipt"]}, {path.name for path in self.workspace.iterdir()})

    def test_repeated_install_is_idempotent(self) -> None:
        SETUP.install_workspace(self.workspace, self.manifest, self.policy_content)
        result = SETUP.install_workspace(self.workspace, self.manifest, self.policy_content)

        self.assertEqual("unchanged", result["action"])
        self.assertEqual(self.manifest["policy"]["sha256"], result["policySha256"])

    def test_different_existing_policy_is_preserved_and_blocks_install(self) -> None:
        self.workspace.mkdir()
        policy = self.workspace / "AGENTS.md"
        original = b"# learner-owned policy\n"
        policy.write_bytes(original)

        with self.assertRaises(SETUP.WorkspaceSetupError) as raised:
            SETUP.install_workspace(self.workspace, self.manifest, self.policy_content)

        self.assertEqual("WORKSPACE_POLICY_CONFLICT", raised.exception.blocker)
        self.assertEqual(original, policy.read_bytes())
        self.assertFalse((self.workspace / self.manifest["receipt"]).exists())

    def test_check_detects_policy_tampering(self) -> None:
        SETUP.install_workspace(self.workspace, self.manifest, self.policy_content)
        (self.workspace / "AGENTS.md").write_text("changed\n", encoding="utf-8")

        with self.assertRaises(SETUP.WorkspaceSetupError) as raised:
            SETUP.validate_workspace(self.workspace, self.manifest)

        self.assertEqual("WORKSPACE_POLICY_DIGEST_MISMATCH", raised.exception.blocker)

    def test_root_manifest_points_to_workspace_contract(self) -> None:
        root_manifest = json.loads(ROOT_MANIFEST_PATH.read_text(encoding="utf-8"))
        contract = root_manifest["learnerWorkspace"]
        self.assertEqual("learner-setup/workspace.manifest.json", contract["manifest"])
        self.assertEqual("learner-setup/AGENTS.md", contract["policy"])
        self.assertEqual("learner-setup/setup_workspace.py", contract["installer"])
        self.assertEqual("TWS_AI_Lab", contract["scope"])
        self.assertEqual("desktop", contract["location"])

    def test_legacy_home_workspace_is_preserved_and_blocks_duplicate(self) -> None:
        home = Path(self.temporary.name) / "student"
        legacy = home / "TWS_AI_Lab"
        target = home / "Desktop" / "TWS_AI_Lab"
        legacy.mkdir(parents=True)

        with self.assertRaises(SETUP.WorkspaceSetupError) as raised:
            SETUP.guard_legacy_workspace(target, self.manifest, home=home)

        self.assertEqual("WORKSPACE_LEGACY_LOCATION_PRESENT", raised.exception.blocker)
        self.assertTrue(legacy.is_dir())
        self.assertFalse(target.exists())

    def test_manifest_rejects_cross_platform_path_traversal(self) -> None:
        bad_manifest = dict(self.manifest)
        bad_manifest["workspaceDirectory"] = ".."
        path = Path(self.temporary.name) / "bad-workspace.manifest.json"
        path.write_text(json.dumps(bad_manifest), encoding="utf-8")

        with self.assertRaises(SETUP.WorkspaceSetupError) as raised:
            SETUP.load_manifest(path)

        self.assertEqual("WORKSPACE_MANIFEST_SCHEMA", raised.exception.blocker)


if __name__ == "__main__":
    unittest.main()
