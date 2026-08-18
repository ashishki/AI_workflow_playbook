"""Repository-wide pytest policy for portable core and environment pilots."""

from __future__ import annotations

import os
import shutil
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parent
HARNESS_SRC = ROOT / "companion" / "ai_workflow_harness_lab" / "src"
ENVIRONMENT_PILOT_MODULES = {
    "test_test_first_pilot_permissions.py": ("codex",),
    "test_test_first_pilot_toolchain.py": ("codex", "bwrap"),
}


def _missing_prerequisites(requirements: tuple[str, ...]) -> list[str]:
    missing: list[str] = []
    for requirement in requirements:
        if requirement == "codex" and shutil.which("codex") is None:
            missing.append("Codex CLI")
        elif requirement == "bwrap" and not Path("/usr/bin/bwrap").is_file():
            missing.append("/usr/bin/bwrap")
    return missing


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "environment_pilot: requires the frozen local Codex and sandbox toolchain",
    )
    inherited = [value for value in os.environ.get("PYTHONPATH", "").split(os.pathsep) if value]
    required = [str(ROOT), str(HARNESS_SRC)]
    os.environ["PYTHONPATH"] = os.pathsep.join(dict.fromkeys([*required, *inherited]))


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    marker = pytest.mark.environment_pilot
    for item in items:
        filename = Path(str(item.fspath)).name
        requirements = ENVIRONMENT_PILOT_MODULES.get(filename)
        if requirements is None:
            continue
        item.add_marker(marker)
        missing = _missing_prerequisites(requirements)
        if missing:
            item.add_marker(
                pytest.mark.skip(
                    reason=(
                        "environment pilot not run; missing prerequisite(s): "
                        + ", ".join(missing)
                    )
                )
            )
