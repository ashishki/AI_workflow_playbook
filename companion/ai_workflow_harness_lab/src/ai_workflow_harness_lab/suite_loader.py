from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import Suite, SuiteTask


class SuiteError(ValueError):
    pass


def load_suite(path: Path) -> Suite:
    path = path.resolve()
    config_path = path / "suite.json"
    if not config_path.exists():
        raise SuiteError(f"missing suite.json: {config_path}")
    data = json.loads(config_path.read_text(encoding="utf-8"))
    for field in ("suite_id", "version", "tasks"):
        if field not in data:
            raise SuiteError(f"suite.json missing {field}")
    tasks: list[SuiteTask] = []
    for item in data["tasks"]:
        tasks.append(load_task(path, item))
    return Suite(path=path, suite_id=data["suite_id"], version=data["version"], tasks=tasks)


def load_task(suite_path: Path, item: dict[str, Any]) -> SuiteTask:
    required = {
        "task_id",
        "version",
        "title",
        "fixture",
        "baseline_prompt",
        "playbook_prompt",
        "scorers",
        "correction_budget",
        "expected_failure_taxonomy",
    }
    missing = sorted(required - set(item))
    if missing:
        raise SuiteError(f"task missing fields: {', '.join(missing)}")
    task = SuiteTask(
        task_id=str(item["task_id"]),
        version=str(item["version"]),
        title=str(item["title"]),
        fixture=suite_path / str(item["fixture"]),
        baseline_prompt=suite_path / str(item["baseline_prompt"]),
        playbook_prompt=suite_path / str(item["playbook_prompt"]),
        scorers=list(item["scorers"]),
        correction_budget=int(item["correction_budget"]),
        expected_failure_taxonomy=list(item["expected_failure_taxonomy"]),
    )
    for path in (task.fixture, task.baseline_prompt, task.playbook_prompt):
        if not path.exists():
            raise SuiteError(f"task {task.task_id} missing path: {path}")
    if not task.fixture.is_dir():
        raise SuiteError(f"task {task.task_id} fixture is not a directory: {task.fixture}")
    if not task.scorers:
        raise SuiteError(f"task {task.task_id} has no scorers")
    return task
