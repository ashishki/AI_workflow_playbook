from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..environment import safe_workspace_path
from .base import failure


def read_path(data: Any, dotted: str) -> Any:
    current = data
    for part in dotted.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def score(workspace: Path, config: dict[str, Any], task_id: str, run_id: str) -> tuple[float, dict[str, Any], list[dict[str, Any]]]:
    try:
        path = safe_workspace_path(workspace, config["path"])
    except ValueError as exc:
        return 0.0, {}, [
            failure(
                task_id,
                run_id,
                f"{task_id}-unsafe-json-path",
                "policy_failure",
                str(exc),
                owner_class="policy",
                score_treatment="policy_gate_failure",
            )
        ]
    failures: list[dict[str, Any]] = []
    metrics: dict[str, Any] = {}
    if not path.exists():
        return 0.0, metrics, [failure(task_id, run_id, f"{task_id}-json-missing", "model_reasoning_failure", f"missing json {config['path']}")]
    data = json.loads(path.read_text(encoding="utf-8"))
    for field, expected in config.get("equals", {}).items():
        actual = read_path(data, field)
        metrics[field] = actual
        if actual != expected:
            failures.append(failure(task_id, run_id, f"{task_id}-{field}-mismatch", "model_reasoning_failure", f"{field} expected {expected!r}, got {actual!r}"))
    return (0.0 if failures else 1.0), metrics, failures
