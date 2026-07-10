from __future__ import annotations

import subprocess
import sys
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
