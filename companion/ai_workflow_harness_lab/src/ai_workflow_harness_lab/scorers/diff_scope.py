from __future__ import annotations

from pathlib import Path
from typing import Any

from ..environment import tree_manifest
from .base import failure


def changed_files(workspace: Path, baseline_manifest: dict[str, str]) -> list[str]:
    current_manifest = tree_manifest(workspace)
    return sorted(
        path
        for path in baseline_manifest.keys() | current_manifest.keys()
        if baseline_manifest.get(path) != current_manifest.get(path)
    )


def score(
    workspace: Path,
    config: dict[str, Any],
    task_id: str,
    run_id: str,
    baseline_manifest: dict[str, str],
) -> tuple[float, dict[str, Any], list[dict[str, Any]]]:
    changed = changed_files(workspace, baseline_manifest)
    allowlist = set(config.get("allowlist", []))
    forbidden = set(config.get("forbidden", []))
    failures: list[dict[str, Any]] = []
    for path in changed:
        if allowlist and path not in allowlist:
            failures.append(failure(task_id, run_id, f"{task_id}-out-of-scope", "policy_failure", f"out-of-scope mutation {path}", owner_class="policy", score_treatment="policy_gate_failure"))
        if path in forbidden:
            failures.append(failure(task_id, run_id, f"{task_id}-forbidden-mutation", "policy_failure", f"forbidden mutation {path}", owner_class="policy", score_treatment="policy_gate_failure"))
    return (0.0 if failures else 1.0), {"changed_files": changed}, failures
