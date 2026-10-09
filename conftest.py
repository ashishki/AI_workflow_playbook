"""Repository-wide pytest policy for portable core and environment pilots."""

from __future__ import annotations

import os
import json
import shutil
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parent
HARNESS_SRC = ROOT / "companion" / "ai_workflow_harness_lab" / "src"
ENVIRONMENT_PILOT_TESTS = {
    ("test_test_first_pilot_permissions.py", "test_frozen_permission_profile_denies_sibling_auth_and_network_access"):
        ("pinned_codex", "saved_auth"),
    ("test_test_first_pilot_toolchain.py", "test_frozen_toolchain_matches_current_pilot_environment"):
        ("frozen_host",),
    ("test_test_first_pilot_toolchain.py", "test_runner_pid_namespace_stops_detached_descendants"):
        ("posix", "bwrap"),
    ("test_test_first_pilot_toolchain.py", "test_toolchain_rejects_special_site_package_entries"):
        ("posix",),
    ("test_test_first_pilot_toolchain.py", "test_runner_requires_one_terminal_critic_allow"):
        ("bash",),
    ("test_test_first_pilot_toolchain.py", "test_runner_requires_one_terminal_approval_decision"):
        ("bash",),
}


def _missing_prerequisites(requirements: tuple[str, ...]) -> list[str]:
    missing: list[str] = []
    for requirement in requirements:
        if requirement == "pinned_codex":
            executable = shutil.which("codex")
            if executable is None:
                missing.append("pinned Codex CLI 0.144.4")
                continue
            result = subprocess.run([executable, "--version"], capture_output=True,
                                    text=True, timeout=10, check=False)
            if result.returncode != 0:
                raise pytest.UsageError("installed Codex CLI identity check failed")
            if result.stdout.strip() != "codex-cli 0.144.4":
                missing.append("pinned Codex CLI 0.144.4 (installed identity differs)")
        elif requirement == "saved_auth" and not (Path.home() / ".codex/auth.json").is_file():
            missing.append("saved-login host setup (contents are not read)")
        elif requirement == "frozen_host":
            lock = json.loads((ROOT / "reports/test_first_pilot/shishki_bot_v1/TOOLCHAIN.json").read_text())
            paths = [lock["python_executable_realpath"], lock["site_packages"]["root"],
                     lock["codex_cli"]["entrypoint_path"], lock["bwrap"]["path"]]
            paths.extend(value["path"] for value in lock["runner_binaries"].values())
            if any(not Path(path).exists() for path in paths):
                missing.append("historical pinned host paths; source archive is not a live host")
        elif requirement == "bwrap" and not Path("/usr/bin/bwrap").is_file():
            missing.append("/usr/bin/bwrap")
        elif requirement == "bash" and not Path("/usr/bin/bash").is_file():
            missing.append("/usr/bin/bash")
        elif requirement == "posix" and os.name != "posix":
            missing.append("POSIX host capability")
    return missing


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption("--strict-environment-pilots", action="store_true", default=False,
                     help="Fail collection when a selected historical host probe lacks prerequisites.")


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "environment_pilot: requires the frozen local Codex and sandbox toolchain",
    )
    inherited = [value for value in os.environ.get("PYTHONPATH", "").split(os.pathsep) if value]
    required = [str(ROOT), str(HARNESS_SRC)]
    os.environ["PYTHONPATH"] = os.pathsep.join(dict.fromkeys([*required, *inherited]))


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    marker = pytest.mark.environment_pilot
    for item in items:
        filename = Path(str(item.fspath)).name
        requirements = ENVIRONMENT_PILOT_TESTS.get((filename, getattr(item, "originalname", None) or item.name))
        if requirements is None:
            continue
        item.add_marker(marker)
        missing = _missing_prerequisites(requirements)
        if missing:
            if config.getoption("strict_environment_pilots"):
                raise pytest.UsageError("selected historical host probe lacks prerequisites: " + ", ".join(missing))
            item.add_marker(
                pytest.mark.skip(
                    reason=(
                        "environment pilot not run; missing prerequisite(s): "
                        + ", ".join(missing)
                    )
                )
            )
