from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

from tools import playbook_validate


ROOT = Path(__file__).resolve().parents[2]


def write_tasks(root: Path, text: str) -> None:
    (root / "docs").mkdir(parents=True)
    (root / "docs/tasks.md").write_text(text, encoding="utf-8")


def copy_project_verification_result_schema(root: Path) -> None:
    schema_dir = root / "schemas"
    schema_dir.mkdir(parents=True, exist_ok=True)
    (schema_dir / "project_verification_result.schema.json").write_text(
        (ROOT / "schemas/project_verification_result.schema.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )


def init_git_repo(root: Path) -> str:
    subprocess.run(["git", "init"], cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=root, check=True)
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        check=True,
    )
    return commit.stdout.strip()


def artifact_ref(root: Path, path: Path) -> dict[str, str]:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return {"path": str(path.relative_to(root)), "sha256": digest}


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


def test_task_parser_accepts_test_governance_fields_and_aliases(
    tmp_path: Path,
) -> None:
    write_tasks(
        tmp_path,
        """# Tasks

## Phase 1

### T01: Govern Tests

Owner: codex
Type: test
Risk-Level: high
Public-Tests-Required: required
Critic_Required: conditional
Holdout-Required: required
Mutation_Required: conditional
Property-Required: not-required
Visual-Contract: optional
Objective: |
  Route test governance deterministically.
Acceptance-Criteria:
  - Governance fields are parsed.
Verification:
  - `echo ok`
""",
    )

    findings, tasks = playbook_validate.validate_tasks(tmp_path)

    assert findings == []
    assert tasks[0]["risk_level"] == "high"
    assert tasks[0]["public_tests_required"] == "required"
    assert tasks[0]["critic_required"] == "conditional"
    assert tasks[0]["holdout_required"] == "required"
    assert tasks[0]["mutation_required"] == "conditional"
    assert tasks[0]["property_required"] == "not_required"
    assert tasks[0]["visual_contract"] == "optional"


def test_task_parser_applies_backward_compatible_governance_defaults(
    tmp_path: Path,
) -> None:
    write_tasks(
        tmp_path,
        """# Tasks

## Phase 1

### T01: Historical Task

Owner: codex
Type: test
Objective: |
  Remain valid without new Markdown fields.
Acceptance-Criteria:
  - Historical syntax remains valid.
Verification:
  - `echo ok`
""",
    )

    findings, tasks = playbook_validate.validate_tasks(tmp_path)

    assert findings == []
    assert tasks[0]["risk_level"] == "medium"
    assert tasks[0]["public_tests_required"] == "conditional"
    assert tasks[0]["critic_required"] == "conditional"
    assert tasks[0]["holdout_required"] == "conditional"
    assert tasks[0]["mutation_required"] == "conditional"
    assert tasks[0]["property_required"] == "conditional"
    assert tasks[0]["visual_contract"] == "optional"


def test_invalid_test_governance_value_fails_schema(tmp_path: Path) -> None:
    write_tasks(
        tmp_path,
        """# Tasks

## Phase 1

### T01: Invalid Governance

Owner: codex
Type: test
Risk-Level: extreme
Objective: |
  Reject an unsupported risk level.
Acceptance-Criteria:
  - Invalid governance fails validation.
Verification:
  - `echo ok`
""",
    )

    findings, _ = playbook_validate.validate_tasks(tmp_path)

    assert any(
        finding.check_id == "TASK_SCHEMA" and "risk_level" in finding.message
        for finding in findings
    )


def test_misspelled_test_governance_field_fails_closed(tmp_path: Path) -> None:
    write_tasks(
        tmp_path,
        """# Tasks

## Phase 1

### T01: Misspelled Governance

Owner: codex
Type: test
Risk-Lvel: critical
Objective: |
  Reject a governance key that would otherwise fall back silently.
Acceptance-Criteria:
  - The typo is reported.
Verification:
  - `echo ok`
""",
    )

    findings, tasks = playbook_validate.validate_tasks(tmp_path)

    assert tasks[0]["risk_level"] == "medium"
    assert any(
        finding.check_id == "TASK_GOVERNANCE_FIELD_UNKNOWN"
        and "Risk-Lvel" in finding.message
        for finding in findings
    )


def test_duplicate_task_field_aliases_fail_without_overwriting_first_value(
    tmp_path: Path,
) -> None:
    write_tasks(
        tmp_path,
        """# Tasks

## Phase 1

### T01: Duplicate Governance

Owner: codex
Type: test
Risk-Level: critical
Risk_Level: low
Objective: |
  Reject conflicting aliases deterministically.
Acceptance-Criteria:
  - The duplicate is reported.
Verification:
  - `echo ok`
""",
    )

    findings, tasks = playbook_validate.validate_tasks(tmp_path)

    assert tasks[0]["risk_level"] == "critical"
    assert any(
        finding.check_id == "TASK_FIELD_DUPLICATE"
        and "Risk_Level" in finding.message
        for finding in findings
    )


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


def test_readiness_blocks_scaffold_placeholders_after_implementation_ready(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "tasks.md").write_text(
        "not_applicable - scaffold placeholder AUTH_MODEL; replace before treating this section as authoritative\n",
        encoding="utf-8",
    )
    playbook = tmp_path / ".playbook"
    playbook.mkdir()
    readiness = {
        "schema_version": "playbook.readiness_state.v1",
        "mode": "lean-core",
        "state": "scaffold",
        "required_decision_policy": "mode_profile_risk_triggered",
        "unresolved_decision_marker": "scaffold placeholder",
        "implementation_ready_requires_no_scaffold_placeholders": True,
        "release_ready_requires_current_verification": True,
    }
    (playbook / "readiness_state.json").write_text(json.dumps(readiness), encoding="utf-8")

    assert playbook_validate.validate_readiness(tmp_path) == []

    readiness["state"] = "implementation_ready"
    (playbook / "readiness_state.json").write_text(json.dumps(readiness), encoding="utf-8")
    findings = playbook_validate.validate_readiness(tmp_path)

    assert [finding.check_id for finding in findings] == ["READINESS_SCAFFOLD_PLACEHOLDER_ACTIVE"]


def test_readiness_release_candidate_is_pre_verification_state(tmp_path: Path) -> None:
    playbook = tmp_path / ".playbook"
    playbook.mkdir()
    readiness = {
        "schema_version": "playbook.readiness_state.v1",
        "mode": "lean-core",
        "state": "release_candidate",
        "required_decision_policy": "mode_profile_risk_triggered",
        "unresolved_decision_marker": "scaffold placeholder",
        "implementation_ready_requires_no_scaffold_placeholders": True,
        "release_ready_requires_current_verification": True,
    }
    (playbook / "readiness_state.json").write_text(json.dumps(readiness), encoding="utf-8")

    assert playbook_validate.validate_readiness(tmp_path) == []


def test_release_verification_requires_real_git_backed_result(tmp_path: Path) -> None:
    copy_project_verification_result_schema(tmp_path)
    result_dir = tmp_path / ".playbook-artifacts"
    result_dir.mkdir()
    verification = {
        "schema_version": "playbook.project_verification_result.v1",
        "project_commit": "not-a-git-repository",
        "required_failures": 0,
        "checks": [],
    }
    (result_dir / "project_verification.json").write_text(json.dumps(verification), encoding="utf-8")

    findings = playbook_validate.validate_release_verification(tmp_path)
    check_ids = {finding.check_id for finding in findings}

    assert "READINESS_RELEASE_VERIFICATION_SCHEMA" in check_ids
    assert "READINESS_RELEASE_PROJECT_CHECK_MISSING" in check_ids
    assert "READINESS_RELEASE_GIT_REQUIRED" in check_ids


def test_release_verification_accepts_current_green_result(tmp_path: Path) -> None:
    copy_project_verification_result_schema(tmp_path)
    commit = init_git_repo(tmp_path)
    check_dir = tmp_path / ".playbook-artifacts/project_verification/project_verification"
    check_dir.mkdir(parents=True)
    stdout_path = check_dir / "stdout.txt"
    stderr_path = check_dir / "stderr.txt"
    stdout_path.write_text("ok\n", encoding="utf-8")
    stderr_path.write_text("", encoding="utf-8")
    result = {
        "schema_version": "playbook.project_verification_result.v1",
        "project_commit": commit,
        "started_at": "2026-07-15T00:00:00Z",
        "finished_at": "2026-07-15T00:00:01Z",
        "platform": "test-platform",
        "python_executable": "/usr/bin/python3",
        "configuration_errors": [],
        "required_failures": 0,
        "checks": [
            {
                "id": "project_verification",
                "argv": ["python", "-m", "pytest", "-q"],
                "cwd": ".",
                "required": True,
                "expected_exit_code": 0,
                "exit_code": 0,
                "passed": True,
                "skipped": False,
                "stdout_ref": artifact_ref(tmp_path, stdout_path),
                "stderr_ref": artifact_ref(tmp_path, stderr_path),
            }
        ],
    }
    (tmp_path / ".playbook-artifacts/project_verification.json").write_text(json.dumps(result), encoding="utf-8")

    assert playbook_validate.validate_release_verification(tmp_path) == []


def test_release_verification_recomputes_failures_and_hashes(tmp_path: Path) -> None:
    copy_project_verification_result_schema(tmp_path)
    commit = init_git_repo(tmp_path)
    check_dir = tmp_path / ".playbook-artifacts/project_verification/project_verification"
    check_dir.mkdir(parents=True)
    stdout_path = check_dir / "stdout.txt"
    stderr_path = check_dir / "stderr.txt"
    stdout_path.write_text("failed\n", encoding="utf-8")
    stderr_path.write_text("", encoding="utf-8")
    result = {
        "schema_version": "playbook.project_verification_result.v1",
        "project_commit": commit,
        "started_at": "2026-07-15T00:00:00Z",
        "finished_at": "2026-07-15T00:00:01Z",
        "platform": "test-platform",
        "python_executable": "/usr/bin/python3",
        "configuration_errors": [],
        "required_failures": 0,
        "checks": [
            {
                "id": "project_verification",
                "argv": ["python", "-m", "pytest", "-q"],
                "cwd": ".",
                "required": True,
                "expected_exit_code": 0,
                "exit_code": 1,
                "passed": False,
                "skipped": False,
                "stdout_ref": {"path": str(stdout_path.relative_to(tmp_path)), "sha256": "0" * 64},
                "stderr_ref": artifact_ref(tmp_path, stderr_path),
            }
        ],
    }
    (tmp_path / ".playbook-artifacts/project_verification.json").write_text(json.dumps(result), encoding="utf-8")

    findings = playbook_validate.validate_release_verification(tmp_path)
    check_ids = {finding.check_id for finding in findings}

    assert "READINESS_RELEASE_FAILURE_COUNT_MISMATCH" in check_ids
    assert "READINESS_RELEASE_ARTIFACT_HASH_MISMATCH" in check_ids


def test_delivery_validation_blocks_self_completion(tmp_path: Path) -> None:
    playbook = tmp_path / ".playbook"
    playbook.mkdir()
    delivery = {
        "schema_version": "playbook.delivery_execution_model.v1",
        "delivery_profile": "solo_verified",
        "orchestrator": {"kind": "human"},
        "implementer": {"kind": "active_codex_session"},
        "reviewer": {"kind": "human"},
        "verifier": {
            "kind": "deterministic_project_verifier",
            "binding_id": "project_verifier",
            "argv": ["{python}", "tools/verify_project.py", "--root", "."],
            "command": "python tools/verify_project.py --root .",
        },
        "completion_authority": {"kind": "active_codex_session"},
        "cli_bindings": {"codex_direct": "active_session"},
        "permission_profile": "repo_local_default",
        "budget": {"spend_budget": "project_defined"},
        "independent_review_triggers": ["meaningful_implementation_change"],
    }
    (playbook / "delivery_execution_model.json").write_text(json.dumps(delivery), encoding="utf-8")

    findings = playbook_validate.validate_delivery(tmp_path)

    assert [finding.check_id for finding in findings] == ["DELIVERY_SELF_COMPLETION_AUTHORITY"]


def test_delivery_validation_requires_contract_for_generated_project(tmp_path: Path) -> None:
    playbook = tmp_path / ".playbook"
    playbook.mkdir()
    (playbook / "project_verification.json").write_text("{}", encoding="utf-8")

    findings = playbook_validate.validate_delivery(tmp_path)

    assert [finding.check_id for finding in findings] == ["DELIVERY_CONTRACT_MISSING"]


def test_delivery_validation_rejects_unstructured_verifier_binding(tmp_path: Path) -> None:
    playbook = tmp_path / ".playbook"
    playbook.mkdir()
    delivery = {
        "schema_version": "playbook.delivery_execution_model.v1",
        "delivery_profile": "solo_verified",
        "orchestrator": {"kind": "human"},
        "implementer": {"kind": "active_codex_session"},
        "reviewer": {"kind": "human"},
        "verifier": {
            "kind": "deterministic_project_verifier",
            "binding_id": "project_verifier",
            "argv": ["echo", "tools/verify_project.py"],
            "command": "echo tools/verify_project.py",
        },
        "completion_authority": {"kind": "human"},
        "cli_bindings": {"codex_direct": "active_session"},
        "permission_profile": "repo_local_default",
        "budget": {"spend_budget": "project_defined"},
        "independent_review_triggers": ["meaningful_implementation_change"],
    }
    (playbook / "delivery_execution_model.json").write_text(json.dumps(delivery), encoding="utf-8")

    findings = playbook_validate.validate_delivery(tmp_path)

    assert [finding.check_id for finding in findings] == ["DELIVERY_VERIFIER_MISSING"]
