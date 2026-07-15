#!/usr/bin/env python3
"""Run a pilot verifier in a read-only, networkless bubblewrap sandbox."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


BWRAP = Path("/usr/bin/bwrap")
PROJECT_ROOT = Path(__file__).resolve().parents[1]
HOST_VENV = PROJECT_ROOT / ".venv"
SANDBOX_VENV = Path("/venv")
SANDBOX_WORKSPACE = Path("/workspace")
SYSTEM_PYTHON = (
    Path(sys.base_prefix)
    / "bin"
    / f"python{sys.version_info.major}.{sys.version_info.minor}"
)
SYSTEM_STDLIB = (
    Path(sys.base_prefix)
    / "lib"
    / f"python{sys.version_info.major}.{sys.version_info.minor}"
)
READ_ONLY_LIBRARY_ROOTS = (Path("/lib"), Path("/lib64"))


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", required=True)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    if args.command and args.command[0] == "--":
        args.command = args.command[1:]
    if not args.command:
        parser.error("a verifier command is required after --")
    return args


def map_executable(command: list[str], workspace: Path) -> list[str]:
    """Map trusted host mount paths to their locations inside the sandbox."""
    mapped = list(command)
    executable = Path(mapped[0])
    if not executable.is_absolute():
        return mapped

    for host_root, sandbox_root in (
        (HOST_VENV, SANDBOX_VENV),
        (workspace, SANDBOX_WORKSPACE),
    ):
        try:
            relative = executable.relative_to(host_root)
        except ValueError:
            continue
        if ".." in relative.parts:
            raise ValueError("verifier executable path may not escape a mounted root")
        mapped[0] = str(sandbox_root / relative)
        return mapped
    return mapped


def build_bwrap_command(workspace: Path, command: list[str]) -> list[str]:
    sandbox_command = [
        str(BWRAP),
        "--die-with-parent",
        "--new-session",
        "--unshare-user",
        "--unshare-ipc",
        "--unshare-pid",
        "--unshare-net",
        "--unshare-uts",
        "--unshare-cgroup-try",
        "--disable-userns",
        "--cap-drop",
        "ALL",
        "--hostname",
        "tfa-verifier",
        "--dir",
        "/usr",
        "--dir",
        "/usr/bin",
        "--ro-bind",
        str(SYSTEM_PYTHON),
        str(SYSTEM_PYTHON),
        "--symlink",
        SYSTEM_PYTHON.name,
        "/usr/bin/python3",
        "--dir",
        "/usr/lib",
        "--ro-bind",
        str(SYSTEM_STDLIB),
        str(SYSTEM_STDLIB),
    ]
    for root in READ_ONLY_LIBRARY_ROOTS:
        if root.exists():
            sandbox_command.extend(("--ro-bind", str(root), str(root)))
    sandbox_command.extend(
        (
            "--ro-bind",
            str(HOST_VENV),
            str(SANDBOX_VENV),
            "--ro-bind",
            str(workspace),
            str(SANDBOX_WORKSPACE),
            "--proc",
            "/proc",
            "--dev",
            "/dev",
            "--tmpfs",
            "/tmp",
            "--dir",
            "/tmp/home",
            "--clearenv",
            "--setenv",
            "HOME",
            "/tmp/home",
            "--setenv",
            "PATH",
            "/venv/bin:/usr/bin",
            "--setenv",
            "LANG",
            "C.UTF-8",
            "--setenv",
            "LC_ALL",
            "C.UTF-8",
            "--setenv",
            "TZ",
            "UTC",
            "--setenv",
            "TMPDIR",
            "/tmp",
            "--setenv",
            "PYTHONDONTWRITEBYTECODE",
            "1",
            "--setenv",
            "PYTHONNOUSERSITE",
            "1",
            "--setenv",
            "PYTHONPYCACHEPREFIX",
            "/dev/null/test-first-pilot-verifier",
            "--setenv",
            "PYTHONHASHSEED",
            "0",
            "--setenv",
            "PYTEST_DISABLE_PLUGIN_AUTOLOAD",
            "1",
            "--chdir",
            str(SANDBOX_WORKSPACE),
            "--",
            *map_executable(command, workspace),
        )
    )
    return sandbox_command


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if sys.platform != "linux":
        print("pilot verifier sandbox requires Linux", file=sys.stderr)
        return 2
    if not BWRAP.is_file() or not os.access(BWRAP, os.X_OK):
        print(f"required bubblewrap executable is unavailable: {BWRAP}", file=sys.stderr)
        return 2
    if not HOST_VENV.is_dir():
        print(f"pilot virtual environment is unavailable: {HOST_VENV}", file=sys.stderr)
        return 2
    if not SYSTEM_PYTHON.is_file() or not SYSTEM_STDLIB.is_dir():
        print("pilot Python toolchain is unavailable", file=sys.stderr)
        return 2

    try:
        workspace = Path(args.workspace).resolve(strict=True)
    except OSError as exc:
        print(f"workspace is unavailable: {exc}", file=sys.stderr)
        return 2
    if not workspace.is_dir():
        print(f"workspace must be a directory: {workspace}", file=sys.stderr)
        return 2

    try:
        completed = subprocess.run(
            build_bwrap_command(workspace, list(args.command)),
            env={},
            check=False,
        )
    except (OSError, ValueError) as exc:
        print(f"pilot verifier sandbox failed to start: {exc}", file=sys.stderr)
        return 2
    return int(completed.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
