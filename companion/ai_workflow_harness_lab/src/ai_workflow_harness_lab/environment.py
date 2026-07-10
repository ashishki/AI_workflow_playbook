from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path


SKIP_DIRS = {".git", "__pycache__", ".pytest_cache"}


def copy_fixture(fixture: Path, workspace: Path) -> None:
    if workspace.exists():
        shutil.rmtree(workspace)
    shutil.copytree(fixture, workspace)


def file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tree_manifest(root: Path) -> dict[str, str]:
    manifest: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if path.is_dir() or any(part in SKIP_DIRS for part in path.relative_to(root).parts):
            continue
        manifest[str(path.relative_to(root))] = file_digest(path)
    return manifest


def environment_digest(root: Path) -> str:
    payload = json.dumps(tree_manifest(root), sort_keys=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def git(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def init_git(workspace: Path) -> str:
    if git(["init"], workspace).returncode != 0:
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
