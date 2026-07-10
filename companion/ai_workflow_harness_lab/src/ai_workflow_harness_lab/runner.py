from __future__ import annotations

import json
import shutil
import tempfile
import sys
from pathlib import Path
from typing import Any

from .adapters.base import Adapter
from .environment import copy_fixture, environment_digest, git, init_git, post_state_manifest
from .evidence import write_bundle
from .models import ScorerResult, Suite, SuiteTask, TrialResult
from .receipts import run_command_receipt
from .scorers import diff_scope, file_state, json_state, shell
from .scorers.base import failure, write_scorer_output
from .scorers import meta


def prompt_for(task: SuiteTask, condition: str) -> Path:
    return task.playbook_prompt if condition == "playbook" else task.baseline_prompt


def run_suite(suite: Suite, condition: str, adapter: Adapter, trials: int, output: Path) -> list[TrialResult]:
    output.mkdir(parents=True, exist_ok=True)
    results: list[TrialResult] = []
    for task in suite.tasks:
        for trial in range(trials):
            results.append(run_trial(suite, task, condition, adapter, trial, output))
    write_run_index(output, results)
    return results


def run_trial(suite: Suite, task: SuiteTask, condition: str, adapter: Adapter, trial: int, output: Path) -> TrialResult:
    trial_dir = output / task.task_id / f"trial-{trial}"
    if trial_dir.exists():
        shutil.rmtree(trial_dir)
    trial_dir.mkdir(parents=True)
    workspace = trial_dir / "workspace"
    copy_fixture(task.fixture, workspace)
    commit_before = init_git(workspace)
    env_digest = environment_digest(workspace)
    prompt_file = trial_dir / "prompt.md"
    prompt_file.write_text(prompt_for(task, condition).read_text(encoding="utf-8"), encoding="utf-8")
    adapter_dir = trial_dir / "adapter"
    adapter_result = adapter.run(task, condition, trial, workspace, prompt_file, adapter_dir)
    run_id = f"{task.task_id}-{condition}-{trial}"
    adapter_failures = classify_adapter_result(task.task_id, run_id, adapter_result.exit_code, adapter_result.metadata)
    verification_receipts, verification_failures = run_required_verification(
        task,
        condition,
        trial,
        workspace,
        trial_dir / "verification",
    )
    receipt_paths = adapter_result.receipt_paths + verification_receipts
    scorer_results = run_scorers(
        task,
        condition,
        trial,
        workspace,
        adapter_result.output_path,
        receipt_paths,
        trial_dir / "scorers",
    )
    post_manifest = post_state_manifest(workspace, trial_dir / "post_state_manifest.json")
    report_path = write_trial_report(trial_dir, task, condition, scorer_results)
    commit_after_result = git(["rev-parse", "HEAD"], workspace)
    commit_after = commit_after_result.stdout.strip() if commit_after_result.returncode == 0 else "git-unavailable"
    failure_records = (
        adapter_failures
        + verification_failures
        + [record for result in scorer_results for record in result.failure_records]
    )
    valid = not any(record.get("invalid_run") for record in failure_records)
    score = task_score(scorer_results, valid)
    run_result_path = write_run_result(
        trial_dir,
        task.task_id,
        run_id,
        score,
        valid,
        failure_records,
    )
    bundle_path = write_bundle(
        output_dir=trial_dir,
        repository=suite.suite_id,
        task_id=task.task_id,
        task_spec_version=task.version,
        condition=condition,
        adapter_version=adapter.adapter_version,
        environment_digest=env_digest,
        commit_before=commit_before,
        commit_after=commit_after,
        receipt_paths=receipt_paths,
        trace_paths=adapter_result.trace_paths + [run_result_path],
        post_state_manifest=post_manifest,
        scorer_outputs=[result.output_path for result in scorer_results],
        failure_records=failure_records,
        report_path=report_path,
    )
    return TrialResult(
        task=task,
        condition=condition,
        trial_index=trial,
        workspace=workspace,
        output_dir=trial_dir,
        bundle_path=bundle_path,
        valid=valid,
        score=score,
        failure_records=failure_records,
    )


def classify_adapter_result(task_id: str, run_id: str, exit_code: int, metadata: dict[str, Any]) -> list[dict[str, Any]]:
    if exit_code == 0:
        return []
    if metadata.get("timed_out"):
        return [
            failure(
                task_id,
                run_id,
                f"{run_id}-adapter-timeout",
                "timeout",
                "adapter command timed out",
                owner_class="harness",
                stage="adapter",
                score_treatment="invalid_run_exclude_from_capability_score",
                invalid_run=True,
            )
        ]
    return [
        failure(
            task_id,
            run_id,
            f"{run_id}-adapter-exit-{exit_code}",
            "tool_adapter_failure",
            f"adapter command exited {exit_code}",
            owner_class="harness",
            stage="adapter",
            score_treatment="invalid_run_exclude_from_capability_score",
            invalid_run=True,
        )
    ]


def materialize_command(command: Any, workspace: Path, task: SuiteTask, condition: str, trial: int) -> list[str]:
    if isinstance(command, str):
        values = ["/bin/sh", "-lc", command]
    elif isinstance(command, list):
        values = [str(part) for part in command]
    else:
        raise ValueError("required_verification.command must be a string or list")
    replacements = {
        "{python}": sys.executable,
        "{workspace}": str(workspace),
        "{task_id}": task.task_id,
        "{condition}": condition,
        "{trial}": str(trial),
    }
    rendered: list[str] = []
    for value in values:
        for placeholder, replacement in replacements.items():
            value = value.replace(placeholder, replacement)
        rendered.append(value)
    return rendered


def run_required_verification(
    task: SuiteTask,
    condition: str,
    trial: int,
    workspace: Path,
    output_dir: Path,
) -> tuple[list[Path], list[dict[str, Any]]]:
    config = task.required_verification
    if not config:
        return [], []
    run_id = f"{task.task_id}-{condition}-{trial}"
    try:
        argv = materialize_command(config["command"], workspace, task, condition, trial)
        expected_exit = int(config.get("expected_exit_code", 0))
        execution = run_command_receipt(
            task.task_id,
            output_dir / "receipts/required-verification",
            argv,
            workspace,
            timeout=float(config["timeout"]) if "timeout" in config else None,
        )
    except Exception as exc:
        return [], [
            failure(
                task.task_id,
                run_id,
                f"{run_id}-verification-harness-failure",
                "environment_failure",
                f"required verification could not run: {exc}",
                owner_class="environment",
                stage="verification",
                score_treatment="invalid_run_exclude_from_capability_score",
                invalid_run=True,
            )
        ]
    if execution.exit_code == expected_exit:
        return [execution.receipt_path], []
    failure_class = "timeout" if execution.timed_out else "model_reasoning_failure"
    return [execution.receipt_path], [
        failure(
            task.task_id,
            run_id,
            f"{run_id}-verification-exit-{execution.exit_code}",
            failure_class,
            f"required verification exited {execution.exit_code}, expected {expected_exit}",
            owner_class="model",
            stage="verification",
            score_treatment="count_as_task_failure",
            invalid_run=False,
        )
    ]


def task_score(scorer_results: list[ScorerResult], valid: bool) -> float:
    if not valid:
        return 0.0
    if not scorer_results:
        return 0.0
    return sum(result.score for result in scorer_results) / len(scorer_results)


def write_run_result(
    trial_dir: Path,
    task_id: str,
    run_id: str,
    score: float,
    valid: bool,
    failure_records: list[dict[str, Any]],
) -> Path:
    policy_fail = any(record.get("failure_class") == "policy_failure" and record.get("terminal") for record in failure_records)
    evidence_invalid = any(record.get("failure_class") == "invalid_evidence" for record in failure_records)
    if not valid:
        verdict = "invalid_run"
        task_status = "not_scored"
        score_value: float | None = None
    elif policy_fail or score < 1.0:
        verdict = "failed"
        task_status = "fail"
        score_value = score
    else:
        verdict = "passed"
        task_status = "pass"
        score_value = score
    payload = {
        "schema_version": "playbook.run_result.v1",
        "run_id": run_id,
        "task_id": task_id,
        "task_score": {
            "status": task_status,
            "score": score_value,
            "reason": "invalid infrastructure run" if not valid else "computed from independent scorers",
        },
        "run_validity": {
            "valid": valid,
            "reason": "no invalid_run failure records" if valid else "one or more invalid_run failure records",
        },
        "policy_status": "fail" if policy_fail else "pass",
        "evidence_status": "invalid" if evidence_invalid else "complete",
        "failure_records": [str(record.get("failure_id")) for record in failure_records],
        "cost_record": {"cost_usd": "unknown", "tokens": "unknown"},
        "latency": {"wall_clock_seconds": "unknown"},
        "human_intervention": {"required": False, "status": "not_requested"},
        "final_verdict": verdict,
    }
    path = trial_dir / "run_result.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def run_scorers(
    task: SuiteTask,
    condition: str,
    trial: int,
    workspace: Path,
    agent_output: Path,
    receipts: list[Path],
    output_dir: Path,
) -> list[ScorerResult]:
    results: list[ScorerResult] = []
    run_id = f"{task.task_id}-{condition}-{trial}"
    for index, config in enumerate(task.scorers):
        scorer_type = config["type"]
        scorer_id = config.get("id", f"{scorer_type}_{index}")
        try:
            if scorer_type == "shell":
                score, metrics, failures = shell.score(workspace, config, task.task_id, run_id)
            elif scorer_type == "file_state":
                score, metrics, failures = file_state.score(workspace, config, task.task_id, run_id)
            elif scorer_type == "diff_scope":
                score, metrics, failures = diff_scope.score(workspace, config, task.task_id, run_id)
            elif scorer_type == "json_state":
                score, metrics, failures = json_state.score(workspace, config, task.task_id, run_id)
            elif scorer_type == "receipt_completeness":
                score, metrics, failures = meta.receipt_completeness(receipts, config, task.task_id, run_id)
            elif scorer_type == "false_completion":
                score, metrics, failures = meta.false_completion(agent_output, receipts, config, task.task_id, run_id)
            elif scorer_type == "retry_budget":
                score, metrics, failures = meta.retry_budget(workspace, config, task.task_id, run_id)
            elif scorer_type == "prompt_injection_canary":
                score, metrics, failures = meta.prompt_injection_canary(workspace, config, task.task_id, run_id)
            elif scorer_type == "resume_idempotency":
                score, metrics, failures = meta.resume_idempotency(workspace, config, task.task_id, run_id)
            else:
                raise ValueError(f"unknown scorer type: {scorer_type}")
        except Exception as exc:
            score = 0.0
            metrics = {"scorer_exception": type(exc).__name__}
            failures = [
                failure(
                    task.task_id,
                    run_id,
                    f"{run_id}-{scorer_id}-scorer-failure",
                    "scorer_failure",
                    f"scorer {scorer_id} failed: {exc}",
                    owner_class="scorer",
                    stage="scoring",
                    score_treatment="invalid_run_exclude_from_capability_score",
                    invalid_run=True,
                )
            ]
        verdict = "passed" if score == 1.0 else "failed"
        path = write_scorer_output(output_dir, scorer_id, task.task_id, verdict, score, metrics, failures)
        results.append(ScorerResult(scorer_id, "1.0.0", verdict, score, path, failures, metrics))
    return results


def write_trial_report(trial_dir: Path, task: SuiteTask, condition: str, scorer_results: list[ScorerResult]) -> Path:
    path = trial_dir / "report.md"
    lines = [
        f"# Trial Report: {task.task_id}",
        "",
        "Mechanism demonstration, not empirical proof of Playbook effectiveness.",
        "",
        f"- Condition: {condition}",
        f"- Scorers: {len(scorer_results)}",
        f"- Failures: {sum(len(result.failure_records) for result in scorer_results)}",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def write_run_index(output: Path, results: list[TrialResult]) -> None:
    payload = {
        "schema_version": "harness_lab.run_index.v1",
        "bundles": [str(result.bundle_path.relative_to(output)) for result in results],
        "task_count": len({result.task.task_id for result in results}),
        "trial_count": len(results),
    }
    (output / "run_index.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
