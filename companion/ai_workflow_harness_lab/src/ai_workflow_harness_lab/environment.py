from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import subprocess
from pathlib import Path


COPY_SKIP_DIRS = {".git", "__pycache__", ".pytest_cache"}
MANIFEST_SKIP_DIRS = {".git"}
MAX_MANIFEST_FILES = 10_000
MAX_MANIFEST_FILE_BYTES = 16 * 1024 * 1024
GIT_BIN = "/usr/bin/git"


def copy_fixture(fixture: Path, workspace: Path) -> None:
    if workspace.exists():
        shutil.rmtree(workspace)
    shutil.copytree(
        fixture,
        workspace,
        ignore=lambda _directory, names: sorted(COPY_SKIP_DIRS.intersection(names)),
    )


def file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    try:
        file_stat = os.fstat(descriptor)
        if not stat.S_ISREG(file_stat.st_mode):
            raise ValueError(f"manifest path is not a regular file: {path}")
        if file_stat.st_size > MAX_MANIFEST_FILE_BYTES:
            raise ValueError(f"manifest file exceeds size limit: {path}")
        with os.fdopen(descriptor, "rb", closefd=False) as handle:
            for chunk in iter(lambda: handle.read(65536), b""):
                digest.update(chunk)
    finally:
        os.close(descriptor)
    return digest.hexdigest()


def safe_workspace_path(root: Path, raw_path: str) -> Path:
    relative = Path(raw_path)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"workspace path escape forbidden: {raw_path}")
    current = root
    for index, part in enumerate(relative.parts):
        current /= part
        try:
            mode = current.lstat().st_mode
        except FileNotFoundError:
            current = current.joinpath(*relative.parts[index + 1 :])
            break
        if stat.S_ISLNK(mode):
            raise ValueError(f"workspace symlink forbidden: {raw_path}")
    if current.exists():
        file_stat = current.lstat()
        if not stat.S_ISREG(file_stat.st_mode):
            raise ValueError(f"workspace path is not a regular file: {raw_path}")
        if file_stat.st_size > MAX_MANIFEST_FILE_BYTES:
            raise ValueError(f"workspace file exceeds size limit: {raw_path}")
    return current


def tree_manifest(root: Path) -> dict[str, str]:
    manifest: dict[str, str] = {}
    visited = 0
    for path in root.rglob("*"):
        visited += 1
        if visited > MAX_MANIFEST_FILES:
            raise ValueError(f"workspace manifest exceeds {MAX_MANIFEST_FILES} entries")
        relative = path.relative_to(root)
        if any(part in MANIFEST_SKIP_DIRS for part in relative.parts):
            continue
        mode = path.lstat().st_mode
        if stat.S_ISLNK(mode):
            target = os.readlink(path).encode("utf-8", errors="surrogateescape")
            manifest[str(relative)] = hashlib.sha256(b"symlink\0" + target).hexdigest()
            continue
        if stat.S_ISDIR(mode):
            continue
        if not stat.S_ISREG(mode):
            marker = f"special:{stat.S_IFMT(mode):o}".encode()
            manifest[str(relative)] = hashlib.sha256(marker).hexdigest()
            continue
        file_stat = path.stat()
        if file_stat.st_size > MAX_MANIFEST_FILE_BYTES:
            marker = f"oversize:{file_stat.st_size}".encode()
            manifest[str(relative)] = hashlib.sha256(marker).hexdigest()
            continue
        manifest[str(relative)] = file_digest(path)
    return manifest


def environment_digest(root: Path) -> str:
    payload = json.dumps(tree_manifest(root), sort_keys=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def git(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    environment = {
        key: value for key, value in os.environ.items() if not key.startswith("GIT_")
    }
    environment.update(
        {
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_TERMINAL_PROMPT": "0",
        }
    )
    return subprocess.run(
        [
            GIT_BIN,
            "-c",
            "core.hooksPath=/dev/null",
            "-c",
            "commit.gpgSign=false",
            *args,
        ],
        cwd=cwd,
        env=environment,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def init_git(workspace: Path) -> str:
    if git(["init", "--template="], workspace).returncode != 0:
        return "git-unavailable"
    git(["config", "user.email", "harness@example.invalid"], workspace)
    git(["config", "user.name", "Harness Lab"], workspace)
    git(["add", "."], workspace)
    git(["commit", "-m", "fixture"], workspace)
    result = git(["rev-parse", "HEAD"], workspace)
    return result.stdout.strip() if result.returncode == 0 else "git-unavailable"


def post_state_manifest(workspace: Path, output_path: Path) -> Path:
    manifest = {
        "schema_version": "harness_lab.post_state_manifest.v1",
        "workspace": str(workspace),
        "files": tree_manifest(workspace),
    }
    output_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output_path
