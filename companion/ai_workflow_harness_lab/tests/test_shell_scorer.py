from __future__ import annotations

import sys
from pathlib import Path

from ai_workflow_harness_lab.scorers.shell import score


def test_shell_scorer_materializes_python_and_workspace(tmp_path: Path) -> None:
    command = (
        '"{python}" -c "from pathlib import Path; '
        "assert Path(r'{workspace}').resolve() == Path.cwd().resolve()\""
    )

    value, metrics, failures = score(
        tmp_path,
        {"command": command, "exit_code": 0, "timeout": 2},
        "task",
        "run",
    )

    assert value == 1.0
    assert failures == []
    assert metrics["exit_code"] == 0
    assert metrics["timed_out"] is False
    assert sys.executable in metrics["command"]


def test_shell_scorer_timeout_is_invalid_run(tmp_path: Path) -> None:
    value, metrics, failures = score(
        tmp_path,
        {"command": '"{python}" -c "import time; time.sleep(1)"', "timeout": 0.01},
        "task",
        "run",
    )

    assert value == 0.0
    assert metrics["timed_out"] is True
    assert failures[0]["failure_class"] == "timeout"
    assert failures[0]["owner_class"] == "scorer"
    assert failures[0]["invalid_run"] is True


def test_unavailable_verifier_is_separate_from_a_failed_task(tmp_path: Path) -> None:
    for exit_code, invalid in ((2, True), (1, False)):
        value, metrics, failures = score(
            tmp_path,
            {"command": f'"{{python}}" -c "raise SystemExit({exit_code})"',
             "exit_code": 0, "invalid_exit_codes": [2]},
            "task", "run",
        )
        assert value == 0
        assert metrics['exit_code'] == exit_code
        assert failures[0]['invalid_run'] is invalid
        assert failures[0]['failure_class'] == (
            'environment_failure' if invalid else 'model_reasoning_failure')
