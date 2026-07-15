from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import test_first_pilot_run_seal as run_seal  # noqa: E402


def make_run(root: Path) -> Path:
    (root / ".git/objects").mkdir(parents=True)
    (root / ".git/objects/object").write_bytes(b"git-object\n")
    (root / "baseline/task/trial-0/workspace/__pycache__").mkdir(parents=True)
    (root / "baseline/task/trial-0/workspace/source.py").write_text(
        "VALUE = 1\n", encoding="utf-8"
    )
    (root / "baseline/task/trial-0/workspace/__pycache__/source.pyc").write_bytes(
        b"cache-bytes"
    )
    (root / "baseline/task/trial-0/bundle.json").write_text("{}\n", encoding="utf-8")
    return root


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_seal_is_deterministic_and_includes_git_caches_and_directories(tmp_path: Path) -> None:
    first_root = make_run(tmp_path / "first")
    second_root = make_run(tmp_path / "second")

    first = run_seal.write_seal(first_root)
    second = run_seal.write_seal(second_root)

    assert first.seal_sha256 == second.seal_sha256
    assert (first_root / run_seal.SEAL_NAME).read_bytes() == (
        second_root / run_seal.SEAL_NAME
    ).read_bytes()
    payload = json.loads((first_root / run_seal.SEAL_NAME).read_text(encoding="utf-8"))
    assert payload["entry_count"] == first.entry_count
    assert payload["entries"][".git"]["type"] == "directory"
    assert payload["entries"][".git/objects/object"]["type"] == "file"
    cache = "baseline/task/trial-0/workspace/__pycache__/source.pyc"
    assert payload["entries"][cache]["sha256"] == sha256(first_root / cache)
    assert run_seal.SEAL_NAME not in payload["entries"]
    assert run_seal.verify_seal(first_root).seal_sha256 == first.seal_sha256


def test_workspace_links_and_specials_are_recorded_without_following(tmp_path: Path) -> None:
    root = make_run(tmp_path / "run")
    workspace = root / "baseline/task/trial-0/workspace"
    secret = tmp_path / "outside-secret.txt"
    secret.write_text("first secret\n", encoding="utf-8")
    (workspace / "linked-secret").symlink_to(secret)
    os.mkfifo(workspace / "named-pipe")

    before = run_seal.snapshot_run(root)
    secret.write_text("different secret\n", encoding="utf-8")
    after = run_seal.snapshot_run(root)

    link = "baseline/task/trial-0/workspace/linked-secret"
    pipe = "baseline/task/trial-0/workspace/named-pipe"
    assert before == after
    assert before[link] == {
        "mode": "0777",
        "target": str(secret),
        "type": "symlink",
    }
    assert before[pipe]["type"] == "fifo"
    result = run_seal.write_seal(root)
    assert run_seal.verify_seal(root).seal_sha256 == result.seal_sha256


@pytest.mark.parametrize("entry_kind", ["symlink", "special"])
def test_links_and_specials_outside_workspace_are_rejected(
    tmp_path: Path, entry_kind: str
) -> None:
    root = make_run(tmp_path / "run")
    if entry_kind == "symlink":
        (root / "evidence-link").symlink_to(root / ".git/objects/object")
    else:
        os.mkfifo(root / "evidence-pipe")

    with pytest.raises(run_seal.SealError, match="outside workspace is forbidden"):
        run_seal.snapshot_run(root)


@pytest.mark.parametrize("mutation", ["changed", "deleted", "extra", "type"])
def test_verify_detects_changed_deleted_extra_and_type_drift(
    tmp_path: Path, mutation: str
) -> None:
    root = make_run(tmp_path / "run")
    run_seal.write_seal(root)
    target = root / "baseline/task/trial-0/workspace/source.py"
    if mutation == "changed":
        target.write_text("VALUE = 2\n", encoding="utf-8")
    elif mutation == "deleted":
        target.unlink()
    elif mutation == "extra":
        (target.parent / "extra.py").write_text("EXTRA = True\n", encoding="utf-8")
    else:
        target.unlink()
        target.mkdir()

    with pytest.raises(run_seal.SealError, match="does not match the exact run closure"):
        run_seal.verify_seal(root)


def test_write_is_exclusive_and_refuses_overwrite(tmp_path: Path) -> None:
    root = make_run(tmp_path / "run")
    first = run_seal.write_seal(root)
    original = first.path.read_bytes()

    with pytest.raises(run_seal.SealError, match="already exists"):
        run_seal.write_seal(root)

    assert first.path.read_bytes() == original


def test_write_detects_mutation_between_snapshot_and_final_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = make_run(tmp_path / "run")
    target = root / "baseline/task/trial-0/workspace/source.py"
    real_snapshot = run_seal._snapshot_fd
    calls = 0

    def mutate_after_confirmation(root_fd: int) -> dict[str, dict[str, object]]:
        nonlocal calls
        calls += 1
        result = real_snapshot(root_fd)
        if calls == 2:
            target.write_text("MUTATED = True\n", encoding="utf-8")
        return result

    monkeypatch.setattr(run_seal, "_snapshot_fd", mutate_after_confirmation)

    with pytest.raises(run_seal.MutationError, match="final seal write"):
        run_seal.write_seal(root)
    assert not (root / run_seal.SEAL_NAME).exists()


def test_failed_exclusive_write_does_not_leave_a_partial_seal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = make_run(tmp_path / "run")

    def fail_write(_descriptor: int, _payload: bytes) -> int:
        raise OSError("synthetic short storage failure")

    monkeypatch.setattr(run_seal.os, "write", fail_write)

    with pytest.raises(run_seal.SealError, match="synthetic short storage failure"):
        run_seal.write_seal(root)
    assert not (root / run_seal.SEAL_NAME).exists()


def test_cli_write_and_verify_report_the_seal_digest(tmp_path: Path) -> None:
    root = make_run(tmp_path / "run")
    tool = ROOT / "tools/test_first_pilot_run_seal.py"

    written = subprocess.run(
        [sys.executable, str(tool), "write", str(root)],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    verified = subprocess.run(
        [sys.executable, str(tool), "verify", str(root)],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert written.returncode == 0, written.stderr
    assert verified.returncode == 0, verified.stderr
    written_payload = json.loads(written.stdout)
    verified_payload = json.loads(verified.stdout)
    assert written_payload["status"] == "write"
    assert verified_payload["status"] == "verify"
    assert written_payload["seal_sha256"] == verified_payload["seal_sha256"]
    assert written_payload["seal_sha256"] == sha256(root / run_seal.SEAL_NAME)
