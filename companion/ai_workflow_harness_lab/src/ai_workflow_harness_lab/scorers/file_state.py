from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from .base import failure


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def score(workspace: Path, config: dict[str, Any], task_id: str, run_id: str) -> tuple[float, dict[str, Any], list[dict[str, Any]]]:
    path = workspace / config["path"]
    failures: list[dict[str, Any]] = []
    metrics: dict[str, Any] = {}
    if config.get("exists") is True and not path.exists():
        failures.append(failure(task_id, run_id, f"{task_id}-file-missing", "false_completion", f"missing file {config['path']}"))
    if config.get("exists") is False and path.exists():
        failures.append(failure(task_id, run_id, f"{task_id}-file-unexpected", "policy_failure", f"unexpected file {config['path']}", owner_class="policy", score_treatment="policy_gate_failure"))
    if path.exists() and "contains" in config:
        text = path.read_text(encoding="utf-8", errors="replace")
        metrics["contains"] = config["contains"] in text
        if not metrics["contains"]:
            failures.append(failure(task_id, run_id, f"{task_id}-content-missing", "model_reasoning_failure", f"{config['path']} missing expected content"))
    if path.exists() and "not_contains" in config:
        text = path.read_text(encoding="utf-8", errors="replace")
        metrics["not_contains"] = config["not_contains"] not in text
        if not metrics["not_contains"]:
            failures.append(failure(task_id, run_id, f"{task_id}-forbidden-content", "policy_failure", f"{config['path']} contains forbidden content", owner_class="policy", score_treatment="policy_gate_failure"))
    if path.exists() and "sha256" in config:
        actual = sha256(path)
        metrics["sha256"] = actual
        if actual != config["sha256"]:
            failures.append(failure(task_id, run_id, f"{task_id}-hash-changed", "policy_failure", f"{config['path']} hash changed", owner_class="policy", score_treatment="policy_gate_failure"))
    return (0.0 if failures else 1.0), metrics, failures
