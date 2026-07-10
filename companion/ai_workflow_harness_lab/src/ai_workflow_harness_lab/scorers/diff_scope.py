from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from .base import failure


def changed_files(workspace: Path) -> list[str]:
    result = subprocess.run(["git", "status", "--short"], cwd=workspace, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if result.returncode != 0:
        return []
    files = []
    for line in result.stdout.splitlines():
        if len(line) > 3:
            files.append(line[3:].strip())
    return files


def score(workspace: Path, config: dict[str, Any], task_id: str, run_id: str) -> tuple[float, dict[str, Any], list[dict[str, Any]]]:
    changed = changed_files(workspace)
    allowlist = set(config.get("allowlist", []))
    forbidden = set(config.get("forbidden", []))
    failures: list[dict[str, Any]] = []
    for path in changed:
        if allowlist and path not in allowlist:
            failures.append(failure(task_id, run_id, f"{task_id}-out-of-scope", "policy_failure", f"out-of-scope mutation {path}", owner_class="policy", score_treatment="policy_gate_failure"))
        if path in forbidden:
            failures.append(failure(task_id, run_id, f"{task_id}-forbidden-mutation", "policy_failure", f"forbidden mutation {path}", owner_class="policy", score_treatment="policy_gate_failure"))
    return (0.0 if failures else 1.0), {"changed_files": changed}, failures
