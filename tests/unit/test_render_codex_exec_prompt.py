from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def write_project(root: Path) -> None:
    docs = root / "docs"
    docs.mkdir(parents=True)
    (docs / "tasks.md").write_text(
        """# Tasks

## Phase 1

### T03: Privacy Event Contract

Owner: codex
Phase: 1
Type: security, privacy, test
Status: review_pending
Risk-Level: high
Critic-Required: required
Planning-Depth: designed_slices
Design-Refs:
  - `docs/design/F01.design.json`
Slice-ID: S01
User-Touchpoint: User can create a privacy event.
Review-Checkpoint: slice_review
Change-Budget: files<=4, lines<=200

Objective: |
  Convert raw updates to privacy-safe event records.

Acceptance-Criteria:
  - Raw content is absent from privacy-safe event output.
  - Unsupported updates fail closed.

Verification:
  - `python3 tools/verify_project.py --root .`

Files:
  - `src/privacy_events/`
  - `tests/test_privacy_events.py`

Context-Refs:
  - `docs/REVIEW_POLICY.md`
""",
        encoding="utf-8",
    )
    (docs / "REVIEW_POLICY.md").write_text(
        "Privacy event work requires deep review, Test Critic, and privacy reviewer.\n",
        encoding="utf-8",
    )
    (docs / "EVIDENCE_INDEX.md").write_text("# Evidence\n", encoding="utf-8")
    (docs / "CODEX_PROMPT.md").write_text("# State\n", encoding="utf-8")
    (docs / "PROJECT_BRIEF.md").write_text("# Brief\n\nUser outcome.\n", encoding="utf-8")
    (docs / "ARCHITECTURE.md").write_text("# Architecture\n\nReuse local services.\n", encoding="utf-8")
    (docs / "design").mkdir()
    (docs / "design/F01.md").write_text("# Feature Design\n\nProgram design body.\n", encoding="utf-8")
    (docs / "design/F01.design.json").write_text(
        """{
  "schema_version": "playbook.feature_design.v1",
  "feature_id": "F01",
  "status": "approved",
  "planning_depth": "designed_slices",
  "risk_level": "high",
  "brief_ref": "docs/PROJECT_BRIEF.md",
  "architecture_refs": ["docs/ARCHITECTURE.md"],
  "approval_policy": "human_required",
  "approved_by": "human",
  "approved_at": "2026-07-29",
  "slices": [
    {
      "slice_id": "S01",
      "status": "planned",
      "user_visible_outcome": "User can create a privacy event.",
      "scope": "API through privacy event tests.",
      "allowed_files": ["src/**", "tests/**"],
      "forbidden_files": ["docs/secret.md"],
      "expected_interfaces": ["create_privacy_event()"],
      "verification": ["python3 -m pytest tests/test_privacy_events.py -q"],
      "review_checkpoint": "slice_review",
      "dependencies": [],
      "change_budget": "files<=4, lines<=200",
      "rollback": "revert S01 diff"
    }
  ]
}
""",
        encoding="utf-8",
    )
    playbook = root / ".playbook"
    playbook.mkdir()
    (playbook / "delivery_execution_model.json").write_text(
        '{"schema_version":"playbook.delivery_execution_model.v1"}\n',
        encoding="utf-8",
    )
    (playbook / "project_verification.json").write_text(
        '{"schema_version":"playbook.project_verification.v1","checks":[]}\n',
        encoding="utf-8",
    )


def test_render_privacy_prompt_includes_task_policy_and_result_marker(tmp_path: Path) -> None:
    write_project(tmp_path)

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools/render_codex_exec_prompt.py"),
            "--root",
            str(tmp_path),
            "--task",
            "T03",
            "--role",
            "privacy_review",
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "Task: T03" in result.stdout
    assert "Role: privacy_review" in result.stdout
    assert "PRIVACY_REVIEW_RESULT: PASS | ADVISORY | STOP_SHIP" in result.stdout
    assert "Privacy Event Contract" in result.stdout
    assert "Privacy event work requires deep review" in result.stdout
    assert "--sandbox read-only" in result.stdout


def test_render_fix_prompt_includes_review_report_and_write_scope(tmp_path: Path) -> None:
    write_project(tmp_path)
    verification = tmp_path / "docs" / "verification"
    verification.mkdir()
    (verification / "T03_privacy_review.md").write_text(
        "PRIVACY_REVIEW_RESULT: STOP_SHIP\nBLOCKER: raw content leak\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools/render_codex_exec_prompt.py"),
            "--root",
            str(tmp_path),
            "--task",
            "T03",
            "--role",
            "fix_from_review",
            "--review",
            "docs/verification/T03_privacy_review.md",
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "WRITE-SCOPED" in result.stdout
    assert "FIX_RESULT: APPLIED | BLOCKED" in result.stdout
    assert "raw content leak" in result.stdout
    assert "--sandbox workspace-write" in result.stdout


def test_render_program_design_review_prompt_is_read_only_and_design_scoped(tmp_path: Path) -> None:
    write_project(tmp_path)

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools/render_codex_exec_prompt.py"),
            "--root",
            str(tmp_path),
            "--task",
            "T03",
            "--role",
            "program_design_review",
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "--sandbox read-only" in result.stdout
    assert "PROGRAM_DESIGN_REVIEW: PASS | ADVISORY | STOP_SHIP" in result.stdout
    assert "Program design body." in result.stdout
    assert "User can create a privacy event." in result.stdout
    assert "## Project Verification Config" not in result.stdout


def test_required_marker_parser_fails_closed_for_missing_marker(tmp_path: Path) -> None:
    report = tmp_path / "review.md"
    report.write_text("Looks fine but no marker.\n", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools/render_codex_exec_prompt.py"),
            "--role",
            "slice_review",
            "--parse-report",
            str(report),
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 1
    assert "missing required marker" in result.stderr


def test_required_marker_parser_accepts_valid_marker(tmp_path: Path) -> None:
    report = tmp_path / "review.md"
    report.write_text("SLICE_REVIEW: PASS\nNo findings.\n", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools/render_codex_exec_prompt.py"),
            "--role",
            "slice_review",
            "--parse-report",
            str(report),
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert '"verdict": "PASS"' in result.stdout
