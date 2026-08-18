from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import jsonschema

from tools import role_run_lib


ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "tools/run_codex_role.py"
SCHEMA = json.loads((ROOT / "schemas/role_run.schema.json").read_text(encoding="utf-8"))


def init_git(root: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "tests@example.com"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "Playbook Tests"], cwd=root, check=True)
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    subprocess.run(["git", "commit", "-qm", "fixture"], cwd=root, check=True)


def write_project(root: Path) -> None:
    (root / "docs/design").mkdir(parents=True)
    (root / "templates").mkdir()
    (root / ".gitignore").write_text(".playbook-artifacts/\n", encoding="utf-8")
    (root / "README.md").write_text("# Fixture\n", encoding="utf-8")
    (root / "docs/PROJECT_BRIEF.md").write_text("# Brief\n\nStatus: approved\n", encoding="utf-8")
    (root / "docs/REVIEW_POLICY.md").write_text("Designed slices require independent review.\n", encoding="utf-8")
    (root / "docs/ARCHITECTURE.md").write_text("# Architecture\n\nReuse existing services.\n", encoding="utf-8")
    (root / "templates/AGENTS.md").write_text("# Agent rules\n", encoding="utf-8")
    (root / "docs/tasks.md").write_text(
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
    (root / "docs/design/F01.md").write_text(
        "# Feature Design\n\n## Product Outcome\n\nCreate privacy-safe events.\n",
        encoding="utf-8",
    )
    design = {
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
                "scope": "API through tests.",
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
                        "timeout_seconds": 600,
                    }
                ],
                "review_checkpoint": "slice_review",
                "dependencies": [],
                "change_budget": "files<=4, lines<=200",
                "rollback": "revert S01 diff",
            }
        ],
    }
    (root / "docs/design/F01.design.json").write_text(
        json.dumps(design, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    init_git(root)


def fake_codex(path: Path) -> Path:
    path.write_text(
        """#!/usr/bin/env python3
import json
import os
import pathlib
import sys

if sys.argv[1:] == ["--version"]:
    print("codex-cli test-1.0")
    raise SystemExit(0)

args = sys.argv[1:]
assert args[0] == "exec"
assert "--ephemeral" in args
assert "--ignore-user-config" in args
assert "--ignore-rules" in args
assert "--strict-config" in args
assert "--json" in args
assert args[args.index("--sandbox") + 1] == "read-only"
report = pathlib.Path(args[args.index("--output-last-message") + 1])
prompt = sys.stdin.read()
assert "Role: program_design_review" in prompt
if os.environ.get("FAKE_CODEX_MUTATE") == "1":
    pathlib.Path("docs/ARCHITECTURE.md").write_text("changed by reviewer\\n", encoding="utf-8")
marker = os.environ.get("FAKE_CODEX_MARKER", "PROGRAM_DESIGN_REVIEW")
verdict = os.environ.get("FAKE_CODEX_VERDICT", "PASS")
if os.environ.get("FAKE_CODEX_NO_MARKER") == "1":
    report.write_text("No marker here.\\n", encoding="utf-8")
else:
    report.write_text(f"{marker}: {verdict}\\nNo findings.\\n", encoding="utf-8")
print(json.dumps({"type": "turn.completed", "model": "gpt-test", "usage": {"input_tokens": 10, "output_tokens": 5}}))
raise SystemExit(int(os.environ.get("FAKE_CODEX_EXIT", "0")))
""",
        encoding="utf-8",
    )
    path.chmod(0o755)
    return path


def run_role(project: Path, codex: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(RUNNER),
            "--root",
            str(project),
            "--task",
            "T03",
            "--feature-id",
            "F01",
            "--role",
            "program_design_review",
            "--codex-bin",
            str(codex),
            "--model",
            "gpt-test",
            "--run-id",
            "test-run",
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={**os.environ, **(env or {})},
        check=False,
    )


def sidecar(project: Path) -> Path:
    return project / ".playbook-artifacts/reports/F01/program_design_review.role_run.json"


def test_role_runner_produces_validated_traceable_review(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    write_project(project)
    result = run_role(project, fake_codex(tmp_path / "codex"))

    assert result.returncode == 0, result.stderr
    payload = json.loads(sidecar(project).read_text(encoding="utf-8"))
    jsonschema.validate(payload, SCHEMA)
    assert payload["status"] == "validated"
    assert payload["verdict"] == "PASS"
    assert payload["sandbox"] == "read-only"
    assert payload["fresh_process"] is True
    assert payload["prompt_sha256"]
    assert payload["context_manifest_sha256"]
    assert payload["observed_model"] == "gpt-test"
    validated, problems = role_run_lib.validate_role_result(
        project,
        sidecar(project),
        expected_role="program_design_review",
        expected_task_id="T03",
        expected_feature_id="F01",
    )
    assert validated is not None
    assert problems == []
    ledger = project / payload["event_ledger_path"]
    event_types = [json.loads(line)["type"] for line in ledger.read_text(encoding="utf-8").splitlines()]
    assert event_types == [
        "role.requested",
        "context.materialized",
        "codex.exec.started",
        "codex.exec.finished",
        "role.postflight",
    ]
    review_record = project / ".playbook-artifacts/reviews/F01/design/program_design_review.review.json"
    assert review_record.exists()


def test_role_runner_fails_closed_on_missing_marker(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    write_project(project)
    result = run_role(project, fake_codex(tmp_path / "codex"), {"FAKE_CODEX_NO_MARKER": "1"})

    assert result.returncode == 2
    payload = json.loads(sidecar(project).read_text(encoding="utf-8"))
    assert payload["status"] == "invalid"
    assert any("missing required marker" in item for item in payload["failure_reasons"])


def test_role_runner_detects_read_only_write_drift(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    write_project(project)
    result = run_role(project, fake_codex(tmp_path / "codex"), {"FAKE_CODEX_MUTATE": "1"})

    assert result.returncode == 2
    payload = json.loads(sidecar(project).read_text(encoding="utf-8"))
    assert payload["write_drift"] is True
    assert "read-only reviewer changed repository state" in payload["failure_reasons"]


def test_stop_ship_is_valid_evidence_but_nonzero_control_signal(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    write_project(project)
    result = run_role(project, fake_codex(tmp_path / "codex"), {"FAKE_CODEX_VERDICT": "STOP_SHIP"})

    assert result.returncode == 1, result.stderr
    payload = json.loads(sidecar(project).read_text(encoding="utf-8"))
    assert payload["status"] == "validated"
    assert payload["verdict"] == "STOP_SHIP"


def test_role_result_tamper_is_detected(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    write_project(project)
    result = run_role(project, fake_codex(tmp_path / "codex"))
    assert result.returncode == 0, result.stderr
    payload = json.loads(sidecar(project).read_text(encoding="utf-8"))
    report = project / payload["report_path"]
    report.write_text("PROGRAM_DESIGN_REVIEW: PASS\nTampered.\n", encoding="utf-8")

    _validated, problems = role_run_lib.validate_role_result(project, sidecar(project))
    assert "role result artifact hash mismatch: report_path" in problems


def test_slice_role_requires_slice_binding(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    write_project(project)
    result = subprocess.run(
        [
            sys.executable,
            str(RUNNER),
            "--root",
            str(project),
            "--task",
            "T03",
            "--feature-id",
            "F01",
            "--slice-id",
            "WRONG",
            "--role",
            "slice_review",
            "--codex-bin",
            str(fake_codex(tmp_path / "codex")),
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 2
    assert "Slice-ID S01 conflicts" in result.stderr


def test_review_policy_routes_supported_roles_through_guarded_runner() -> None:
    from tools import feature_review_policy

    design = {
        "planning_depth": "designed_slices",
        "risk_level": "high",
        "feature_id": "F01",
    }
    report = feature_review_policy.report(feature_id="F01", design=design)

    assert {item["role"] for item in report["reviews"]} == {
        "product_design_review",
        "program_design_review",
    }
    assert all(item["runner_required"] is True for item in report["reviews"])
    assert all(item["execution_surface"] == "codex_role_runner" for item in report["reviews"])
