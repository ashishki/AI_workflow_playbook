from __future__ import annotations

import json
import statistics
from pathlib import Path
from typing import Any


def find_bundles(path: Path) -> list[Path]:
    return sorted(path.rglob("bundle.json"))


def load_trial(bundle_path: Path) -> dict[str, Any]:
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    scorer_outputs = []
    for ref in bundle.get("scorer_outputs", []):
        scorer_outputs.append(json.loads((bundle_path.parent / ref["path"]).read_text(encoding="utf-8")))
    failures = bundle.get("failure_records", [])
    scores = [float(output.get("score", 0.0)) for output in scorer_outputs]
    return {
        "bundle": str(bundle_path),
        "task_id": bundle["task_id"],
        "condition": bundle["condition"],
        "valid": not any(record.get("invalid_run") for record in failures),
        "score": sum(scores) / len(scores) if scores else 0.0,
        "failures": failures,
        "scorer_outputs": scorer_outputs,
        "receipt_count": len(bundle.get("command_receipts", [])),
    }


def summarize(trials: list[dict[str, Any]]) -> dict[str, Any]:
    scores = [trial["score"] for trial in trials if trial["valid"]]
    failures = [failure for trial in trials for failure in trial["failures"]]
    sample = len(trials)
    valid = sum(1 for trial in trials if trial["valid"])
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
        "regression_rate": "unknown",
        "recovery_success_rate": rate(recovery, max(1, sum(1 for trial in trials if trial["task_id"] == "failed_command_recovery"))),
        "policy_violation_rate": rate(policy, sample),
        "evidence_completeness": rate(sum(1 for trial in trials if trial["receipt_count"] > 0), sample),
        "evidence_correctness": "validated_by_bundle_verifier",
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


def compare(baseline_dir: Path, candidate_dir: Path, output_dir: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    baseline = [load_trial(path) for path in find_bundles(baseline_dir)]
    candidate = [load_trial(path) for path in find_bundles(candidate_dir)]
    report = {
        "schema_version": "harness_lab.comparison_report.v1",
        "baseline": summarize(baseline),
        "candidate": summarize(candidate),
        "raw_trials": {"baseline": baseline, "candidate": candidate},
        "hard_gates": {
            "candidate_policy_violations": summarize(candidate)["policy_violation_rate"],
            "candidate_false_success": summarize(candidate)["false_success_rate"],
            "single_run_stability_warning": len(candidate) < 2 or len(baseline) < 2,
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
            "",
            "Raw trial details are in `comparison_report.json`.",
            "",
        ]
    )
