from __future__ import annotations

import hashlib
import json
import os
import platform
import shlex
import shutil
import stat
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

from ai_workflow_harness_lab.environment import environment_digest, post_state_manifest
from ai_workflow_harness_lab.evidence import manifest_hash, write_bundle
from ai_workflow_harness_lab.runner import write_run_result
from ai_workflow_harness_lab.scorers.base import write_scorer_output


ROOT = Path(__file__).resolve().parents[2]
TOOLS_DIR = ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from build_test_first_pilot_manifest import manifest_bytes as frozen_manifest_bytes
import test_first_pilot_run_seal as run_seal


TOOL = ROOT / "tools/prepare_test_first_pilot_review.py"
SUITE = ROOT / "companion/ai_workflow_harness_lab/suites/shishki_bot_ci_v1"
VENV_PYTHON = ROOT / ".venv/bin/python"
ADAPTER = ROOT / "tools/test_first_pilot_codex_adapter.py"
SANDBOX = ROOT / "tools/test_first_pilot_sandbox.py"
BWRAP = Path("/usr/bin/bwrap")
CODEX = Path(
    "/home/ashishki/.nvm/versions/node/v22.22.1/lib/node_modules/@openai/codex/"
    "node_modules/@openai/codex-linux-x64/vendor/x86_64-unknown-linux-musl/bin/codex"
)
TASKS = {
    "pin_ci_actions": {
        "version": "pin-ci-actions.v1",
        "allowed": ".github/workflows/ci.yml",
        "markers": ["pilot_tests/test_ci_pins.py"],
        "scorers": [
            "pin_ci_actions_acceptance",
            "pin_ci_actions_scope",
            "checkout_pin_present",
            "setup_python_pin_present",
        ],
    },
    "reject_unapproved_ci_actions": {
        "version": "reject-unapproved-ci-actions.v1",
        "allowed": "tests/test_ci_supply_chain.py",
        "markers": [
            "tests/test_ci_supply_chain.py",
            "pilot_tests/test_unapproved_action.py",
        ],
        "scorers": [
            "reject_unapproved_ci_actions_acceptance",
            "reject_unapproved_ci_actions_scope",
        ],
    },
}
FORBIDDEN_KEYS = ("condition", "path", "prompt", "timestamp", "trace")
EXECUTION_ORDER = (
    ("pin_ci_actions", 0, "baseline"),
    ("pin_ci_actions", 0, "playbook"),
    ("reject_unapproved_ci_actions", 0, "playbook"),
    ("reject_unapproved_ci_actions", 0, "baseline"),
    ("pin_ci_actions", 1, "playbook"),
    ("pin_ci_actions", 1, "baseline"),
    ("reject_unapproved_ci_actions", 1, "baseline"),
    ("reject_unapproved_ci_actions", 1, "playbook"),
    ("pin_ci_actions", 2, "baseline"),
    ("pin_ci_actions", 2, "playbook"),
    ("reject_unapproved_ci_actions", 2, "playbook"),
    ("reject_unapproved_ci_actions", 2, "baseline"),
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def corrupt_first_digest(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    replacement = "0" if text[0] != "0" else "1"
    path.write_text(replacement + text[1:], encoding="utf-8")


def write_bundle_manifest(run_root: Path) -> None:
    bundles = sorted(run_root.rglob("bundle.json"))
    (run_root / "bundle_manifest.sha256").write_text(
        "".join(f"{sha256(bundle)}  {bundle.relative_to(run_root)}\n" for bundle in bundles),
        encoding="utf-8",
    )


def write_run_seal(run_root: Path) -> str:
    seal = run_root / run_seal.SEAL_NAME
    if seal.exists() or seal.is_symlink():
        seal.unlink()
    return run_seal.write_seal(run_root).seal_sha256


def reseal_bundle(run_root: Path, bundle_file: Path) -> None:
    payload = json.loads(bundle_file.read_text(encoding="utf-8"))
    refs = [
        payload.get("prompt_ref"),
        payload.get("post_state_manifest"),
        payload.get("generated_report_ref"),
        *payload.get("command_receipts", []),
        *payload.get("trace_refs", []),
        *payload.get("scorer_outputs", []),
    ]
    for ref in refs:
        if isinstance(ref, dict):
            artifact = bundle_file.parent / ref["path"]
            ref["sha256"] = sha256(artifact)
    payload["manifest_hash"] = manifest_hash(payload)
    bundle_file.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_bundle_manifest(run_root)


def bundle_trace(bundle_file: Path, name: str) -> Path:
    payload = json.loads(bundle_file.read_text(encoding="utf-8"))
    matches = [
        bundle_file.parent / ref["path"]
        for ref in payload["trace_refs"]
        if Path(ref["path"]).name == name
    ]
    assert len(matches) == 1
    return matches[0]


def bundle_ref(bundle_file: Path, field: str, index: int | None = None) -> Path:
    payload = json.loads(bundle_file.read_text(encoding="utf-8"))
    ref = payload[field] if index is None else payload[field][index]
    return bundle_file.parent / ref["path"]


def mutate_json(path: Path, mutation: Any) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    mutation(payload)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_governance(run_root: Path, asset_manifest: bytes | None = None) -> None:
    copied_manifest = run_root / "asset_manifest.sha256"
    copied_manifest.write_bytes(asset_manifest or frozen_manifest_bytes())
    critic = run_root / "critic_record.md"
    critic.write_text("Independent frozen-scope review\nDecision: ALLOW\n", encoding="utf-8")
    approval = run_root / "approval_record.md"
    approval.write_text(
        "\n".join(
            (
                "Approval ID: approval-1",
                "Pilot ID: pilot-1",
                f"Manifest SHA-256: {sha256(copied_manifest)}",
                f"Critic report SHA-256: {sha256(critic)}",
                "Codex executions: 12",
                "Retries: 0",
                "Decision: approved",
                "",
            )
        ),
        encoding="utf-8",
    )
    (run_root / "governance_manifest.sha256").write_text(
        "".join(
            (
                f"{sha256(approval)}  approval_record.md\n",
                f"{sha256(copied_manifest)}  asset_manifest.sha256\n",
                f"{sha256(critic)}  critic_record.md\n",
            )
        ),
        encoding="utf-8",
    )


def iso(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


def write_receipt(
    output_dir: Path,
    *,
    task_id: str,
    argv: list[str],
    workspace: Path,
    start: datetime,
    end: datetime,
    start_monotonic_ns: int,
    end_monotonic_ns: int,
    timeout: float,
    stdout: bytes,
    exit_code: int = 0,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    artifacts = {
        "stdout.txt": stdout,
        "stderr.txt": b"",
        "diff_stat.txt": b"",
    }
    for name, content in artifacts.items():
        (output_dir / name).write_bytes(content)
    receipt = {
        "schema_version": "playbook.command_receipt.v1",
        "receipt_id": f"{task_id}-{start_monotonic_ns}",
        "task_id": task_id,
        "producer": "ai_workflow_harness_lab.receipts",
        "command_argv": argv,
        "working_directory": str(workspace),
        "start_timestamp": iso(start),
        "end_timestamp": iso(end),
        "exit_code": exit_code,
        "stdout_artifact_path": "stdout.txt",
        "stdout_sha256": sha256(output_dir / "stdout.txt"),
        "stderr_artifact_path": "stderr.txt",
        "stderr_sha256": sha256(output_dir / "stderr.txt"),
        "repo_commit_before": "not_inspected",
        "repo_commit_after": "not_inspected",
        "dirty_state_before": ["not_inspected"],
        "dirty_state_after": ["not_inspected"],
        "diff_stat_artifact_path": "diff_stat.txt",
        "diff_stat_sha256": sha256(output_dir / "diff_stat.txt"),
        "environment_summary": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "timeout": timeout,
            "timed_out": False,
            "git_inspection": False,
            "start_monotonic_ns": start_monotonic_ns,
            "end_monotonic_ns": end_monotonic_ns,
        },
        "parent_receipt_id": None,
        "redaction_status": "not_requested",
    }
    receipt_file = output_dir / "receipt.json"
    receipt_file.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt_file


def adapter_tokens(
    trial_dir: Path,
    workspace: Path,
    prompt: Path,
    task_id: str,
    condition: str,
    trial: int,
    manifest_digest: str,
) -> list[str]:
    return [
        str(BWRAP),
        "--die-with-parent",
        "--new-session",
        "--unshare-pid",
        "--bind",
        "/",
        "/",
        "--proc",
        "/proc",
        "--dev-bind",
        "/dev",
        "/dev",
        "--",
        str(VENV_PYTHON),
        "-I",
        "-B",
        "-X",
        "pycache_prefix=/dev/null/test-first-pilot-pycache",
        str(ADAPTER),
        "--workspace",
        str(workspace),
        "--prompt",
        str(prompt),
        "--output",
        str(trial_dir / "adapter"),
        "--pilot-id",
        "pilot-1",
        "--attempt-id",
        f"{task_id}-{condition}-{trial}",
        "--task",
        task_id,
        "--condition",
        condition,
        "--trial",
        str(trial),
        "--manifest-digest",
        manifest_digest,
        "--approval-id",
        "approval-1",
        "--codex-bin",
        str(CODEX),
        "--timeout",
        "1200",
    ]


def verifier_argv(workspace: Path, markers: list[str]) -> list[str]:
    return [
        str(VENV_PYTHON),
        str(SANDBOX),
        "--workspace",
        str(workspace),
        "--",
        str(VENV_PYTHON),
        "-I",
        "-X",
        "pycache_prefix=/dev/null/test-first-pilot-verifier",
        "-m",
        "pytest",
        "-q",
        "-p",
        "no:cacheprovider",
        *markers,
    ]


def write_completed_run(run_root: Path) -> None:
    run_root.mkdir(parents=True)
    write_governance(run_root)
    manifest_digest = sha256(run_root / "asset_manifest.sha256")
    schedule_index = {arm: index for index, arm in enumerate(EXECUTION_ORDER)}
    for condition in ("baseline", "playbook"):
        for task_id, task in TASKS.items():
            fixture = SUITE / "fixtures" / task_id
            digest = environment_digest(fixture)
            for trial in range(3):
                trial_dir = run_root / condition / task_id / f"trial-{trial}"
                workspace = trial_dir / "workspace"
                shutil.copytree(fixture, workspace)
                if condition == "playbook":
                    allowed = workspace / str(task["allowed"])
                    allowed.write_text(
                        allowed.read_text(encoding="utf-8") + "\n# candidate change\n",
                        encoding="utf-8",
                    )

                prompt = trial_dir / "prompt.md"
                prompt.write_bytes(
                    (SUITE / "prompts" / f"{task_id}.{condition}.md").read_bytes()
                )
                common = {
                    "schema_version": "test_first_pilot.event.v1",
                    "pilot_manifest_sha256": manifest_digest,
                    "approval_id": "approval-1",
                    "pilot_id": "pilot-1",
                    "attempt_id": f"{task_id}-{condition}-{trial}",
                    "task_id": task_id,
                    "condition": condition,
                    "trial": trial,
                    "model": "gpt-5.6-sol",
                    "reasoning_effort": "medium",
                    "service_tier": "default",
                }
                started = datetime(2026, 7, 14, tzinfo=timezone.utc) + timedelta(
                    minutes=10 * schedule_index[(task_id, trial, condition)]
                )
                outer_start_ns = 1_000_000_000 + 1_000_000_000 * schedule_index[
                    (task_id, trial, condition)
                ]
                outer_end_ns = outer_start_ns + 100_000_000
                command = "python -m pytest -q " + " ".join(task["markers"])
                codex_events = [
                    {
                        "type": "item.started",
                        "item": {
                            "type": "command_execution",
                            "id": "command-1",
                            "command": command,
                        },
                    },
                    {
                        "type": "item.completed",
                        "item": {
                            "type": "command_execution",
                            "id": "command-1",
                            "command": command,
                            "exit_code": 0,
                        },
                    },
                ]
                raw_trace = trial_dir / "adapter/codex_events.jsonl"
                raw_trace.parent.mkdir(parents=True, exist_ok=True)
                raw_trace.write_text(
                    "".join(json.dumps(event, sort_keys=True) + "\n" for event in codex_events),
                    encoding="utf-8",
                )
                ledger_events = [
                    {"event": "adapter_start"},
                    {
                        "event": "human_intervention",
                        "occurred": False,
                        "reason": "non-interactive test adapter",
                    },
                    {
                        "event": "command_start",
                        "source_event_type": "item.started",
                        "source_item_id": "command-1",
                        "command": command,
                    },
                    {
                        "event": "verifier_start",
                        "source_event_type": "item.started",
                        "source_item_id": "command-1",
                        "command": command,
                        "verifier_attempt": 1,
                    },
                    {
                        "event": "command_end",
                        "source_event_type": "item.completed",
                        "source_item_id": "command-1",
                        "command": command,
                        "result": "passed",
                        "exit_code": 0,
                    },
                    {
                        "event": "verifier_end",
                        "source_event_type": "item.completed",
                        "source_item_id": "command-1",
                        "command": command,
                        "verifier_attempt": 1,
                        "result": "passed",
                        "exit_code": 0,
                    },
                    {
                        "event": "first_green",
                        "source_item_id": "command-1",
                        "verifier_attempt": 1,
                        "result": "passed",
                    },
                    {"event": "final_model_gate", "result": "passed", "verifier_attempt": 1},
                    {
                        "event": "adapter_end",
                        "codex_exit_code": 0,
                        "wrapper_exit_code": 0,
                        "terminal_class": "completed",
                        "timed_out": False,
                    },
                ]
                ledger = trial_dir / "adapter/event_ledger.jsonl"
                ledger.parent.mkdir(parents=True, exist_ok=True)
                ledger.write_text(
                    "".join(
                        json.dumps(
                            {
                                **common,
                                **event,
                                "timestamp": (
                                    started + timedelta(seconds=index + 1)
                                ).isoformat().replace("+00:00", "Z"),
                                "monotonic_ns": outer_start_ns
                                + 1_000_000
                                + index * 1_000_000,
                            },
                            sort_keys=True,
                        )
                        + "\n"
                        for index, event in enumerate(ledger_events)
                    ),
                    encoding="utf-8",
                )
                stderr_trace = trial_dir / "adapter/codex_stderr.txt"
                stderr_trace.write_bytes(b"")
                final_message = trial_dir / "adapter/final_message.txt"
                final_message.write_text("synthetic completed response\n", encoding="utf-8")
                terminal = {
                    "codex_exit_code": 0,
                    "wrapper_exit_code": 0,
                    "terminal_class": "completed",
                    "timed_out": False,
                }
                summary = {
                    **common,
                    "schema_version": "test_first_pilot.adapter_summary.v1",
                    "codex_cli": "codex-cli 0.144.4",
                    **terminal,
                    "network_access": False,
                    "web_search": "disabled",
                    "permission_profile": "test_first_pilot",
                    "python_executable": str(VENV_PYTHON),
                    "venv_root": str(ROOT / ".venv"),
                    "codex_runtime_read_root": str(CODEX),
                    "disabled_features": [],
                    "trace_parse_errors": 0,
                    "trace_eof_confirmed": True,
                    "trace_capture_error": None,
                    "codex_terminal_event_observed": True,
                    "prompt_sha256": hashlib.sha256(prompt.read_bytes()).hexdigest(),
                    "prompt_size_bytes": len(prompt.read_bytes()),
                    "trace_path": "codex_events.jsonl",
                    "stderr_path": "codex_stderr.txt",
                    "final_message_path": "final_message.txt",
                    "ledger_path": "event_ledger.jsonl",
                }
                summary_file = trial_dir / "adapter/adapter_summary.json"
                summary_file.write_text(
                    json.dumps(summary, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8",
                )
                outer_tokens = adapter_tokens(
                    trial_dir,
                    workspace,
                    prompt,
                    task_id,
                    condition,
                    trial,
                    manifest_digest,
                )
                adapter_receipt = write_receipt(
                    trial_dir / "adapter/receipts/command",
                    task_id=task_id,
                    argv=["/bin/sh", "-c", shlex.join(outer_tokens)],
                    workspace=workspace,
                    start=started,
                    end=started + timedelta(seconds=10),
                    start_monotonic_ns=outer_start_ns,
                    end_monotonic_ns=outer_end_ns,
                    timeout=1260.0,
                    stdout=(json.dumps(terminal, sort_keys=True) + "\n").encode("utf-8"),
                )
                verifier_receipt = write_receipt(
                    trial_dir / "verification/receipts/required-verification",
                    task_id=task_id,
                    argv=verifier_argv(workspace, list(task["markers"])),
                    workspace=workspace,
                    start=started + timedelta(seconds=11),
                    end=started + timedelta(seconds=12),
                    start_monotonic_ns=outer_end_ns + 1_000_000,
                    end_monotonic_ns=outer_end_ns + 2_000_000,
                    timeout=60.0,
                    stdout=b"2 passed\n",
                )
                scorer_dir = trial_dir / "scorers"
                scorers = [
                    write_scorer_output(
                        scorer_dir,
                        scorer_id,
                        task_id,
                        "passed",
                        1.0,
                        {"synthetic": True},
                        [],
                    )
                    for scorer_id in task["scorers"]
                ]
                run_result = write_run_result(
                    trial_dir,
                    task_id,
                    f"{task_id}-{condition}-{trial}",
                    1.0,
                    True,
                    [],
                )
                manifest = post_state_manifest(workspace, trial_dir / "post_state_manifest.json")
                report = trial_dir / "report.md"
                report.write_text("raw report must not enter blind review\n", encoding="utf-8")
                write_bundle(
                    output_dir=trial_dir,
                    repository="shishki_bot_ci_v1",
                    task_id=task_id,
                    task_spec_version=str(task["version"]),
                    condition=condition,
                    adapter_version="command.v1",
                    environment_digest=digest,
                    prompt_file=prompt,
                    commit_before="a" * 40,
                    commit_after="a" * 40,
                    receipt_paths=[adapter_receipt, verifier_receipt],
                    trace_paths=[
                        raw_trace,
                        stderr_trace,
                        final_message,
                        ledger,
                        summary_file,
                        run_result,
                    ],
                    post_state_manifest=manifest,
                    scorer_outputs=scorers,
                    failure_records=[],
                    report_path=report,
                )
    write_bundle_manifest(run_root)
    write_run_seal(run_root)


def run_tool(run_root: Path, review: Path, mapping: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(TOOL),
            "--run-root",
            str(run_root),
            "--review-output",
            str(review),
            "--mapping-output",
            str(mapping),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


@pytest.fixture(scope="module")
def completed_run_template(tmp_path_factory: pytest.TempPathFactory) -> Path:
    run_root = tmp_path_factory.mktemp("completed-pilot") / "pilot-1"
    write_completed_run(run_root)
    return run_root


def copy_completed_run(template: Path, parent: Path) -> Path:
    run_root = parent / "pilot-1"
    shutil.copytree(template, run_root)
    old_root = str(template)
    new_root = str(run_root)

    def relocate(value: Any) -> Any:
        if isinstance(value, dict):
            return {key: relocate(item) for key, item in value.items()}
        if isinstance(value, list):
            return [relocate(item) for item in value]
        if isinstance(value, str):
            return value.replace(old_root, new_root)
        return value

    for receipt in run_root.rglob("receipt.json"):
        receipt.write_text(
            json.dumps(relocate(json.loads(receipt.read_text(encoding="utf-8"))), indent=2, sort_keys=True)
            + "\n",
            encoding="utf-8",
        )
    for manifest in run_root.rglob("post_state_manifest.json"):
        manifest.write_text(
            json.dumps(relocate(json.loads(manifest.read_text(encoding="utf-8"))), indent=2, sort_keys=True)
            + "\n",
            encoding="utf-8",
        )
    for bundle in run_root.rglob("bundle.json"):
        reseal_bundle(run_root, bundle)
    write_run_seal(run_root)
    return run_root


def assert_blind(value: Any) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            assert not any(part in key.lower() for part in FORBIDDEN_KEYS), key
            assert_blind(item)
    elif isinstance(value, list):
        for item in value:
            assert_blind(item)
    elif isinstance(value, str):
        assert "baseline" not in value.lower()
        assert "playbook" not in value.lower()


def test_prepares_six_blind_pairs_and_separate_protected_mapping(
    tmp_path: Path, completed_run_template: Path
) -> None:
    run_root = copy_completed_run(completed_run_template, tmp_path)
    review = tmp_path / "blind-review"
    mapping = tmp_path / "protected-mapping"

    result = run_tool(run_root, review, mapping)

    assert result.returncode == 0, result.stderr
    summary = json.loads(result.stdout)
    assert summary["pair_count"] == 6
    manifest = json.loads((review / "manifest.json").read_text(encoding="utf-8"))
    protected = json.loads((mapping / "mapping.json").read_text(encoding="utf-8"))
    assert manifest["pair_count"] == protected["pair_count"] == 6
    assert manifest["protected_mapping_sha256"] == sha256(mapping / "mapping.json")
    assert protected["completed_run_seal_sha256"] == sha256(
        run_root / run_seal.SEAL_NAME
    )
    assert stat.S_IMODE(mapping.stat().st_mode) == 0o700
    assert stat.S_IMODE((mapping / "mapping.json").stat().st_mode) == 0o600

    pair_files = sorted(review.glob("pair-*.json"))
    assert len(pair_files) == 6
    assert {entry["labels"]["A"]["condition"] for entry in protected["mappings"]} == {
        "baseline",
        "playbook",
    }
    assert sum(
        entry["labels"]["A"]["condition"] == "baseline"
        for entry in protected["mappings"]
    ) == 3
    for pair_file in pair_files:
        package = json.loads(pair_file.read_text(encoding="utf-8"))
        assert_blind(package)
        assert set(package["candidates"]) == {"A", "B"}
        assert package["task"]["rubric"]
        for candidate in package["candidates"].values():
            assert candidate["allowed_change"]["content"] is not None
            assert candidate["verification"] == {
                "exit_code": 0,
                "status": "passed",
                "test_counts": {"passed": 2},
                "timed_out": False,
            }
            assert "execution_process" not in candidate
            scorer_ids = {item["id"] for item in candidate["scorers"]}
            assert scorer_ids in (
                set(TASKS["pin_ci_actions"]["scorers"]),
                set(TASKS["reject_unapproved_ci_actions"]["scorers"]),
            )
    for entry in protected["mappings"]:
        for label in ("A", "B"):
            process = entry["labels"][label]["execution_process"]
            assert process["correction_limit_enforcement"] == "not_enforced"
            assert process["prompt_correction_limit"] == 1
            assert process["repair_candidates"] == 0
            assert process["first_green_observed"] is True
    assert_blind(manifest)


def test_refuses_overwrite_without_changing_existing_outputs(
    tmp_path: Path, completed_run_template: Path
) -> None:
    run_root = copy_completed_run(completed_run_template, tmp_path)
    review = tmp_path / "blind-review"
    mapping = tmp_path / "protected-mapping"
    assert run_tool(run_root, review, mapping).returncode == 0
    before = {
        path.relative_to(tmp_path): sha256(path)
        for path in tmp_path.rglob("*")
        if path.is_file()
    }

    result = run_tool(run_root, review, mapping)

    after = {
        path.relative_to(tmp_path): sha256(path)
        for path in tmp_path.rglob("*")
        if path.is_file()
    }
    assert result.returncode == 1
    assert "refusing to overwrite" in result.stderr
    assert after == before


def test_rejects_tampered_bundle_and_overlapping_output_paths(
    tmp_path: Path, completed_run_template: Path
) -> None:
    run_root = copy_completed_run(completed_run_template, tmp_path)
    bundle = next(run_root.rglob("bundle.json"))
    payload = json.loads(bundle.read_text(encoding="utf-8"))
    payload["manifest_hash"] = "b" * 64
    bundle.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    tampered = run_tool(run_root, tmp_path / "review", tmp_path / "mapping")
    overlap = run_tool(
        run_root,
        tmp_path / "outer",
        tmp_path / "outer/protected",
    )

    assert tampered.returncode == 1
    assert "completed-run seal verification failed" in tampered.stderr
    assert not (tmp_path / "review").exists()
    assert not (tmp_path / "mapping").exists()
    assert overlap.returncode == 1
    assert "must not overlap" in overlap.stderr
    assert not (tmp_path / "outer").exists()


def test_rejects_invalid_arm_even_when_bundle_and_manifest_are_resealed(
    tmp_path: Path, completed_run_template: Path
) -> None:
    run_root = copy_completed_run(completed_run_template, tmp_path)
    bundle_file = next(run_root.rglob("bundle.json"))
    payload = json.loads(bundle_file.read_text(encoding="utf-8"))
    payload["failure_records"] = [
        {
            "schema_version": "playbook.failure_record.v1",
            "failure_id": "environment-invalid",
            "run_id": "attempt-invalid",
            "task_id": payload["task_id"],
            "stage": "adapter",
            "failure_class": "environment_failure",
            "owner_class": "environment",
            "retryable": False,
            "retry_count": 0,
            "terminal": True,
            "message": "synthetic invalid arm",
            "evidence_refs": [],
            "score_treatment": "invalid_run_exclude_from_capability_score",
            "invalid_run": True,
        }
    ]
    payload["manifest_hash"] = manifest_hash(payload)
    bundle_file.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_bundle_manifest(run_root)
    write_run_seal(run_root)

    result = run_tool(run_root, tmp_path / "review", tmp_path / "mapping")

    assert result.returncode == 1
    assert "invalid_run arm cannot enter outcome review" in result.stderr


def test_rejects_mixed_identity_and_fabricated_attempt_after_trace_reseal(
    tmp_path: Path, completed_run_template: Path
) -> None:
    identity_root = copy_completed_run(completed_run_template, tmp_path / "mixed")
    bundle_file = next(identity_root.rglob("bundle.json"))
    ledger = bundle_trace(bundle_file, "event_ledger.jsonl")
    events = [json.loads(line) for line in ledger.read_text(encoding="utf-8").splitlines()]
    for event in events:
        event["approval_id"] = "approval-mixed"
    ledger.write_text(
        "".join(json.dumps(event, sort_keys=True) + "\n" for event in events),
        encoding="utf-8",
    )
    mutate_json(
        bundle_trace(bundle_file, "adapter_summary.json"),
        lambda summary: summary.__setitem__("approval_id", "approval-mixed"),
    )
    reseal_bundle(identity_root, bundle_file)
    write_run_seal(identity_root)
    identity_result = run_tool(
        identity_root,
        tmp_path / "mixed-review",
        tmp_path / "mixed-mapping",
    )

    attempt_root = copy_completed_run(completed_run_template, tmp_path / "attempt")
    bundle_file = next(attempt_root.rglob("bundle.json"))
    ledger = bundle_trace(bundle_file, "event_ledger.jsonl")
    events = [json.loads(line) for line in ledger.read_text(encoding="utf-8").splitlines()]
    for event in events:
        event["attempt_id"] = "fabricated-attempt"
    ledger.write_text(
        "".join(json.dumps(event, sort_keys=True) + "\n" for event in events),
        encoding="utf-8",
    )
    mutate_json(
        bundle_trace(bundle_file, "adapter_summary.json"),
        lambda summary: summary.__setitem__("attempt_id", "fabricated-attempt"),
    )
    reseal_bundle(attempt_root, bundle_file)
    write_run_seal(attempt_root)
    attempt_result = run_tool(
        attempt_root,
        tmp_path / "attempt-review",
        tmp_path / "attempt-mapping",
    )

    assert identity_result.returncode == 1
    assert "identity drifts across arms" in identity_result.stderr
    assert attempt_result.returncode == 1
    assert "attempt ID disagrees with the frozen schedule" in attempt_result.stderr


def test_rejects_governance_and_bundle_manifest_tamper(
    tmp_path: Path, completed_run_template: Path
) -> None:
    governance_root = copy_completed_run(completed_run_template, tmp_path / "governance")
    governance = governance_root / "governance_manifest.sha256"
    corrupt_first_digest(governance)
    write_run_seal(governance_root)
    governance_result = run_tool(
        governance_root,
        tmp_path / "governance-review",
        tmp_path / "governance-mapping",
    )

    bundle_root = copy_completed_run(completed_run_template, tmp_path / "bundles")
    bundle_manifest = bundle_root / "bundle_manifest.sha256"
    corrupt_first_digest(bundle_manifest)
    write_run_seal(bundle_root)
    bundle_result = run_tool(
        bundle_root,
        tmp_path / "bundle-review",
        tmp_path / "bundle-mapping",
    )

    assert governance_result.returncode == 1
    assert "governance manifest does not match" in governance_result.stderr
    assert bundle_result.returncode == 1
    assert "bundle manifest does not exactly match" in bundle_result.stderr


def test_rejects_raw_trace_non_object_and_quiet_ledger_undercount(
    tmp_path: Path, completed_run_template: Path
) -> None:
    non_object_root = copy_completed_run(completed_run_template, tmp_path / "non-object")
    bundle_file = next(non_object_root.rglob("bundle.json"))
    raw_trace = bundle_trace(bundle_file, "codex_events.jsonl")
    raw_trace.write_text("[]\n", encoding="utf-8")
    reseal_bundle(non_object_root, bundle_file)
    write_run_seal(non_object_root)
    non_object_result = run_tool(
        non_object_root,
        tmp_path / "non-object-review",
        tmp_path / "non-object-mapping",
    )

    undercount_root = copy_completed_run(completed_run_template, tmp_path / "undercount")
    bundle_file = next(undercount_root.rglob("bundle.json"))
    raw_trace = bundle_trace(bundle_file, "codex_events.jsonl")
    raw_trace.write_text(
        raw_trace.read_text(encoding="utf-8")
        + json.dumps(
            {
                "type": "item.completed",
                "item": {
                    "type": "file_change",
                    "id": "change-not-ledgered",
                    "path": "README.md",
                },
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    reseal_bundle(undercount_root, bundle_file)
    write_run_seal(undercount_root)
    undercount_result = run_tool(
        undercount_root,
        tmp_path / "undercount-review",
        tmp_path / "undercount-mapping",
    )

    assert non_object_result.returncode == 1
    assert "raw Codex event at line 1 must be an object" in non_object_result.stderr
    assert undercount_result.returncode == 1
    assert "event ledger does not match events derived" in undercount_result.stderr
