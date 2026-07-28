#!/usr/bin/env python3
"""Track and validate Nokiy deck pipeline phase evidence."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


PHASES = (
    "source",
    "outline",
    "copy",
    "sample",
    "build",
    "visual_qa",
    "mechanical_qa",
    "pdf",
)
STATUSES = ("pending", "pass", "fail", "skipped")
PREREQUISITES = {
    "outline": ("source",),
    "copy": ("outline",),
    "sample": ("copy",),
    "build": ("copy", "sample"),
    "visual_qa": ("build",),
    "mechanical_qa": ("visual_qa",),
    "pdf": ("mechanical_qa",),
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def state_path(run_dir: str) -> Path:
    return Path(run_dir).expanduser().resolve() / "deck_pipeline_state.json"


def load(run_dir: str) -> tuple[Path, dict]:
    path = state_path(run_dir)
    if not path.exists():
        raise SystemExit(f"state file not found: {path}")
    return path, json.loads(path.read_text(encoding="utf-8"))


def save(path: Path, state: dict) -> None:
    state["updated_at"] = now()
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def phase_ok(state: dict, phase: str) -> bool:
    status = state["phases"][phase]["status"]
    if status == "pass":
        return True
    if status == "skipped" and phase in {"sample", "pdf"}:
        return True
    return False


def cmd_init(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir).expanduser().resolve()
    run_dir.mkdir(parents=True, exist_ok=True)
    path = state_path(str(run_dir))
    if path.exists() and not args.force:
        raise SystemExit(f"state file already exists: {path}")
    sample_status = "skipped" if args.mode == "revision" else "pending"
    pdf_status = "pending" if args.pdf_requested else "skipped"
    state = {
        "schema_version": 1,
        "mode": args.mode,
        "sources": [str(Path(p).expanduser().resolve()) for p in args.source],
        "pdf_requested": bool(args.pdf_requested),
        "created_at": now(),
        "updated_at": now(),
        "phases": {
            phase: {
                "status": sample_status if phase == "sample" else pdf_status if phase == "pdf" else "pending",
                "evidence": [],
                "note": "existing deck is the visual reference" if phase == "sample" and sample_status == "skipped" else "",
                "updated_at": now(),
            }
            for phase in PHASES
        },
    }
    save(path, state)
    print(path)
    return 0


def cmd_set(args: argparse.Namespace) -> int:
    path, state = load(args.run_dir)
    if args.status in {"pass", "skipped"}:
        for prerequisite in PREREQUISITES.get(args.phase, ()):
            if not phase_ok(state, prerequisite):
                raise SystemExit(
                    f"cannot set {args.phase}={args.status}; prerequisite {prerequisite} is "
                    f"{state['phases'][prerequisite]['status']}"
                )
    evidence = [str(Path(p).expanduser().resolve()) for p in args.evidence]
    if args.status == "pass":
        if not evidence:
            raise SystemExit("pass status requires at least one --evidence path")
        missing = [p for p in evidence if not Path(p).exists()]
        if missing:
            raise SystemExit("missing evidence: " + ", ".join(missing))
    phase = state["phases"][args.phase]
    phase.update({"status": args.status, "evidence": evidence, "note": args.note or "", "updated_at": now()})
    save(path, state)
    print(f"{args.phase}: {args.status}")
    return 0


def completion_errors(state: dict) -> list[str]:
    errors = []
    for phase in ("source", "outline", "copy", "build", "visual_qa", "mechanical_qa"):
        if state["phases"][phase]["status"] != "pass":
            errors.append(f"{phase}={state['phases'][phase]['status']}")
    if not phase_ok(state, "sample"):
        errors.append(f"sample={state['phases']['sample']['status']}")
    pdf_status = state["phases"]["pdf"]["status"]
    expected_pdf = "pass" if state.get("pdf_requested") else "skipped"
    if pdf_status != expected_pdf:
        errors.append(f"pdf={pdf_status}, expected {expected_pdf}")
    return errors


def cmd_check(args: argparse.Namespace) -> int:
    _, state = load(args.run_dir)
    errors = completion_errors(state)
    if errors:
        print("FAIL: " + "; ".join(errors))
        return 1
    print("PASS")
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    path, state = load(args.run_dir)
    print(f"state: {path}")
    print(f"mode: {state['mode']}")
    for phase in PHASES:
        item = state["phases"][phase]
        print(f"{phase:14} {item['status']:8} evidence={len(item['evidence'])}")
    return 0


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    commands = root.add_subparsers(dest="command", required=True)

    init = commands.add_parser("init")
    init.add_argument("--run-dir", required=True)
    init.add_argument("--mode", choices=("editable", "image", "revision"), default="editable")
    init.add_argument("--source", action="append", default=[])
    init.add_argument("--pdf-requested", action="store_true")
    init.add_argument("--force", action="store_true")
    init.set_defaults(func=cmd_init)

    set_phase = commands.add_parser("set")
    set_phase.add_argument("--run-dir", required=True)
    set_phase.add_argument("--phase", choices=PHASES, required=True)
    set_phase.add_argument("--status", choices=STATUSES, required=True)
    set_phase.add_argument("--evidence", action="append", default=[])
    set_phase.add_argument("--note")
    set_phase.set_defaults(func=cmd_set)

    check = commands.add_parser("check")
    check.add_argument("--run-dir", required=True)
    check.set_defaults(func=cmd_check)

    show = commands.add_parser("show")
    show.add_argument("--run-dir", required=True)
    show.set_defaults(func=cmd_show)
    return root


def main() -> int:
    args = parser().parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

