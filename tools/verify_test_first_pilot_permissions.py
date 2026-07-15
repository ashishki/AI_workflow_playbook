#!/usr/bin/env python3
"""Probe the frozen Codex permission profile without making a model request."""

from __future__ import annotations

import os
import shutil
import socket
import subprocess
import sys
import tempfile
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS_DIR))

from test_first_pilot_codex_adapter import (
    CODEX_CLI_VERSION,
    PERMISSION_PROFILE,
    codex_runtime_root,
    permission_config,
    safe_environment,
)


PROBE = r"""
import socket
import sys
from pathlib import Path

workspace, venv_python, sibling, auth_file, port = sys.argv[1:]

def require_denied(raw_path: str) -> None:
    try:
        Path(raw_path).read_bytes()
    except OSError:
        return
    raise AssertionError(f"unexpected read access: {raw_path}")

assert Path.cwd() == Path(workspace)
assert Path(venv_python).is_file()
require_denied(sibling)
require_denied(auth_file)
Path("workspace-write-probe.txt").write_text("ok\n", encoding="utf-8")
try:
    socket.create_connection(("127.0.0.1", int(port)), timeout=0.2)
except OSError:
    pass
else:
    raise AssertionError("network namespace reached the host listener")
print("permission-profile-ok")
"""


def main() -> int:
    codex_bin = shutil.which("codex")
    if codex_bin is None:
        print("Codex executable is unavailable", file=sys.stderr)
        return 2
    version = subprocess.run(
        [codex_bin, "--version"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if version.returncode != 0 or version.stdout.strip() != CODEX_CLI_VERSION:
        print("Codex CLI version does not match the frozen pilot", file=sys.stderr)
        return 2

    auth_file = Path.home() / ".codex/auth.json"
    if not auth_file.is_file():
        print("saved ChatGPT login file is unavailable", file=sys.stderr)
        return 2

    # Keep the lexical .venv path: the adapter grants this root, not its /usr target.
    python_executable = Path(os.path.abspath(sys.executable))
    venv_root = python_executable.parent.parent
    codex_runtime = codex_runtime_root(codex_bin)
    with tempfile.TemporaryDirectory(prefix="tfa-permission-probe-") as raw_temp:
        temp = Path(raw_temp)
        workspace = temp / "workspace"
        workspace.mkdir()
        sibling = temp / "sibling-secret.txt"
        sibling.write_text("denied\n", encoding="utf-8")
        codex_home = temp / "codex-home"
        codex_home.mkdir()

        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            listener.listen()
            port = listener.getsockname()[1]
            command = [
                codex_bin,
                "sandbox",
                "-P",
                PERMISSION_PROFILE,
                "-C",
                str(workspace),
                "-c",
                f'default_permissions="{PERMISSION_PROFILE}"',
                "-c",
                permission_config(venv_root, codex_runtime),
                "-c",
                f"permissions.{PERMISSION_PROFILE}.network.enabled=false",
                "--",
                str(python_executable),
                "-c",
                PROBE,
                str(workspace),
                str(python_executable),
                str(sibling),
                str(auth_file),
                str(port),
            ]
            environment = safe_environment(dict(os.environ), python_executable)
            environment["CODEX_HOME"] = str(codex_home)
            environment.pop("CODEX_THREAD_ID", None)
            result = subprocess.run(
                command,
                cwd=workspace,
                env=environment,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=30,
                check=False,
            )
    if result.returncode != 0 or result.stdout.strip() != "permission-profile-ok":
        print(result.stderr or result.stdout or "permission probe failed", file=sys.stderr)
        return 1
    print("permission-profile: ok; workspace-only write, bounded read, network denied")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
