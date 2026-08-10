from __future__ import annotations

import subprocess
import sys
import json
from pathlib import Path

from tools import approve_feature_design


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
    registry_payload = {
  "schema_version": "playbook.feature_design.v1",
  "feature_id": "F01",
  "status": "review_required",
  "planning_depth": "designed_slices",
  "risk_level": "high",
  "brief_ref": "docs/PROJECT_BRIEF.md",
  "architecture_refs": ["docs/ARCHITECTURE.md"],
  "approval_policy": "human_required",
  "slices": [
    {
      "slice_id": "S01",
      "status": "planned",
      "user_visible_outcome": "User can create a privacy event.",
      "scope": "API through privacy event tests.",
      "allowed_files": ["src/**", "tests/**"],
      "forbidden_files": ["docs/secret.md"],
      "expected_interfaces": ["create_privacy_event()"],
      "verification": [
        {
          "id": "slice_tests",
          "argv": ["{python}", "-m", "pytest", "tests/test_privacy_events.py", "-q"],
          "cwd": ".",
          "required": True,
          "expected_exit_code": 0,
          "timeout_seconds": 600
        }
      ],
      "review_checkpoint": "slice_review",
      "dependencies": [],
      "change_budget": "files<=4, lines<=200",
      "rollback": "revert S01 diff"
    }
  ]
}
    registry_path = docs / "design/F01.design.json"
    registry_path.write_text(
        json.dumps(registry_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    reports = root / ".playbook-artifacts/reports/F01"
    reports.mkdir(parents=True, exist_ok=True)
    product = reports / "product_design_review.md"
    program = reports / "program_design_review.md"
    product.write_text("PRODUCT_DESIGN_REVIEW: PASS\nNo findings.\n", encoding="utf-8")
    program.write_text("PROGRAM_DESIGN_REVIEW: PASS\nNo findings.\n", encoding="utf-8")
    approve_feature_design.write_design_review_record(
        root=root,
        feature_id="F01",
        role="product_design_review",
        report_path=".playbook-artifacts/reports/F01/product_design_review.md",
        reviewed_design=registry_payload,
        reviewer_binding="test:product",
    )
    approve_feature_design.write_design_review_record(
        root=root,
        feature_id="F01",
        role="program_design_review",
        report_path=".playbook-artifacts/reports/F01/program_design_review.md",
        reviewed_design=registry_payload,
        reviewer_binding="test:program",
    )
    approved = approve_feature_design.approve_registry_payload(
        root=root,
        registry_path=registry_path,
        payload=registry_payload,
        human_id="human:tester",
        approval_method="test_harness",
        approval_ref="tests/unit/test_render_codex_exec_prompt.py",
        approved_at="2026-07-29",
        review_refs=[],
        advisory_acknowledgement="none",
    )
    registry_path.write_text(
        json.dumps(approved, indent=2, sort_keys=True) + "\n",
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


def test_render_design_author_prompt_is_write_scoped_but_forbids_application_code(tmp_path: Path) -> None:
    write_project(tmp_path)
    planning = tmp_path / ".playbook-artifacts/planning/T03/planning_decision.json"
    planning.parent.mkdir(parents=True)
    planning.write_text('{"schema_version":"playbook.planning_decision.v1"}\n', encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools/render_codex_exec_prompt.py"),
            "--root",
            str(tmp_path),
            "--task",
            "T03",
            "--role",
            "design_author",
            "--feature-id",
            "F01",
            "--planning-decision",
            ".playbook-artifacts/planning/T03/planning_decision.json",
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "--sandbox workspace-write" in result.stdout
    assert "DESIGN_AUTHOR_RESULT: DRAFTED | BLOCKED" in result.stdout
    assert "Do not write application code" in result.stdout
    assert "docs/design/F01.design.json" in result.stdout


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
