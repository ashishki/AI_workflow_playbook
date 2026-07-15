from __future__ import annotations

import hashlib
import re
import subprocess
from pathlib import Path

from ai_workflow_harness_lab.environment import copy_fixture, init_git, tree_manifest
from ai_workflow_harness_lab.scorers import diff_scope, file_state


def score(workspace: Path, baseline: dict[str, str], allowlist: list[str]):
    return diff_scope.score(
        workspace,
        {"allowlist": allowlist},
        "task",
        "run",
        baseline,
    )


def test_committed_out_of_scope_change_is_still_detected(tmp_path: Path) -> None:
    (tmp_path / "allowed.txt").write_text("before\n", encoding="utf-8")
    (tmp_path / "outside.txt").write_text("before\n", encoding="utf-8")
    baseline = tree_manifest(tmp_path)
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "fixture"], cwd=tmp_path, check=True)
    (tmp_path / "outside.txt").write_text("after\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "hide mutation"], cwd=tmp_path, check=True)

    result, metrics, failures = score(tmp_path, baseline, ["allowed.txt"])

    assert result == 0.0
    assert metrics["changed_files"] == ["outside.txt"]
    assert failures[0]["failure_class"] == "policy_failure"


def test_missing_git_metadata_does_not_hide_out_of_scope_change(tmp_path: Path) -> None:
    (tmp_path / "allowed.txt").write_text("before\n", encoding="utf-8")
    (tmp_path / "outside.txt").write_text("before\n", encoding="utf-8")
    baseline = tree_manifest(tmp_path)
    (tmp_path / "outside.txt").unlink()

    result, metrics, failures = score(tmp_path, baseline, ["allowed.txt"])

    assert result == 0.0
    assert metrics["changed_files"] == ["outside.txt"]
    assert failures[0]["failure_class"] == "policy_failure"


def test_only_allowlisted_manifest_change_passes(tmp_path: Path) -> None:
    (tmp_path / "allowed.txt").write_text("before\n", encoding="utf-8")
    baseline = tree_manifest(tmp_path)
    (tmp_path / "allowed.txt").write_text("after\n", encoding="utf-8")

    result, metrics, failures = score(tmp_path, baseline, ["allowed.txt"])

    assert result == 1.0
    assert metrics["changed_files"] == ["allowed.txt"]
    assert failures == []


def test_fixture_copy_drops_caches_and_manifest_detects_new_cache_files(tmp_path: Path) -> None:
    fixture = tmp_path / "fixture"
    cache = fixture / "pkg/__pycache__"
    cache.mkdir(parents=True)
    (fixture / "pkg/module.py").write_text("VALUE = 1\n", encoding="utf-8")
    (cache / "module.pyc").write_bytes(b"untrusted bytecode")
    workspace = tmp_path / "workspace"

    copy_fixture(fixture, workspace)
    assert not (workspace / "pkg/__pycache__").exists()
    baseline = tree_manifest(workspace)
    created = workspace / "pkg/__pycache__/module.pyc"
    created.parent.mkdir()
    created.write_bytes(b"later bytecode")
    result, metrics, failures = score(workspace, baseline, ["pkg/module.py"])

    assert result == 0.0
    assert metrics["changed_files"] == ["pkg/__pycache__/module.pyc"]
    assert failures[0]["failure_class"] == "policy_failure"


def test_init_git_ignores_inherited_config_templates_and_hooks(
    tmp_path: Path, monkeypatch
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "tracked.txt").write_text("fixture\n", encoding="utf-8")
    hooks = tmp_path / "hooks"
    hooks.mkdir()
    marker = tmp_path / "hook-ran"
    hook = hooks / "pre-commit"
    hook.write_text(f"#!/bin/sh\n/usr/bin/touch {marker}\nexit 1\n", encoding="utf-8")
    hook.chmod(0o700)
    global_config = tmp_path / "gitconfig"
    global_config.write_text(
        f"[core]\n\thooksPath = {hooks}\n[commit]\n\tgpgSign = true\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(global_config))
    monkeypatch.setenv("GIT_CONFIG_COUNT", "1")
    monkeypatch.setenv("GIT_CONFIG_KEY_0", "core.hooksPath")
    monkeypatch.setenv("GIT_CONFIG_VALUE_0", str(hooks))

    commit = init_git(workspace)

    assert re.fullmatch(r"[0-9a-f]{40}", commit)
    assert not marker.exists()
    assert not (workspace / ".git/hooks").exists()


def test_manifest_hashes_symlink_metadata_without_reading_target(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    secret = tmp_path / "secret.txt"
    secret.write_text("first secret\n", encoding="utf-8")
    (workspace / "linked.txt").symlink_to(secret)

    before = tree_manifest(workspace)
    secret.write_text("changed secret\n", encoding="utf-8")
    after = tree_manifest(workspace)

    assert before == after
    assert before["linked.txt"] != hashlib.sha256(secret.read_bytes()).hexdigest()


def test_file_state_rejects_symlink_instead_of_following_it(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    secret = tmp_path / "secret.txt"
    secret.write_text("expected token\n", encoding="utf-8")
    (workspace / "allowed.txt").symlink_to(secret)

    value, _, failures = file_state.score(
        workspace,
        {"path": "allowed.txt", "contains": "expected token"},
        "task",
        "run",
    )

    assert value == 0.0
    assert failures[0]["failure_class"] == "policy_failure"
    assert "symlink forbidden" in failures[0]["message"]
