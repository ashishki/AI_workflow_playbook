from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import jsonschema


ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "tools" / "run_codex_role.py"
SCHEMA = json.loads((ROOT / "schemas" / "codex_role_run.schema.json").read_text(encoding="utf-8"))


RENDERER = r'''#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

MARKERS = {
    "product_design_review": "PRODUCT_DESIGN_REVIEW",
    "program_design_review": "PROGRAM_DESIGN_REVIEW",
    "slice_review": "SLICE_REVIEW",
    "maintainability_review": "MAINTAINABILITY_REVIEW",
}

parser = argparse.ArgumentParser()
parser.add_argument("--root")
parser.add_argument("--task")
parser.add_argument("--role", required=True)
parser.add_argument("--feature-id")
parser.add_argument("--slice-id")
parser.add_argument("--parse-report")
args = parser.parse_args()
if args.parse_report:
    text = Path(args.parse_report).read_text(encoding="utf-8")
    marker = MARKERS[args.role]
    match = re.search(rf"(?m)^{marker}: (PASS|ADVISORY|STOP_SHIP)\s*$", text)
    if not match:
        raise SystemExit("missing required marker")
    print(json.dumps({"role": args.role, "verdict": match.group(1)}))
else:
    print(f"Role: {args.role}")
    print(f"Task: {args.task}")
    print(f"Feature: {args.feature_id}")
    print(f"Slice: {args.slice_id}")
    print(f"Required marker: {MARKERS[args.role]}: PASS | ADVISORY | STOP_SHIP")
'''


FAKE_CODEX = r'''#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path
import sys

if sys.argv[1:] == ["--version"]:
    print("codex-cli 0.test")
    raise SystemExit(0)
if "CODEX_THREAD_ID" in os.environ:
    print("parent thread leaked", file=sys.stderr)
    raise SystemExit(7)
args = sys.argv[1:]
assert args[0] == "exec"
assert "--json" in args
assert args[args.index("--sandbox") + 1] == "read-only"
report = Path(args[args.index("--output-last-message") + 1])
prompt = args[-1]
marker = next(
    value
    for value in (
        "PRODUCT_DESIGN_REVIEW",
        "PROGRAM_DESIGN_REVIEW",
        "SLICE_REVIEW",
        "MAINTAINABILITY_REVIEW",
    )
    if value in prompt
)
mode = os.environ.get("FAKE_CODEX_MODE", "pass")
if mode == "write-drift":
    Path("reviewer-drift.txt").write_text("not allowed\n", encoding="utf-8")
if mode == "missing-marker":
    report.write_text("Review completed without a marker.\n", encoding="utf-8")
else:
    report.write_text(f"{marker}: PASS\nNo findings.\n", encoding="utf-8")
print(json.dumps({"type": "thread.started", "thread_id": "fake-thread"}))
print(json.dumps({"type": "turn.completed", "usage": {"input_tokens": 10, "output_tokens": 5}}))
raise SystemExit(0)
'''


def write_executable(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    path.chmod(0o755)
    return path


def make_project(tmp_path: Path) -> tuple[Path, Path]:
    project = tmp_path / "project"
    project.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=project, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=project, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=project, check=True)
    (project / ".gitignore").write_text(".playbook-artifacts/\n", encoding="utf-8")
    tools = project / "tools"
    tools.mkdir()
    write_executable(tools / "render_codex_exec_prompt.py", RENDERER)
    docs = project / "docs"
    (docs / "design").mkdir(parents=True)
    (docs / "tasks.md").write_text("# Tasks\n\nT01 reviewer task.\n", encoding="utf-8")
    (docs / "PROJECT_BRIEF.md").write_text("# Brief\n", encoding="utf-8")
    (docs / "ARCHITECTURE.md").write_text("# Architecture\n", encoding="utf-8")
    (docs / "design" / "F01.md").write_text("# Feature Design\n", encoding="utf-8")
    (docs / "design" / "F01.design.json").write_text(
        json.dumps(
            {
                "schema_version": "playbook.feature_design.v1",
                "feature_id": "F01",
                "status": "review_required",
                "planning_depth": "designed_slices",
                "risk_level": "high",
                "brief_ref": "docs/PROJECT_BRIEF.md",
                "architecture_refs": ["docs/ARCHITECTURE.md"],
                "approval_policy": "human_required",
                "slices": [],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    fake_codex = write_executable(tmp_path / "fake-codex", FAKE_CODEX)
    subprocess.run(["git", "add", "."], cwd=project, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "fixture"], cwd=project, check=True)
    return project, fake_codex


def runner_command(project: Path, codex: Path, run_id: str) -> list[str]:
    return [
        sys.executable,
        str(RUNNER),
        "run",
        "--root",
        str(project),
        "--task",
        "T01",
        "--feature-id",
        "F01",
        "--role",
        "program_design_review",
        "--codex-bin",
        str(codex),
        "--run-id",
        run_id,
        "--no-publish",
    ]


def run_role(
    project: Path,
    codex: Path,
    run_id: str,
    *,
    mode: str = "pass",
    parent_thread: bool = False,
) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["FAKE_CODEX_MODE"] = mode
    if parent_thread:
        env["CODEX_THREAD_ID"] = "interactive-parent"
    return subprocess.run(
        runner_command(project, codex, run_id),
        cwd=ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def result_path(project: Path, run_id: str) -> Path:
    return project / ".playbook-artifacts" / "runs" / run_id / "result.json"


def test_valid_role_run_is_schema_valid_replayable_and_parent_context_is_scrubbed(
    tmp_path: Path,
) -> None:
    project, codex = make_project(tmp_path)

    result = run_role(project, codex, "run-ok", parent_thread=True)

    assert result.returncode == 0, result.stderr
    path = result_path(project, "run-ok")
    payload = json.loads(path.read_text(encoding="utf-8"))
    jsonschema.validate(payload, SCHEMA)
    assert payload["status"] == "validated"
    assert payload["verdict"] == "PASS"
    assert payload["sandbox"] == "read-only"
    assert payload["codex"]["parent_codex_context_scrubbed"] is True
    assert payload["postflight"]["workspace_unchanged"] is True
    assert payload["postflight"]["event_count"] == 2
    ledger = path.parent / "events.jsonl"
    events = [json.loads(line) for line in ledger.read_text(encoding="utf-8").splitlines()]
    assert [event["sequence"] for event in events] == list(range(1, len(events) + 1))
    assert events[-1]["event_type"] == "role.result.written"

    verify = subprocess.run(
        [
            sys.executable,
            str(RUNNER),
            "verify",
            "--root",
            str(project),
            "--result",
            str(path),
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert verify.returncode == 0, verify.stderr


def test_missing_required_marker_fails_postflight(tmp_path: Path) -> None:
    project, codex = make_project(tmp_path)
    result = run_role(project, codex, "run-missing", mode="missing-marker")
    assert result.returncode == 1, result.stderr
    payload = json.loads(result_path(project, "run-missing").read_text(encoding="utf-8"))
    assert payload["status"] == "postflight_failed"
    assert payload["postflight"]["marker_valid"] is False
    assert any("marker" in error for error in payload["postflight"]["errors"])


def test_read_only_reviewer_write_drift_is_rejected(tmp_path: Path) -> None:
    project, codex = make_project(tmp_path)
    result = run_role(project, codex, "run-drift", mode="write-drift")
    assert result.returncode == 1, result.stderr
    payload = json.loads(result_path(project, "run-drift").read_text(encoding="utf-8"))
    assert payload["status"] == "postflight_failed"
    assert payload["postflight"]["workspace_unchanged"] is False
    assert payload["postflight"]["changed_paths"] == ["reviewer-drift.txt"]


def test_report_tamper_invalidates_saved_role_result(tmp_path: Path) -> None:
    project, codex = make_project(tmp_path)
    assert run_role(project, codex, "run-report-tamper").returncode == 0
    path = result_path(project, "run-report-tamper")
    payload = json.loads(path.read_text(encoding="utf-8"))
    report = project / payload["outputs"]["report_path"]
    report.write_text("PROGRAM_DESIGN_REVIEW: STOP_SHIP\nTampered.\n", encoding="utf-8")
    verify = subprocess.run(
        [sys.executable, str(RUNNER), "verify", "--root", str(project), "--result", str(path)],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert verify.returncode == 2
    assert "artifact hash mismatch" in verify.stderr


def test_ledger_tamper_invalidates_saved_role_result(tmp_path: Path) -> None:
    project, codex = make_project(tmp_path)
    assert run_role(project, codex, "run-ledger-tamper").returncode == 0
    path = result_path(project, "run-ledger-tamper")
    ledger = path.parent / "events.jsonl"
    events = [json.loads(line) for line in ledger.read_text(encoding="utf-8").splitlines()]
    events[0]["details"]["task_id"] = "T99"
    ledger.write_text(
        "".join(json.dumps(event, sort_keys=True) + "\n" for event in events),
        encoding="utf-8",
    )
    verify = subprocess.run(
        [sys.executable, str(RUNNER), "verify", "--root", str(project), "--result", str(path)],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert verify.returncode == 2
    assert "ledger event hash mismatch" in verify.stderr


def test_slice_role_requires_explicit_feature_and_slice_identity(tmp_path: Path) -> None:
    project, codex = make_project(tmp_path)
    result = subprocess.run(
        [
            sys.executable,
            str(RUNNER),
            "run",
            "--root",
            str(project),
            "--task",
            "T01",
            "--role",
            "slice_review",
            "--codex-bin",
            str(codex),
            "--no-publish",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert result.returncode == 2
    assert "requires --feature-id and --slice-id" in result.stderr
