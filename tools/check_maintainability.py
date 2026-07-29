#!/usr/bin/env python3
"""Report maintainability advisory and stop-ship signals for one task diff."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

try:
    import feature_design_lib
    import playbook_validate
except ImportError:  # pragma: no cover
    from tools import feature_design_lib, playbook_validate  # type: ignore


def git(root: Path, args: list[str]) -> tuple[int, str]:
    result = subprocess.run(["git", *args], cwd=root, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    return result.returncode, result.stdout


def changed_files(root: Path) -> list[str]:
    code, stdout = git(root, ["diff", "--name-only", "HEAD", "--"])
    files = [line.strip() for line in stdout.splitlines() if line.strip()] if code == 0 else []
    other_code, other_stdout = git(root, ["ls-files", "--others", "--exclude-standard"])
    if other_code == 0:
        files.extend(line.strip() for line in other_stdout.splitlines() if line.strip())
    return sorted(set(files))


def changed_lines(root: Path) -> int:
    code, stdout = git(root, ["diff", "--numstat", "HEAD", "--"])
    if code != 0:
        return 0
    total = 0
    for line in stdout.splitlines():
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        for value in parts[:2]:
            if value.isdigit():
                total += int(value)
    return total


def load_task(root: Path, task_id: str) -> dict[str, Any]:
    for block in playbook_validate.parse_task_blocks(root / "docs/tasks.md"):
        if block.task_id == task_id:
            return block.to_record()
    raise SystemExit(f"task {task_id} not found")


def load_design_and_slice(root: Path, task: dict[str, Any]) -> tuple[dict[str, Any] | None, dict[str, Any] | None, list[dict[str, str]]]:
    signals: list[dict[str, str]] = []
    for ref in task.get("design_refs", []):
        path, _raw = playbook_validate.design_registry_path(root, ref)
        if path is None or not path.exists():
            continue
        findings, design = feature_design_lib.validate_design_file(root, path)
        if any(finding.severity == "error" for finding in findings):
            signals.append({"severity": "stop_ship", "check_id": "MAINTAINABILITY_DESIGN_INVALID", "message": "required design has validation errors"})
        if design is None:
            continue
        slice_item = feature_design_lib.find_slice(design, str(task.get("slice_id", ""))) if task.get("slice_id") else None
        return design, slice_item, signals
    return None, None, signals


def evaluate(root: Path, task_id: str) -> dict[str, Any]:
    task = load_task(root, task_id)
    files = changed_files(root)
    line_delta = changed_lines(root)
    design, slice_item, signals = load_design_and_slice(root, task)
    if not files:
        signals.append({"severity": "advisory", "check_id": "MAINTAINABILITY_NO_DIFF", "message": "no git diff against HEAD was observed"})
    budget = feature_design_lib.parse_change_budget(task.get("change_budget") or (slice_item or {}).get("change_budget"))
    if "files" in budget and len(files) > budget["files"]:
        signals.append(
            {
                "severity": "advisory",
                "check_id": "MAINTAINABILITY_CHANGE_BUDGET_FILES",
                "message": f"changed files {len(files)} exceed budget {budget['files']}",
            }
        )
    if "lines" in budget and line_delta > budget["lines"]:
        signals.append(
            {
                "severity": "advisory",
                "check_id": "MAINTAINABILITY_CHANGE_BUDGET_LINES",
                "message": f"line delta {line_delta} exceeds budget {budget['lines']}",
            }
        )
    if slice_item is not None:
        outside, forbidden = feature_design_lib.task_files_within_slice(files, slice_item)
        for path in forbidden:
            signals.append(
                {
                    "severity": "stop_ship",
                    "check_id": "MAINTAINABILITY_FORBIDDEN_FILE",
                    "message": f"changed forbidden file {path}",
                }
            )
        for path in outside:
            signals.append(
                {
                    "severity": "advisory",
                    "check_id": "MAINTAINABILITY_OUTSIDE_ALLOWED_FILES",
                    "message": f"changed file outside approved slice tree {path}",
                }
            )
    if design is None and task.get("planning_depth") in {"compact_design", "designed_slices"}:
        signals.append({"severity": "stop_ship", "check_id": "MAINTAINABILITY_DESIGN_MISSING", "message": "task requires design but no design registry was loaded"})
    status = "stop_ship" if any(signal["severity"] == "stop_ship" for signal in signals) else "advisory" if signals else "pass"
    return {
        "schema_version": "playbook.maintainability_check.v1",
        "task_id": task_id,
        "changed_files": files,
        "changed_file_count": len(files),
        "line_delta": line_delta,
        "signals": signals,
        "status": status,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".")
    parser.add_argument("--task", required=True)
    parser.add_argument("--json", dest="json_path")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.root).resolve()
    report = evaluate(root, args.task)
    if args.json_path:
        output = Path(args.json_path)
        if not output.is_absolute():
            output = root / output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 1 if report["status"] == "stop_ship" else 0


if __name__ == "__main__":
    raise SystemExit(main())
