"""Import a validated Codex Role Runner result into existing Lab evidence."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from .evidence import write_bundle
from .receipts import sha256_file


def _copy(root: Path, output: Path, relative: str) -> Path:
    source = (root / relative).resolve()
    if not source.is_file():
        raise ValueError(f"missing role-run artifact: {relative}")
    target = output / "role_run" / Path(relative).name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    return target


def _trace_metrics(trace_path: Path) -> dict[str, int]:
    """Read the public Codex JSONL counters without interpreting findings."""
    events = 0
    tool_calls = 0
    usage: dict[str, int] = {}
    for line in trace_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        events += 1
        event = json.loads(line)
        item = event.get("item") if isinstance(event, dict) else None
        if isinstance(item, dict) and item.get("type") == "command_execution":
            tool_calls += 1
        candidate = event.get("usage") if isinstance(event, dict) else None
        if isinstance(candidate, dict):
            usage = {key: int(value) for key, value in candidate.items() if isinstance(value, int)}
    return {
        "trace_events": events,
        "tool_call_count": tool_calls,
        "input_tokens": usage.get("input_tokens", 0),
        "cached_input_tokens": usage.get("cached_input_tokens", 0),
        "output_tokens": usage.get("output_tokens", 0),
        "reasoning_output_tokens": usage.get("reasoning_output_tokens", 0),
    }


def _latency_seconds(started_at: str, finished_at: str) -> float:
    from datetime import datetime

    start = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
    finish = datetime.fromisoformat(finished_at.replace("Z", "+00:00"))
    return (finish - start).total_seconds()


def import_role_run(
    *,
    root: Path,
    result_path: Path,
    output: Path,
    condition: str,
    task_spec_version: str,
    trial_index: int,
    provider: str,
    model_id: str,
    cli_version: str,
    reasoning_profile: str,
    permission_policy: str,
    delivery_profile: str,
    repository: str,
    integrity_source: str,
    role_runner: Path | None = None,
) -> Path:
    """Create a standard EvidenceBundle from an externally executed role result.

    ``declared_baseline`` is appropriate for a manually captured direct exec:
    it preserves evidence but deliberately does not claim runner attestation.
    ``role_runner_verified`` invokes the supplied Role Runner's ``verify``
    command before importing.  This is intentionally an importer: it never
    decides whether a STOP_SHIP finding is correct.
    """
    root = root.resolve()
    result_path = result_path.resolve()
    if integrity_source not in {"declared_baseline", "role_runner_verified"}:
        raise ValueError("unsupported integrity source")
    if integrity_source == "role_runner_verified":
        if role_runner is None:
            raise ValueError("--role-runner is required for role_runner_verified evidence")
        verifier = role_runner.resolve()
        if not verifier.is_file():
            raise ValueError(f"missing Role Runner: {verifier}")
        verified = subprocess.run(
            [sys.executable, str(verifier), "verify", "--root", str(root), "--result", str(result_path)],
            capture_output=True,
            text=True,
            check=False,
        )
        if verified.returncode != 0:
            detail = verified.stderr.strip() or verified.stdout.strip() or "unknown verification error"
            raise ValueError(f"Role Runner verification failed: {detail}")
    result = json.loads(result_path.read_text(encoding="utf-8"))
    if result.get("schema_version") != "playbook.codex_role_run.v1":
        raise ValueError("unsupported role result schema")
    if result.get("status") != "validated":
        raise ValueError("role result is not validated")
    task_id = str(result["task_id"])
    output = output / f"trial-{trial_index}"
    output.mkdir(parents=True, exist_ok=False)
    copied_result = _copy(root, output, str(result_path.relative_to(root)))
    copied = {"result": copied_result}
    for key in ("prompt_path", "context_manifest_path"):
        copied[key] = _copy(root, output, str(result["inputs"][key]))
    for key in ("trace_path", "stderr_path", "report_path"):
        value = result["outputs"].get(key)
        if value:
            copied[key] = _copy(root, output, str(value))
    copied["ledger"] = _copy(root, output, str((result_path.parent / "events.jsonl").relative_to(root)))
    receipt = {
        "schema_version": "playbook.command_receipt.v1", "receipt_id": f"{result['run_id']}-import",
        "task_id": task_id, "producer": "role_run_evidence_bridge.v1", "command_argv": ["codex", "exec"],
        "working_directory": str(root), "start_timestamp": result["started_at"], "end_timestamp": result["finished_at"],
        "exit_code": result["codex"]["exit_code"], "stdout_artifact_path": "codex_events.jsonl",
        "stdout_sha256": sha256_file(copied["trace_path"]), "stderr_artifact_path": "codex_stderr.txt",
        "stderr_sha256": sha256_file(copied["stderr_path"]), "repo_commit_before": result["base_commit"],
        "repo_commit_after": result["base_commit"], "dirty_state_before": ["external-role-run"],
        "dirty_state_after": ["external-role-run"], "diff_stat_artifact_path": "diff_stat.txt",
        "diff_stat_sha256": "", "environment_summary": result["codex"], "parent_receipt_id": None,
        "redaction_status": "not_requested"}
    diff = output / "role_run/diff_stat.txt"; diff.write_text("\n", encoding="utf-8"); receipt["diff_stat_sha256"] = sha256_file(diff)
    receipt_path = output / "role_run/receipt.json"; receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    metrics = _trace_metrics(copied["trace_path"])
    metrics.update({
        "role": result["role"],
        "review_verdict": result.get("verdict"),
        "workspace_unchanged": result["postflight"]["workspace_unchanged"],
        "latency_seconds": _latency_seconds(result["started_at"], result["finished_at"]),
        "retry_count": 0,
        "human_intervention_count": 0,
    })
    score = {"schema_version":"playbook.scorer_output.v1","scorer_id":"role_run_integrity","scorer_version":"1.0.0","scorer_code_hash":"importer","task_id":task_id,"verdict":"pass","score":1.0,"metrics":metrics,"failure_records":[]}
    scorer = output / "scorers/role_run_integrity.json"; scorer.parent.mkdir(); scorer.write_text(json.dumps(score,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    unit = {"schema_version":"playbook.harness_eval_unit.v1","unit_id":f"role-run-{task_id}-{condition}-{trial_index}","task_id":task_id,"condition":condition,"trial_index":trial_index,"evaluation_mode":"empirical","identity_source":integrity_source,"model":{"provider":provider,"id":model_id},"cli_version":cli_version,"harness_version":"role_run_evidence_bridge.v1","adapter_version":"role_run_import.v1","prompt_version":task_spec_version,"prompt_hash":sha256_file(copied["prompt_path"]),"reasoning_profile":reasoning_profile,"tool_registry_version":"codex_internal_not_captured","memory_policy_version":"fresh_role_process","permission_policy_version":permission_policy,"environment":{"commit":result["base_commit"]},"dataset_version":task_spec_version,"scorer_version":"role_run_integrity:1.0.0","budget":{},"timeout_seconds":None,"retry_policy":"single_attempt_no_retry","delivery_profile":delivery_profile,"compatibility_fingerprint":""}
    import hashlib
    fp = dict(unit); fp.pop("condition"); fp.pop("unit_id"); fp.pop("prompt_hash"); fp.pop("identity_source"); fp["compatibility_fingerprint"]=""; unit["compatibility_fingerprint"]=hashlib.sha256(json.dumps(fp,sort_keys=True,separators=(",",":" )).encode()).hexdigest()
    unit_path=output/"harness_eval_unit.json"; unit_path.write_text(json.dumps(unit,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return write_bundle(output_dir=output, repository=repository, task_id=task_id, task_spec_version=task_spec_version, condition=condition, adapter_version="role_run_import.v1", environment_digest=result["base_commit"], prompt_file=copied["prompt_path"], commit_before=result["base_commit"], commit_after=result["base_commit"], receipt_paths=[receipt_path], trace_paths=[copied["trace_path"],copied["ledger"]], post_state_manifest=copied["result"], scorer_outputs=[scorer], failure_records=[], report_path=copied["report_path"], harness_eval_unit_path=unit_path)
