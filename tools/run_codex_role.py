#!/usr/bin/env python3
"""Run a supported Codex review role through guarded preflight and postflight."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Any

TOOL_ROOT = Path(__file__).resolve().parents[1]
if str(TOOL_ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(TOOL_ROOT / "tools"))

try:
    import approve_feature_design
    import feature_design_lib
    import feature_review_policy
    import render_codex_exec_prompt
    import role_run_lib
except ImportError as exc:  # pragma: no cover
    raise SystemExit(f"run_codex_role: failed to import Playbook helpers: {exc}") from exc

TIMEOUT_EXIT_CODE = 124


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--root", type=Path, default=Path("."))
    result.add_argument("--task", required=True)
    result.add_argument("--feature-id", default="")
    result.add_argument("--slice-id", default="")
    result.add_argument("--role", required=True, choices=sorted(role_run_lib.SUPPORTED_ROLES))
    result.add_argument("--model", default=os.environ.get("PLAYBOOK_CODEX_MODEL", ""))
    result.add_argument("--reasoning-effort", default=os.environ.get("PLAYBOOK_CODEX_REASONING", "medium"))
    result.add_argument("--timeout", type=float, default=900.0)
    result.add_argument("--run-id", default="")
    result.add_argument("--replace", action="store_true")
    result.add_argument("--dry-run", action="store_true")
    result.add_argument("--codex-bin", default="codex", help=argparse.SUPPRESS)
    return result


def resolve_review(
    root: Path,
    *,
    task_id: str,
    requested_feature_id: str,
    requested_slice_id: str,
    role: str,
) -> tuple[dict[str, Any], str, dict[str, Any], dict[str, Any], dict[str, Any] | None]:
    task_record, raw_task = render_codex_exec_prompt.load_task(root, task_id)
    feature_id = render_codex_exec_prompt.feature_id_from_task_or_args(task_record, requested_feature_id)
    registry_ref = f"docs/design/{feature_id}.design.json"
    declared_refs = [str(value).strip().strip("`") for value in task_record.get("design_refs", [])]
    if registry_ref not in declared_refs:
        raise ValueError(f"task {task_id} Design-Refs must include {registry_ref}")
    registry_path = root / registry_ref
    findings, design = feature_design_lib.validate_design_file(root, registry_path)
    if design is None:
        rendered = "; ".join(f"{item.check_id}: {item.message}" for item in findings)
        raise ValueError(f"feature design is missing or invalid: {rendered or registry_ref}")
    if str(design.get("feature_id", "")) != feature_id:
        raise ValueError("feature design identity mismatch")
    task_depth = str(task_record.get("planning_depth", "")).strip()
    design_depth = str(design.get("planning_depth", "")).strip()
    if task_depth and design_depth and task_depth != design_depth:
        raise ValueError(f"task Planning-Depth {task_depth} conflicts with design {design_depth}")

    spec = role_run_lib.role_spec(role, render_codex_exec_prompt.ROLE_MARKERS[role])
    slice_item: dict[str, Any] | None = None
    slice_id = requested_slice_id.strip()
    if spec["phase"] == "slice":
        slice_id = slice_id or str(task_record.get("slice_id", "")).strip()
        if not slice_id:
            raise ValueError(f"role {role} requires --slice-id or task Slice-ID")
        declared_slice = str(task_record.get("slice_id", "")).strip()
        if declared_slice and declared_slice != slice_id:
            raise ValueError(f"task Slice-ID {declared_slice} conflicts with requested slice {slice_id}")
        slice_item = feature_design_lib.find_slice(design, slice_id)
        if slice_item is None:
            raise ValueError(f"slice {slice_id} is not present in {registry_ref}")
        policy = feature_review_policy.report(feature_id=feature_id, design=design, slice_item=slice_item)
    else:
        if slice_id:
            raise ValueError(f"role {role} is a design role and does not accept --slice-id")
        policy = feature_review_policy.report(feature_id=feature_id, design=design)

    review = next((item for item in policy["reviews"] if item.get("role") == role), None)
    if review is None:
        raise ValueError(f"role {role} is not allowed by the current {spec['phase']} review policy")
    review = {**review, "task_id": task_id, "runner_required": True}
    return task_record, raw_task, design, review, slice_item


def build_codex_command(
    *,
    codex_bin: str,
    root: Path,
    report_path: Path,
    model: str,
    reasoning_effort: str,
) -> list[str]:
    command = [
        codex_bin,
        "exec",
        "--ephemeral",
        "--ignore-user-config",
        "--ignore-rules",
        "--strict-config",
        "--cd",
        str(root),
        "--color",
        "never",
        "--json",
        "--sandbox",
        "read-only",
        "--output-last-message",
        str(report_path),
    ]
    if model:
        command.extend(("--model", model))
    command.extend(
        (
            "-c",
            f'model_reasoning_effort="{reasoning_effort}"',
            "-c",
            'approval_policy="never"',
            "-c",
            'web_search="disabled"',
            "-c",
            "include_apps_instructions=false",
            "-c",
            "include_collaboration_mode_instructions=false",
            "-",
        )
    )
    return command


def codex_version(codex_bin: str, root: Path) -> str:
    try:
        completed = subprocess.run(
            [codex_bin, "--version"],
            cwd=root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=15,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return "unavailable"
    value = (completed.stdout or completed.stderr).strip()
    return value or f"exit-{completed.returncode}"


def command_receipt(
    *,
    root: Path,
    run_dir: Path,
    run_id: str,
    task_id: str,
    command: list[str],
    start_timestamp: str,
    end_timestamp: str,
    exit_code: int,
    trace_path: Path,
    stderr_path: Path,
    workspace_delta_path: Path,
    before: dict[str, Any],
    after: dict[str, Any],
    timeout: float,
    timed_out: bool,
    cli_version: str,
    requested_model: str,
    reasoning_effort: str,
) -> dict[str, Any]:
    return {
        "schema_version": "playbook.command_receipt.v1",
        "receipt_id": f"{run_id}-codex-exec",
        "task_id": task_id,
        "producer": role_run_lib.ROLE_RUN_PRODUCER,
        "command_argv": command,
        "working_directory": str(root),
        "start_timestamp": start_timestamp,
        "end_timestamp": end_timestamp,
        "exit_code": exit_code,
        "stdout_artifact_path": role_run_lib.repo_rel(run_dir, trace_path),
        "stdout_sha256": role_run_lib.sha256_file(trace_path),
        "stderr_artifact_path": role_run_lib.repo_rel(run_dir, stderr_path),
        "stderr_sha256": role_run_lib.sha256_file(stderr_path),
        "repo_commit_before": str(before["commit"]),
        "repo_commit_after": str(after["commit"]),
        "dirty_state_before": list(before["status_entries"]),
        "dirty_state_after": list(after["status_entries"]),
        "diff_stat_artifact_path": role_run_lib.repo_rel(run_dir, workspace_delta_path),
        "diff_stat_sha256": role_run_lib.sha256_file(workspace_delta_path),
        "environment_summary": {
            "timeout": timeout,
            "timed_out": timed_out,
            "codex_cli_version": cli_version,
            "requested_model": requested_model or "provider-default",
            "reasoning_effort": reasoning_effort,
            "sandbox": "read-only",
            "fresh_process": True,
        },
        "parent_receipt_id": None,
        "redaction_status": "not_requested",
    }


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    root = args.root.resolve()
    if not root.exists():
        print(f"run_codex_role: project root does not exist: {root}", file=sys.stderr)
        return 2
    try:
        task_record, raw_task, design, review, slice_item = resolve_review(
            root,
            task_id=args.task,
            requested_feature_id=args.feature_id,
            requested_slice_id=args.slice_id,
            role=args.role,
        )
        spec = role_run_lib.role_spec(args.role, render_codex_exec_prompt.ROLE_MARKERS[args.role])
        feature_id = str(design["feature_id"])
        slice_id = str(slice_item.get("slice_id", "")) if slice_item else ""
        before = role_run_lib.workspace_state(root)
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"run_codex_role: preflight failed: {exc}", file=sys.stderr)
        return 2

    timestamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    run_id = role_run_lib.safe_id(args.run_id or f"{args.task}-{args.role}-{timestamp}-{uuid.uuid4().hex[:8]}")
    run_dir = root / ".playbook-artifacts/runs" / run_id
    if run_dir.exists() and not args.replace:
        print(f"run_codex_role: run directory already exists: {run_dir}", file=sys.stderr)
        return 2
    run_dir.mkdir(parents=True, exist_ok=True)

    report_path = role_run_lib.safe_repo_path(root, str(review["report_path"]))
    if report_path is None:
        print("run_codex_role: review policy produced an unsafe report path", file=sys.stderr)
        return 2
    report_path.parent.mkdir(parents=True, exist_ok=True)
    sidecar_path = role_run_lib.role_result_sidecar_path(report_path)
    if (report_path.exists() or sidecar_path.exists()) and not args.replace:
        print("run_codex_role: report already exists; pass --replace for an explicit rerun", file=sys.stderr)
        return 2
    if args.replace:
        report_path.unlink(missing_ok=True)
        sidecar_path.unlink(missing_ok=True)

    output_rel = role_run_lib.repo_rel(root, report_path)
    namespace = argparse.Namespace(
        root=root,
        task=args.task,
        role=args.role,
        review=[],
        human_approval_ref="",
        feature_id=feature_id,
        planning_decision="",
        output_path=output_rel,
    )
    prompt = render_codex_exec_prompt.render(namespace)
    prompt_path = run_dir / "prompt.md"
    role_run_lib.atomic_write_text(prompt_path, prompt)
    prompt_sha = role_run_lib.sha256_file(prompt_path)
    spec_path = run_dir / "role_spec.json"
    role_run_lib.atomic_write_json(spec_path, spec)
    context = role_run_lib.build_context_manifest(
        root,
        task_id=args.task,
        raw_task=raw_task,
        task_record=task_record,
        feature_id=feature_id,
        slice_id=slice_id,
        role=args.role,
        prompt_path=prompt_path,
        prompt_sha256=prompt_sha,
        spec=spec,
    )
    context_path = run_dir / "context_manifest.json"
    role_run_lib.atomic_write_json(context_path, context)
    ledger_path = run_dir / "events.jsonl"
    role_run_lib.append_event(
        ledger_path,
        "role.requested",
        run_id=run_id,
        task_id=args.task,
        feature_id=feature_id,
        slice_id=slice_id or None,
        role=args.role,
    )
    role_run_lib.append_event(
        ledger_path,
        "context.materialized",
        prompt_sha256=prompt_sha,
        context_manifest_sha256=role_run_lib.sha256_file(context_path),
        source_count=len(context["sources"]),
    )

    if args.dry_run:
        role_run_lib.append_event(ledger_path, "role.prepared", dry_run=True)
        print(f"run_codex_role: prepared run_id={run_id} prompt={role_run_lib.repo_rel(root, prompt_path)}")
        return 0

    command = build_codex_command(
        codex_bin=args.codex_bin,
        root=root,
        report_path=report_path,
        model=args.model,
        reasoning_effort=args.reasoning_effort,
    )
    cli_version = codex_version(args.codex_bin, root)
    trace_path = run_dir / "codex_trace.jsonl"
    stderr_path = run_dir / "codex_stderr.txt"
    start_timestamp = role_run_lib.utc_now()
    timed_out = False
    role_run_lib.append_event(
        ledger_path,
        "codex.exec.started",
        command_argv=command,
        codex_cli_version=cli_version,
        requested_model=args.model or "provider-default",
        sandbox="read-only",
    )
    try:
        completed = subprocess.run(
            command,
            cwd=root,
            input=prompt.encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=args.timeout,
            check=False,
        )
        exit_code = int(completed.returncode)
        stdout = completed.stdout
        stderr = completed.stderr
    except FileNotFoundError as exc:
        exit_code = 127
        stdout = b""
        stderr = f"run_codex_role: command not found: {exc.filename}\n".encode("utf-8")
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        exit_code = TIMEOUT_EXIT_CODE
        stdout = exc.stdout or b""
        stderr = (exc.stderr or b"") + f"\nrun_codex_role: timeout after {args.timeout} seconds\n".encode("utf-8")
    end_timestamp = role_run_lib.utc_now()
    trace_path.write_bytes(stdout)
    stderr_path.write_bytes(stderr)

    events, trace_problems = role_run_lib.parse_jsonl_objects(trace_path)
    failure_reasons = list(trace_problems)
    verdict = ""
    marker = str(spec["expected_marker"])
    if not report_path.exists() or not report_path.is_file() or not report_path.read_text(encoding="utf-8", errors="replace").strip():
        failure_reasons.append("Codex did not produce a non-empty review report")
    else:
        try:
            parsed = render_codex_exec_prompt.parse_required_marker(
                args.role,
                report_path.read_text(encoding="utf-8", errors="replace"),
            )
            verdict = str(parsed["verdict"])
        except ValueError as exc:
            failure_reasons.append(str(exc))
    try:
        after = role_run_lib.workspace_state(root)
    except RuntimeError as exc:
        after = before
        failure_reasons.append(str(exc))
    write_drift = before["state_sha256"] != after["state_sha256"]
    if write_drift:
        failure_reasons.append("read-only reviewer changed repository state")
    if exit_code != 0:
        failure_reasons.append(f"codex exec exited with {exit_code}")

    workspace_delta_path = run_dir / "workspace_state_delta.json"
    role_run_lib.atomic_write_json(
        workspace_delta_path,
        {
            "schema_version": "playbook.workspace_state_delta.v1",
            "before": before,
            "after": after,
            "write_drift": write_drift,
        },
    )
    receipt = command_receipt(
        root=root,
        run_dir=run_dir,
        run_id=run_id,
        task_id=args.task,
        command=command,
        start_timestamp=start_timestamp,
        end_timestamp=end_timestamp,
        exit_code=exit_code,
        trace_path=trace_path,
        stderr_path=stderr_path,
        workspace_delta_path=workspace_delta_path,
        before=before,
        after=after,
        timeout=args.timeout,
        timed_out=timed_out,
        cli_version=cli_version,
        requested_model=args.model,
        reasoning_effort=args.reasoning_effort,
    )
    receipt_path = run_dir / "command_receipt.json"
    role_run_lib.atomic_write_json(receipt_path, receipt)

    status = "validated" if not failure_reasons else "invalid"
    role_run_lib.append_event(
        ledger_path,
        "codex.exec.finished",
        exit_code=exit_code,
        timed_out=timed_out,
        trace_event_count=len(events),
        report_path=output_rel,
    )
    role_run_lib.append_event(
        ledger_path,
        "role.postflight",
        status=status,
        verdict=verdict or None,
        write_drift=write_drift,
        failure_reasons=sorted(set(failure_reasons)),
        receipt_sha256=role_run_lib.sha256_file(receipt_path),
    )

    result_payload = {
        "schema_version": role_run_lib.ROLE_RUN_SCHEMA_VERSION,
        "run_id": run_id,
        "role": args.role,
        "phase": spec["phase"],
        "task_id": args.task,
        "feature_id": feature_id,
        "slice_id": slice_id or None,
        "status": status,
        "verdict": verdict or None,
        "marker": marker,
        "base_commit": before["commit"],
        "codex_cli_version": cli_version,
        "requested_model": args.model or "provider-default",
        "observed_model": role_run_lib.observed_model(events),
        "reasoning_effort": args.reasoning_effort,
        "sandbox": "read-only",
        "fresh_process": True,
        "timeout_seconds": args.timeout,
        "started_at": start_timestamp,
        "finished_at": end_timestamp,
        "exit_code": exit_code,
        "timed_out": timed_out,
        "prompt_path": role_run_lib.repo_rel(root, prompt_path),
        "prompt_sha256": role_run_lib.sha256_file(prompt_path),
        "context_manifest_path": role_run_lib.repo_rel(root, context_path),
        "context_manifest_sha256": role_run_lib.sha256_file(context_path),
        "report_path": output_rel,
        "report_sha256": role_run_lib.sha256_file(report_path) if report_path.exists() else role_run_lib.sha256_bytes(b""),
        "trace_path": role_run_lib.repo_rel(root, trace_path),
        "trace_sha256": role_run_lib.sha256_file(trace_path),
        "stderr_path": role_run_lib.repo_rel(root, stderr_path),
        "stderr_sha256": role_run_lib.sha256_file(stderr_path),
        "receipt_path": role_run_lib.repo_rel(root, receipt_path),
        "receipt_sha256": role_run_lib.sha256_file(receipt_path),
        "event_ledger_path": role_run_lib.repo_rel(root, ledger_path),
        "event_ledger_sha256": role_run_lib.sha256_file(ledger_path),
        "workspace_state_before_sha256": before["state_sha256"],
        "workspace_state_after_sha256": after["state_sha256"],
        "write_drift": write_drift,
        "failure_reasons": sorted(set(failure_reasons)),
        "canonical_result_path": role_run_lib.repo_rel(root, run_dir / "result.json"),
    }
    result_path = run_dir / "result.json"
    role_run_lib.atomic_write_json(result_path, result_payload)
    role_run_lib.atomic_write_json(sidecar_path, result_payload)

    if status == "validated" and spec["phase"] == "design":
        try:
            approve_feature_design.write_design_review_record(
                root=root,
                feature_id=feature_id,
                role=args.role,
                report_path=output_rel,
                reviewed_design=design,
                reviewer_binding=f"codex_role_runner:{run_id}",
                read_only=True,
            )
        except Exception as exc:  # fail closed: a valid report without binding is not enough
            result_payload["status"] = "invalid"
            result_payload["failure_reasons"] = sorted(set(result_payload["failure_reasons"] + [str(exc)]))
            role_run_lib.atomic_write_json(result_path, result_payload)
            role_run_lib.atomic_write_json(sidecar_path, result_payload)
            print(f"run_codex_role: failed to bind design review record: {exc}", file=sys.stderr)
            return 2

    print(
        "run_codex_role: "
        f"status={result_payload['status']} role={args.role} verdict={result_payload['verdict']} "
        f"run_id={run_id} result={role_run_lib.repo_rel(root, result_path)}"
    )
    if result_payload["status"] != "validated":
        for reason in result_payload["failure_reasons"]:
            print(f"run_codex_role: {reason}", file=sys.stderr)
        return TIMEOUT_EXIT_CODE if timed_out else 2
    return 1 if verdict == "STOP_SHIP" else 0


if __name__ == "__main__":
    raise SystemExit(main())
