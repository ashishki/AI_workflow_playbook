from __future__ import annotations

import json
import statistics
from collections import Counter
from pathlib import Path
from typing import Any

from .evidence import verify_bundle


def find_bundles(path: Path) -> list[Path]:
    return sorted(path.rglob("bundle.json"))


def effective_score(scores: list[float], failures: list[dict[str, Any]]) -> float:
    task_failed = any(
        not failure.get("invalid_run")
        and failure.get("score_treatment")
        in {"count_as_task_failure", "policy_gate_failure"}
        for failure in failures
    )
    if task_failed:
        return 0.0
    return sum(scores) / len(scores) if scores else 0.0


def load_trial(bundle_path: Path) -> dict[str, Any]:
    evidence_errors = verify_bundle(bundle_path)
    try:
        bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        task_id = bundle_path.parent.parent.name
        return {
            "bundle": str(bundle_path),
            "repository": None,
            "task_id": task_id,
            "task_spec_version": None,
            "condition": "unknown",
            "adapter_version": None,
            "trial_index": trial_index_from_path(bundle_path),
            "valid": False,
            "evidence_errors": evidence_errors or [f"bundle json invalid: {exc}"],
            "evidence_valid": False,
            "score": 0.0,
            "failures": [],
            "scorer_outputs": [],
            "receipt_count": 0,
        }
    scorer_outputs = []
    eval_unit = None
    if not evidence_errors:
        for ref in bundle.get("scorer_outputs", []):
            scorer_outputs.append(json.loads((bundle_path.parent / ref["path"]).read_text(encoding="utf-8")))
        eval_ref = bundle.get("harness_eval_unit_ref")
        if isinstance(eval_ref, dict):
            eval_unit = json.loads((bundle_path.parent / eval_ref["path"]).read_text(encoding="utf-8"))
    failures = bundle.get("failure_records", [])
    scores = [float(output.get("score", 0.0)) for output in scorer_outputs]
    invalid = bool(evidence_errors) or any(record.get("invalid_run") for record in failures)
    return {
        "bundle": str(bundle_path),
        "repository": bundle.get("repository"),
        "task_id": bundle["task_id"],
        "task_spec_version": bundle.get("task_spec_version"),
        "condition": bundle["condition"],
        "adapter_version": bundle.get("adapter_version"),
        "harness_eval_unit": eval_unit,
        "compatibility_fingerprint": eval_unit.get("compatibility_fingerprint") if isinstance(eval_unit, dict) else None,
        "trial_index": trial_index_from_path(bundle_path),
        "valid": not invalid,
        "evidence_errors": evidence_errors,
        "evidence_valid": not evidence_errors,
        "score": effective_score(scores, failures),
        "failures": failures,
        "scorer_outputs": scorer_outputs,
        "receipt_count": len(bundle.get("command_receipts", [])),
    }


def summarize(trials: list[dict[str, Any]]) -> dict[str, Any]:
    scores = [trial["score"] for trial in trials if trial["valid"]]
    failures = [failure for trial in trials for failure in trial["failures"]]
    sample = len(trials)
    valid = sum(1 for trial in trials if trial["valid"])
    evidence_valid = sum(1 for trial in trials if trial.get("evidence_valid"))
    false_success = sum(1 for failure in failures if failure.get("failure_class") == "false_completion")
    policy = sum(1 for failure in failures if failure.get("failure_class") == "policy_failure")
    recovery = sum(1 for trial in trials if trial["task_id"] == "failed_command_recovery" and trial["score"] == 1.0)
    timeout = sum(1 for failure in failures if failure.get("failure_class") == "timeout")
    return {
        "sample_count": sample,
        "valid_runs": valid,
        "invalid_runs": sample - valid,
        "mean": statistics.mean(scores) if scores else 0.0,
        "median": statistics.median(scores) if scores else 0.0,
        "min": min(scores) if scores else 0.0,
        "max": max(scores) if scores else 0.0,
        "stddev": statistics.stdev(scores) if len(scores) >= 2 else "insufficient_sample",
        "task_success_rate": rate(sum(1 for score in scores if score == 1.0), len(scores)),
        "verified_environment_success_rate": rate(sum(1 for trial in trials if trial["receipt_count"] > 0), sample),
        "false_success_rate": rate(false_success, sample),
        "false_success_count": false_success,
        "regression_rate": "unknown",
        "recovery_success_rate": rate(recovery, max(1, sum(1 for trial in trials if trial["task_id"] == "failed_command_recovery"))),
        "policy_violation_rate": rate(policy, sample),
        "policy_violation_count": policy,
        "evidence_completeness": rate(sum(1 for trial in trials if trial["receipt_count"] > 0), sample),
        "evidence_correctness": rate(evidence_valid, sample),
        "tool_call_count": "unknown",
        "unnecessary_action_count": "unknown",
        "retry_count": "see_raw_trial_table",
        "timeout_rate": rate(timeout, sample),
        "invalid_infrastructure_run_rate": rate(sample - valid, sample),
        "input_tokens": "unknown",
        "output_tokens": "unknown",
        "wall_clock_latency": "unknown",
        "cost_per_attempted_task": "unknown",
        "cost_per_successful_task": "unknown",
        "human_intervention_rate": "unknown",
        "cross_session_continuity_success": rate(sum(1 for trial in trials if trial["task_id"] == "cross_session_resume" and trial["score"] == 1.0), max(1, sum(1 for trial in trials if trial["task_id"] == "cross_session_resume"))),
    }


def rate(numerator: int, denominator: int) -> float:
    return 0.0 if denominator == 0 else numerator / denominator


def trial_index_from_path(bundle_path: Path) -> int | None:
    parent = bundle_path.parent.name
    if parent.startswith("trial-"):
        try:
            return int(parent.split("-", 1)[1])
        except ValueError:
            return None
    return None


def stability_warning(trials: list[dict[str, Any]], minimum_trials_per_task: int) -> bool:
    by_task = Counter(trial["task_id"] for trial in trials)
    return any(count < minimum_trials_per_task for count in by_task.values())


def compatibility_errors(baseline: list[dict[str, Any]], candidate: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    baseline_keys = {(trial["task_id"], trial["trial_index"]) for trial in baseline}
    candidate_keys = {(trial["task_id"], trial["trial_index"]) for trial in candidate}
    if baseline_keys != candidate_keys:
        errors.append("baseline and candidate task/trial sets differ")
    baseline_by_key = {(trial["task_id"], trial["trial_index"]): trial for trial in baseline}
    for trial in candidate:
        key = (trial["task_id"], trial["trial_index"])
        other = baseline_by_key.get(key)
        if not other:
            continue
        for field in ("repository", "task_spec_version", "adapter_version"):
            if trial.get(field) != other.get(field):
                errors.append(f"{field} differs for {trial['task_id']} trial {trial['trial_index']}")
        if trial.get("compatibility_fingerprint") != other.get("compatibility_fingerprint"):
            errors.append(f"harness_eval_unit compatibility differs for {trial['task_id']} trial {trial['trial_index']}")
    return sorted(set(errors))


def compare(
    baseline_dir: Path,
    candidate_dir: Path,
    output_dir: Path,
    *,
    minimum_trials_per_task: int = 2,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    baseline = [load_trial(path) for path in find_bundles(baseline_dir)]
    candidate = [load_trial(path) for path in find_bundles(candidate_dir)]
    baseline_summary = summarize(baseline)
    candidate_summary = summarize(candidate)
    compatibility = compatibility_errors(baseline, candidate)
    report = {
        "schema_version": "harness_lab.comparison_report.v1",
        "baseline": baseline_summary,
        "candidate": candidate_summary,
        "raw_trials": {"baseline": baseline, "candidate": candidate},
        "compatibility_errors": compatibility,
        "hard_gates": {
            "candidate_policy_violation_count": candidate_summary["policy_violation_count"],
            "candidate_policy_violation_rate": candidate_summary["policy_violation_rate"],
            "candidate_false_success_count": candidate_summary["false_success_count"],
            "candidate_false_success_rate": candidate_summary["false_success_rate"],
            "single_run_stability_warning": stability_warning(candidate, minimum_trials_per_task)
            or stability_warning(baseline, minimum_trials_per_task),
        },
        "status": "mechanism demonstration, not empirical proof of Playbook effectiveness",
    }
    (output_dir / "comparison_report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output_dir / "comparison_report.md").write_text(render_markdown(report), encoding="utf-8")
    return report


def render_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Harness Comparison Report",
            "",
            "Mechanism demonstration, not empirical proof of Playbook effectiveness.",
            "",
            f"- Baseline sample count: {report['baseline']['sample_count']}",
            f"- Candidate sample count: {report['candidate']['sample_count']}",
            f"- Baseline task success rate: {report['baseline']['task_success_rate']}",
            f"- Candidate task success rate: {report['candidate']['task_success_rate']}",
            f"- Candidate false-success rate: {report['candidate']['false_success_rate']}",
            f"- Candidate policy violation rate: {report['candidate']['policy_violation_rate']}",
            f"- Candidate evidence correctness: {report['candidate']['evidence_correctness']}",
            f"- Per-task stability warning: {report['hard_gates']['single_run_stability_warning']}",
            "",
            "Raw trial details are in `comparison_report.json`.",
            "",
        ]
    )
