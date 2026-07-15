from __future__ import annotations

import os
import socket
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from ai_workflow_harness_lab.runner import PROJECT_ROOT, materialize_command
from ai_workflow_harness_lab.scorers.shell import score


SANDBOX = PROJECT_ROOT / "tools/test_first_pilot_sandbox.py"
BWRAP = Path("/usr/bin/bwrap")


def sandbox_command(workspace: Path, *command: str) -> list[str]:
    return [
        sys.executable,
        str(SANDBOX),
        "--workspace",
        str(workspace),
        "--",
        *command,
    ]


@pytest.mark.skipif(not BWRAP.is_file(), reason="bubblewrap is required for the Linux pilot")
def test_sandbox_clears_secrets_blocks_host_writes_and_unshares_network(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    host_secret = tmp_path / "host-secret.txt"
    host_secret.write_text("not-for-verifier\n", encoding="utf-8")

    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen()
        port = listener.getsockname()[1]
        probe = f"""
import os
import socket
from pathlib import Path

assert Path.cwd() == Path('/workspace')
assert os.environ['HOME'] == '/tmp/home'
assert 'TFA_HOST_SECRET' not in os.environ
assert not Path({str(host_secret)!r}).exists()
assert not Path('/etc/passwd').exists()
assert not Path('/usr/bin/git').exists()
try:
    Path('forbidden.txt').write_text('no')
except OSError:
    pass
else:
    raise AssertionError('workspace was writable')
Path('/tmp/allowed.txt').write_text('ok')
try:
    socket.create_connection(('127.0.0.1', {port}), timeout=0.2)
except OSError:
    pass
else:
    raise AssertionError('host network namespace was reachable')
print('sandbox-ok')
"""
        env = {**os.environ, "TFA_HOST_SECRET": "must-not-propagate"}
        result = subprocess.run(
            sandbox_command(workspace, sys.executable, "-c", probe),
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10,
            check=False,
        )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "sandbox-ok"
    assert not (workspace / "forbidden.txt").exists()


@pytest.mark.skipif(not BWRAP.is_file(), reason="bubblewrap is required for the Linux pilot")
def test_sandbox_propagates_verifier_exit_code(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    result = subprocess.run(
        sandbox_command(workspace, sys.executable, "-c", "raise SystemExit(7)"),
        timeout=10,
        check=False,
    )

    assert result.returncode == 7


@pytest.mark.skipif(not BWRAP.is_file(), reason="bubblewrap is required for the Linux pilot")
def test_shell_scorer_materializes_project_root_and_uses_sandbox(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace with spaces"
    workspace.mkdir()
    (workspace / "probe.py").write_text(
        "from pathlib import Path\nassert Path.cwd() == Path('/workspace')\n",
        encoding="utf-8",
    )
    command = (
        "{python} {project_root}/tools/test_first_pilot_sandbox.py "
        "--workspace {workspace} -- {python} probe.py"
    )

    value, metrics, failures = score(
        workspace,
        {"command": command, "exit_code": 0, "timeout": 10},
        "task",
        "run",
    )

    assert value == 1.0, metrics
    assert failures == []
    assert "{project_root}" not in metrics["command"]
    assert str(PROJECT_ROOT / "tools/test_first_pilot_sandbox.py") in metrics["command"]


def test_required_verifier_materializes_project_root(tmp_path: Path) -> None:
    task = SimpleNamespace(task_id="task-a")

    rendered = materialize_command(
        ["{python}", "{project_root}/tools/probe.py", "{workspace}"],
        tmp_path,
        task,
        "baseline",
        0,
    )

    assert rendered == [
        sys.executable,
        str(PROJECT_ROOT / "tools/probe.py"),
        str(tmp_path),
    ]
