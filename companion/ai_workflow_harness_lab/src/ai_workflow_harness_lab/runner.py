from __future__ import annotations

import json
import hashlib
import sys
from pathlib import Path
from typing import Any

from . import __version__
from .adapters.base import Adapter
from .environment import copy_fixture, environment_digest, init_git, post_state_manifest, tree_manifest
from .evidence import write_bundle
from .models import ScorerResult, Suite, SuiteTask, TrialResult
from .receipts import run_command_receipt, sha256_file
from .scorers import diff_scope, file_state, json_state, shell
from .scorers.base import failure, write_scorer_output
from .scorers import meta


PROJECT_ROOT = Path(__file__).resolve().parents[4]


class RunError(RuntimeError):
    pass


def prompt_for(task: SuiteTask, condition: str) -> Path:
    return task.playbook_prompt if condition == "playbook" else task.baseline_prompt


def run_suite(
    suite: Suite,
    condition: str,
    adapter: Adapter,
    trials: int,
    output: Path,
    *,
    trial_start: int = 0,
    task_ids: list[str] | None = None,
    append: bool = False,
) -> list[TrialResult]:
    if trial_start < 0:
        raise RunError("trial_start must be nonnegative")

    tasks = select_tasks(suite, task_ids)
    existing_bundles = prepare_output(output, append=append)
    trial_indices = range(trial_start, trial_start + trials)
    collisions = [
        output / task.task_id / f"trial-{trial}"
        for task in tasks
        for trial in trial_indices
        if (output / task.task_id / f"trial-{trial}").exists()
    ]
    if collisions:
        paths = ", ".join(str(path) for path in collisions)
        raise RunError(f"trial directory already exists; refusing to overwrite evidence: {paths}")

    results: list[TrialResult] = []
    for task in tasks:
        for trial in range(trial_start, trial_start + trials):
            results.append(run_trial(suite, task, condition, adapter, trial, output))
    write_run_index(output, results, existing_bundles=existing_bundles)
    return results


def select_tasks(suite: Suite, task_ids: list[str] | None) -> list[SuiteTask]:
    if not task_ids:
        return suite.tasks

    requested = set(task_ids)
    available = {task.task_id for task in suite.tasks}
    unknown = sorted(requested - available)
    if unknown:
        raise RunError(
            f"unknown task ID(s): {', '.join(unknown)}; available task IDs: {', '.join(sorted(available))}"
        )
    return [task for task in suite.tasks if task.task_id in requested]


def prepare_output(output: Path, *, append: bool) -> list[str]:
    index_path = output / "run_index.json"
    if output.exists():
        if not output.is_dir():
            raise RunError(f"output path exists and is not a directory: {output}")
        if not append:
            raise RunError(f"output already exists; use --append to retain prior evidence: {output}")
        if any(output.iterdir()) and not index_path.is_file():
            raise RunError(f"non-empty output is missing run_index.json; refusing unsafe append: {output}")
    else:
        output.mkdir(parents=True)

    if not index_path.exists():
        return []
    try:
        payload = json.loads(index_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RunError(f"cannot read existing run_index.json: {exc}") from exc
    if payload.get("schema_version") != "harness_lab.run_index.v1":
        raise RunError("existing run_index.json has unsupported schema_version")
    bundles = payload.get("bundles")
    if not isinstance(bundles, list) or not all(isinstance(path, str) for path in bundles):
        raise RunError("existing run_index.json bundles must be a list of paths")
    return list(dict.fromkeys(bundles))


def run_trial(suite: Suite, task: SuiteTask, condition: str, adapter: Adapter, trial: int, output: Path) -> TrialResult:
    trial_dir = output / task.task_id / f"trial-{trial}"
    if trial_dir.exists():
        raise RunError(f"trial directory already exists; refusing to overwrite evidence: {trial_dir}")
    try:
        trial_dir.mkdir(parents=True, exist_ok=False)
    except FileExistsError as exc:
        raise RunError(f"trial directory already exists; refusing to overwrite evidence: {trial_dir}") from exc
    workspace = trial_dir / "workspace"
    copy_fixture(task.fixture, workspace)
    baseline_manifest = tree_manifest(workspace)
    commit_before = init_git(workspace)
    env_digest = environment_digest(workspace)
    prompt_file = trial_dir / "prompt.md"
    prompt_file.write_bytes(prompt_for(task, condition).read_bytes())
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
        baseline_manifest,
    )
    post_manifest = post_state_manifest(workspace, trial_dir / "post_state_manifest.json")
    report_path = write_trial_report(trial_dir, task, condition, scorer_results)
    harness_eval_unit_path = write_harness_eval_unit(
        trial_dir,
        suite,
        task,
        condition,
        trial,
        adapter,
        adapter_result.metadata,
        prompt_file,
        env_digest,
        scorer_results,
    )
    commit_after = "not_inspected_after_agent_execution"
    failure_records = (
        adapter_failures
        + verification_failures
        + [record for result in scorer_results for record in result.failure_records]
    )
    valid = not any(record.get("invalid_run") for record in failure_records)
    score = task_score(scorer_results, valid, failure_records)
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
        prompt_file=prompt_file,
        commit_before=commit_before,
        commit_after=commit_after,
        receipt_paths=receipt_paths,
        trace_paths=adapter_result.trace_paths + [run_result_path],
        post_state_manifest=post_manifest,
        scorer_outputs=[result.output_path for result in scorer_results],
        failure_records=failure_records,
        report_path=report_path,
        harness_eval_unit_path=harness_eval_unit_path,
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


def stable_hash(data: dict[str, Any]) -> str:
    payload = json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def write_harness_eval_unit(
    trial_dir: Path,
    suite: Suite,
    task: SuiteTask,
    condition: str,
    trial: int,
    adapter: Adapter,
    adapter_metadata: dict[str, Any],
    prompt_file: Path,
    env_digest: str,
    scorer_results: list[ScorerResult],
) -> Path:
    scorer_version = ",".join(f"{result.scorer_id}:{result.scorer_version}" for result in scorer_results)
    timeout = adapter_metadata.get("timeout_seconds", "unknown")
    compatibility = {
        "model": adapter_metadata.get("model", {"provider": "unknown", "id": "unknown", "parameters": "unknown"}),
        "cli_version": adapter_metadata.get("cli_version", "unknown"),
        "reasoning_profile": adapter_metadata.get("reasoning_profile", "unknown"),
        "harness_version": __version__,
        "adapter_version": adapter.adapter_version,
        "command_template": adapter_metadata.get("command_template", "not_applicable"),
        "tool_registry_version": "harness_lab_builtin.v1",
        "memory_policy_version": "stateless_fixture_workspace.v1",
        "permission_policy_version": adapter_metadata.get("permission_policy_version", "adapter_default.v1"),
        "environment_digest": env_digest,
        "dataset_version": suite.version,
        "scorer_version": scorer_version,
        "timeout_seconds": timeout,
        "retry_policy": "single_attempt_no_retry",
        "delivery_profile": adapter_metadata.get("delivery_profile", "harness_lab_single_adapter"),
    }
    unit = {
        "schema_version": "playbook.harness_eval_unit.v1",
        "unit_id": f"{suite.suite_id}-{task.task_id}-{condition}-{trial}",
        "task_id": task.task_id,
        "condition": condition,
        "trial_index": trial,
        "model": compatibility["model"],
        "cli_version": compatibility["cli_version"],
        "reasoning_profile": compatibility["reasoning_profile"],
        "harness_version": __version__,
        "adapter_version": adapter.adapter_version,
        "prompt_version": f"{task.version}:{condition}",
        "prompt_hash": sha256_file(prompt_file),
        "tool_registry_version": compatibility["tool_registry_version"],
        "memory_policy_version": compatibility["memory_policy_version"],
        "permission_policy_version": compatibility["permission_policy_version"],
        "environment": {"digest": env_digest, "workspace_policy": "fresh_fixture_copy"},
        "dataset_version": suite.version,
        "scorer_version": scorer_version,
        "budget": {"correction_budget": task.correction_budget, "timeout_seconds": timeout},
        "timeout_seconds": timeout,
        "retry_policy": compatibility["retry_policy"],
        "delivery_profile": compatibility["delivery_profile"],
        "compatibility_fingerprint": stable_hash(compatibility),
    }
    path = trial_dir / "harness_eval_unit.json"
    path.write_text(json.dumps(unit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


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
        "{project_root}": str(PROJECT_ROOT),
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
            inspect_git=False,
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


def task_score(
    scorer_results: list[ScorerResult],
    valid: bool,
    failure_records: list[dict[str, Any]] | None = None,
) -> float:
    if not valid:
        return 0.0
    if any(
        not record.get("invalid_run")
        and record.get("score_treatment")
        in {"count_as_task_failure", "policy_gate_failure"}
        for record in (failure_records or [])
    ):
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
    task_fail = any(
        not record.get("invalid_run")
        and record.get("score_treatment") == "count_as_task_failure"
        for record in failure_records
    )
    evidence_invalid = any(record.get("failure_class") == "invalid_evidence" for record in failure_records)
    if not valid:
        verdict = "invalid_run"
        task_status = "not_scored"
        score_value: float | None = None
    elif policy_fail or task_fail or score < 1.0:
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
    baseline_manifest: dict[str, str],
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
                score, metrics, failures = diff_scope.score(
                    workspace,
                    config,
                    task.task_id,
                    run_id,
                    baseline_manifest,
                )
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


def write_run_index(output: Path, results: list[TrialResult], *, existing_bundles: list[str] | None = None) -> None:
    new_bundles = [str(result.bundle_path.relative_to(output)) for result in results]
    bundles = list(dict.fromkeys([*(existing_bundles or []), *new_bundles]))
    payload = {
        "schema_version": "harness_lab.run_index.v1",
        "bundles": bundles,
        "task_count": len({Path(bundle).parts[0] for bundle in bundles if Path(bundle).parts}),
        "trial_count": len(bundles),
    }
    index_path = output / "run_index.json"
    temporary_path = output / ".run_index.json.tmp"
    temporary_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary_path.replace(index_path)
