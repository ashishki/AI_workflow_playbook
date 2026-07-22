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
