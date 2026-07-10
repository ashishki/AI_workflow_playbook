from __future__ import annotations

from pathlib import Path

from tools import playbook_validate


def write_tasks(root: Path, text: str) -> None:
    (root / "docs").mkdir(parents=True)
    (root / "docs/tasks.md").write_text(text, encoding="utf-8")


def test_task_parser_accepts_valid_task(tmp_path: Path) -> None:
    write_tasks(
        tmp_path,
        """# Tasks

## Phase 1 - Bootstrap

### T01: Do The Thing

Owner: codex
Type: test, governance
Status: planned
Depends-On: none
Runtime-Verification: required
Correction-Budget: 2

Objective: |
  Make a small verified change.

Acceptance-Criteria:
  - The change exists.

Verification:
  - `python3 tools/verify_project.py --root .`

Context-Refs:
  - `docs/tasks.md`
""",
    )
    findings, tasks = playbook_validate.validate_tasks(tmp_path)

    assert findings == []
    assert tasks[0]["phase"] == "Phase 1 - Bootstrap"
    assert tasks[0]["runtime_verification"] == "required"
    assert tasks[0]["correction_budget"] == 2


def test_task_without_verifier_fails(tmp_path: Path) -> None:
    write_tasks(
        tmp_path,
        """# Tasks

## Phase 1

### T01: Missing Verify

Owner: codex
Type: test

Objective: |
  No verifier.

Acceptance-Criteria:
  - Has criteria.
""",
    )

    findings, _ = playbook_validate.validate_tasks(tmp_path)

    assert any(finding.check_id == "TASK_VERIFIER_REQUIRED" for finding in findings)


def test_cyclic_dependency_fails(tmp_path: Path) -> None:
    write_tasks(
        tmp_path,
        """# Tasks

## Phase 1

### T01: First

Owner: codex
Type: test
Depends-On: T02
Objective: |
  First.
Acceptance-Criteria:
  - ok
Verification:
  - `echo ok`

### T02: Second

Owner: codex
Type: test
Depends-On: T01
Objective: |
  Second.
Acceptance-Criteria:
  - ok
Verification:
  - `echo ok`
""",
    )

    findings, _ = playbook_validate.validate_tasks(tmp_path)

    assert any(finding.check_id == "TASK_CYCLIC_DEPENDENCY" for finding in findings)


def test_missing_context_ref_fails(tmp_path: Path) -> None:
    write_tasks(
        tmp_path,
        """# Tasks

## Phase 1

### T01: Ref

Owner: codex
Type: test
Objective: |
  Ref.
Acceptance-Criteria:
  - ok
Verification:
  - `echo ok`
Context-Refs:
  - `docs/missing.md`
""",
    )

    findings, _ = playbook_validate.validate_tasks(tmp_path)

    assert any(finding.check_id == "REFERENCE_MISSING_CONTEXT" for finding in findings)


def test_placeholder_detection_ignores_fenced_code(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "tasks.md").write_text(
        """# Tasks

```
{{EXAMPLE_OK}}
```

outside {{BROKEN}}
""",
        encoding="utf-8",
    )

    findings = playbook_validate.validate_placeholders(tmp_path)

    assert [finding.message for finding in findings] == ["unresolved placeholder {{BROKEN}}"]
