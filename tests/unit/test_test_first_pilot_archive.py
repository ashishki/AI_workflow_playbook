from __future__ import annotations

import io
import json
import shutil
import subprocess
import sys
import tarfile
from dataclasses import replace
from pathlib import Path

import pytest

from tools import verify_test_first_pilot_archive as archive


ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def retained_source(tmp_path: Path) -> Path:
    source = tmp_path / "source"
    archive.export_git_snapshot(ROOT, archive.RETAINED, source)
    return source


@pytest.mark.parametrize("snapshot", [archive.RETAINED, archive.ORIGINAL])
def test_exact_git_snapshots_match_their_separate_full_source_closures(snapshot: archive.SourceSnapshot) -> None:
    result = archive.verify_archive(ROOT, snapshot)
    assert result["status"] == "PASS"
    assert result["asset_count"] == snapshot.asset_count
    assert result["revision"] == snapshot.revision
    assert result["manifest_sha256"] == snapshot.manifest_sha256
    assert result["scope"] == "source_integrity_only"
    assert result["pilot_execution"] == "NOT_RUN"
    assert result["execution_authority"] == "not_established_by_source_check"


@pytest.mark.parametrize("mutation", ["content", "extra", "missing", "symlink"])
def test_archived_full_closure_rejects_real_source_mutations(retained_source: Path, tmp_path: Path, mutation: str) -> None:
    target = retained_source / "schemas/test_first_pilot_event.schema.json"
    if mutation == "content":
        target.write_bytes(target.read_bytes() + b"\n")
    elif mutation == "extra":
        (retained_source / "tools/unregistered_source.py").write_text("VALUE = 1\n", encoding="utf-8")
    elif mutation == "missing":
        target.unlink()
    else:
        outside = tmp_path / "outside.json"
        outside.write_text("{}\n", encoding="utf-8")
        target.unlink()
        target.symlink_to(outside)
    with pytest.raises(archive.ArchiveError, match="full execution closure rejected"):
        archive.verify_snapshot(retained_source, archive.RETAINED)


@pytest.mark.parametrize("relative", [archive.MANIFEST_PATH, archive.BUILDER_PATH])
def test_unauthenticated_manifest_or_builder_is_never_executed(
    retained_source: Path, monkeypatch: pytest.MonkeyPatch, relative: str,
) -> None:
    target = retained_source / relative
    target.write_bytes(target.read_bytes() + b"\n")
    def forbidden_execution(*args: object, **kwargs: object) -> None:
        pytest.fail("a modified manifest/builder reached subprocess execution")
    monkeypatch.setattr(archive.subprocess, "run", forbidden_execution)
    with pytest.raises(archive.ArchiveError, match="manifest|builder"):
        archive.verify_snapshot(retained_source, archive.RETAINED)


def test_missing_pinned_git_commit_is_an_availability_error(tmp_path: Path) -> None:
    missing = replace(archive.RETAINED, revision="0" * 40)
    with pytest.raises(archive.ArchiveAvailabilityError, match="required local Git commit is unavailable"):
        archive.export_git_snapshot(ROOT, missing, tmp_path / "missing")


def test_cli_reports_missing_history_as_error_not_pass_or_skip(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-q", str(tmp_path / "empty-repository")], check=True)
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools/verify_test_first_pilot_archive.py"), "--check", "--root", str(tmp_path / "empty-repository")],
        text=True, capture_output=True, check=False,
    )
    assert result.returncode == 2
    assert json.loads(result.stderr)["status"] == "ERROR_AVAILABILITY"


@pytest.mark.parametrize("mutation", ["manifest", "toolchain", "registry", "prompt", "fixture", "extra", "symlink"])
def test_current_frozen_governance_and_suite_remain_immutable(retained_source: Path, tmp_path: Path, mutation: str) -> None:
    current = tmp_path / "current"
    for relative in archive.CURRENT_FROZEN_PATHS:
        destination = current / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(retained_source / relative, destination)
    shutil.copytree(retained_source / archive.SUITE_PATH, current / archive.SUITE_PATH)
    targets = {
        "manifest": archive.MANIFEST_PATH,
        "toolchain": "reports/test_first_pilot/shishki_bot_v1/TOOLCHAIN.json",
        "registry": "reports/test_first_pilot/shishki_bot_v1/PILOT_REGISTRY.md",
        "prompt": f"{archive.SUITE_PATH}/prompts/pin_ci_actions.baseline.md",
        "fixture": f"{archive.SUITE_PATH}/fixtures/pin_ci_actions/.github/workflows/ci.yml",
    }
    if mutation in targets:
        target = current / targets[mutation]
        target.write_bytes(target.read_bytes() + b"\n")
    elif mutation == "extra":
        (current / archive.SUITE_PATH / "extra.txt").write_text("drift\n", encoding="utf-8")
    else:
        target = current / archive.SUITE_PATH / "prompts/pin_ci_actions.baseline.md"
        target.unlink()
        target.symlink_to(retained_source / archive.SUITE_PATH / "prompts/pin_ci_actions.baseline.md")
    with pytest.raises(archive.ArchiveError, match="current frozen|symbolic link"):
        archive.verify_current_frozen_assets(current, retained_source)


@pytest.mark.parametrize("kind", ["escape", "symlink", "hardlink", "fifo", "duplicate"])
def test_git_archive_transport_rejects_unsafe_or_nonregular_members(tmp_path: Path, kind: str) -> None:
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w") as output:
        entry = tarfile.TarInfo("../escape" if kind == "escape" else "entry")
        if kind == "symlink":
            entry.type = tarfile.SYMTYPE
            entry.linkname = "outside"
        elif kind == "hardlink":
            entry.type = tarfile.LNKTYPE
            entry.linkname = "outside"
        elif kind == "fifo":
            entry.type = tarfile.FIFOTYPE
        else:
            entry.size = 1
        output.addfile(entry, io.BytesIO(b"x") if entry.isfile() else None)
        if kind == "duplicate":
            output.addfile(entry, io.BytesIO(b"x"))
    with pytest.raises(archive.ArchiveError, match="unsafe|regular|duplicate"):
        archive.extract_source_archive(buffer.getvalue(), tmp_path / "snapshot")
    assert not (tmp_path / "escape").exists()


def test_original_live_builder_still_rejects_current_development_tree() -> None:
    result = subprocess.run(
        [sys.executable, "-I", "-S", "-B", str(ROOT / archive.BUILDER_PATH), "--check"],
        cwd=ROOT, text=True, capture_output=True, check=False,
    )
    assert result.returncode == 1
    assert result.stderr.strip() == "frozen asset manifest is missing or stale"
