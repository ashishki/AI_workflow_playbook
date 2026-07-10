from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from .base import failure


def score(workspace: Path, config: dict[str, Any], task_id: str, run_id: str) -> tuple[float, dict[str, Any], list[dict[str, Any]]]:
    command = config["command"]
    result = subprocess.run(command, cwd=workspace, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    expected = int(config.get("exit_code", 0))
    metrics = {"exit_code": result.returncode, "stdout": result.stdout[-500:], "stderr": result.stderr[-500:]}
    if result.returncode != expected:
        return 0.0, metrics, [failure(task_id, run_id, f"{task_id}-shell", "model_reasoning_failure", f"shell scorer expected exit {expected}, got {result.returncode}")]
    return 1.0, metrics, []
