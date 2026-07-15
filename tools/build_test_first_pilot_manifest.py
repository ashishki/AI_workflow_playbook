#!/usr/bin/env python3
"""Build or verify the frozen test-first pilot asset manifest."""

from __future__ import annotations

import argparse
import hashlib
import os
import stat
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "reports/test_first_pilot/shishki_bot_v1/ASSET_MANIFEST.sha256"
EXACT_PATHS = {
    "companion/ai_workflow_harness_lab/README.md",
    "companion/ai_workflow_harness_lab/pyproject.toml",
    "docs/evaluation/PLAYBOOK_EMPIRICAL_VALIDATION.md",
    "docs/evaluation/TEST_FIRST_PILOT_PLAN.md",
    "prompts/audit/PROMPT_PILOT_OUTCOME_CRITIC.md",
    "pytest.ini",
    "reports/test_first_pilot/shishki_bot_v1/APPROVAL_TEMPLATE.md",
    "reports/test_first_pilot/shishki_bot_v1/PILOT_REGISTRY.md",
    "reports/test_first_pilot/shishki_bot_v1/TOOLCHAIN.json",
    "templates/PILOT_OUTCOME_CRITIC_REPORT.md",
    "tests/unit/test_prepare_test_first_pilot_review.py",
    "tests/unit/test_test_first_pilot_adapter.py",
    "tests/unit/test_test_first_pilot_assets.py",
    "tests/unit/test_test_first_pilot_permissions.py",
    "tests/unit/test_test_first_pilot_sandbox.py",
    "tests/unit/test_test_first_pilot_toolchain.py",
    "tools/build_test_first_pilot_manifest.py",
    "tools/prepare_test_first_pilot_review.py",
    "tools/run_test_first_pilot.sh",
    "tools/test_first_pilot_codex_adapter.py",
    "tools/test_first_pilot_sandbox.py",
    "tools/validate_harness_evidence.py",
    "tools/verify_test_first_pilot_permissions.py",
    "tools/verify_test_first_pilot_toolchain.py",
}
TREE_ROOTS = (
    "companion/ai_workflow_harness_lab/src/ai_workflow_harness_lab",
    "companion/ai_workflow_harness_lab/suites",
    "companion/ai_workflow_harness_lab/tests",
    "schemas",
    "tests",
    "tools",
)
IGNORED_PARTS = {"__pycache__", ".pytest_cache"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    try:
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise RuntimeError(f"frozen asset must be a regular file: {path}")
        with os.fdopen(descriptor, "rb", closefd=False) as handle:
            for chunk in iter(lambda: handle.read(65536), b""):
                digest.update(chunk)
    finally:
        os.close(descriptor)
    return digest.hexdigest()


def reject_symlink_components(path: Path) -> None:
    try:
        relative = path.relative_to(ROOT)
    except ValueError as exc:
        raise RuntimeError(f"frozen asset escapes repository root: {path}") from exc
    current = ROOT
    for part in relative.parts:
        current /= part
        try:
            mode = current.lstat().st_mode
        except FileNotFoundError:
            return
        if stat.S_ISLNK(mode):
            raise RuntimeError(f"symbolic link is not allowed in frozen asset path: {current}")


def asset_paths() -> list[Path]:
    relative_paths = set(EXACT_PATHS)
    for raw_root in TREE_ROOTS:
        tree_root = ROOT / raw_root
        reject_symlink_components(tree_root)
        if not tree_root.is_dir():
            raise RuntimeError(f"asset tree is missing: {raw_root}")
        for path in tree_root.rglob("*"):
            relative = path.relative_to(ROOT)
            if path.is_symlink():
                raise RuntimeError(f"symbolic link is not allowed in asset tree: {relative}")
            if any(part in IGNORED_PARTS for part in relative.parts):
                continue
            if path.is_dir():
                continue
            if not path.is_file():
                raise RuntimeError(f"asset tree entry must be a regular file: {relative}")
            relative_paths.add(str(relative))

    paths: list[Path] = []
    for relative in sorted(relative_paths):
        path = ROOT / relative
        reject_symlink_components(path)
        if not path.is_file():
            raise RuntimeError(f"frozen asset must be a regular file: {relative}")
        paths.append(path)
    return paths


def manifest_bytes() -> bytes:
    lines = [f"{sha256(path)}  {path.relative_to(ROOT)}" for path in asset_paths()]
    return ("\n".join(lines) + "\n").encode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    expected = manifest_bytes()
    if args.write:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        temporary = OUTPUT.with_suffix(".sha256.tmp")
        temporary.write_bytes(expected)
        temporary.replace(OUTPUT)
        print(f"wrote {len(expected.splitlines())} frozen asset digests to {OUTPUT}")
        return 0
    if not OUTPUT.is_file() or OUTPUT.read_bytes() != expected:
        print("frozen asset manifest is missing or stale", file=sys.stderr)
        return 1
    print(f"asset manifest: ok ({len(expected.splitlines())} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
