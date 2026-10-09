#!/usr/bin/env python3
"""Verify historical pilot source closure; this grants no execution authority.

The retained 179-file manifest is a later source snapshot, not the 119-file
manifest cited by the July pilot result. Both anchors are checked from local Git
objects without fetching history, using only the authenticated stdlib builder.
The original live builder and runner retain their current-tree/host drift gates.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import stat
import subprocess
import sys
import tarfile
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = "reports/test_first_pilot/shishki_bot_v1/ASSET_MANIFEST.sha256"
BUILDER_PATH = "tools/build_test_first_pilot_manifest.py"
SUITE_PATH = "companion/ai_workflow_harness_lab/suites/shishki_bot_ci_v1"
CURRENT_FROZEN_PATHS = (
    MANIFEST_PATH,
    "reports/test_first_pilot/shishki_bot_v1/TOOLCHAIN.json",
    "reports/test_first_pilot/shishki_bot_v1/PILOT_REGISTRY.md",
    BUILDER_PATH,
    "tools/run_test_first_pilot.sh",
    "tools/verify_test_first_pilot_permissions.py",
)
IGNORED_PARTS = {"__pycache__", ".pytest_cache"}


@dataclass(frozen=True)
class SourceSnapshot:
    label: str
    revision: str
    manifest_sha256: str
    asset_count: int


RETAINED = SourceSnapshot(
    "retained_source_snapshot",
    "965612aa463fca1a35a55104633d0e09da33d615",
    "f9f1faa4a5400b21cf22afd94cff334cf2053a472da19713677b9e57557687a9",
    179,
)
ORIGINAL = SourceSnapshot(
    "original_july_source_snapshot",
    "d00575aa4fe599e7a72acfb732aa5fb16ffc4df4",
    "38e7e7742238db7e3ec3ef486a3f57ed12f94a425df90ad9dd581cbade8bf7d3",
    119,
)


class ArchiveError(RuntimeError):
    """The source snapshot failed integrity verification."""


class ArchiveAvailabilityError(ArchiveError):
    """Required local Git history is unavailable; verification did not pass."""


def safe_relative_path(raw: str) -> PurePosixPath:
    parts = raw.rstrip("/").split("/")
    if not raw or raw.startswith("/") or "\\" in raw or ":" in parts[0]:
        raise ArchiveError(f"unsafe source path: {raw!r}")
    if any(part in {"", ".", ".."} for part in parts):
        raise ArchiveError(f"unsafe source path: {raw!r}")
    return PurePosixPath(*parts)


def regular_bytes(root: Path, relative: str) -> bytes:
    path = root
    for part in safe_relative_path(relative).parts:
        path /= part
        try:
            mode = path.lstat().st_mode
        except FileNotFoundError as exc:
            raise ArchiveError(f"source file is missing: {relative}") from exc
        if stat.S_ISLNK(mode):
            raise ArchiveError(f"symbolic link is not allowed: {relative}")
    if not stat.S_ISREG(mode):
        raise ArchiveError(f"source must be a regular file: {relative}")
    descriptor = os.open(
        path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0),
    )
    try:
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise ArchiveError(f"source must be a regular file: {relative}")
        with os.fdopen(descriptor, "rb", closefd=False) as handle:
            return handle.read()
    finally:
        os.close(descriptor)


def extract_source_archive(raw_archive: bytes, destination: Path) -> None:
    """Extract only unique regular files/directories into an empty directory."""
    if destination.is_symlink():
        raise ArchiveError("source destination must not be a symbolic link")
    destination.mkdir(parents=True, exist_ok=True)
    if any(destination.iterdir()):
        raise ArchiveError("source destination must be empty")
    with tarfile.open(fileobj=io.BytesIO(raw_archive), mode="r:") as archive:
        members = archive.getmembers()
        seen: set[PurePosixPath] = set()
        for member in members:
            relative = safe_relative_path(member.name)
            if relative in seen:
                raise ArchiveError(f"duplicate source archive path: {member.name}")
            seen.add(relative)
            if not member.isdir() and not member.isfile():
                raise ArchiveError(f"source archive entry must be regular: {member.name}")
        for member in members:
            relative = safe_relative_path(member.name)
            path = destination.joinpath(*relative.parts)
            if member.isdir():
                path.mkdir(parents=True, exist_ok=True)
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            source = archive.extractfile(member)
            if source is None:
                raise ArchiveError(f"source archive file is unreadable: {member.name}")
            with source, path.open("xb") as target:
                target.write(source.read())


def export_git_snapshot(repository: Path, snapshot: SourceSnapshot, destination: Path) -> None:
    environment = {
        "PATH": os.defpath,
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_ATTR_NOSYSTEM": "1",
        "GIT_TERMINAL_PROMPT": "0",
    }
    command = [
        "git", "-c", f"core.attributesFile={os.devnull}",
        "-c", f"core.hooksPath={os.devnull}", "-C", str(repository),
    ]
    try:
        revision = subprocess.run(
            [*command, "rev-parse", "--verify", f"{snapshot.revision}^{{commit}}"],
            env=environment, stdin=subprocess.DEVNULL, capture_output=True,
            text=True, timeout=30, check=False,
        )
        if revision.returncode != 0 or revision.stdout.strip() != snapshot.revision:
            raise ArchiveAvailabilityError(
                f"required local Git commit is unavailable: {snapshot.revision}; "
                "use a checkout with full history (no fetch attempted)"
            )
        archive = subprocess.run(
            [*command, "archive", "--format=tar", snapshot.revision],
            env=environment, stdin=subprocess.DEVNULL, capture_output=True,
            timeout=30, check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ArchiveAvailabilityError(f"local Git snapshot could not be read: {exc}") from exc
    if archive.returncode != 0:
        raise ArchiveAvailabilityError(f"local Git archive failed for {snapshot.revision}")
    extract_source_archive(archive.stdout, destination)


def pinned_manifest(source: Path, snapshot: SourceSnapshot) -> dict[str, str]:
    raw = regular_bytes(source, MANIFEST_PATH)
    if hashlib.sha256(raw).hexdigest() != snapshot.manifest_sha256:
        raise ArchiveError("archived manifest does not match its external SHA-256 pin")
    entries: dict[str, str] = {}
    for line in raw.decode("utf-8").splitlines(keepends=True):
        match = re.fullmatch(r"([0-9a-f]{64})  (.+)\n", line)
        if match is None:
            raise ArchiveError("archived manifest has a malformed entry")
        digest, relative = match.groups()
        safe_relative_path(relative)
        if relative in entries:
            raise ArchiveError(f"archived manifest repeats a path: {relative}")
        entries[relative] = digest
    if len(entries) != snapshot.asset_count or list(entries) != sorted(entries):
        raise ArchiveError("archived manifest count/order does not match the pinned snapshot")
    return entries


def verify_current_frozen_assets(repository: Path, source: Path) -> None:
    """Keep the current retained governance, original gates and suite immutable."""
    entries = pinned_manifest(source, RETAINED)
    for relative in CURRENT_FROZEN_PATHS:
        if regular_bytes(repository, relative) != regular_bytes(source, relative):
            raise ArchiveError(f"current frozen source differs from the retained snapshot: {relative}")
    expected = {relative for relative in entries if relative.startswith(f"{SUITE_PATH}/")}
    suite = repository / SUITE_PATH
    # Check ancestors before traversing; never follow a symlinked fixture root.
    regular_bytes(repository, f"{SUITE_PATH}/suite.json")
    observed: set[str] = set()
    for path in suite.rglob("*"):
        relative = path.relative_to(repository).as_posix()
        mode = path.lstat().st_mode
        if stat.S_ISLNK(mode):
            raise ArchiveError(f"symbolic link is not allowed: {relative}")
        if any(part in IGNORED_PARTS for part in path.relative_to(suite).parts):
            continue
        if stat.S_ISDIR(mode):
            continue
        if not stat.S_ISREG(mode):
            raise ArchiveError(f"source must be a regular file: {relative}")
        observed.add(relative)
    if observed != expected:
        raise ArchiveError("current frozen suite file closure differs from the retained snapshot")
    for relative in sorted(expected):
        if hashlib.sha256(regular_bytes(repository, relative)).hexdigest() != entries[relative]:
            raise ArchiveError(f"current frozen suite asset changed: {relative}")


def verify_snapshot(
    source: Path, snapshot: SourceSnapshot, *, current_root: Path | None = None,
) -> dict[str, object]:
    entries = pinned_manifest(source, snapshot)
    builder = regular_bytes(source, BUILDER_PATH)
    if hashlib.sha256(builder).hexdigest() != entries.get(BUILDER_PATH):
        raise ArchiveError("archived builder does not match the authenticated manifest")
    # Authenticate the only executable archive asset before running it. The
    # original stdlib builder still checks every tree entry and the full closure.
    result = subprocess.run(
        [sys.executable, "-I", "-S", "-B", str(source / BUILDER_PATH), "--check"],
        cwd=source, stdin=subprocess.DEVNULL,
        env={"PATH": os.defpath, "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8"},
        text=True, capture_output=True, timeout=30, check=False,
    )
    expected = f"asset manifest: ok ({snapshot.asset_count} files)"
    if result.returncode != 0 or result.stdout.strip() != expected:
        detail = result.stderr.strip() or result.stdout.strip() or "no diagnostic"
        raise ArchiveError(f"archived full execution closure rejected: {detail}")
    if current_root is not None:
        if snapshot != RETAINED:
            raise ArchiveError("current frozen source comparison requires the retained snapshot")
        verify_current_frozen_assets(current_root, source)
    return {
        "status": "PASS", "scope": "source_integrity_only",
        "snapshot": snapshot.label, "revision": snapshot.revision,
        "manifest_sha256": snapshot.manifest_sha256, "asset_count": snapshot.asset_count,
        "pilot_execution": "NOT_RUN", "execution_authority": "not_established_by_source_check",
    }


def verify_archive(repository: Path, snapshot: SourceSnapshot = RETAINED) -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="test-first-pilot-source-") as temporary:
        source = Path(temporary) / "snapshot"
        export_git_snapshot(repository, snapshot, source)
        return verify_snapshot(
            source, snapshot, current_root=repository if snapshot == RETAINED else None,
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", required=True)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--original", action="store_true", help="check the separate July 119-file source snapshot")
    args = parser.parse_args()
    try:
        result = verify_archive(args.root.resolve(), ORIGINAL if args.original else RETAINED)
    except (ArchiveError, OSError, subprocess.TimeoutExpired, tarfile.TarError) as exc:
        status = "ERROR_AVAILABILITY" if isinstance(exc, ArchiveAvailabilityError) else "REJECTED"
        print(json.dumps({"status": status, "scope": "source_integrity_only", "error": str(exc)}), file=sys.stderr)
        return 2 if status == "ERROR_AVAILABILITY" else 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
