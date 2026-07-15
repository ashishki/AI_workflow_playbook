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


def passing_verify_argv() -> str:
    return json.dumps(["{python}", "-c", "raise SystemExit(0)"])


def test_lean_core_is_minimal_and_valid(tmp_path: Path) -> None:
    target = tmp_path / "lean-core"
    result = run_init(
        target,
        "--mode",
        "lean-core",
        "--project-name",
        "Lean Smoke",
        "--operational-pain",
        "Agents need a small verified project scaffold.",
        "--current-workaround",
        "Manual copying of playbook files.",
        "--first-proof-metric",
        "Generated project verifier exits zero.",
        "--verify-argv",
        passing_verify_argv(),
    )

    assert result.returncode == 0, result.stderr
    assert (target / "AGENTS.md").exists()
    assert (target / "docs/tasks.md").exists()
    assert (target / "docs/CONTRACT_LITE.md").exists()
    assert (target / "docs/PROBLEM_FIT.md").exists()
    assert (target / "tools/verify_project.py").exists()
    assert (target / "tools/resolve_release_readiness.py").exists()
    assert (target / ".playbook/project_verification.json").exists()
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
    verification = subprocess.run(
        [sys.executable, "tools/verify_project.py", "--root", "."],
        cwd=target,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert verification.returncode == 0, verification.stderr
    result_path = target / ".playbook-artifacts/project_verification.json"
    assert result_path.exists()
    verification_result = json.loads(result_path.read_text(encoding="utf-8"))
    assert verification_result["required_failures"] == 0
    assert {check["id"] for check in verification_result["checks"]} == {
        "playbook_contract",
        "project_verification",
    }
    release = subprocess.run(
        [sys.executable, "tools/resolve_release_readiness.py", "--root", "."],
        cwd=target,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert release.returncode == 1
    assert "READINESS_RELEASE_GIT_REQUIRED" in release.stderr


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
        "--operational-pain",
        "Hook installation must preserve user settings.",
        "--current-workaround",
        "Manual hook copying.",
        "--first-proof-metric",
        "Hook smoke test passes.",
        "--verify-argv",
        passing_verify_argv(),
        "--install-claude-hooks",
    )

    assert result.returncode == 0, result.stderr
    settings = json.loads(settings_path.read_text(encoding="utf-8"))
    assert settings["permissions"]["allow"] == ["Bash(git status:*)"]
    assert "hooks" in settings
    assert (target / "hooks/guard_files.sh").exists()
    assert (target / "hooks/guard_files.sh").stat().st_mode & 0o111
    assert "hook smoke test passed" in result.stdout
    workflow = (target / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert "permissions:\n  contents: read" in workflow
    assert "actions/checkout@9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0" in workflow
    assert "persist-credentials: false" in workflow
    assert "python -m pip install pytest" not in workflow


def test_initializer_rejects_unknown_readiness_values(tmp_path: Path) -> None:
    target = tmp_path / "bad-readiness"
    result = run_init(
        target,
        "--mode",
        "lean-core",
        "--project-name",
        "Bad Readiness",
        "--operational-pain",
        "unknown",
        "--current-workaround",
        "Manual process.",
        "--first-proof-metric",
        "Verifier exits zero.",
        "--verify-argv",
        passing_verify_argv(),
    )

    assert result.returncode == 2
    assert "--operational-pain is required" in result.stderr


def test_initializer_rejects_legacy_shell_verify_command_without_argv(tmp_path: Path) -> None:
    target = tmp_path / "legacy-shell"
    result = run_init(
        target,
        "--mode",
        "lean-core",
        "--project-name",
        "Legacy Shell",
        "--operational-pain",
        "Project verification must be executable without shell parsing.",
        "--current-workaround",
        "Manual command review.",
        "--first-proof-metric",
        "Initializer rejects unsafe verification input.",
        "--verify-command",
        "pytest -q",
    )

    assert result.returncode == 2
    assert "--verify-command is not enforced" in result.stderr


def test_generated_verifier_fails_when_project_verification_fails(tmp_path: Path) -> None:
    target = tmp_path / "failing-project"
    result = run_init(
        target,
        "--mode",
        "lean-core",
        "--project-name",
        "Failing Project",
        "--operational-pain",
        "Project tests must be part of completion evidence.",
        "--current-workaround",
        "Manual pytest inspection.",
        "--first-proof-metric",
        "Generated verifier exits non-zero when pytest fails.",
        "--verify-argv",
        json.dumps([sys.executable, "-m", "pytest", "-q"]),
    )
    assert result.returncode == 0, result.stderr
    tests_dir = target / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_fail.py").write_text("def test_fails():\n    assert False\n", encoding="utf-8")

    verification = subprocess.run(
        [sys.executable, "tools/verify_project.py", "--root", "."],
        cwd=target,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert verification.returncode == 1
    result_path = target / ".playbook-artifacts/project_verification.json"
    verification_result = json.loads(result_path.read_text(encoding="utf-8"))
    assert verification_result["required_failures"] == 1
    project_check = next(check for check in verification_result["checks"] if check["id"] == "project_verification")
    assert project_check["passed"] is False
    assert project_check["exit_code"] == 1


def test_generated_verifier_rejects_recursive_project_verification(tmp_path: Path) -> None:
    target = tmp_path / "recursive-project"
    result = run_init(
        target,
        "--mode",
        "lean-core",
        "--project-name",
        "Recursive Project",
        "--operational-pain",
        "Self-referential verification must fail closed.",
        "--current-workaround",
        "Manual config inspection.",
        "--first-proof-metric",
        "Generated verifier rejects recursive checks.",
        "--verify-argv",
        json.dumps(["{python}", "tools/verify_project.py", "--root", "."]),
    )
    assert result.returncode == 0, result.stderr

    verification = subprocess.run(
        [sys.executable, "tools/verify_project.py", "--root", "."],
        cwd=target,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert verification.returncode == 2
    assert "must not call tools/verify_project.py recursively" in verification.stderr


def test_required_platform_skip_fails_project_verification(tmp_path: Path) -> None:
    target = tmp_path / "platform-skip"
    result = run_init(
        target,
        "--mode",
        "lean-core",
        "--project-name",
        "Platform Skip",
        "--operational-pain",
        "Required checks must not disappear on unsupported platforms.",
        "--current-workaround",
        "Manual platform review.",
        "--first-proof-metric",
        "Generated verifier blocks skipped required checks.",
        "--verify-argv",
        passing_verify_argv(),
    )
    assert result.returncode == 0, result.stderr
    config_path = target / ".playbook/project_verification.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    config["checks"][1]["platforms"] = ["definitely-not-this-platform"]
    config_path.write_text(json.dumps(config, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    verification = subprocess.run(
        [sys.executable, "tools/verify_project.py", "--root", "."],
        cwd=target,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert verification.returncode == 1
    result_payload = json.loads((target / ".playbook-artifacts/project_verification.json").read_text(encoding="utf-8"))
    skipped = next(check for check in result_payload["checks"] if check["id"] == "project_verification")
    assert skipped["skipped"] is True
    assert skipped["passed"] is False
    assert result_payload["required_failures"] == 1
