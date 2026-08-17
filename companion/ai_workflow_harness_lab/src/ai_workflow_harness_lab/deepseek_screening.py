from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .adapters.deepseek_harness import DeepSeekHarnessAdapter
from .comparison import compare, find_bundles
from .deepseek_runtime import DSH_EXPECTED_VERSION, default_profile_path, doctor
from .runner import RunError, run_suite
from .suite_loader import load_suite

PROJECT_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_SUITE = PROJECT_ROOT / "companion/ai_workflow_harness_lab/suites/real_mini_repo_v1"
DEFAULT_OUTPUT = PROJECT_ROOT / ".playbook-artifacts/deepseek-harness-screening"


@dataclass(frozen=True)
class ScreeningConfig:
    suite_path: Path = DEFAULT_SUITE
    output_root: Path = DEFAULT_OUTPUT
    trials: int = 3
    provider: str = "deepseek-official"
    model_id: str = "deepseek-v4-flash"
    profile_path: Path = default_profile_path()
    max_tokens: int | None = 32768
    request_timeout_seconds: float | None = 900.0
    reasoning_profile: str = "high"
    permission_policy: str = "workspace-write"
    expected_version: str = DSH_EXPECTED_VERSION
    input_price_per_million: float | None = None
    output_price_per_million: float | None = None
    resume: bool = False


class ScreeningError(RuntimeError):
    pass


def utc_stamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@contextmanager
def screening_test_environment():
    """Avoid transient pytest/bytecode artifacts in diff-scope metrics."""

    original_bytecode = os.environ.get("PYTHONDONTWRITEBYTECODE")
    original_pytest = os.environ.get("PYTEST_ADDOPTS")
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    pytest_options = (original_pytest or "").strip()
    if "no:cacheprovider" not in pytest_options:
        pytest_options = (pytest_options + " -p no:cacheprovider").strip()
    os.environ["PYTEST_ADDOPTS"] = pytest_options
    try:
        yield
    finally:
        if original_bytecode is None:
            os.environ.pop("PYTHONDONTWRITEBYTECODE", None)
        else:
            os.environ["PYTHONDONTWRITEBYTECODE"] = original_bytecode
        if original_pytest is None:
            os.environ.pop("PYTEST_ADDOPTS", None)
        else:
            os.environ["PYTEST_ADDOPTS"] = original_pytest


def run_screening(config: ScreeningConfig) -> tuple[int, dict[str, Any]]:
    if config.trials <= 0:
        raise ScreeningError("trials must be positive")
    suite = load_suite(config.suite_path)
    output = config.output_root.resolve()
    state_path = output / "screening_state.json"
    if output.exists() and any(output.iterdir()) and not config.resume:
        raise ScreeningError(f"output already exists; use --resume: {output}")
    output.mkdir(parents=True, exist_ok=True)

    doctor_report = doctor(
        profile_path=config.profile_path,
        require_credential=True,
        expected_version=config.expected_version,
    )
    (output / "doctor.json").write_text(json.dumps(doctor_report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if doctor_report["status"] != "pass":
        return 2, {"status": "doctor_failed", "doctor": doctor_report, "output": str(output)}

    adapter = DeepSeekHarnessAdapter(
        provider=config.provider,
        model_id=config.model_id,
        profile_path=config.profile_path,
        max_tokens=config.max_tokens,
        request_timeout_seconds=config.request_timeout_seconds,
        reasoning_profile=config.reasoning_profile,
        permission_policy=config.permission_policy,
        expected_version=config.expected_version,
        input_price_per_million=config.input_price_per_million,
        output_price_per_million=config.output_price_per_million,
    )
    state = load_state(state_path, suite.suite_id, config)
    state["profile_sha256"] = doctor_report.get("profile_sha256")
    write_state(state_path, state)
    for condition in ("baseline", "playbook"):
        condition_dir = output / condition
        for task in suite.tasks:
            for trial in range(config.trials):
                key = run_key(condition, task.task_id, trial)
                trial_dir = condition_dir / task.task_id / f"trial-{trial}"
                bundle_path = trial_dir / "bundle.json"
                if bundle_path.is_file():
                    state["completed"][key] = str(bundle_path.relative_to(output))
                    write_state(state_path, state)
                    continue
                if trial_dir.exists():
                    if not config.resume:
                        raise ScreeningError(f"partial trial exists; use --resume: {trial_dir}")
                    quarantine_trial(output, condition, task.task_id, trial, trial_dir, "interrupted")
                    rebuild_run_index(condition_dir)
                append = (condition_dir / "run_index.json").is_file()
                try:
                    with screening_test_environment():
                        results = run_suite(
                            suite,
                            condition,
                            adapter,
                            1,
                            condition_dir,
                            trial_start=trial,
                            task_ids=[task.task_id],
                            append=append,
                        )
                except RunError as exc:
                    raise ScreeningError(str(exc)) from exc
                result = results[0]
                summary_path = result.output_dir / "adapter" / "adapter_summary.json"
                summary = read_json(summary_path)
                if summary.get("rate_limited"):
                    quarantine = quarantine_trial(output, condition, task.task_id, trial, result.output_dir, "rate-limit")
                    rebuild_run_index(condition_dir)
                    state["paused"] = {
                        "reason": "rate_limit",
                        "condition": condition,
                        "task_id": task.task_id,
                        "trial": trial,
                        "quarantine": str(quarantine.relative_to(output)),
                        "at": utc_stamp(),
                    }
                    write_state(state_path, state)
                    return 75, {"status": "paused_rate_limit", "state": state, "output": str(output)}
                if summary.get("credential_error"):
                    quarantine = quarantine_trial(output, condition, task.task_id, trial, result.output_dir, "credential")
                    rebuild_run_index(condition_dir)
                    state["paused"] = {
                        "reason": "credential",
                        "condition": condition,
                        "task_id": task.task_id,
                        "trial": trial,
                        "quarantine": str(quarantine.relative_to(output)),
                        "at": utc_stamp(),
                    }
                    write_state(state_path, state)
                    return 76, {"status": "paused_credential", "state": state, "output": str(output)}
                state["completed"][key] = str(result.bundle_path.relative_to(output))
                state["paused"] = None
                write_state(state_path, state)

    comparison_dir = output / "comparison"
    report = compare(
        output / "baseline",
        output / "playbook",
        comparison_dir,
        minimum_trials_per_task=config.trials,
        require_empirical=True,
    )
    loc_payload = run_loc_delta(output, config.trials * len(suite.tasks))
    runtime = aggregate_runtime_metrics(output)
    recommendation = build_recommendation(report, loc_payload, runtime, expected_pairs=config.trials * len(suite.tasks))
    recommendation_path = comparison_dir / "recommendation.json"
    recommendation_path.write_text(json.dumps(recommendation, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_recommendation_markdown(comparison_dir / "recommendation.md", recommendation)
    state["status"] = "complete"
    state["paused"] = None
    state["comparison"] = str((comparison_dir / "comparison_report.json").relative_to(output))
    state["recommendation"] = str(recommendation_path.relative_to(output))
    write_state(state_path, state)
    return 0, {
        "status": "complete",
        "output": str(output),
        "comparison": str(comparison_dir / "comparison_report.json"),
        "recommendation": str(recommendation_path),
        "advisory_decision": recommendation["advisory_decision"],
        "human_decision": "pending",
    }


def run_key(condition: str, task_id: str, trial: int) -> str:
    return f"{condition}:{task_id}:{trial}"


def load_state(path: Path, suite_id: str, config: ScreeningConfig) -> dict[str, Any]:
    if path.is_file():
        payload = read_json(path)
        if payload.get("suite_id") != suite_id:
            raise ScreeningError("existing screening state belongs to a different suite")
        return payload
    return {
        "schema_version": "harness_lab.deepseek_screening_state.v1",
        "suite_id": suite_id,
        "created_at": utc_stamp(),
        "status": "running",
        "trials_per_task": config.trials,
        "provider": config.provider,
        "model_id": config.model_id,
        "profile_sha256": None,
        "completed": {},
        "paused": None,
    }


def write_state(path: Path, state: dict[str, Any]) -> None:
    state["updated_at"] = utc_stamp()
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ScreeningError(f"cannot read JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ScreeningError(f"JSON object required: {path}")
    return value


def quarantine_trial(
    output: Path,
    condition: str,
    task_id: str,
    trial: int,
    trial_dir: Path,
    reason: str,
) -> Path:
    target = output / "quarantine" / reason / condition / task_id / f"trial-{trial}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        raise ScreeningError(f"quarantine collision: {target}")
    shutil.move(str(trial_dir), str(target))
    return target


def rebuild_run_index(condition_dir: Path) -> None:
    bundles = sorted(path.relative_to(condition_dir).as_posix() for path in condition_dir.rglob("bundle.json"))
    payload = {
        "schema_version": "harness_lab.run_index.v1",
        "bundles": bundles,
        "task_count": len({Path(path).parts[0] for path in bundles}),
        "trial_count": len(bundles),
    }
    if not bundles and not condition_dir.exists():
        return
    condition_dir.mkdir(parents=True, exist_ok=True)
    (condition_dir / "run_index.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_loc_delta(output: Path, expected_pairs: int) -> dict[str, Any]:
    comparison_dir = output / "comparison"
    json_path = comparison_dir / "loc_delta.json"
    markdown_path = comparison_dir / "loc_delta.md"
    command = [
        sys.executable,
        str(PROJECT_ROOT / "tools/harness_loc_delta.py"),
        "--baseline",
        str(output / "baseline"),
        "--candidate",
        str(output / "playbook"),
        "--json",
        str(json_path),
        "--markdown",
        str(markdown_path),
        "--append-report",
        str(comparison_dir / "comparison_report.md"),
        "--expect-trials",
        str(expected_pairs),
    ]
    result = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)
    (comparison_dir / "loc_delta.stdout.txt").write_text(result.stdout, encoding="utf-8")
    (comparison_dir / "loc_delta.stderr.txt").write_text(result.stderr, encoding="utf-8")
    if result.returncode != 0 or not json_path.is_file():
        raise ScreeningError(f"LOC delta failed with exit {result.returncode}: {result.stderr.strip()}")
    return read_json(json_path)


def aggregate_runtime_metrics(output: Path) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for condition in ("baseline", "playbook"):
        summaries = [read_json(bundle.parent / "adapter" / "adapter_summary.json") for bundle in find_bundles(output / condition)]
        metrics = [item.get("runtime_metrics", {}) for item in summaries]
        result[condition] = aggregate_condition_metrics(metrics)
    path = output / "comparison" / "runtime_metrics.json"
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def aggregate_condition_metrics(metrics: list[dict[str, Any]]) -> dict[str, Any]:
    fields = (
        "input_tokens",
        "output_tokens",
        "cache_read_tokens",
        "cache_write_tokens",
        "tool_calls",
        "tool_failures",
        "steps",
        "turns",
        "wall_clock_seconds",
    )
    totals: dict[str, float] = {}
    for field in fields:
        totals[field] = sum(float(item.get(field, 0) or 0) for item in metrics)
    costs = [item.get("cost_usd") for item in metrics if isinstance(item.get("cost_usd"), (int, float))]
    totals["cost_usd"] = sum(float(value) for value in costs) if costs else "unknown"
    sample = len(metrics)
    means = {
        field: (totals[field] / sample if sample else 0.0)
        for field in fields
    }
    return {"sample_count": sample, "totals": totals, "means": means}


def build_recommendation(
    comparison: dict[str, Any],
    loc: dict[str, Any],
    runtime: dict[str, Any],
    *,
    expected_pairs: int,
) -> dict[str, Any]:
    reasons: list[str] = []
    guardrail_failures: list[str] = []
    baseline = comparison["baseline"]
    candidate = comparison["candidate"]
    hard = comparison["hard_gates"]
    compatibility = list(comparison.get("compatibility_errors", []))

    if compatibility:
        reasons.append("baseline/candidate identity or task pairing is incompatible")
    if baseline["invalid_runs"] or candidate["invalid_runs"]:
        reasons.append("one or more empirical runs are invalid")
    if hard["single_run_stability_warning"]:
        reasons.append("minimum trials per task were not satisfied")
    if candidate["task_success_rate"] < baseline["task_success_rate"]:
        guardrail_failures.append("task success regressed")
    if candidate["false_success_count"] > 0:
        guardrail_failures.append("candidate produced false completion")
    if candidate["policy_violation_count"] > 0:
        guardrail_failures.append("candidate produced policy violations")
    if candidate["evidence_correctness"] < baseline["evidence_correctness"]:
        guardrail_failures.append("evidence correctness regressed")

    paired = int(loc.get("paired_trials", 0))
    baseline_total = float(loc.get("baseline", {}).get("total", 0) or 0)
    candidate_total = float(loc.get("candidate", {}).get("total", 0) or 0)
    reduction = 0.0 if baseline_total <= 0 else (baseline_total - candidate_total) / baseline_total

    if guardrail_failures:
        decision = "reject"
        reasons.extend(guardrail_failures)
    elif compatibility or reasons or paired != expected_pairs:
        decision = "inconclusive"
        if paired != expected_pairs:
            reasons.append(f"expected {expected_pairs} paired trials, observed {paired}")
    elif reduction >= 0.10:
        decision = "promote"
        reasons.append(f"candidate reduced changed LOC by {reduction:.1%} without observed guardrail regression")
    else:
        decision = "accept_without_claim"
        reasons.append("guardrails passed but the target LOC reduction was below 10%")

    return {
        "schema_version": "harness_lab.deepseek_screening_recommendation.v1",
        "advisory_decision": decision,
        "human_decision": "pending",
        "expected_paired_trials": expected_pairs,
        "observed_paired_trials": paired,
        "target_metric": {
            "baseline_changed_loc": baseline_total,
            "candidate_changed_loc": candidate_total,
            "reduction_ratio": reduction,
        },
        "guardrails": {
            "baseline_task_success_rate": baseline["task_success_rate"],
            "candidate_task_success_rate": candidate["task_success_rate"],
            "candidate_false_success_count": candidate["false_success_count"],
            "candidate_policy_violation_count": candidate["policy_violation_count"],
            "baseline_evidence_correctness": baseline["evidence_correctness"],
            "candidate_evidence_correctness": candidate["evidence_correctness"],
        },
        "runtime_metrics": runtime,
        "compatibility_errors": compatibility,
        "reasons": reasons,
        "scope": "DeepSeek model executed through pinned DeepSeek Harness only; this does not establish the same effect for Codex.",
        "generated_at": utc_stamp(),
    }


def write_recommendation_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# DeepSeek Harness Screening Recommendation",
        "",
        f"- Advisory decision: `{payload['advisory_decision']}`",
        "- Human decision: `pending`",
        f"- Paired trials: {payload['observed_paired_trials']} / {payload['expected_paired_trials']}",
        f"- Changed LOC reduction: {payload['target_metric']['reduction_ratio']:.1%}",
        "",
        "## Reasons",
        "",
        *[f"- {reason}" for reason in payload["reasons"]],
        "",
        "## Boundary",
        "",
        payload["scope"],
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
