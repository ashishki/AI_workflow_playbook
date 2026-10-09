from pathlib import Path
from unittest.mock import patch
import importlib.util

import pytest
_spec = importlib.util.spec_from_file_location("repository_environment_policy", Path(__file__).resolve().parents[2] / "conftest.py")
policy = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(policy)


class Item:
    def __init__(self, filename, name):
        self.fspath = Path(filename)
        self.name = self.originalname = name
        self.markers = []

    def add_marker(self, marker):
        self.markers.append(marker)


class Config:
    def __init__(self, strict=False):
        self.strict = strict

    def getoption(self, name):
        assert name == "strict_environment_pilots"
        return self.strict


def test_unavailable_host_does_not_skip_portable_contracts_in_same_module():
    live = Item("test_test_first_pilot_toolchain.py", "test_frozen_toolchain_matches_current_pilot_environment")
    portable = Item("test_test_first_pilot_toolchain.py", "test_toolchain_lock_pins_import_closure_and_absolute_executables")
    with patch.object(policy, "_missing_prerequisites", return_value=["historical host"]):
        policy.pytest_collection_modifyitems(Config(), [live, portable])
    assert {m.name for m in live.markers} == {"environment_pilot", "skip"}
    assert portable.markers == []


def test_matching_prerequisites_leave_real_probe_assertions_active():
    item = Item("test_test_first_pilot_permissions.py", "test_frozen_permission_profile_denies_sibling_auth_and_network_access")
    with patch.object(policy, "_missing_prerequisites", return_value=[]):
        policy.pytest_collection_modifyitems(Config(), [item])
    assert [m.name for m in item.markers] == ["environment_pilot"]


def test_strict_mode_refuses_prerequisite_skips():
    item = Item("test_test_first_pilot_permissions.py", "test_frozen_permission_profile_denies_sibling_auth_and_network_access")
    with patch.object(policy, "_missing_prerequisites", return_value=["pinned CLI"]):
        with pytest.raises(pytest.UsageError, match="lacks prerequisites"):
            policy.pytest_collection_modifyitems(Config(strict=True), [item])
    assert all(m.name != "skip" for m in item.markers)


def test_cli_identity_failure_is_not_converted_to_unavailable_skip():
    with patch.object(policy.shutil, "which", return_value="/unit/codex"), \
         patch.object(policy.subprocess, "run", return_value=type("R", (), {"returncode": 1})()):
        with pytest.raises(pytest.UsageError, match="identity check failed"):
            policy._missing_prerequisites(("pinned_codex",))
