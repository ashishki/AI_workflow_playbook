from __future__ import annotations

import subprocess
import sys
import json
from pathlib import Path
from types import SimpleNamespace

from ai_workflow_harness_lab.adapters.command import CommandAdapter
from ai_workflow_harness_lab.evidence import manifest_hash
from ai_workflow_harness_lab.receipts import sha256_file


ROOT = Path(__file__).resolve().parents[3]
SUITE = ROOT / "companion/ai_workflow_harness_lab/suites/playbook_core_v1"
PYTHONPATH = str(ROOT / "companion/ai_workflow_harness_lab/src")


def sha256(path: Path) -> str:
    return sha256_file(path)


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "ai_workflow_harness_lab.cli", *args],
        cwd=ROOT,
        env={"PYTHONPATH": PYTHONPATH},
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def test_validate_suite() -> None:
    result = run_cli("validate-suite", str(SUITE))

    assert result.returncode == 0, result.stderr
    assert '"tasks": 5' in result.stdout


def test_run_filters_repeatable_task_ids(tmp_path: Path) -> None:
    output = tmp_path / "filtered"
    result = run_cli(
        "run",
        "--suite",
        str(SUITE),
        "--condition",
        "playbook",
        "--adapter",
        "scripted",
        "--task-id",
        "fake_test_success",
        "--task-id",
        "immutable_contract",
        "--output",
        str(output),
    )

    assert result.returncode == 0, result.stderr
    index = json.loads((output / "run_index.json").read_text(encoding="utf-8"))
    assert {Path(bundle).parts[0] for bundle in index["bundles"]} == {
        "fake_test_success",
        "immutable_contract",
    }
    assert index["task_count"] == 2
    assert index["trial_count"] == 2
    assert not (output / "prompt_injection").exists()


def test_run_uses_logical_trial_start_and_rejects_negative_start(tmp_path: Path) -> None:
    output = tmp_path / "trial-start"
    result = run_cli(
        "run",
        "--suite",
        str(SUITE),
        "--condition",
        "playbook",
        "--adapter",
        "scripted",
        "--task-id",
        "fake_test_success",
        "--trial-start",
        "4",
        "--trials",
        "2",
        "--output",
        str(output),
    )

    assert result.returncode == 0, result.stderr
    assert (output / "fake_test_success/trial-4/bundle.json").is_file()
    assert (output / "fake_test_success/trial-5/bundle.json").is_file()
    assert not (output / "fake_test_success/trial-0").exists()

    rejected = run_cli(
        "run",
        "--suite",
        str(SUITE),
        "--condition",
        "playbook",
        "--adapter",
        "scripted",
        "--trial-start",
        "-1",
        "--output",
        str(tmp_path / "negative"),
    )
    assert rejected.returncode == 2
    assert "must be nonnegative" in rejected.stderr


def test_run_append_accumulates_index_and_retains_evidence(tmp_path: Path) -> None:
    output = tmp_path / "append"
    common = (
        "run",
        "--suite",
        str(SUITE),
        "--condition",
        "playbook",
        "--adapter",
        "scripted",
        "--task-id",
        "fake_test_success",
        "--output",
        str(output),
    )
    first = run_cli(*common)
    assert first.returncode == 0, first.stderr
    first_bundle = output / "fake_test_success/trial-0/bundle.json"
    original_bundle = first_bundle.read_bytes()
    original_index = (output / "run_index.json").read_bytes()

    without_append = run_cli(*common, "--trial-start", "1")
    assert without_append.returncode == 1
    assert "use --append" in without_append.stderr
    assert first_bundle.read_bytes() == original_bundle
    assert (output / "run_index.json").read_bytes() == original_index
    assert not (output / "fake_test_success/trial-1").exists()

    appended = run_cli(*common, "--append", "--trial-start", "1")
    assert appended.returncode == 0, appended.stderr
    index = json.loads((output / "run_index.json").read_text(encoding="utf-8"))
    assert index["bundles"] == [
        "fake_test_success/trial-0/bundle.json",
        "fake_test_success/trial-1/bundle.json",
    ]
    assert len(index["bundles"]) == len(set(index["bundles"]))
    assert index["task_count"] == 1
    assert index["trial_count"] == 2
    assert first_bundle.read_bytes() == original_bundle


def test_run_append_collision_never_overwrites_trial_evidence(tmp_path: Path) -> None:
    output = tmp_path / "collision"
    args = (
        "run",
        "--suite",
        str(SUITE),
        "--condition",
        "playbook",
        "--adapter",
        "scripted",
        "--task-id",
        "fake_test_success",
        "--trial-start",
        "2",
        "--output",
        str(output),
    )
    first = run_cli(*args)
    assert first.returncode == 0, first.stderr
    trial_dir = output / "fake_test_success/trial-2"
    before = {
        str(path.relative_to(trial_dir)): path.read_bytes()
        for path in trial_dir.rglob("*")
        if path.is_file()
    }
    index_before = (output / "run_index.json").read_bytes()

    collision = run_cli(*args, "--append")

    assert collision.returncode == 1
    assert "trial directory already exists" in collision.stderr
    after = {
        str(path.relative_to(trial_dir)): path.read_bytes()
        for path in trial_dir.rglob("*")
        if path.is_file()
    }
    assert after == before
    assert (output / "run_index.json").read_bytes() == index_before


def test_run_rejects_unknown_task_id_before_creating_output(tmp_path: Path) -> None:
    output = tmp_path / "unknown-task"
    result = run_cli(
        "run",
        "--suite",
        str(SUITE),
        "--condition",
        "playbook",
        "--adapter",
        "scripted",
        "--task-id",
        "does_not_exist",
        "--output",
        str(output),
    )

    assert result.returncode == 1
    assert "unknown task ID(s): does_not_exist" in result.stderr
    assert "available task IDs:" in result.stderr
    assert not output.exists()


def test_scripted_run_verify_and_compare(tmp_path: Path) -> None:
    baseline = tmp_path / "baseline"
    playbook = tmp_path / "playbook"
    comparison = tmp_path / "comparison"

    assert run_cli("run", "--suite", str(SUITE), "--condition", "baseline", "--adapter", "scripted", "--trials", "1", "--output", str(baseline)).returncode == 0
    assert run_cli("run", "--suite", str(SUITE), "--condition", "playbook", "--adapter", "scripted", "--trials", "1", "--output", str(playbook)).returncode == 0
    bundle = playbook / "fake_test_success/trial-0/bundle.json"
    verify = run_cli("verify-bundle", str(bundle))
    assert verify.returncode == 0, verify.stderr
    bundle_payload = json.loads(bundle.read_text(encoding="utf-8"))
    assert bundle_payload["harness_eval_unit_ref"]["path"] == "harness_eval_unit.json"
    eval_unit = json.loads((bundle.parent / "harness_eval_unit.json").read_text(encoding="utf-8"))
    assert eval_unit["compatibility_fingerprint"]
    compare = run_cli("compare", "--baseline", str(baseline), "--candidate", str(playbook), "--output", str(comparison))
    assert compare.returncode == 0, compare.stderr
    assert (comparison / "comparison_report.json").exists()


def test_command_adapter_smoke(tmp_path: Path) -> None:
    output = tmp_path / "command"
    template = f"{sys.executable} -c \"from pathlib import Path; Path('{{workspace}}/cmd_adapter.txt').write_text('ok')\""
    result = run_cli(
        "run",
        "--suite",
        str(SUITE),
        "--condition",
        "playbook",
        "--adapter",
        "command",
        "--command-template",
        template,
        "--trials",
        "1",
        "--output",
        str(output),
    )

    assert result.returncode == 0, result.stderr
    assert (output / "fake_test_success/trial-0/bundle.json").exists()
    receipt = json.loads(
        (
            output
            / "fake_test_success/trial-0/adapter/receipts/command/receipt.json"
        ).read_text(encoding="utf-8")
    )
    environment = receipt["environment_summary"]
    assert environment["start_monotonic_ns"] <= environment["end_monotonic_ns"]


def test_command_adapter_does_not_source_login_profile(
    tmp_path: Path, monkeypatch
) -> None:
    home = tmp_path / "home"
    home.mkdir()
    marker = tmp_path / "profile-was-sourced"
    (home / ".profile").write_text(
        f"/usr/bin/touch {marker}\n", encoding="utf-8"
    )
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    prompt = tmp_path / "prompt.md"
    prompt.write_text("task\n", encoding="utf-8")
    output = tmp_path / "output"
    monkeypatch.setenv("HOME", str(home))

    result = CommandAdapter(":").run(
        SimpleNamespace(task_id="profile-probe"),
        "playbook",
        0,
        workspace,
        prompt,
        output,
    )

    receipt = json.loads(
        (output / "receipts/command/receipt.json").read_text(encoding="utf-8")
    )
    assert result.exit_code == 0
    assert receipt["command_argv"] == ["/bin/sh", "-c", ":"]
    assert not marker.exists()


def test_command_adapter_bundles_wrapper_trace_files(tmp_path: Path) -> None:
    output = tmp_path / "command-traces"
    template = (
        f"{sys.executable} -c \"from pathlib import Path; "
        "root=Path('{output_dir}'); "
        "[(root/name).write_text('trace') for name in "
        "('codex_events.jsonl','final_message.txt','event_ledger.jsonl','adapter_summary.json')]\""
    )

    result = run_cli(
        "run",
        "--suite",
        str(SUITE),
        "--condition",
        "playbook",
        "--adapter",
        "command",
        "--command-template",
        template,
        "--task-id",
        "fake_test_success",
        "--output",
        str(output),
    )

    assert result.returncode == 0, result.stderr
    bundle = json.loads(
        (output / "fake_test_success/trial-0/bundle.json").read_text(encoding="utf-8")
    )
    trace_paths = {artifact["path"] for artifact in bundle["trace_refs"]}
    assert any(path.endswith("codex_events.jsonl") for path in trace_paths)
    assert any(path.endswith("final_message.txt") for path in trace_paths)
    assert any(path.endswith("event_ledger.jsonl") for path in trace_paths)
    assert any(path.endswith("adapter_summary.json") for path in trace_paths)


def test_command_adapter_failure_can_fail_pipeline(tmp_path: Path) -> None:
    output = tmp_path / "command-fails"
    template = f"{sys.executable} -c \"raise SystemExit(7)\""
    result = run_cli(
        "run",
        "--suite",
        str(SUITE),
        "--condition",
        "playbook",
        "--adapter",
        "command",
        "--command-template",
        template,
        "--trials",
        "1",
        "--output",
        str(output),
        "--fail-on-invalid-run",
    )

    assert result.returncode == 1
    bundle = json.loads((output / "fake_test_success/trial-0/bundle.json").read_text(encoding="utf-8"))
    assert any(record["failure_class"] == "tool_adapter_failure" for record in bundle["failure_records"])
    assert any(record["invalid_run"] for record in bundle["failure_records"])
    receipt = json.loads((output / "fake_test_success/trial-0/adapter/receipts/command/receipt.json").read_text(encoding="utf-8"))
    assert receipt["exit_code"] == 7
    assert receipt["repo_commit_before"] == "not_inspected"
    assert receipt["repo_commit_after"] == "not_inspected"
    assert receipt["environment_summary"]["git_inspection"] is False


def test_command_adapter_timeout_is_invalid_run(tmp_path: Path) -> None:
    output = tmp_path / "command-timeout"
    template = f"{sys.executable} -c \"import time; time.sleep(1)\""
    result = run_cli(
        "run",
        "--suite",
        str(SUITE),
        "--condition",
        "playbook",
        "--adapter",
        "command",
        "--command-template",
        template,
        "--adapter-timeout",
        "0.1",
        "--trials",
        "1",
        "--output",
        str(output),
        "--fail-on-invalid-run",
    )

    assert result.returncode == 1
    bundle = json.loads((output / "fake_test_success/trial-0/bundle.json").read_text(encoding="utf-8"))
    assert any(record["failure_class"] == "timeout" for record in bundle["failure_records"])


def test_compare_validates_bundles_and_hard_gates(tmp_path: Path) -> None:
    baseline = tmp_path / "baseline"
    playbook = tmp_path / "playbook"
    comparison = tmp_path / "comparison"

    assert run_cli("run", "--suite", str(SUITE), "--condition", "baseline", "--adapter", "scripted", "--trials", "1", "--output", str(baseline)).returncode == 0
    assert run_cli("run", "--suite", str(SUITE), "--condition", "playbook", "--adapter", "scripted", "--trials", "1", "--output", str(playbook)).returncode == 0
    result = run_cli(
        "compare",
        "--baseline",
        str(baseline),
        "--candidate",
        str(playbook),
        "--output",
        str(comparison),
        "--fail-on-hard-gate",
        "--max-policy-violations",
        "0",
        "--max-false-success-rate",
        "0",
    )

    assert result.returncode == 0, result.stderr
    report = json.loads((comparison / "comparison_report.json").read_text(encoding="utf-8"))
    assert report["hard_gates"]["single_run_stability_warning"] is True
    assert report["candidate"]["evidence_correctness"] == 1.0


def test_compare_hard_gate_failure_returns_nonzero(tmp_path: Path) -> None:
    baseline = tmp_path / "baseline"
    comparison = tmp_path / "comparison"

    assert run_cli("run", "--suite", str(SUITE), "--condition", "baseline", "--adapter", "scripted", "--trials", "1", "--output", str(baseline)).returncode == 0
    result = run_cli(
        "compare",
        "--baseline",
        str(baseline),
        "--candidate",
        str(baseline),
        "--output",
        str(comparison),
        "--fail-on-hard-gate",
        "--max-policy-violations",
        "0",
        "--max-false-success-rate",
        "0",
    )

    assert result.returncode == 1


def test_compare_rejects_invalid_bundle_with_flag(tmp_path: Path) -> None:
    baseline = tmp_path / "baseline"
    playbook = tmp_path / "playbook"
    comparison = tmp_path / "comparison"

    assert run_cli("run", "--suite", str(SUITE), "--condition", "baseline", "--adapter", "scripted", "--trials", "1", "--output", str(baseline)).returncode == 0
    assert run_cli("run", "--suite", str(SUITE), "--condition", "playbook", "--adapter", "scripted", "--trials", "1", "--output", str(playbook)).returncode == 0
    stdout_path = playbook / "fake_test_success/trial-0/verification/receipts/required-verification/stdout.txt"
    stdout_path.write_text("tampered\n", encoding="utf-8")
    result = run_cli(
        "compare",
        "--baseline",
        str(baseline),
        "--candidate",
        str(playbook),
        "--output",
        str(comparison),
        "--fail-on-invalid-run",
    )

    assert result.returncode == 1
    report = json.loads((comparison / "comparison_report.json").read_text(encoding="utf-8"))
    assert report["candidate"]["invalid_runs"] >= 1


def test_compare_rejects_harness_eval_unit_mismatch(tmp_path: Path) -> None:
    baseline = tmp_path / "baseline"
    playbook = tmp_path / "playbook"
    comparison = tmp_path / "comparison"

    assert run_cli("run", "--suite", str(SUITE), "--condition", "baseline", "--adapter", "scripted", "--task-id", "fake_test_success", "--output", str(baseline)).returncode == 0
    assert run_cli("run", "--suite", str(SUITE), "--condition", "playbook", "--adapter", "scripted", "--task-id", "fake_test_success", "--output", str(playbook)).returncode == 0
    eval_unit_path = playbook / "fake_test_success/trial-0/harness_eval_unit.json"
    eval_unit = json.loads(eval_unit_path.read_text(encoding="utf-8"))
    eval_unit["compatibility_fingerprint"] = "0" * 64
    eval_unit_path.write_text(json.dumps(eval_unit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    bundle_path = playbook / "fake_test_success/trial-0/bundle.json"
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    bundle["harness_eval_unit_ref"]["sha256"] = sha256(eval_unit_path)
    bundle["manifest_hash"] = manifest_hash(bundle)
    bundle_path.write_text(json.dumps(bundle, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    result = run_cli(
        "compare",
        "--baseline",
        str(baseline),
        "--candidate",
        str(playbook),
        "--output",
        str(comparison),
        "--fail-on-invalid-run",
    )

    assert result.returncode == 1
    report = json.loads((comparison / "comparison_report.json").read_text(encoding="utf-8"))
    assert "harness_eval_unit compatibility differs for fake_test_success trial 0" in report["compatibility_errors"]


def test_verify_bundle_rejects_path_escape(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    assert run_cli("run", "--suite", str(SUITE), "--condition", "playbook", "--adapter", "scripted", "--trials", "1", "--output", str(run_dir)).returncode == 0
    bundle_path = run_dir / "fake_test_success/trial-0/bundle.json"
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    bundle["command_receipts"][0]["path"] = "../../secret.json"
    bundle_path.write_text(json.dumps(bundle, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    result = run_cli("verify-bundle", str(bundle_path))

    assert result.returncode == 1
    assert "path escape forbidden" in result.stderr
