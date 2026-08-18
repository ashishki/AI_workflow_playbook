"""Repository-level pytest classification for frozen environment pilots."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest


PILOT_REQUIREMENTS = {
    ("test_test_first_pilot_permissions.py", "test_frozen_permission_profile_denies_sibling_auth_and_network_access"): {"codex", "bwrap"},
    ("test_test_first_pilot_toolchain.py", "test_frozen_toolchain_matches_current_pilot_environment"): {"codex", "bwrap"},
    ("test_test_first_pilot_toolchain.py", "test_toolchain_verifier_fails_closed_on_drift"): {"codex", "bwrap"},
    ("test_test_first_pilot_toolchain.py", "test_runner_pid_namespace_stops_detached_descendants"): {"bwrap"},
}


def missing_prerequisites(requirements: set[str]) -> list[str]:
    missing: list[str] = []
    if "codex" in requirements and shutil.which("codex") is None:
        missing.append("codex")
    if "bwrap" in requirements and not Path("/usr/bin/bwrap").is_file():
        missing.append("/usr/bin/bwrap")
    return missing


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Mark host-bound checks and skip only when their prerequisites are absent."""
    marker = pytest.mark.environment_pilot
    for item in items:
        key = (Path(str(item.fspath)).name, item.name)
        requirements = PILOT_REQUIREMENTS.get(key)
        if requirements is None:
            continue
        item.add_marker(marker)
        missing = missing_prerequisites(requirements)
        if missing:
            item.add_marker(
                pytest.mark.skip(
                    reason="environment pilot not run; missing prerequisites: " + ", ".join(missing)
                )
            )
