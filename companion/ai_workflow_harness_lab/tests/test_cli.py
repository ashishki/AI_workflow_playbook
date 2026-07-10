from __future__ import annotations

import subprocess
import sys
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SUITE = ROOT / "companion/ai_workflow_harness_lab/suites/playbook_core_v1"
PYTHONPATH = str(ROOT / "companion/ai_workflow_harness_lab/src")


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


def test_scripted_run_verify_and_compare(tmp_path: Path) -> None:
    baseline = tmp_path / "baseline"
    playbook = tmp_path / "playbook"
    comparison = tmp_path / "comparison"

    assert run_cli("run", "--suite", str(SUITE), "--condition", "baseline", "--adapter", "scripted", "--trials", "1", "--output", str(baseline)).returncode == 0
    assert run_cli("run", "--suite", str(SUITE), "--condition", "playbook", "--adapter", "scripted", "--trials", "1", "--output", str(playbook)).returncode == 0
    bundle = playbook / "fake_test_success/trial-0/bundle.json"
    verify = run_cli("verify-bundle", str(bundle))
    assert verify.returncode == 0, verify.stderr
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
