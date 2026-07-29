from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def init_repo(root: Path) -> None:
    subprocess.run(["git", "init"], cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=root, check=True)


def write_project(root: Path) -> None:
    (root / "docs/design").mkdir(parents=True)
    (root / "docs/PROJECT_BRIEF.md").write_text("# Brief\n", encoding="utf-8")
    (root / "docs/tasks.md").write_text(
        """# Tasks

## Phase 1

### T01: Slice

Owner: codex
Type: feature
Planning-Depth: designed_slices
Design-Refs:
  - `docs/design/F01.design.json`
Slice-ID: S01
User-Touchpoint: User sees smoke output.
Review-Checkpoint: slice_review
Change-Budget: files<=1, lines<=1
Objective: |
  Implement slice.
Acceptance-Criteria:
  - Slice works.
Verification:
  - `python -m pytest`
Files:
  - `app/smoke.py`
""",
        encoding="utf-8",
    )
    (root / "docs/design/F01.design.json").write_text(
        json.dumps(
            {
                "schema_version": "playbook.feature_design.v1",
                "feature_id": "F01",
                "status": "approved",
                "planning_depth": "designed_slices",
                "risk_level": "high",
                "brief_ref": "docs/PROJECT_BRIEF.md",
                "architecture_refs": [],
                "approval_policy": "human_required",
                "approved_by": "human",
                "approved_at": "2026-07-29",
                "slices": [
                    {
                        "slice_id": "S01",
                        "status": "planned",
                        "user_visible_outcome": "User sees smoke output.",
                        "scope": "App smoke.",
                        "allowed_files": ["app/**"],
                        "forbidden_files": ["secrets/**"],
                        "expected_interfaces": ["smoke()"],
                        "verification": ["python -m pytest"],
                        "review_checkpoint": "slice_review",
                        "dependencies": [],
                        "change_budget": "files<=1, lines<=1",
                        "rollback": "revert",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )


def test_maintainability_check_flags_forbidden_file_and_budget(tmp_path: Path) -> None:
    init_repo(tmp_path)
    write_project(tmp_path)
    (tmp_path / "app").mkdir()
    (tmp_path / "app/smoke.py").write_text("def smoke():\n    return True\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-m", "base"], cwd=tmp_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    (tmp_path / "app/smoke.py").write_text("def smoke():\n    return False\n", encoding="utf-8")
    (tmp_path / "secrets").mkdir()
    (tmp_path / "secrets/token.txt").write_text("secret\n", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(ROOT / "tools/check_maintainability.py"), "--root", str(tmp_path), "--task", "T01"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 1
    report = json.loads(result.stdout)
    check_ids = {signal["check_id"] for signal in report["signals"]}
    assert "MAINTAINABILITY_FORBIDDEN_FILE" in check_ids
    assert "MAINTAINABILITY_CHANGE_BUDGET_FILES" in check_ids
