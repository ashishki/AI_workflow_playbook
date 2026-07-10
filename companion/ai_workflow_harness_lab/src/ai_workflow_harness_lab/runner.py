from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path
from typing import Any

from .adapters.base import Adapter
from .environment import copy_fixture, environment_digest, git, init_git, post_state_manifest
from .evidence import write_bundle
from .models import ScorerResult, Suite, SuiteTask, TrialResult
from .scorers import diff_scope, file_state, json_state, shell
from .scorers.base import write_scorer_output
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
    scorer_results = run_scorers(task, condition, trial, workspace, adapter_result.output_path, adapter_result.receipt_paths, trial_dir / "scorers")
    post_manifest = post_state_manifest(workspace, trial_dir / "post_state_manifest.json")
    report_path = write_trial_report(trial_dir, task, condition, scorer_results)
    commit_after_result = git(["rev-parse", "HEAD"], workspace)
    commit_after = commit_after_result.stdout.strip() if commit_after_result.returncode == 0 else "git-unavailable"
    failure_records = [record for result in scorer_results for record in result.failure_records]
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
        receipt_paths=adapter_result.receipt_paths,
        trace_paths=adapter_result.trace_paths,
        post_state_manifest=post_manifest,
        scorer_outputs=[result.output_path for result in scorer_results],
        failure_records=failure_records,
        report_path=report_path,
    )
    score = sum(result.score for result in scorer_results) / len(scorer_results)
    return TrialResult(
        task=task,
        condition=condition,
        trial_index=trial,
        workspace=workspace,
        output_dir=trial_dir,
        bundle_path=bundle_path,
        valid=True,
        score=score,
        failure_records=failure_records,
    )


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
