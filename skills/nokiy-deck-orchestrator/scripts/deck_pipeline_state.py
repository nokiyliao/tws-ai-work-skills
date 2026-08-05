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
    "case_lock",
    "proposal",
    "outline",
    "copy",
    "asset_selection",
    "asset_verification",
    "sample",
    "build",
    "visual_qa",
    "mechanical_qa",
    "pdf",
    "deploy",
    "register",
    "readback",
)
STATUSES = ("pending", "pass", "fail", "skipped")
PREREQUISITES = {
    "case_lock": ("source",),
    "proposal": ("case_lock",),
    "outline": ("proposal",),
    "copy": ("outline",),
    "asset_selection": ("copy",),
    "asset_verification": ("asset_selection",),
    "sample": ("copy", "asset_verification"),
    "build": ("copy", "asset_verification", "sample"),
    "visual_qa": ("build",),
    "mechanical_qa": ("visual_qa",),
    "pdf": ("mechanical_qa",),
    "deploy": ("mechanical_qa",),
    "register": ("deploy",),
    "readback": ("register",),
}
ENTRY_SKILL = "nokiy-deck-orchestrator"
ROUTABLE_PHASES = ("proposal", "copy", "sample", "build", "visual_qa", "mechanical_qa")


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


def validate_tws_input(path: Path, lead_id: str, customer_name: str, mode: str) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"invalid input.json: {exc}") from exc
    required = {
        "schema_version", "job_id", "lead_id", "company_name", "location",
        "permit", "building_use", "floor_area_m2", "source_snapshot",
        "deck_mode", "asset_catalog", "output_filename", "created_at",
    }
    missing = sorted(required - data.keys())
    if missing:
        raise SystemExit("input.json missing required fields: " + ", ".join(missing))
    if data["schema_version"] != "tws-presentation-input-v1":
        raise SystemExit("input.json schema_version must be tws-presentation-input-v1")
    if data["lead_id"] != lead_id:
        raise SystemExit(f"lead_id mismatch: argument={lead_id}, input={data['lead_id']}")
    if data["company_name"] != customer_name:
        raise SystemExit("customer_name mismatch between argument and input.json")
    if data["deck_mode"] != mode:
        raise SystemExit(f"deck_mode mismatch: argument={mode}, input={data['deck_mode']}")
    if not str(data["output_filename"]).lower().endswith(".pptx"):
        raise SystemExit("output_filename must end with .pptx")
    catalog = Path(data["asset_catalog"]).expanduser()
    snapshot = Path(data["source_snapshot"]).expanduser()
    if not catalog.is_file():
        raise SystemExit(f"asset catalog not found: {catalog}")
    if not snapshot.exists():
        raise SystemExit(f"source snapshot not found: {snapshot}")
    return data


def phase_ok(state: dict, phase: str) -> bool:
    status = state["phases"][phase]["status"]
    if status == "pass":
        return True
    if status == "skipped" and phase in {
        "case_lock", "proposal", "asset_selection", "asset_verification",
        "sample", "pdf", "deploy", "register", "readback",
    }:
        return True
    return False


def delegation_errors(state: dict, phase: str) -> list[str]:
    """Validate that an internal presentation skill has an orchestrator handoff."""
    errors: list[str] = []
    if state.get("schema_version") != 3:
        errors.append("state schema_version must be 3; reinitialize with the current orchestrator")
    routing = state.get("routing") or {}
    if routing.get("entry_skill") != ENTRY_SKILL:
        errors.append(f"routing.entry_skill must be {ENTRY_SKILL}")
    if phase not in ROUTABLE_PHASES:
        errors.append(f"phase is not delegatable: {phase}")
        return errors
    phases = state.get("phases") or {}
    if phase not in phases:
        errors.append(f"state has no phase: {phase}")
        return errors
    for prerequisite in PREREQUISITES.get(phase, ()):
        if prerequisite not in phases or not phase_ok(state, prerequisite):
            status = phases.get(prerequisite, {}).get("status", "missing")
            errors.append(f"prerequisite {prerequisite} is {status}")
    if phases[phase].get("status") not in {"pending", "fail"}:
        errors.append(f"phase {phase} is {phases[phase].get('status')}; no new delegation is open")
    return errors


def cmd_init(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir).expanduser().resolve()
    run_dir.mkdir(parents=True, exist_ok=True)
    path = state_path(str(run_dir))
    if path.exists() and not args.force:
        raise SystemExit(f"state file already exists: {path}")
    tws = args.workflow == "tws-new-factory"
    if tws and (not args.lead_id or not args.customer_name or not args.input):
        raise SystemExit("tws-new-factory requires --lead-id, --customer-name, and --input")
    input_path = Path(args.input).expanduser().resolve() if args.input else None
    if input_path and not input_path.exists():
        raise SystemExit(f"input file not found: {input_path}")
    input_data = validate_tws_input(input_path, args.lead_id, args.customer_name, args.mode) if tws else {}
    sample_status = "skipped" if args.mode == "revision" else "pending"
    pdf_status = "pending" if args.pdf_requested else "skipped"
    tws_only = {"case_lock", "proposal", "asset_selection", "asset_verification", "deploy", "register", "readback"}
    state = {
        "schema_version": 3,
        "routing": {
            "entry_skill": ENTRY_SKILL,
            "contract": "tws_deck_routing_v1",
        },
        "workflow": args.workflow,
        "mode": args.mode,
        "job_id": args.job_id or input_data.get("job_id") or run_dir.name,
        "lead_id": args.lead_id or "",
        "customer_name": args.customer_name or "",
        "input": str(input_path) if input_path else "",
        "sources": [str(Path(p).expanduser().resolve()) for p in args.source],
        "pdf_requested": bool(args.pdf_requested),
        "created_at": now(),
        "updated_at": now(),
        "phases": {
            phase: {
                "status": (
                    "skipped" if phase in tws_only and not tws else
                    sample_status if phase == "sample" else
                    pdf_status if phase == "pdf" else
                    "pending"
                ),
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


def completion_errors(state: dict, target: str) -> list[str]:
    errors = []
    required = ["source", "outline", "copy", "build", "visual_qa", "mechanical_qa"]
    if state.get("workflow") == "tws-new-factory":
        required += ["case_lock", "proposal", "asset_selection", "asset_verification"]
        if target == "publish":
            required += ["deploy", "register", "readback"]
    for phase in required:
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
    errors = completion_errors(state, args.target)
    if errors:
        print("FAIL: " + "; ".join(errors))
        return 1
    print("PASS")
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    path, state = load(args.run_dir)
    print(f"state: {path}")
    print(f"mode: {state['mode']}")
    print(f"workflow: {state.get('workflow', 'general')}")
    if state.get("lead_id"):
        print(f"case: {state['lead_id']} | {state.get('customer_name', '')}")
    for phase in PHASES:
        item = state["phases"][phase]
        print(f"{phase:14} {item['status']:8} evidence={len(item['evidence'])}")
    return 0


def cmd_route(args: argparse.Namespace) -> int:
    path, state = load(args.run_dir)
    errors = delegation_errors(state, args.phase)
    report = {
        "status": "FAIL" if errors else "PASS",
        "entry_skill": (state.get("routing") or {}).get("entry_skill"),
        "phase": args.phase,
        "state": str(path),
        "errors": errors,
    }
    print(json.dumps(report, ensure_ascii=True, indent=2))
    return 1 if errors else 0


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    commands = root.add_subparsers(dest="command", required=True)

    init = commands.add_parser("init")
    init.add_argument("--run-dir", required=True)
    init.add_argument("--mode", choices=("editable", "image", "revision"), default="editable")
    init.add_argument("--workflow", choices=("general", "tws-new-factory"), default="general")
    init.add_argument("--job-id")
    init.add_argument("--lead-id")
    init.add_argument("--customer-name")
    init.add_argument("--input")
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
    check.add_argument("--target", choices=("build", "publish"), default="build")
    check.set_defaults(func=cmd_check)

    show = commands.add_parser("show")
    show.add_argument("--run-dir", required=True)
    show.set_defaults(func=cmd_show)

    route = commands.add_parser("route", help="verify orchestrator delegation before an internal skill runs")
    route.add_argument("--run-dir", required=True)
    route.add_argument("--phase", choices=ROUTABLE_PHASES, required=True)
    route.set_defaults(func=cmd_route)
    return root


def main() -> int:
    args = parser().parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
