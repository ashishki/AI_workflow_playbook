from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ChangeabilityError(ValueError):
    pass


def load_changeability_suite(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    required = {"schema_version", "suite_id", "version", "evaluation_mode", "sequences"}
    missing = sorted(required - set(data))
    if missing:
        raise ChangeabilityError(f"suite missing fields: {', '.join(missing)}")
    if data["schema_version"] != "playbook.changeability_suite.v1":
        raise ChangeabilityError("unsupported changeability suite schema_version")
    if data["evaluation_mode"] not in {"mechanism_demonstration", "empirical"}:
        raise ChangeabilityError("unsupported evaluation_mode")
    if not isinstance(data.get("sequences"), list) or not data["sequences"]:
        raise ChangeabilityError("suite must contain at least one sequence")
    for sequence in data["sequences"]:
        tasks = sequence.get("tasks") if isinstance(sequence, dict) else None
        if not isinstance(tasks, list) or len(tasks) < 3:
            raise ChangeabilityError("each changeability_sequence requires at least three tasks")
    return data


def summarize_sequence(sequence: dict[str, Any]) -> dict[str, Any]:
    tasks = sequence["tasks"]
    policy_violations = [item for task in tasks for item in task.get("policy_violations", [])]
    architecture_violations = [item for task in tasks for item in task.get("architecture_violations", [])]
    return {
        "sequence_id": sequence["sequence_id"],
        "success_each_step": [bool(task["success"]) for task in tasks],
        "diff_lines_each_step": [int(task["diff_lines"]) for task in tasks],
        "files_touched_each_step": [int(task["files_touched"]) for task in tasks],
        "new_test_failures": sum(int(task["new_test_failures"]) for task in tasks),
        "required_refactor_before_small_change": any(bool(task["required_refactor_before_change"]) for task in tasks[1:]),
        "tool_calls": sum(int(task["tool_calls"]) for task in tasks),
        "tokens": sum(int(task["tokens"]) for task in tasks),
        "latency_ms": sum(int(task["latency_ms"]) for task in tasks),
        "policy_violations": policy_violations,
        "architecture_violations": architecture_violations,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Changeability Sequence Result",
        "",
        report["status"],
        "",
        f"- Suite: {report['suite_id']} {report['suite_version']}",
        f"- Evaluation mode: {report['evaluation_mode']}",
        f"- Sequences: {report['summary']['sequence_count']}",
        f"- All steps succeeded: {report['summary']['all_steps_succeeded']}",
        f"- Total diff lines: {report['summary']['total_diff_lines']}",
        f"- Total files touched: {report['summary']['total_files_touched']}",
        "",
        "This synthetic fixture is a runnable mechanism demonstration only. It does not prove maintainability of real systems.",
        "",
    ]
    return "\n".join(lines)


def run_changeability_suite(suite_path: Path, output_dir: Path) -> dict[str, Any]:
    suite = load_changeability_suite(suite_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    sequence_results = [summarize_sequence(sequence) for sequence in suite["sequences"]]
    total_diff = sum(sum(item["diff_lines_each_step"]) for item in sequence_results)
    total_files = sum(sum(item["files_touched_each_step"]) for item in sequence_results)
    all_success = all(all(item["success_each_step"]) for item in sequence_results)
    status = (
        "mechanism demonstration, not empirical proof of maintainability"
        if suite["evaluation_mode"] == "mechanism_demonstration"
        else "empirical changeability result"
    )
    report = {
        "schema_version": "playbook.changeability_result.v1",
        "suite_id": suite["suite_id"],
        "suite_version": suite["version"],
        "evaluation_mode": suite["evaluation_mode"],
        "status": status,
        "sequence_results": sequence_results,
        "summary": {
            "sequence_count": len(sequence_results),
            "all_steps_succeeded": all_success,
            "total_diff_lines": total_diff,
            "total_files_touched": total_files,
        },
    }
    (output_dir / "changeability_result.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output_dir / "changeability_result.md").write_text(render_markdown(report), encoding="utf-8")
    return report
