from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def run_init(target: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(ROOT / "tools/init_playbook_project.py"), str(target), *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def test_lean_core_is_minimal_and_valid(tmp_path: Path) -> None:
    target = tmp_path / "lean-core"
    result = run_init(target, "--mode", "lean-core", "--project-name", "Lean Smoke")

    assert result.returncode == 0, result.stderr
    assert (target / "AGENTS.md").exists()
    assert (target / "docs/tasks.md").exists()
    assert (target / "docs/CONTRACT_LITE.md").exists()
    assert (target / "docs/PROBLEM_FIT.md").exists()
    assert (target / "tools/verify_project.py").exists()
    assert not (target / "PLAYBOOK.md").exists()
    assert not (target / "docs/ARCHITECTURE.md").exists()
    assert not (target / "docs/EVIDENCE_INDEX.md").exists()
    assert not (target / "docs/ai_cost_architecture.md").exists()

    validation = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools/playbook_validate.py"),
            "--root",
            str(target),
            "--check",
            "tasks",
            "--check",
            "placeholders",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert validation.returncode == 0, validation.stderr


def test_install_claude_hooks_merges_settings(tmp_path: Path) -> None:
    target = tmp_path / "standard"
    settings_path = target / ".claude/settings.json"
    settings_path.parent.mkdir(parents=True)
    settings_path.write_text(
        json.dumps({"permissions": {"allow": ["Bash(git status:*)"]}}, indent=2),
        encoding="utf-8",
    )

    result = run_init(
        target,
        "--mode",
        "standard",
        "--project-name",
        "Hook Smoke",
        "--install-claude-hooks",
    )

    assert result.returncode == 0, result.stderr
    settings = json.loads(settings_path.read_text(encoding="utf-8"))
    assert settings["permissions"]["allow"] == ["Bash(git status:*)"]
    assert "hooks" in settings
    assert (target / "hooks/guard_files.sh").exists()
    assert (target / "hooks/guard_files.sh").stat().st_mode & 0o111
    assert "hook smoke test passed" in result.stdout
