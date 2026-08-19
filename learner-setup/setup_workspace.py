#!/usr/bin/env python3
"""Install or verify the versioned TWS AI learner workspace."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any


DEFAULT_MANIFEST = Path(__file__).with_name("workspace.manifest.json")
EXPECTED_MANIFEST_KEYS = {
    "schemaVersion",
    "name",
    "version",
    "workspaceDirectory",
    "policy",
    "courseDirectories",
    "receipt",
    "conflictPolicy",
}
EXPECTED_POLICY_KEYS = {"source", "target", "sha256"}


class WorkspaceSetupError(RuntimeError):
    def __init__(self, blocker: str, detail: str, **context: Any) -> None:
        super().__init__(detail)
        self.blocker = blocker
        self.detail = detail
        self.context = context


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_manifest(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise WorkspaceSetupError("WORKSPACE_MANIFEST_MISSING", str(path)) from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise WorkspaceSetupError("WORKSPACE_MANIFEST_INVALID", str(exc), manifest=str(path)) from exc

    if not isinstance(data, dict) or set(data) != EXPECTED_MANIFEST_KEYS:
        raise WorkspaceSetupError(
            "WORKSPACE_MANIFEST_SCHEMA",
            "manifest root keys do not match the approved schema",
            manifest=str(path),
        )
    if data["schemaVersion"] != 1 or data["conflictPolicy"] != "preserve-and-fail":
        raise WorkspaceSetupError(
            "WORKSPACE_MANIFEST_SCHEMA",
            "unsupported schemaVersion or conflictPolicy",
            manifest=str(path),
        )

    policy = data["policy"]
    directories = data["courseDirectories"]
    if not isinstance(policy, dict) or set(policy) != EXPECTED_POLICY_KEYS:
        raise WorkspaceSetupError("WORKSPACE_MANIFEST_SCHEMA", "invalid policy contract", manifest=str(path))
    if not isinstance(directories, list) or not directories or not all(isinstance(item, str) and item for item in directories):
        raise WorkspaceSetupError("WORKSPACE_MANIFEST_SCHEMA", "invalid courseDirectories", manifest=str(path))
    if len(set(directories)) != len(directories):
        raise WorkspaceSetupError("WORKSPACE_MANIFEST_SCHEMA", "duplicate courseDirectories", manifest=str(path))

    path_fields = [
        data["workspaceDirectory"],
        policy["source"],
        policy["target"],
        data["receipt"],
        *directories,
    ]
    if not all(
        isinstance(item, str)
        and item not in {"", ".", ".."}
        and "/" not in item
        and "\\" not in item
        and Path(item).name == item
        for item in path_fields
    ):
        raise WorkspaceSetupError("WORKSPACE_MANIFEST_SCHEMA", "paths must be single relative names", manifest=str(path))
    expected_digest = policy["sha256"]
    if not isinstance(expected_digest, str) or len(expected_digest) != 64 or any(char not in "0123456789abcdef" for char in expected_digest):
        raise WorkspaceSetupError("WORKSPACE_MANIFEST_SCHEMA", "policy sha256 must be lowercase hexadecimal", manifest=str(path))
    return data


def resolve_policy_source(manifest_path: Path, manifest: dict[str, Any], override: Path | None) -> tuple[Path, bytes]:
    source = override if override is not None else manifest_path.parent / manifest["policy"]["source"]
    try:
        content = source.read_bytes()
    except FileNotFoundError as exc:
        raise WorkspaceSetupError("WORKSPACE_POLICY_SOURCE_MISSING", str(source)) from exc
    except OSError as exc:
        raise WorkspaceSetupError("WORKSPACE_POLICY_SOURCE_UNREADABLE", str(exc), policy=str(source)) from exc

    actual = sha256_bytes(content)
    expected = manifest["policy"]["sha256"]
    if actual != expected:
        raise WorkspaceSetupError(
            "WORKSPACE_POLICY_SOURCE_DIGEST_MISMATCH",
            "source AGENTS.md does not match workspace manifest",
            policy=str(source),
            expectedSha256=expected,
            actualSha256=actual,
        )
    return source, content


def default_workspace(manifest: dict[str, Any]) -> Path:
    return Path.home() / manifest["workspaceDirectory"]


def atomic_write(path: Path, content: bytes) -> None:
    handle = tempfile.NamedTemporaryFile(mode="wb", dir=path.parent, prefix=f".{path.name}.", delete=False)
    temporary = Path(handle.name)
    try:
        with handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o644)
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def expected_receipt(manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        "schemaVersion": 1,
        "workspaceManifestVersion": manifest["version"],
        "policy": {
            "target": manifest["policy"]["target"],
            "sha256": manifest["policy"]["sha256"],
        },
        "courseDirectories": manifest["courseDirectories"],
    }


def validate_workspace(workspace: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    if workspace.is_symlink():
        raise WorkspaceSetupError("WORKSPACE_ROOT_SYMLINK", str(workspace))
    if not workspace.is_dir():
        raise WorkspaceSetupError("WORKSPACE_ROOT_MISSING", str(workspace))

    policy_target = workspace / manifest["policy"]["target"]
    if policy_target.is_symlink():
        raise WorkspaceSetupError("WORKSPACE_POLICY_SYMLINK", str(policy_target))
    if not policy_target.is_file():
        raise WorkspaceSetupError("WORKSPACE_POLICY_MISSING", str(policy_target))
    actual_digest = sha256_file(policy_target)
    expected_digest = manifest["policy"]["sha256"]
    if actual_digest != expected_digest:
        raise WorkspaceSetupError(
            "WORKSPACE_POLICY_DIGEST_MISMATCH",
            "installed AGENTS.md does not match workspace manifest",
            policy=str(policy_target),
            expectedSha256=expected_digest,
            actualSha256=actual_digest,
        )

    for directory_name in manifest["courseDirectories"]:
        directory = workspace / directory_name
        if directory.is_symlink() or not directory.is_dir():
            raise WorkspaceSetupError("WORKSPACE_COURSE_DIRECTORY_MISSING", str(directory))

    receipt_path = workspace / manifest["receipt"]
    if receipt_path.is_symlink():
        raise WorkspaceSetupError("WORKSPACE_RECEIPT_SYMLINK", str(receipt_path))
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise WorkspaceSetupError("WORKSPACE_RECEIPT_MISSING", str(receipt_path)) from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise WorkspaceSetupError("WORKSPACE_RECEIPT_INVALID", str(exc), receipt=str(receipt_path)) from exc
    if receipt != expected_receipt(manifest):
        raise WorkspaceSetupError("WORKSPACE_RECEIPT_MISMATCH", str(receipt_path))

    return {
        "status": "PASS",
        "mode": "check",
        "workspace": str(workspace),
        "policy": str(policy_target),
        "policySha256": actual_digest,
        "courseDirectories": manifest["courseDirectories"],
        "receipt": str(receipt_path),
    }


def install_workspace(workspace: Path, manifest: dict[str, Any], policy_content: bytes) -> dict[str, Any]:
    policy_target = workspace / manifest["policy"]["target"]
    receipt_path = workspace / manifest["receipt"]
    expected_digest = manifest["policy"]["sha256"]

    if workspace.is_symlink():
        raise WorkspaceSetupError("WORKSPACE_ROOT_SYMLINK", str(workspace))
    if workspace.exists() and not workspace.is_dir():
        raise WorkspaceSetupError("WORKSPACE_ROOT_NOT_DIRECTORY", str(workspace))
    if policy_target.is_symlink():
        raise WorkspaceSetupError("WORKSPACE_POLICY_SYMLINK", str(policy_target))

    action = "installed"
    if policy_target.exists():
        if not policy_target.is_file():
            raise WorkspaceSetupError("WORKSPACE_POLICY_NOT_FILE", str(policy_target))
        actual_digest = sha256_file(policy_target)
        if actual_digest != expected_digest:
            raise WorkspaceSetupError(
                "WORKSPACE_POLICY_CONFLICT",
                "existing AGENTS.md was preserved because its digest differs",
                policy=str(policy_target),
                expectedSha256=expected_digest,
                actualSha256=actual_digest,
            )
        action = "unchanged"

    for directory_name in manifest["courseDirectories"]:
        directory = workspace / directory_name
        if directory.is_symlink() or (directory.exists() and not directory.is_dir()):
            raise WorkspaceSetupError("WORKSPACE_COURSE_DIRECTORY_CONFLICT", str(directory))
    if receipt_path.is_symlink() or (receipt_path.exists() and not receipt_path.is_file()):
        raise WorkspaceSetupError("WORKSPACE_RECEIPT_CONFLICT", str(receipt_path))

    workspace.mkdir(parents=True, exist_ok=True)
    for directory_name in manifest["courseDirectories"]:
        directory = workspace / directory_name
        directory.mkdir(exist_ok=True)

    if action == "installed":
        atomic_write(policy_target, policy_content)
    receipt_content = (json.dumps(expected_receipt(manifest), ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    atomic_write(receipt_path, receipt_content)

    result = validate_workspace(workspace, manifest)
    result["mode"] = "install"
    result["action"] = action
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("install", "check"), nargs="?", default="install")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--policy", type=Path)
    parser.add_argument("--workspace", type=Path)
    args = parser.parse_args(argv)

    try:
        manifest_path = args.manifest.expanduser().resolve()
        manifest = load_manifest(manifest_path)
        _, policy_content = resolve_policy_source(
            manifest_path,
            manifest,
            args.policy.expanduser().resolve() if args.policy else None,
        )
        workspace = (args.workspace.expanduser() if args.workspace else default_workspace(manifest)).absolute()
        result = (
            install_workspace(workspace, manifest, policy_content)
            if args.mode == "install"
            else validate_workspace(workspace, manifest)
        )
        result["manifestVersion"] = manifest["version"]
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0
    except WorkspaceSetupError as exc:
        print(json.dumps({
            "status": "FAIL",
            "mode": args.mode,
            "blocker": exc.blocker,
            "detail": exc.detail,
            **exc.context,
        }, ensure_ascii=False, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
