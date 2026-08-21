"""Import a validated Codex Role Runner result into existing Lab evidence."""

from __future__ import annotations

import json
import shutil
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
) -> Path:
    """Create a standard EvidenceBundle from an externally executed role result.

    The caller supplies the same declared identity fields for both arms.  This is
    intentionally an importer: it never decides whether a STOP_SHIP finding is
    correct, only whether the review execution and its evidence are valid.
    """
    root = root.resolve()
    result_path = result_path.resolve()
    result = json.loads(result_path.read_text(encoding="utf-8"))
    if result.get("schema_version") != "playbook.codex_role_run.v1":
        raise ValueError("unsupported role result schema")
    if result.get("status") != "validated":
        raise ValueError("role result is not validated")
    task_id = str(result["task_id"])
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
    score = {"schema_version":"playbook.scorer_output.v1","scorer_id":"role_run_integrity","scorer_version":"1.0.0","scorer_code_hash":"importer","task_id":task_id,"verdict":"pass","score":1.0,"metrics":{"role":result["role"],"review_verdict":result.get("verdict"),"trace_events":result["postflight"]["event_count"],"workspace_unchanged":result["postflight"]["workspace_unchanged"]},"failure_records":[]}
    scorer = output / "scorers/role_run_integrity.json"; scorer.parent.mkdir(); scorer.write_text(json.dumps(score,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    unit = {"schema_version":"playbook.harness_eval_unit.v1","unit_id":f"role-run-{task_id}-{condition}-{trial_index}","task_id":task_id,"condition":condition,"trial_index":trial_index,"evaluation_mode":"empirical","identity_source":"attested","model":{"provider":provider,"id":model_id},"cli_version":cli_version,"harness_version":"role_run_evidence_bridge.v1","adapter_version":"role_run_import.v1","prompt_version":task_spec_version,"prompt_hash":sha256_file(copied["prompt_path"]),"reasoning_profile":reasoning_profile,"tool_registry_version":"codex_internal_not_captured","memory_policy_version":"fresh_role_process","permission_policy_version":permission_policy,"environment":{"commit":result["base_commit"]},"dataset_version":task_spec_version,"scorer_version":"role_run_integrity:1.0.0","budget":{},"timeout_seconds":None,"retry_policy":"single_attempt_no_retry","delivery_profile":delivery_profile,"compatibility_fingerprint":""}
    import hashlib
    fp = dict(unit); fp.pop("condition"); fp.pop("prompt_hash"); fp["compatibility_fingerprint"]=""; unit["compatibility_fingerprint"]=hashlib.sha256(json.dumps(fp,sort_keys=True,separators=(",",":" )).encode()).hexdigest()
    unit_path=output/"harness_eval_unit.json"; unit_path.write_text(json.dumps(unit,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return write_bundle(output_dir=output, repository=repository, task_id=task_id, task_spec_version=task_spec_version, condition=condition, adapter_version="role_run_import.v1", environment_digest=result["base_commit"], prompt_file=copied["prompt_path"], commit_before=result["base_commit"], commit_after=result["base_commit"], receipt_paths=[receipt_path], trace_paths=[copied["trace_path"],copied["ledger"]], post_state_manifest=copied["result"], scorer_outputs=[scorer], failure_records=[], report_path=copied["report_path"], harness_eval_unit_path=unit_path)
