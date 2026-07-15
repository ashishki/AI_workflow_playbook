#!/usr/bin/env python3
"""Fail closed when the frozen local pilot toolchain has drifted."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import stat
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LOCK = ROOT / "reports/test_first_pilot/shishki_bot_v1/TOOLCHAIN.json"
CODEX_ENTRYPOINT = Path(
    "/home/ashishki/.nvm/versions/node/v22.22.1/lib/node_modules/@openai/codex/"
    "node_modules/@openai/codex-linux-x64/vendor/x86_64-unknown-linux-musl/bin/codex"
)
CODEX_PACKAGE_JSON = Path(
    "/home/ashishki/.nvm/versions/node/v22.22.1/lib/node_modules/@openai/codex/package.json"
)
CODEX_PLATFORM_PACKAGE_JSON = Path(
    "/home/ashishki/.nvm/versions/node/v22.22.1/lib/node_modules/@openai/codex/"
    "node_modules/@openai/codex-linux-x64/vendor/x86_64-unknown-linux-musl/"
    "codex-package.json"
)
BWRAP = Path("/usr/bin/bwrap")
RUNNER_BINARIES = {
    "bash": Path("/usr/bin/bash"),
    "cp": Path("/usr/bin/cp"),
    "git": Path("/usr/bin/git"),
    "mkdir": Path("/usr/bin/mkdir"),
    "sha256sum": Path("/usr/bin/sha256sum"),
    "sh": Path("/bin/sh"),
}
PINNED_VERSIONS = {
    "bwrap": "bubblewrap 0.9.0",
    "codex": "codex-cli 0.144.4",
    "git": "git version 2.43.0",
}
PYCACHE_PREFIX = "/dev/null/test-first-pilot-pycache"
SITE_PACKAGES = ROOT / ".venv/lib/python3.12/site-packages"
VERSION_METADATA = {
    "harness_version": SITE_PACKAGES
    / "ai_workflow_harness_lab-0.1.0.dist-info/METADATA",
    "jsonschema_version": SITE_PACKAGES / "jsonschema-4.26.0.dist-info/METADATA",
    "pytest_version": SITE_PACKAGES / "pytest-9.1.1.dist-info/METADATA",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def clean_environment() -> dict[str, str]:
    return {
        "HOME": os.environ.get("HOME", "/nonexistent"),
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "PATH": f"{CODEX_ENTRYPOINT.parent}:/usr/bin:/bin",
        "PIP_CONFIG_FILE": "/dev/null",
        "PIP_DISABLE_PIP_VERSION_CHECK": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONNOUSERSITE": "1",
        "PYTHONPYCACHEPREFIX": PYCACHE_PREFIX,
        "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
    }


def metadata_version(path: Path) -> str:
    for line in path.read_bytes().splitlines():
        if line.startswith(b"Version: "):
            return line.removeprefix(b"Version: ").decode("ascii")
        if not line:
            break
    raise RuntimeError(f"version is missing from {path}")


def reject_symlink_components(path: Path) -> None:
    current = Path(path.anchor)
    for part in path.parts[1:]:
        current /= part
        try:
            mode = current.lstat().st_mode
        except FileNotFoundError:
            return
        if stat.S_ISLNK(mode):
            raise RuntimeError(f"symlink is not allowed in site-packages path: {current}")


def site_packages_state(root: Path = SITE_PACKAGES) -> dict[str, object]:
    reject_symlink_components(root)
    if not root.is_dir():
        raise RuntimeError(f"site-packages root is unavailable: {root}")
    lines: list[bytes] = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        mode = path.lstat().st_mode
        if stat.S_ISLNK(mode):
            raise RuntimeError(f"site-packages symlink is not allowed: {relative}")
        if "__pycache__" in relative.parts or path.suffix == ".pyc":
            continue
        if stat.S_ISDIR(mode):
            continue
        if not stat.S_ISREG(mode):
            raise RuntimeError(
                f"site-packages entry must be a regular file: {relative}"
            )
        lines.append(f"{sha256(path)}  {relative.as_posix()}\n".encode("utf-8"))
    manifest = b"".join(lines)
    return {
        "file_count": len(lines),
        "manifest_sha256": hashlib.sha256(manifest).hexdigest(),
        "root": str(root),
    }


def current_state() -> dict[str, object]:
    python_path = Path(sys.executable).resolve()
    return {
        "bwrap": {
            "path": str(BWRAP),
            "sha256": sha256(BWRAP),
            "version": PINNED_VERSIONS["bwrap"],
        },
        "codex_cli": {
            "entrypoint_path": str(CODEX_ENTRYPOINT),
            "entrypoint_sha256": sha256(CODEX_ENTRYPOINT),
            "package_json_path": str(CODEX_PACKAGE_JSON),
            "package_json_sha256": sha256(CODEX_PACKAGE_JSON),
            "platform_package_json_path": str(CODEX_PLATFORM_PACKAGE_JSON),
            "platform_package_sha256": sha256(CODEX_PLATFORM_PACKAGE_JSON),
            "version": PINNED_VERSIONS["codex"],
        },
        "harness_cli_sha256": sha256(ROOT / ".venv/bin/harness-lab"),
        "harness_version": metadata_version(VERSION_METADATA["harness_version"]),
        "jsonschema_version": metadata_version(VERSION_METADATA["jsonschema_version"]),
        "platform": platform.platform(),
        "pytest_cli_sha256": sha256(ROOT / ".venv/bin/pytest"),
        "pytest_version": metadata_version(VERSION_METADATA["pytest_version"]),
        "python_build": " ".join(sys.version.split()),
        "python_executable_realpath": str(python_path),
        "python_executable_sha256": sha256(python_path),
        "python_implementation": platform.python_implementation(),
        "python_version": platform.python_version(),
        "runner_binaries": {
            name: {
                "path": str(path),
                "realpath": str(path.resolve()),
                "sha256": sha256(path),
                **(
                    {"version": PINNED_VERSIONS["git"]}
                    if name == "git"
                    else {}
                ),
            }
            for name, path in sorted(RUNNER_BINARIES.items())
        },
        "site_packages": site_packages_state(),
        "schema_version": "test_first_pilot.toolchain.v2",
    }


def reexec_isolated() -> None:
    if sys.flags.isolated and sys.flags.no_site:
        return
    executable = str(Path(sys.executable).absolute())
    os.execve(
        executable,
        [
            executable,
            "-I",
            "-S",
            "-B",
            "-X",
            f"pycache_prefix={PYCACHE_PREFIX}",
            str(Path(__file__).resolve()),
            *sys.argv[1:],
        ],
        clean_environment(),
    )


def main() -> int:
    reexec_isolated()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lock", type=Path, default=DEFAULT_LOCK)
    args = parser.parse_args()
    expected = json.loads(args.lock.read_text(encoding="utf-8"))
    observed = current_state()
    if observed != expected:
        print(
            json.dumps(
                {"status": "drift", "expected": expected, "observed": observed},
                indent=2,
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 1
    print(json.dumps({"status": "ok", "toolchain": expected}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
