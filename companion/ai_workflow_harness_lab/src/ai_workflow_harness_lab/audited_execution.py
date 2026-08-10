from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any


MANIFEST_SCHEMA = "playbook.audited_run_manifest.v1"
STATE_SCHEMA = "playbook.audited_state.v1"
ROUND_CONTRACT_SCHEMA = "playbook.audited_round_contract.v1"
EXECUTOR_REPORT_SCHEMA = "playbook.audited_executor_report.v1"
AUDIT_REPORT_SCHEMA = "playbook.audited_audit_report.v1"
RUN_RESULT_SCHEMA = "playbook.audited_run_result.v1"


class AuditedExecutionError(ValueError):
    pass


def now_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        tmp = handle.name
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
    os.replace(tmp, path)


def safe_child_path(base: Path, raw: str) -> Path:
    clean = raw.strip().strip("`")
    if not clean:
        raise AuditedExecutionError("empty path is not allowed")
    path = Path(clean)
    if path.is_absolute() or ".." in path.parts:
        raise AuditedExecutionError(f"path must stay inside audited run: {raw}")
    resolved = (base / path).resolve()
    try:
        resolved.relative_to(base.resolve())
    except ValueError as exc:
        raise AuditedExecutionError(f"path must stay inside audited run: {raw}") from exc
    return resolved


def run_dir(root: Path, run_id: str) -> Path:
    return root / ".playbook-artifacts/audited-runs" / run_id


def state_path(base: Path) -> Path:
    return base / "audited_state.json"


def manifest_path(base: Path) -> Path:
    return base / "manifest.json"


def result_path(base: Path) -> Path:
    return base / "result.json"


def round_dir(base: Path, round_number: int) -> Path:
    return base / "rounds" / f"{round_number:04d}"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def default_budgets(max_rounds: int) -> dict[str, Any]:
    return {
        "max_rounds": max_rounds,
        "max_wall_clock_seconds": 3600,
        "max_repeated_failure_count": 2,
        "max_no_progress_rounds": 2,
        "max_tool_calls_per_round": 40,
        "max_total_cost_usd": "unknown",
        "human_escalation_policy": "stop_and_request_human_input",
    }


def init_run(
    *,
    root: Path,
    run_id: str,
    original_goal_ref: str,
    requirements: list[dict[str, Any]],
    task_id: str = "",
    feature_id: str = "",
    slice_id: str = "",
    max_rounds: int = 3,
    budgets: dict[str, Any] | None = None,
) -> dict[str, Any]:
    base = run_dir(root, run_id)
    if base.exists():
        raise AuditedExecutionError(f"audited run already exists: {run_id}")
    budget_payload = {**default_budgets(max_rounds), **(budgets or {})}
    manifest = {
        "schema_version": MANIFEST_SCHEMA,
        "run_id": run_id,
        "execution_profile": "audited_rounds",
        "task_id": task_id,
        "feature_id": feature_id,
        "slice_id": slice_id,
        "original_goal_ref": original_goal_ref,
        **budget_payload,
        "created_at": now_utc(),
        "status": "active",
    }
    state_requirements = [
        {
            "id": str(item["id"]),
            "description": str(item.get("description", item["id"])),
            "status": "open",
            "evidence_refs": [],
        }
        for item in requirements
    ]
    state = {
        "schema_version": STATE_SCHEMA,
        "run_id": run_id,
        "original_goal_ref": original_goal_ref,
        "requirements": state_requirements,
        "facts": [],
        "blockers": [],
        "verified_artifacts": [],
        "open_requirements": [item["id"] for item in state_requirements],
        "audit_refs": [],
        "round_counters": {
            "completed_rounds": 0,
            "next_round": 1,
            "consecutive_failures": 0,
            "consecutive_no_progress": 0,
        },
        "budgets": budget_payload,
        "status": "active",
    }
    result = {
        "schema_version": RUN_RESULT_SCHEMA,
        "run_id": run_id,
        "status": "active",
        "stop_reason": None,
        "generated_at": now_utc(),
    }
    atomic_write_json(manifest_path(base), manifest)
    atomic_write_json(state_path(base), state)
    atomic_write_json(result_path(base), result)
    return manifest


def load_state(base: Path) -> dict[str, Any]:
    state = read_json(state_path(base))
    if state.get("schema_version") != STATE_SCHEMA:
        raise AuditedExecutionError("audited_state.json has unsupported schema_version")
    return state


def load_manifest(base: Path) -> dict[str, Any]:
    manifest = read_json(manifest_path(base))
    if manifest.get("schema_version") != MANIFEST_SCHEMA:
        raise AuditedExecutionError("manifest.json has unsupported schema_version")
    return manifest


def write_result(base: Path, status: str, stop_reason: str | None) -> None:
    manifest = load_manifest(base)
    result = {
        "schema_version": RUN_RESULT_SCHEMA,
        "run_id": manifest["run_id"],
        "status": status,
        "stop_reason": stop_reason,
        "generated_at": now_utc(),
    }
    atomic_write_json(result_path(base), result)


def all_requirements_verified(state: dict[str, Any]) -> bool:
    return all(item.get("status") == "verified" for item in state.get("requirements", []))


def stop_run(base: Path, reason: str) -> dict[str, Any]:
    state = load_state(base)
    state["status"] = "stopped"
    state["stop_reason"] = reason
    atomic_write_json(state_path(base), state)
    write_result(base, "stopped", reason)
    return state


def propose_next_round(
    *,
    root: Path,
    run_id: str,
    action: str = "execute",
    acceptance_requirement_ids: list[str] | None = None,
    allowed_files: list[str] | None = None,
    verification: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    base = run_dir(root, run_id)
    manifest = load_manifest(base)
    state = load_state(base)
    counters = state["round_counters"]
    if counters["next_round"] > int(manifest["max_rounds"]):
        stop_run(base, "budget_exhausted")
        raise AuditedExecutionError("max_rounds exhausted")
    if action == "done" and not all_requirements_verified(state):
        raise AuditedExecutionError("done is blocked until all requirements are verified")
    round_number = int(counters["next_round"])
    rdir = round_dir(base, round_number)
    proposal = {
        "schema_version": "playbook.audited_manager_proposal.v1",
        "run_id": run_id,
        "round": round_number,
        "action": action,
        "proposed_at": now_utc(),
        "state_ref": "audited_state.json",
    }
    contract = {
        "schema_version": ROUND_CONTRACT_SCHEMA,
        "run_id": run_id,
        "round": round_number,
        "action": action,
        "original_goal_ref": manifest["original_goal_ref"],
        "acceptance_requirement_ids": acceptance_requirement_ids or list(state.get("open_requirements", [])),
        "allowed_files": allowed_files or [],
        "verification": verification or [],
        "permissions": {
            "executor_can_write": True,
            "auditor_can_write": False,
        },
        "budget": {
            "max_tool_calls": manifest["max_tool_calls_per_round"],
        },
    }
    atomic_write_json(rdir / "manager_proposal.json", proposal)
    atomic_write_json(rdir / "round_contract.json", contract)
    return contract


def executor_prompt(root: Path, run_id: str, round_number: int) -> str:
    base = run_dir(root, run_id)
    state = load_state(base)
    contract = read_json(round_dir(base, round_number) / "round_contract.json")
    prompt = "\n".join(
        [
            f"# Audited Executor Round {round_number}",
            "",
            f"Original goal ref: {contract['original_goal_ref']}",
            "",
            "## Current Audited State",
            "",
            "```json",
            json.dumps(state, indent=2, sort_keys=True),
            "```",
            "",
            "## Current Round Contract",
            "",
            "```json",
            json.dumps(contract, indent=2, sort_keys=True),
            "```",
            "",
            "Return an executor report. All claims are unverified until audited.",
        ]
    )
    output = round_dir(base, round_number) / "executor_prompt.md"
    output.write_text(prompt + "\n", encoding="utf-8")
    return prompt


def audit_prompt(root: Path, run_id: str, round_number: int) -> str:
    base = run_dir(root, run_id)
    state = load_state(base)
    contract = read_json(round_dir(base, round_number) / "round_contract.json")
    executor_report = round_dir(base, round_number) / "executor_report.json"
    prompt = "\n".join(
        [
            f"# Audited Read-Only Audit Round {round_number}",
            "",
            "READ-ONLY: inspect environment state and receipts only. Do not modify files.",
            "",
            "## Audited State",
            "",
            "```json",
            json.dumps(state, indent=2, sort_keys=True),
            "```",
            "",
            "## Round Contract",
            "",
            "```json",
            json.dumps(contract, indent=2, sort_keys=True),
            "```",
            "",
            "## Executor Report Ref",
            "",
            str(executor_report.relative_to(base)),
        ]
    )
    output = round_dir(base, round_number) / "audit_prompt.md"
    output.write_text(prompt + "\n", encoding="utf-8")
    return prompt


def validate_receipts(base: Path, audit: dict[str, Any]) -> None:
    for receipt in audit.get("receipts", []):
        if not isinstance(receipt, dict):
            raise AuditedExecutionError("audit receipt entry must be an object")
        ref = str(receipt.get("ref", "")).strip()
        path = safe_child_path(base, ref)
        if not path.exists():
            raise AuditedExecutionError(f"audit receipt missing: {ref}")
        expected = str(receipt.get("sha256", "")).strip()
        if expected != sha256_file(path):
            raise AuditedExecutionError(f"audit receipt hash mismatch: {ref}")


def apply_audit(root: Path, run_id: str, round_number: int) -> dict[str, Any]:
    base = run_dir(root, run_id)
    state = load_state(base)
    manifest = load_manifest(base)
    rdir = round_dir(base, round_number)
    audit_path = rdir / "audit_report.json"
    if not audit_path.exists():
        raise AuditedExecutionError("audit_report.json is missing")
    audit = read_json(audit_path)
    if audit.get("schema_version") != AUDIT_REPORT_SCHEMA:
        raise AuditedExecutionError("audit report has unsupported schema_version")
    if audit.get("read_only") is not True:
        raise AuditedExecutionError("audit report must declare read_only=true")
    validate_receipts(base, audit)
    verdict = str(audit.get("verdict", "")).strip()
    if verdict not in {"verified", "rejected", "no_progress", "policy_violation", "human_input_required"}:
        raise AuditedExecutionError(f"unsupported audit verdict: {verdict}")
    if audit.get("manager_action") == "done" and verdict != "verified":
        raise AuditedExecutionError("done requires verified audit")
    requirements_by_id = {item["id"]: item for item in state.get("requirements", [])}
    if verdict == "verified":
        for result in audit.get("requirement_results", []):
            if not isinstance(result, dict) or result.get("status") != "verified":
                continue
            req = requirements_by_id.get(str(result.get("id", "")))
            if req is None:
                raise AuditedExecutionError(f"audit references unknown requirement: {result.get('id')}")
            req["status"] = "verified"
            req["evidence_refs"] = list(result.get("evidence_refs", [])) or [str(audit_path.relative_to(base))]
        state["facts"].extend(audit.get("facts", []))
        state["round_counters"]["consecutive_failures"] = 0
        state["round_counters"]["consecutive_no_progress"] = 0
    elif verdict == "no_progress":
        state["round_counters"]["consecutive_no_progress"] += 1
        state["round_counters"]["consecutive_failures"] = 0
    else:
        state["round_counters"]["consecutive_failures"] += 1
    state["audit_refs"].append(str(audit_path.relative_to(base)))
    state["round_counters"]["completed_rounds"] = max(int(state["round_counters"]["completed_rounds"]), round_number)
    state["round_counters"]["next_round"] = round_number + 1
    state["open_requirements"] = [item["id"] for item in state.get("requirements", []) if item.get("status") != "verified"]
    if audit.get("manager_action") == "done" and state["open_requirements"]:
        raise AuditedExecutionError("done is blocked until all requirements are verified")
    if all_requirements_verified(state):
        state["status"] = "complete"
        write_result(base, "complete", "all_requirements_verified")
    elif state["round_counters"]["next_round"] > int(manifest["max_rounds"]):
        state["status"] = "stopped"
        state["stop_reason"] = "budget_exhausted"
        write_result(base, "stopped", "budget_exhausted")
    elif state["round_counters"]["consecutive_no_progress"] >= int(manifest["max_no_progress_rounds"]):
        state["status"] = "stopped"
        state["stop_reason"] = "no_progress"
        write_result(base, "stopped", "no_progress")
    elif state["round_counters"]["consecutive_failures"] >= int(manifest["max_repeated_failure_count"]):
        state["status"] = "stopped"
        state["stop_reason"] = "repeated_failure"
        write_result(base, "stopped", "repeated_failure")
    atomic_write_json(state_path(base), state)
    return state


def build_audited_parser(sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    audited = sub.add_parser("audited-run")
    audited_sub = audited.add_subparsers(dest="audited_command", required=True)
    init = audited_sub.add_parser("init")
    init.add_argument("--root", type=Path, default=Path("."))
    init.add_argument("--run-id", required=True)
    init.add_argument("--goal-ref", required=True)
    init.add_argument("--requirement", action="append", required=True)
    init.add_argument("--task", default="")
    init.add_argument("--feature-id", default="")
    init.add_argument("--slice-id", default="")
    init.add_argument("--max-rounds", type=int, default=3)
    next_cmd = audited_sub.add_parser("next")
    next_cmd.add_argument("--root", type=Path, default=Path("."))
    next_cmd.add_argument("--run-id", required=True)
    next_cmd.add_argument("--action", choices=("execute", "done", "blocked", "ask"), default="execute")
    ep = audited_sub.add_parser("executor-prompt")
    ep.add_argument("--root", type=Path, default=Path("."))
    ep.add_argument("--run-id", required=True)
    ep.add_argument("--round", type=int, required=True)
    ap = audited_sub.add_parser("audit-prompt")
    ap.add_argument("--root", type=Path, default=Path("."))
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--round", type=int, required=True)
    apply = audited_sub.add_parser("apply-audit")
    apply.add_argument("--root", type=Path, default=Path("."))
    apply.add_argument("--run-id", required=True)
    apply.add_argument("--round", type=int, required=True)
    status = audited_sub.add_parser("status")
    status.add_argument("--root", type=Path, default=Path("."))
    status.add_argument("--run-id", required=True)
    stop = audited_sub.add_parser("stop")
    stop.add_argument("--root", type=Path, default=Path("."))
    stop.add_argument("--run-id", required=True)
    stop.add_argument("--reason", required=True)


def handle_audited_command(args: argparse.Namespace) -> int:
    root = args.root.resolve()
    if args.audited_command == "init":
        requirements = [{"id": item.split(":", 1)[0], "description": item.split(":", 1)[1] if ":" in item else item} for item in args.requirement]
        manifest = init_run(
            root=root,
            run_id=args.run_id,
            original_goal_ref=args.goal_ref,
            requirements=requirements,
            task_id=args.task,
            feature_id=args.feature_id,
            slice_id=args.slice_id,
            max_rounds=args.max_rounds,
        )
        print(json.dumps({"manifest": str(manifest_path(run_dir(root, args.run_id)).relative_to(root)), "status": manifest["status"]}, indent=2))
        return 0
    if args.audited_command == "next":
        try:
            contract = propose_next_round(root=root, run_id=args.run_id, action=args.action)
        except AuditedExecutionError as exc:
            print(f"audited-run next: {exc}", file=sys.stderr)
            return 1
        print(json.dumps({"round": contract["round"], "contract": str((round_dir(run_dir(root, args.run_id), contract["round"]) / "round_contract.json").relative_to(root))}, indent=2))
        return 0
    if args.audited_command == "executor-prompt":
        print(executor_prompt(root, args.run_id, args.round))
        return 0
    if args.audited_command == "audit-prompt":
        print(audit_prompt(root, args.run_id, args.round))
        return 0
    if args.audited_command == "apply-audit":
        try:
            state = apply_audit(root, args.run_id, args.round)
        except AuditedExecutionError as exc:
            print(f"audited-run apply-audit: {exc}", file=sys.stderr)
            return 1
        print(json.dumps({"status": state["status"], "open_requirements": state["open_requirements"]}, indent=2))
        return 0
    if args.audited_command == "status":
        state = load_state(run_dir(root, args.run_id))
        print(json.dumps({"status": state["status"], "open_requirements": state["open_requirements"], "round_counters": state["round_counters"]}, indent=2))
        return 0
    if args.audited_command == "stop":
        state = stop_run(run_dir(root, args.run_id), args.reason)
        print(json.dumps({"status": state["status"], "stop_reason": state["stop_reason"]}, indent=2))
        return 0
    return 2
