#!/usr/bin/env python3
from __future__ import annotations
"""Recover image generation PNGs from Codex session JSONL records.

Use this when Image 2.0 displayed an image in chat but no PNG appeared under
~/.codex/generated_images. The session log stores the PNG as base64 in
image_generation_end.payload.result.
"""

import argparse
import base64
import hashlib
import json
import struct
import sys
from pathlib import Path
from typing import Optional


def default_codex_home() -> Path:
    return Path.home() / ".codex"


def latest_session(codex_home: Path) -> Path:
    sessions_root = codex_home / "sessions"
    candidates = sorted(sessions_root.glob("**/*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not candidates:
        raise SystemExit(f"no session JSONL files found under {sessions_root}")
    return candidates[0]


def safe_name(value: str) -> str:
    return (
        value.replace(":", "")
        .replace("-", "")
        .replace(".", "_")
        .replace("/", "_")
        .replace("\\", "_")
    )


def png_dimensions(path: Path) -> tuple[int | None, int | None]:
    data = path.read_bytes()[:24]
    if len(data) >= 24 and data[:8] == b"\x89PNG\r\n\x1a\n" and data[12:16] == b"IHDR":
        return struct.unpack(">II", data[16:24])
    return None, None


def extract(session: Path, out_dir: Path, limit_last: Optional[int] = None,
            prompt_contains: Optional[str] = None, call_id: Optional[str] = None):
    rows = []
    with session.open("r", encoding="utf-8") as f:
        for line in f:
            if '"image_generation_end"' not in line or '"result"' not in line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            payload = obj.get("payload", {})
            result = payload.get("result")
            if not result:
                continue
            prompt = payload.get("revised_prompt", "")
            candidate_call_id = payload.get("call_id", "image")
            if prompt_contains and prompt_contains.lower() not in prompt.lower():
                continue
            if call_id and call_id != candidate_call_id:
                continue
            rows.append(
                {
                    "timestamp": obj.get("timestamp", ""),
                    "call_id": candidate_call_id,
                    "status": payload.get("status", ""),
                    "prompt": prompt,
                    "result": result,
                }
            )

    if limit_last:
        rows = rows[-limit_last:]

    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = []
    for i, row in enumerate(rows, 1):
        name = f"{i:03d}_{safe_name(row['timestamp'])}_{safe_name(row['call_id'])}.png"
        path = out_dir / name
        encoded = row["result"]
        if isinstance(encoded, str) and encoded.startswith("data:") and "," in encoded:
            encoded = encoded.split(",", 1)[1]
        path.write_bytes(base64.b64decode(encoded))
        width, height = png_dimensions(path)
        if width is None or height is None:
            raise SystemExit(f"recovered result is not a valid PNG: {path}")
        manifest.append(
            {k: v for k, v in row.items() if k != "result"} |
            {
                "file": str(path),
                "session_path": str(session),
                "sha1": hashlib.sha1(path.read_bytes()).hexdigest(),
                "width": width,
                "height": height,
            }
        )

    (out_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--session", type=Path, help="Codex session JSONL. Defaults to newest under ~/.codex/sessions.")
    parser.add_argument("--out", type=Path, required=True, help="Folder where recovered PNGs and manifest.json will be written.")
    parser.add_argument("--limit-last", type=int, help="Only write the last N image generation outputs.")
    parser.add_argument("--prompt-contains", help="Only recover outputs whose revised prompt contains this text.")
    parser.add_argument("--call-id", help="Only recover outputs with this image-generation call id.")
    args = parser.parse_args()

    codex_home = default_codex_home()
    if args.session:
        session = args.session
    else:
        session = latest_session(codex_home)
        print("warning: using the newest session JSONL; pass --session to avoid cross-thread recovery", file=sys.stderr)
    manifest = extract(session, args.out, args.limit_last, args.prompt_contains, args.call_id)
    print(f"session: {session}")
    print(f"recovered: {len(manifest)} image(s)")
    for item in manifest[-10:]:
        print(item["file"])


if __name__ == "__main__":
    main()
