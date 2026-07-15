from __future__ import annotations

import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any

from .base import failure


PROJECT_ROOT = Path(__file__).resolve().parents[5]


def output_tail(value: str | bytes | None) -> str:
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="replace")
    return (value or "")[-500:]


def score(workspace: Path, config: dict[str, Any], task_id: str, run_id: str) -> tuple[float, dict[str, Any], list[dict[str, Any]]]:
    command = str(config["command"])
    command = command.replace("{python}", shlex.quote(sys.executable))
    command = command.replace("{project_root}", shlex.quote(str(PROJECT_ROOT)))
    command = command.replace("{workspace}", shlex.quote(str(workspace)))
    timeout = float(config["timeout"]) if "timeout" in config else None
    try:
        result = subprocess.run(
            command,
            cwd=workspace,
            shell=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        metrics = {
            "command": command,
            "timeout_seconds": timeout,
            "timed_out": True,
            "stdout": output_tail(exc.stdout),
            "stderr": output_tail(exc.stderr),
        }
        return 0.0, metrics, [
            failure(
                task_id,
                run_id,
                f"{task_id}-shell-timeout",
                "timeout",
                f"shell scorer exceeded {timeout} seconds",
                owner_class="scorer",
                score_treatment="invalid_run_exclude_from_capability_score",
                invalid_run=True,
            )
        ]
    expected = int(config.get("exit_code", 0))
    metrics = {
        "command": command,
        "exit_code": result.returncode,
        "timeout_seconds": timeout,
        "timed_out": False,
        "stdout": output_tail(result.stdout),
        "stderr": output_tail(result.stderr),
    }
    if result.returncode != expected:
        return 0.0, metrics, [failure(task_id, run_id, f"{task_id}-shell", "model_reasoning_failure", f"shell scorer expected exit {expected}, got {result.returncode}")]
    return 1.0, metrics, []
