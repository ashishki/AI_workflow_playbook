from __future__ import annotations

import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def run_hook(name: str, payload: dict[str, object], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(ROOT / "hooks" / name)],
        input=json.dumps(payload),
        cwd=cwd or ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def test_guard_files_blocks_protected_file() -> None:
    result = run_hook("guard_files.sh", {"tool_input": {"file_path": "docs/IMPLEMENTATION_CONTRACT.md"}})

    assert result.returncode == 2
    assert "immutable" in result.stderr


def test_guard_files_allows_unprotected_file() -> None:
    result = run_hook("guard_files.sh", {"tool_input": {"file_path": "docs/tasks.md"}})

    assert result.returncode == 0


def test_enforce_codex_exec_blocks_application_code() -> None:
    result = run_hook("enforce_codex_exec.sh", {"tool_input": {"file_path": "src/app.py"}})

    assert result.returncode == 2
    assert "direct Claude edits" in result.stderr


def test_log_bash_writes_command_log(tmp_path: Path) -> None:
    log_path = tmp_path / "hooks_log.txt"
    result = subprocess.run(
        ["bash", str(ROOT / "hooks/log_bash.sh")],
        input=json.dumps(
            {
                "tool_input": {"command": "python3 -m pytest -q"},
                "tool_response": {"exit_code": 1, "stdout": ""},
            }
        ),
        cwd=ROOT,
        env={"PLAYBOOK_HOOKS_LOG": str(log_path)},
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 0
    assert "python3 -m pytest -q" in log_path.read_text(encoding="utf-8")
