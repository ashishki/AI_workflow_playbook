from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_integrity_check_fails_missing_context_ref(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "tasks.md").write_text(
        """# Tasks

Context-Refs:
  - `docs/missing.md`
""",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(ROOT / "tools/integrity_check.py"), "--root", str(tmp_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 1
    assert "Missing Context-Refs path" in result.stdout


def test_cost_rollup_strict_valid_input(tmp_path: Path) -> None:
    telemetry = tmp_path / "telemetry.jsonl"
    output = tmp_path / "rollup.md"
    entry = {
        "timestamp": "2026-01-01T00:00:00Z",
        "project": "test",
        "run_id": "run-1",
        "source": "unit",
        "provider": "unknown",
        "model": "unknown",
        "agent_role": "tester",
        "environment": "test",
        "input_tokens": 2,
        "output_tokens": 3,
        "total_tokens": 5,
        "estimated_cost_usd": 0.01,
    }
    telemetry.write_text(json.dumps(entry) + "\n", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools/cost_rollup.py"),
            "--input",
            str(telemetry),
            "--output",
            str(output),
            "--strict",
            "--require-file",
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "AI Cost Rollup" in output.read_text(encoding="utf-8")


def test_skill_security_gate_no_skills_ok(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools/skill_security_gate.py"),
            "--root",
            str(tmp_path),
            "--discover-agent-skills",
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 0
    assert "0 skills" in result.stdout
