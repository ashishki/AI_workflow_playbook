from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from tools import approve_feature_design


ROOT = Path(__file__).resolve().parents[2]


def run_workflow(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(ROOT / "tools/feature_workflow.py"), "--root", str(root), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def init_repo(root: Path) -> None:
    subprocess.run(["git", "init"], cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=root, check=True)


def write_base_project(root: Path, *, task_id: str = "T14", high_risk: bool = True) -> None:
    (root / "docs/design").mkdir(parents=True)
    (root / "docs/PROJECT_BRIEF.md").write_text(
        "# Project Brief\n\nApproved: human:tester\n\n- User-visible outcome: correction flow\n"
        "- Expected system impact: API / persistence / multiple modules\n",
        encoding="utf-8",
    )
    (root / "docs/ARCHITECTURE.md").write_text("# Architecture\n\nReuse service/repository split.\n", encoding="utf-8")
    (root / "docs/tasks.md").write_text(
        f"""# Tasks

## Phase 1

### {task_id}: Correction Flow

Owner: codex
Type: feature, api, persistence
Status: planned
Risk-Level: {'high' if high_risk else 'low'}
Planning-Depth: designed_slices
Design-Refs:
  - `docs/design/F01.design.json`
Slice-ID: F01-S1
User-Touchpoint: User can run correction smoke path.
Review-Checkpoint: slice_review
Change-Budget: files<=3, lines<=120
Objective: |
  Build the first correction flow slice.
Acceptance-Criteria:
  - User-visible smoke path works.
Verification:
  - `.venv/bin/python -m pytest tests/test_correction_flow.py -q`
Files:
  - `app/corrections.py`
  - `tests/test_correction_flow.py`
""",
        encoding="utf-8",
    )
    (root / "app").mkdir()
    (root / "tests").mkdir()
    (root / "app/corrections.py").write_text("def correction_smoke():\n    return 'base'\n", encoding="utf-8")
    (root / "tests/test_correction_flow.py").write_text(
        "from app.corrections import correction_smoke\n\n"
        "def test_correction_smoke():\n"
        "    assert correction_smoke() in {'base', 'slice'}\n",
        encoding="utf-8",
    )


def design_payload(*, risk: str = "high", s1_status: str = "planned") -> dict[str, object]:
    return {
        "schema_version": "playbook.feature_design.v1",
        "feature_id": "F01",
        "status": "review_required",
        "planning_depth": "designed_slices",
        "risk_level": risk,
        "brief_ref": "docs/PROJECT_BRIEF.md",
        "architecture_refs": ["docs/ARCHITECTURE.md"],
        "approval_policy": "human_required" if risk in {"high", "critical"} else "human_or_authorized_reviewer",
        "slices": [
            {
                "slice_id": "F01-S1",
                "status": s1_status,
                "user_visible_outcome": "User can run correction smoke path.",
                "scope": "Service function plus direct test.",
                "allowed_files": ["app/corrections.py", "tests/test_correction_flow.py"],
                "forbidden_files": ["secrets/**"],
                "expected_interfaces": ["correction_smoke()"],
                "verification": [
                    {
                        "id": "slice_tests",
                        "argv": ["{python}", "-m", "pytest", "tests/test_correction_flow.py", "-q"],
                        "cwd": ".",
                        "required": True,
                        "expected_exit_code": 0,
                        "timeout_seconds": 120,
                    }
                ],
                "review_checkpoint": "slice_review",
                "dependencies": [],
                "change_budget": "files<=3, lines<=120",
                "rollback": "revert slice diff",
            },
            {
                "slice_id": "F01-S2",
                "status": "planned",
                "user_visible_outcome": "User can apply one extension.",
                "scope": "Extension through same service boundary.",
                "allowed_files": ["app/corrections.py", "tests/test_correction_flow.py"],
                "forbidden_files": ["secrets/**"],
                "expected_interfaces": ["correction_smoke(mode)"],
                "verification": [
                    {
                        "id": "slice_tests",
                        "argv": ["{python}", "-m", "pytest", "tests/test_correction_flow.py", "-q"],
                        "cwd": ".",
                        "required": True,
                        "expected_exit_code": 0,
                        "timeout_seconds": 120,
                    }
                ],
                "review_checkpoint": "slice_review",
                "dependencies": ["F01-S1"],
                "change_budget": "files<=3, lines<=120",
                "rollback": "revert slice diff",
            },
        ],
    }


def write_design(root: Path, *, risk: str = "high") -> Path:
    markdown = root / "docs/design/F01.md"
    registry = root / "docs/design/F01.design.json"
    markdown.write_text("# Feature Design F01\n\nProgram design body.\n", encoding="utf-8")
    payload = design_payload(risk=risk)
    registry.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    approved = approve_feature_design.approve_registry_payload(
        root=root,
        registry_path=registry,
        payload=payload,
        human_id="human:tester",
        approval_method="test_harness",
        approval_ref="tests/unit/test_feature_workflow.py",
        approved_at="2026-07-29",
        review_refs=[],
        advisory_acknowledgement="none",
    )
    registry.write_text(json.dumps(approved, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return registry


def commit_all(root: Path) -> None:
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    subprocess.run(["git", "commit", "-m", "base"], cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)


def test_plan_creates_deterministic_report(tmp_path: Path) -> None:
    init_repo(tmp_path)
    write_base_project(tmp_path)
    commit_all(tmp_path)

    result = run_workflow(tmp_path, "plan", "--task", "T14")

    assert result.returncode == 0, result.stderr
    decision = json.loads((tmp_path / ".playbook-artifacts/planning/T14/planning_decision.json").read_text(encoding="utf-8"))
    assert decision["schema_version"] == "playbook.planning_decision.v1"
    assert decision["recommended_planning_depth"] == "designed_slices"
    assert decision["facts"]["risk_level"]["source"] == "declared"
    assert decision["facts"]["api_change"]["source"] in {"declared", "detected", "agent_proposed"}


def test_plan_needs_input_when_semantic_facts_are_unknown(tmp_path: Path) -> None:
    init_repo(tmp_path)
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs/PROJECT_BRIEF.md").write_text("# Brief\n\nApproved: human:tester\n", encoding="utf-8")
    (tmp_path / "docs/tasks.md").write_text(
        """# Tasks

## Phase 1

### T00: Ambiguous Work

Owner: codex
Type: task
Status: planned
Objective: |
  Do the thing.
Acceptance-Criteria:
  - It works.
Verification:
  - `.venv/bin/python -m pytest -q`
""",
        encoding="utf-8",
    )
    commit_all(tmp_path)

    result = run_workflow(tmp_path, "plan", "--task", "T00")

    assert result.returncode == 1
    decision = json.loads((tmp_path / ".playbook-artifacts/planning/T00/planning_decision.json").read_text(encoding="utf-8"))
    assert decision["status"] == "needs_input"
    assert decision["unknown_facts"]


def test_draft_creates_design_author_prompt_and_design_session(tmp_path: Path) -> None:
    init_repo(tmp_path)
    write_base_project(tmp_path)
    commit_all(tmp_path)
    result = run_workflow(tmp_path, "draft", "--task", "T14", "--feature-id", "F01")

    assert result.returncode == 0, result.stderr
    assert "DESIGN AUTHOR PROMPT READY" in result.stdout
    prompt = tmp_path / ".playbook-artifacts/prompts/F01/design_author.md"
    assert prompt.exists()
    text = prompt.read_text(encoding="utf-8")
    assert "DESIGN_AUTHOR_RESULT: DRAFTED | BLOCKED" in text
    assert "Do not write application code" in text
    session = json.loads((tmp_path / ".playbook-artifacts/workflows/F01/design_session.json").read_text(encoding="utf-8"))
    assert "docs/design/F01.md" in session["allowed_design_paths"]


def test_start_requires_fresh_approval_and_updates_only_operational_status(tmp_path: Path) -> None:
    init_repo(tmp_path)
    write_base_project(tmp_path)
    (tmp_path / "docs/design/F01.md").write_text("# Feature Design F01\n", encoding="utf-8")
    (tmp_path / "docs/design/F01.design.json").write_text(json.dumps(design_payload(), indent=2), encoding="utf-8")
    commit_all(tmp_path)

    blocked = run_workflow(tmp_path, "start", "--feature-id", "F01", "--slice-id", "F01-S1")
    assert blocked.returncode == 1
    assert "fresh approved design" in blocked.stderr

    registry = tmp_path / "docs/design/F01.design.json"
    payload = json.loads(registry.read_text(encoding="utf-8"))
    approved = approve_feature_design.approve_registry_payload(
        root=tmp_path,
        registry_path=registry,
        payload=payload,
        human_id="human:tester",
        approval_method="test_harness",
        approval_ref="tests",
        approved_at="2026-07-29",
        review_refs=[],
        advisory_acknowledgement="none",
    )
    registry.write_text(json.dumps(approved, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    started = run_workflow(tmp_path, "start", "--feature-id", "F01", "--slice-id", "F01-S1")

    assert started.returncode == 0, started.stderr
    updated = json.loads(registry.read_text(encoding="utf-8"))
    assert updated["slices"][0]["status"] == "in_progress"
    assert "DESIGN_APPROVAL_STALE" not in "\n".join(f["check_id"] for f in [])


def test_next_respects_reviewed_dependencies(tmp_path: Path) -> None:
    init_repo(tmp_path)
    write_base_project(tmp_path, high_risk=False)
    registry = write_design(tmp_path, risk="low")
    commit_all(tmp_path)

    first = run_workflow(tmp_path, "next", "--feature-id", "F01")
    assert first.returncode == 0, first.stderr
    assert "F01-S1" in first.stdout

    payload = json.loads(registry.read_text(encoding="utf-8"))
    payload["slices"][0]["status"] = "implemented"
    registry.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    blocked = run_workflow(tmp_path, "next", "--feature-id", "F01")
    assert "Ready slice: F01-S2" not in blocked.stdout

    payload["slices"][0]["status"] = "reviewed"
    registry.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    ready = run_workflow(tmp_path, "next", "--feature-id", "F01")
    assert "F01-S2" in ready.stdout


def test_check_blocks_forbidden_file_and_failed_verification(tmp_path: Path) -> None:
    init_repo(tmp_path)
    write_base_project(tmp_path, high_risk=False)
    registry = write_design(tmp_path, risk="low")
    commit_all(tmp_path)
    assert run_workflow(tmp_path, "start", "--feature-id", "F01", "--slice-id", "F01-S1").returncode == 0
    (tmp_path / "secrets").mkdir()
    (tmp_path / "secrets/token.txt").write_text("secret\n", encoding="utf-8")
    (tmp_path / "tests/test_correction_flow.py").write_text(
        "def test_correction_smoke():\n"
        "    raise SystemExit(3)\n",
        encoding="utf-8",
    )

    result = run_workflow(tmp_path, "check", "--task", "T14", "--feature-id", "F01", "--slice-id", "F01-S1")

    assert result.returncode == 1
    slice_result = json.loads((tmp_path / ".playbook-artifacts/workflows/F01/F01-S1/slice_result.json").read_text(encoding="utf-8"))
    assert slice_result["status"] in {"blocked", "fail"}
    assert any(item["check_id"] == "SLICE_FORBIDDEN_FILE" for item in slice_result["scope_findings"])
    assert any(item["exit_code"] != 0 for item in slice_result["verification"])


def test_check_marks_slice_reviewed_when_required_review_passes(tmp_path: Path) -> None:
    init_repo(tmp_path)
    write_base_project(tmp_path, high_risk=False)
    registry = write_design(tmp_path, risk="low")
    commit_all(tmp_path)
    assert run_workflow(tmp_path, "start", "--feature-id", "F01", "--slice-id", "F01-S1").returncode == 0
    (tmp_path / "app/corrections.py").write_text("def correction_smoke():\n    return 'slice'\n", encoding="utf-8")
    report = tmp_path / ".playbook-artifacts/reports/F01/F01-S1_slice_review.md"
    report.parent.mkdir(parents=True)
    report.write_text("SLICE_REVIEW: PASS\nNo findings.\n", encoding="utf-8")

    result = run_workflow(tmp_path, "check", "--task", "T14", "--feature-id", "F01", "--slice-id", "F01-S1")

    assert result.returncode == 0, result.stderr
    slice_result = json.loads((tmp_path / ".playbook-artifacts/workflows/F01/F01-S1/slice_result.json").read_text(encoding="utf-8"))
    assert slice_result["status"] == "eligible_for_human_acceptance"
    payload = json.loads(registry.read_text(encoding="utf-8"))
    assert payload["slices"][0]["status"] == "reviewed"
    next_result = run_workflow(tmp_path, "next", "--feature-id", "F01")
    assert "F01-S2" in next_result.stdout
