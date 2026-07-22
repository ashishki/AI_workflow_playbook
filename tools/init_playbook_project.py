#!/usr/bin/env python3
"""Initialize a downstream repository with a proportional playbook kit."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


PLAYBOOK_ROOT = Path(__file__).resolve().parents[1]
UNKNOWN_PLACEHOLDER_RE = re.compile(r"(?<!\$)\{\{[^{}\n]+\}\}")
NOT_READY_VALUES = {"", "unknown", "tbd", "todo"}


@dataclass
class CopyResult:
    created: list[Path]
    skipped: list[Path]


def read_template(relative_path: str) -> str:
    return (PLAYBOOK_ROOT / relative_path).read_text(encoding="utf-8")


def render(text: str, replacements: dict[str, str]) -> str:
    rendered = text
    for key, value in replacements.items():
        rendered = rendered.replace("{{" + key + "}}", value)
    rendered = UNKNOWN_PLACEHOLDER_RE.sub(scaffold_placeholder, rendered)
    return rendered


def scaffold_placeholder(match: re.Match[str]) -> str:
    name = match.group(0).strip("{} ")
    return f"not_applicable - scaffold placeholder {name}; replace before treating this section as authoritative"


def parse_verify_argv(raw_values: list[str]) -> tuple[list[list[str]], list[str]]:
    parsed: list[list[str]] = []
    errors: list[str] = []
    for index, raw in enumerate(raw_values, 1):
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as exc:
            errors.append(f"--verify-argv #{index} must be a JSON array of strings: {exc}")
            continue
        if not isinstance(value, list) or not value or not all(isinstance(part, str) and part for part in value):
            errors.append(f"--verify-argv #{index} must be a non-empty JSON array of non-empty strings")
            continue
        parsed.append(value)
    return parsed, errors


def display_verify_commands(argvs: list[list[str]]) -> str:
    return "\n".join(" ".join(shlex.quote(part) for part in argv) for argv in argvs)


def project_verification_config(verify_argvs: list[list[str]]) -> str:
    checks: list[dict[str, object]] = [
        {
            "id": "playbook_contract",
            "argv": [
                "{python}",
                "tools/playbook_validate.py",
                "--root",
                ".",
                "--check",
                "tasks",
                "--check",
                "placeholders",
                "--check",
                "readiness",
                "--check",
                "delivery",
            ],
            "required": True,
            "expected_exit_code": 0,
            "timeout_seconds": 60,
        }
    ]
    for index, argv in enumerate(verify_argvs, 1):
        checks.append(
            {
                "id": "project_verification" if index == 1 else f"project_verification_{index}",
                "argv": argv,
                "required": True,
                "expected_exit_code": 0,
                "timeout_seconds": 600,
            }
        )
    payload = {
        "schema_version": "playbook.project_verification.v1",
        "checks": checks,
    }
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def readiness_state_config(mode: str) -> str:
    payload = {
        "schema_version": "playbook.readiness_state.v1",
        "mode": mode,
        "state": "scaffold",
        "required_decision_policy": "mode_profile_risk_triggered",
        "unresolved_decision_marker": "scaffold placeholder",
        "implementation_ready_requires_no_scaffold_placeholders": True,
        "release_ready_requires_current_verification": True,
        "notes": [
            "Initializer output is a scaffold until project-specific decisions are resolved.",
            "Do not mark implementation_ready, release_candidate, or release_ready while generated scaffold placeholders remain active.",
            "Release readiness is resolved after tools/verify_project.py by tools/resolve_release_readiness.py.",
        ],
    }
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def delivery_execution_model_config() -> str:
    payload = {
        "schema_version": "playbook.delivery_execution_model.v1",
        "delivery_profile": "solo_verified",
        "orchestrator": {"kind": "human", "authority": "select_task_and_accept_completion"},
        "implementer": {"kind": "active_codex_session", "may_write_code": True},
        "reviewer": {
            "kind": "human_or_independent_agent_by_risk",
            "required_when": ["medium_or_higher_risk", "auth_secrets_billing", "destructive_or_external_write"],
        },
        "verifier": {
            "kind": "deterministic_project_verifier",
            "binding_id": "project_verifier",
            "argv": ["{python}", "tools/verify_project.py", "--root", "."],
            "command": "python tools/verify_project.py --root .",
        },
        "completion_authority": {"kind": "human", "requires": ["project_verification_passed", "risk_review_satisfied"]},
        "cli_bindings": {
            "codex_direct": "active_session_runs_shell_directly",
            "external_codex_exec": "ci_harness_or_non_codex_orchestrator_only",
        },
        "permission_profile": "repo_local_default",
        "budget": {"model_call_budget": "project_defined", "spend_budget": "project_defined"},
        "independent_review_triggers": [
            "meaningful_implementation_change",
            "security_or_privacy_boundary",
            "production_release_claim",
        ],
    }
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def readiness_value(value: str) -> str:
    return value.strip()


def validate_required_readiness(args: argparse.Namespace) -> list[str]:
    required = {
        "operational_pain": "--operational-pain",
        "current_workaround": "--current-workaround",
        "first_proof_metric": "--first-proof-metric",
    }
    errors: list[str] = []
    for attr, flag in required.items():
        value = readiness_value(str(getattr(args, attr, "")))
        if value.lower() in NOT_READY_VALUES:
            errors.append(f"{flag} is required and cannot be unknown/TBD/TODO/empty")
    return errors


def should_skip(path: Path, force: bool) -> bool:
    return path.exists() and not force


def write_text_file(path: Path, content: str, force: bool, dry_run: bool, result: CopyResult) -> None:
    if should_skip(path, force):
        result.skipped.append(path)
        return
    result.created.append(path)
    if dry_run:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def copy_file(
    source_relative: str,
    destination: Path,
    replacements: dict[str, str],
    force: bool,
    dry_run: bool,
    result: CopyResult,
) -> None:
    content = render(read_template(source_relative), replacements)
    write_text_file(destination, content, force=force, dry_run=dry_run, result=result)


def copy_binary_or_text_file(source: Path, destination: Path, force: bool, dry_run: bool, result: CopyResult) -> None:
    if should_skip(destination, force):
        result.skipped.append(destination)
        return
    result.created.append(destination)
    if dry_run:
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def copy_tree(source_relative: str, destination: Path, force: bool, dry_run: bool, result: CopyResult) -> None:
    source = PLAYBOOK_ROOT / source_relative
    if not source.exists():
        return
    for item in sorted(source.rglob("*")):
        if item.is_dir():
            continue
        if "__pycache__" in item.parts:
            continue
        relative = item.relative_to(source)
        copy_binary_or_text_file(item, destination / relative, force=force, dry_run=dry_run, result=result)


def copy_rendered_tree(
    source_relative: str,
    destination: Path,
    replacements: dict[str, str],
    force: bool,
    dry_run: bool,
    result: CopyResult,
) -> None:
    source = PLAYBOOK_ROOT / source_relative
    if not source.exists():
        return
    for item in sorted(source.rglob("*")):
        if item.is_dir() or "__pycache__" in item.parts:
            continue
        relative = item.relative_to(source)
        if item.suffix.lower() in {".md", ".json", ".yml", ".yaml", ".toml", ".txt"}:
            copy_file(str(item.relative_to(PLAYBOOK_ROOT)), destination / relative, replacements, force, dry_run, result)
        else:
            copy_binary_or_text_file(item, destination / relative, force=force, dry_run=dry_run, result=result)


def copy_prompt_files(
    destination: Path,
    replacements: dict[str, str],
    force: bool,
    dry_run: bool,
    result: CopyResult,
) -> None:
    source = PLAYBOOK_ROOT / "prompts"
    for item in sorted(source.glob("*.md")):
        copy_file(str(item.relative_to(PLAYBOOK_ROOT)), destination / item.name, replacements, force, dry_run, result)


def chmod_executable(path: Path) -> None:
    if not path.exists():
        return
    mode = path.stat().st_mode
    path.chmod(mode | 0o111)


def verify_project_script() -> str:
    return """#!/usr/bin/env python3
\"\"\"Generated project verification entrypoint.\"\"\"

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SHELL_NAMES = {"sh", "bash", "zsh", "fish", "cmd", "cmd.exe", "powershell", "powershell.exe", "pwsh", "pwsh.exe"}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_commit(root: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 and result.stdout.strip() else "not-a-git-repository"


def artifact_ref(path: Path, root: Path) -> dict[str, str]:
    return {
        "path": str(path.relative_to(root)),
        "sha256": sha256_file(path),
    }


def safe_relative_path(root: Path, raw: str) -> Path | None:
    path = Path(raw)
    if path.is_absolute() or ".." in path.parts:
        return None
    resolved = (root / path).resolve()
    try:
        resolved.relative_to(root)
    except ValueError:
        return None
    return resolved


def load_config(root: Path, explicit_path: str | None) -> tuple[dict[str, Any] | None, list[str]]:
    path = Path(explicit_path) if explicit_path else root / ".playbook/project_verification.json"
    if not path.is_absolute():
        path = root / path
    if not path.is_file():
        return None, [f"project verification config missing: {path}"]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, [f"project verification config is invalid JSON: {exc}"]
    if not isinstance(data, dict):
        return None, ["project verification config must be a JSON object"]
    return data, []


def materialize_argv(argv: list[str], root: Path) -> list[str]:
    replacements = {
        "{python}": sys.executable,
        "{root}": str(root),
    }
    rendered: list[str] = []
    for value in argv:
        for placeholder, replacement in replacements.items():
            value = value.replace(placeholder, replacement)
        rendered.append(value)
    return rendered


def has_self_reference(argv: list[str]) -> bool:
    for value in argv:
        normalized = value.replace("\\\\", "/")
        if normalized == "verify_project.py" or normalized.endswith("/verify_project.py") or "tools/verify_project.py" in normalized:
            return True
    return False


def validate_check(raw: Any, root: Path) -> tuple[dict[str, Any] | None, list[str]]:
    errors: list[str] = []
    if not isinstance(raw, dict):
        return None, ["check must be an object"]
    check_id = raw.get("id")
    argv = raw.get("argv")
    if not isinstance(check_id, str) or not check_id:
        errors.append("check.id must be a non-empty string")
    elif not all(char.isalnum() or char in "_.-" for char in check_id):
        errors.append(f"check {check_id} id may contain only letters, numbers, underscore, dot, or hyphen")
    if not isinstance(argv, list) or not argv or not all(isinstance(part, str) and part for part in argv):
        errors.append(f"check {check_id or '<unknown>'} argv must be a non-empty array of strings")
        argv = []
    argv = list(argv)
    if has_self_reference(argv):
        errors.append(f"check {check_id or '<unknown>'} must not call tools/verify_project.py recursively")
    shell_name = Path(argv[0]).name.lower() if argv else ""
    if shell_name in SHELL_NAMES and raw.get("allow_shell") is not True:
        errors.append(f"check {check_id or '<unknown>'} uses shell execution without allow_shell=true")
    cwd_raw = raw.get("cwd", ".")
    if not isinstance(cwd_raw, str) or safe_relative_path(root, cwd_raw) is None:
        errors.append(f"check {check_id or '<unknown>'} cwd must be relative and stay inside project root")
    expected_exit = raw.get("expected_exit_code", 0)
    if not isinstance(expected_exit, int):
        errors.append(f"check {check_id or '<unknown>'} expected_exit_code must be an integer")
    required = raw.get("required", True)
    if not isinstance(required, bool):
        errors.append(f"check {check_id or '<unknown>'} required must be boolean")
    timeout = raw.get("timeout_seconds")
    if timeout is not None and (not isinstance(timeout, (int, float)) or timeout <= 0):
        errors.append(f"check {check_id or '<unknown>'} timeout_seconds must be positive")
    env = raw.get("env", {})
    if not isinstance(env, dict) or not all(isinstance(key, str) and isinstance(value, str) for key, value in env.items()):
        errors.append(f"check {check_id or '<unknown>'} env must map strings to strings")
    platforms = raw.get("platforms")
    if platforms is not None and (not isinstance(platforms, list) or not all(isinstance(item, str) for item in platforms)):
        errors.append(f"check {check_id or '<unknown>'} platforms must be an array of strings")
    if errors:
        return None, errors
    return {
        "id": check_id,
        "argv": argv,
        "cwd": cwd_raw,
        "required": required,
        "expected_exit_code": expected_exit,
        "timeout_seconds": timeout,
        "env": env,
        "platforms": platforms,
    }, []


def validate_config(config: dict[str, Any], root: Path) -> tuple[list[dict[str, Any]], list[str]]:
    errors: list[str] = []
    if config.get("schema_version") != "playbook.project_verification.v1":
        errors.append("project verification config schema_version must be playbook.project_verification.v1")
    raw_checks = config.get("checks")
    if not isinstance(raw_checks, list) or not raw_checks:
        errors.append("project verification config checks must be a non-empty array")
        return [], errors
    checks: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw in raw_checks:
        check, check_errors = validate_check(raw, root)
        errors.extend(check_errors)
        if check is None:
            continue
        if check["id"] in seen:
            errors.append(f"duplicate check id: {check['id']}")
            continue
        seen.add(check["id"])
        checks.append(check)
    return checks, errors


def write_result(root: Path, checks: list[dict[str, Any]], config_errors: list[str], started_at: str) -> Path:
    artifacts_root = root / ".playbook-artifacts"
    artifacts_root.mkdir(parents=True, exist_ok=True)
    required_failures = sum(
        1
        for check in checks
        if check.get("required") and not check.get("passed", False)
    )
    payload = {
        "schema_version": "playbook.project_verification_result.v1",
        "project_commit": git_commit(root),
        "started_at": started_at,
        "finished_at": utc_now(),
        "platform": platform.platform(),
        "python_executable": sys.executable,
        "checks": checks,
        "configuration_errors": config_errors,
        "required_failures": required_failures,
    }
    result_path = artifacts_root / "project_verification.json"
    result_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\\n", encoding="utf-8")
    return result_path


def run_check(root: Path, artifacts_root: Path, check: dict[str, Any]) -> dict[str, Any]:
    current_platform = sys.platform
    platforms = check.get("platforms")
    argv = materialize_argv(check["argv"], root)
    check_dir = artifacts_root / "project_verification" / check["id"]
    check_dir.mkdir(parents=True, exist_ok=True)
    stdout_path = check_dir / "stdout.txt"
    stderr_path = check_dir / "stderr.txt"
    if platforms and current_platform not in platforms:
        stdout_path.write_text("", encoding="utf-8")
        stderr_path.write_text(f"skipped on platform {current_platform}\\n", encoding="utf-8")
        passed = not check["required"]
        return {
            "id": check["id"],
            "argv": argv,
            "cwd": check["cwd"],
            "required": check["required"],
            "expected_exit_code": check["expected_exit_code"],
            "exit_code": None,
            "passed": passed,
            "skipped": True,
            "stdout_ref": artifact_ref(stdout_path, root),
            "stderr_ref": artifact_ref(stderr_path, root),
        }
    env = os.environ.copy()
    env.update(check.get("env", {}))
    cwd = safe_relative_path(root, check["cwd"])
    assert cwd is not None
    timed_out = False
    try:
        completed = subprocess.run(
            argv,
            cwd=cwd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=check.get("timeout_seconds"),
            check=False,
        )
        exit_code = int(completed.returncode)
        stdout = completed.stdout
        stderr = completed.stderr
    except FileNotFoundError as exc:
        exit_code = 127
        stdout = b""
        stderr = f"verify_project: command not found: {exc.filename}\\n".encode("utf-8")
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        exit_code = 124
        stdout = exc.stdout or b""
        stderr = (exc.stderr or b"") + f"\\nverify_project: timeout after {check.get('timeout_seconds')} seconds\\n".encode("utf-8")
    stdout_path.write_bytes(stdout)
    stderr_path.write_bytes(stderr)
    passed = exit_code == check["expected_exit_code"]
    return {
        "id": check["id"],
        "argv": argv,
        "cwd": check["cwd"],
        "required": check["required"],
        "expected_exit_code": check["expected_exit_code"],
        "exit_code": exit_code,
        "passed": passed,
        "skipped": False,
        "timed_out": timed_out,
        "stdout_ref": artifact_ref(stdout_path, root),
        "stderr_ref": artifact_ref(stderr_path, root),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".")
    parser.add_argument("--config", default=None)
    args = parser.parse_args()
    root = Path(args.root).resolve()
    started_at = utc_now()
    config, load_errors = load_config(root, args.config)
    if config is None:
        result_path = write_result(root, [], load_errors, started_at)
        for error in load_errors:
            print(f"verify_project: {error}", file=sys.stderr)
        print(f"verify_project: result={result_path}")
        return 2
    checks, config_errors = validate_config(config, root)
    if config_errors:
        result_path = write_result(root, [], config_errors, started_at)
        for error in config_errors:
            print(f"verify_project: {error}", file=sys.stderr)
        print(f"verify_project: result={result_path}")
        return 2
    artifacts_root = root / ".playbook-artifacts"
    results = [run_check(root, artifacts_root, check) for check in checks]
    result_path = write_result(root, results, [], started_at)
    required_failures = sum(1 for item in results if item["required"] and not item["passed"])
    for item in results:
        status = "SKIP" if item["skipped"] else "PASS" if item["passed"] else "FAIL"
        print(f"{status}: {item['id']} exit={item['exit_code']}")
    print(f"verify_project: required_failures={required_failures} result={result_path}")
    return 1 if required_failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
"""


def problem_fit_note(replacements: dict[str, str]) -> str:
    return render(
        """# Problem Fit Note

Project: {{PROJECT_NAME}}
Mode: {{MODE}}
Last updated: {{DATE}}

## Operational Pain

{{OPERATIONAL_PAIN}}

## Current Workaround

{{CURRENT_WORKAROUND}}

## First Proof Metric

{{FIRST_PROOF_METRIC}}

## Out-Of-Bounds Claims Before Evidence

- production-ready autonomous system
- replaces accountable human review
- verified success without command evidence

## Verification Command

`{{VERIFY_COMMAND}}`
""",
        replacements,
    )


def add_common_files(args: argparse.Namespace, target: Path, replacements: dict[str, str], result: CopyResult) -> None:
    copy_file("templates/PROJECT_BRIEF.md", target / "docs/PROJECT_BRIEF.md", replacements, args.force, args.dry_run, result)
    copy_file("templates/TASKS.md", target / "docs/tasks.md", replacements, args.force, args.dry_run, result)
    copy_file("docs/project_fit_guide.md", target / "docs/project_fit_guide.md", replacements, args.force, args.dry_run, result)
    copy_file("docs/adoption_modes.md", target / "docs/adoption_modes.md", replacements, args.force, args.dry_run, result)
    copy_file("docs/cost_budget_guardrails.md", target / "docs/cost_budget_guardrails.md", replacements, args.force, args.dry_run, result)
    copy_file("docs/cost_telemetry_protocol.md", target / "docs/cost_telemetry_protocol.md", replacements, args.force, args.dry_run, result)
    copy_file("docs/cache_context_layout.md", target / "docs/cache_context_layout.md", replacements, args.force, args.dry_run, result)
    copy_file("docs/external_skill_security_policy.md", target / "docs/external_skill_security_policy.md", replacements, args.force, args.dry_run, result)
    copy_file("docs/codex_exec_subagent_protocol.md", target / "docs/codex_exec_subagent_protocol.md", replacements, args.force, args.dry_run, result)
    copy_file("templates/COST_BUDGET.md", target / "docs/COST_BUDGET.md", replacements, args.force, args.dry_run, result)
    copy_file("templates/README_INDEX.md", target / "docs/README.md", replacements, args.force, args.dry_run, result)
    copy_binary_or_text_file(
        PLAYBOOK_ROOT / "tools/integrity_check.py",
        target / "tools/integrity_check.py",
        args.force,
        args.dry_run,
        result,
    )
    copy_binary_or_text_file(
        PLAYBOOK_ROOT / "tools/cost_rollup.py",
        target / "tools/cost_rollup.py",
        args.force,
        args.dry_run,
        result,
    )
    copy_binary_or_text_file(
        PLAYBOOK_ROOT / "tools/skill_security_gate.py",
        target / "tools/skill_security_gate.py",
        args.force,
        args.dry_run,
        result,
    )
    copy_binary_or_text_file(
        PLAYBOOK_ROOT / "tools/render_codex_exec_prompt.py",
        target / "tools/render_codex_exec_prompt.py",
        args.force,
        args.dry_run,
        result,
    )
    copy_binary_or_text_file(
        PLAYBOOK_ROOT / "tools/playbook_validate.py",
        target / "tools/playbook_validate.py",
        args.force,
        args.dry_run,
        result,
    )
    copy_binary_or_text_file(
        PLAYBOOK_ROOT / "tools/resolve_release_readiness.py",
        target / "tools/resolve_release_readiness.py",
        args.force,
        args.dry_run,
        result,
    )
    write_text_file(
        target / "tools/verify_project.py",
        verify_project_script(),
        force=args.force,
        dry_run=args.dry_run,
        result=result,
    )
    copy_binary_or_text_file(
        PLAYBOOK_ROOT / "schemas/cost_telemetry_entry.schema.json",
        target / "schemas/cost_telemetry_entry.schema.json",
        args.force,
        args.dry_run,
        result,
    )
    copy_binary_or_text_file(
        PLAYBOOK_ROOT / "schemas/task.schema.json",
        target / "schemas/task.schema.json",
        args.force,
        args.dry_run,
        result,
    )
    copy_binary_or_text_file(
        PLAYBOOK_ROOT / "schemas/project_verification.schema.json",
        target / "schemas/project_verification.schema.json",
        args.force,
        args.dry_run,
        result,
    )
    copy_binary_or_text_file(
        PLAYBOOK_ROOT / "schemas/project_verification_result.schema.json",
        target / "schemas/project_verification_result.schema.json",
        args.force,
        args.dry_run,
        result,
    )
    copy_binary_or_text_file(
        PLAYBOOK_ROOT / "schemas/readiness_state.schema.json",
        target / "schemas/readiness_state.schema.json",
        args.force,
        args.dry_run,
        result,
    )
    copy_binary_or_text_file(
        PLAYBOOK_ROOT / "schemas/delivery_execution_model.schema.json",
        target / "schemas/delivery_execution_model.schema.json",
        args.force,
        args.dry_run,
        result,
    )
    copy_binary_or_text_file(
        PLAYBOOK_ROOT / "schemas/release_readiness_result.schema.json",
        target / "schemas/release_readiness_result.schema.json",
        args.force,
        args.dry_run,
        result,
    )


def add_lean_core_files(args: argparse.Namespace, target: Path, replacements: dict[str, str], result: CopyResult) -> None:
    copy_file("templates/TASKS.md", target / "docs/tasks.md", replacements, args.force, args.dry_run, result)
    copy_file("templates/CONTRACT_LITE.md", target / "docs/CONTRACT_LITE.md", replacements, args.force, args.dry_run, result)
    copy_file("templates/AGENTS.md", target / "AGENTS.md", replacements, args.force, args.dry_run, result)
    write_text_file(
        target / "docs/PROBLEM_FIT.md",
        problem_fit_note(replacements),
        force=args.force,
        dry_run=args.dry_run,
        result=result,
    )
    copy_binary_or_text_file(
        PLAYBOOK_ROOT / "tools/integrity_check.py",
        target / "tools/integrity_check.py",
        args.force,
        args.dry_run,
        result,
    )
    copy_binary_or_text_file(
        PLAYBOOK_ROOT / "tools/playbook_validate.py",
        target / "tools/playbook_validate.py",
        args.force,
        args.dry_run,
        result,
    )
    copy_binary_or_text_file(
        PLAYBOOK_ROOT / "tools/render_codex_exec_prompt.py",
        target / "tools/render_codex_exec_prompt.py",
        args.force,
        args.dry_run,
        result,
    )
    copy_binary_or_text_file(
        PLAYBOOK_ROOT / "tools/resolve_release_readiness.py",
        target / "tools/resolve_release_readiness.py",
        args.force,
        args.dry_run,
        result,
    )
    write_text_file(
        target / "tools/verify_project.py",
        verify_project_script(),
        force=args.force,
        dry_run=args.dry_run,
        result=result,
    )
    copy_binary_or_text_file(
        PLAYBOOK_ROOT / "schemas/task.schema.json",
        target / "schemas/task.schema.json",
        args.force,
        args.dry_run,
        result,
    )
    copy_binary_or_text_file(
        PLAYBOOK_ROOT / "schemas/project_verification.schema.json",
        target / "schemas/project_verification.schema.json",
        args.force,
        args.dry_run,
        result,
    )
    copy_binary_or_text_file(
        PLAYBOOK_ROOT / "schemas/project_verification_result.schema.json",
        target / "schemas/project_verification_result.schema.json",
        args.force,
        args.dry_run,
        result,
    )
    copy_binary_or_text_file(
        PLAYBOOK_ROOT / "schemas/readiness_state.schema.json",
        target / "schemas/readiness_state.schema.json",
        args.force,
        args.dry_run,
        result,
    )
    copy_binary_or_text_file(
        PLAYBOOK_ROOT / "schemas/delivery_execution_model.schema.json",
        target / "schemas/delivery_execution_model.schema.json",
        args.force,
        args.dry_run,
        result,
    )
    copy_binary_or_text_file(
        PLAYBOOK_ROOT / "schemas/release_readiness_result.schema.json",
        target / "schemas/release_readiness_result.schema.json",
        args.force,
        args.dry_run,
        result,
    )


def add_lean_files(args: argparse.Namespace, target: Path, replacements: dict[str, str], result: CopyResult) -> None:
    copy_file("templates/CONTRACT_LITE.md", target / "docs/CONTRACT_LITE.md", replacements, args.force, args.dry_run, result)
    copy_file("templates/LEAN_CODEX_PROMPT.md", target / "AGENTS.md", replacements, args.force, args.dry_run, result)
    copy_file("templates/LEAN_REVIEW_CHECKLIST.md", target / "docs/LEAN_REVIEW_CHECKLIST.md", replacements, args.force, args.dry_run, result)


def add_standard_files(args: argparse.Namespace, target: Path, replacements: dict[str, str], result: CopyResult) -> None:
    copy_file("PLAYBOOK.md", target / "PLAYBOOK.md", replacements, args.force, args.dry_run, result)
    copy_file("templates/ARCHITECTURE.md", target / "docs/ARCHITECTURE.md", replacements, args.force, args.dry_run, result)
    copy_file(
        "templates/IMPLEMENTATION_CONTRACT.md",
        target / "docs/IMPLEMENTATION_CONTRACT.md",
        replacements,
        args.force,
        args.dry_run,
        result,
    )
    copy_file("templates/CODEX_PROMPT.md", target / "docs/CODEX_PROMPT.md", replacements, args.force, args.dry_run, result)
    copy_file("templates/DECISION_LOG.md", target / "docs/DECISION_LOG.md", replacements, args.force, args.dry_run, result)
    copy_file(
        "templates/IMPLEMENTATION_JOURNAL.md",
        target / "docs/IMPLEMENTATION_JOURNAL.md",
        replacements,
        args.force,
        args.dry_run,
        result,
    )
    copy_file("templates/EVIDENCE_INDEX.md", target / "docs/EVIDENCE_INDEX.md", replacements, args.force, args.dry_run, result)
    copy_file("ci/ci.yml", target / ".github/workflows/ci.yml", replacements, args.force, args.dry_run, result)
    copy_prompt_files(target / "docs/prompts", replacements, args.force, args.dry_run, result)
    copy_rendered_tree("prompts/audit", target / "docs/audit", replacements, args.force, args.dry_run, result)
    copy_tree("hooks", target / "hooks", args.force, args.dry_run, result)
    if not args.dry_run:
        for hook in (target / "hooks").glob("*.sh"):
            chmod_executable(hook)


def hook_commands(settings: dict[str, object]) -> list[str]:
    commands: list[str] = []
    hooks = settings.get("hooks", {})
    if not isinstance(hooks, dict):
        return commands
    for entries in hooks.values():
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            for hook in entry.get("hooks", []):
                if isinstance(hook, dict) and isinstance(hook.get("command"), str):
                    commands.append(hook["command"])
    return commands


def merge_settings(existing: dict[str, object], incoming: dict[str, object]) -> dict[str, object]:
    merged = dict(existing)
    existing_hooks = merged.setdefault("hooks", {})
    incoming_hooks = incoming.get("hooks", {})
    if not isinstance(existing_hooks, dict) or not isinstance(incoming_hooks, dict):
        merged["hooks"] = incoming_hooks
        return merged

    for event, incoming_entries in incoming_hooks.items():
        if not isinstance(incoming_entries, list):
            continue
        current_entries = existing_hooks.setdefault(event, [])
        if not isinstance(current_entries, list):
            existing_hooks[event] = incoming_entries
            continue
        seen = {
            json.dumps(entry, sort_keys=True)
            for entry in current_entries
            if isinstance(entry, dict)
        }
        for entry in incoming_entries:
            key = json.dumps(entry, sort_keys=True)
            if key not in seen:
                current_entries.append(entry)
                seen.add(key)
    return merged


def install_claude_hooks(args: argparse.Namespace, target: Path, result: CopyResult) -> tuple[list[str], bool]:
    messages: list[str] = []
    failed = False
    template_path = PLAYBOOK_ROOT / "templates/.claude/settings.json"
    settings = json.loads(template_path.read_text(encoding="utf-8"))
    settings_path = target / ".claude/settings.json"

    if settings_path.exists():
        existing = json.loads(settings_path.read_text(encoding="utf-8"))
        settings = merge_settings(existing, settings)

    write_text_file(
        settings_path,
        json.dumps(settings, indent=2, sort_keys=True) + "\n",
        force=True,
        dry_run=args.dry_run,
        result=result,
    )

    for command in hook_commands(settings):
        if not command.startswith("./hooks/"):
            continue
        hook_name = Path(command).name
        source = PLAYBOOK_ROOT / "hooks" / hook_name
        if source.exists():
            copy_binary_or_text_file(source, target / "hooks" / hook_name, args.force, args.dry_run, result)

    if not args.dry_run:
        for hook in (target / "hooks").glob("*.sh"):
            chmod_executable(hook)
        smoke_hook = target / "hooks" / "guard_files.sh"
        if smoke_hook.exists():
            smoke = subprocess.run(
                [str(smoke_hook)],
                input=json.dumps({"tool_input": {"file_path": "docs/README.md"}}),
                text=True,
                cwd=target,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            if smoke.returncode != 0:
                failed = True
                messages.append(
                    "hook smoke test failed: "
                    + (smoke.stderr.strip() or smoke.stdout.strip() or str(smoke.returncode))
                )
            else:
                messages.append("hook smoke test passed")
        else:
            failed = True
            messages.append("hook smoke test skipped: guard_files.sh not installed")
    return messages, failed


def add_optional_files(args: argparse.Namespace, target: Path, replacements: dict[str, str], result: CopyResult) -> None:
    if args.with_cost_architecture:
        copy_file(
            "templates/COST_ARCHITECTURE.md",
            target / "docs/ai_cost_architecture.md",
            replacements,
            args.force,
            args.dry_run,
            result,
        )
    if args.with_router_eval:
        copy_file("templates/ROUTER_EVAL.md", target / "docs/router_eval.md", replacements, args.force, args.dry_run, result)
    if args.with_cost_adapter:
        copy_tree("templates/cost_adapters", target / "templates/cost_adapters", args.force, args.dry_run, result)
        copy_file(
            "templates/COST_TELEMETRY_ADAPTER.md",
            target / "docs/COST_TELEMETRY_ADAPTER.md",
            replacements,
            args.force,
            args.dry_run,
            result,
        )
    for skill_name in args.external_skill:
        slug = skill_name.strip().lower().replace(" ", "-")
        if not slug:
            continue
        skill_replacements = dict(replacements)
        skill_replacements["SKILL_NAME"] = skill_name
        copy_file(
            "templates/EXTERNAL_SKILL_TRUST_RECORD.md",
            target / f"docs/security/skills/{slug}/TRUST_RECORD.md",
            skill_replacements,
            args.force,
            args.dry_run,
            result,
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Bootstrap a project with AI Workflow Playbook artifacts.")
    parser.add_argument("target", help="Target repository directory.")
    parser.add_argument("--mode", choices=("lean-core", "lean", "standard", "strict"), default="standard")
    parser.add_argument("--project-name", default="")
    parser.add_argument("--answers-file", help="JSON file with initializer readiness answers.")
    parser.add_argument("--operational-pain", default="")
    parser.add_argument("--current-workaround", default="")
    parser.add_argument("--first-proof-metric", default="")
    parser.add_argument(
        "--verify-argv",
        action="append",
        default=[],
        help='Required project verification check as a JSON argv array, e.g. \'["{python}", "-m", "pytest", "-q"]\'. Repeat for multiple checks.',
    )
    parser.add_argument(
        "--verify-command",
        default="",
        help="Deprecated display-only shell command. Use --verify-argv so generated verification can execute without shell parsing.",
    )
    parser.add_argument("--with-cost-architecture", action="store_true")
    parser.add_argument("--with-router-eval", action="store_true")
    parser.add_argument("--with-cost-adapter", action="store_true")
    parser.add_argument("--external-skill", action="append", default=[], help="Create trust record for this external skill.")
    parser.add_argument("--install-claude-hooks", action="store_true", help="Merge .claude/settings.json and install hook scripts.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing files.")
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.answers_file:
        answers = json.loads(Path(args.answers_file).read_text(encoding="utf-8"))
        for attr in ("operational_pain", "current_workaround", "first_proof_metric"):
            if not getattr(args, attr) and attr in answers:
                setattr(args, attr, str(answers[attr]))
    verify_argvs, verify_errors = parse_verify_argv(args.verify_argv)
    if args.verify_command and not verify_argvs:
        verify_errors.append("--verify-command is not enforced; provide --verify-argv with a JSON argv array instead")
    if not verify_argvs:
        verify_errors.append("--verify-argv is required so generated verify_project.py can run actual project verification")
    readiness_errors = validate_required_readiness(args)
    if readiness_errors or verify_errors:
        for error in [*readiness_errors, *verify_errors]:
            print(f"init_playbook_project: {error}", file=sys.stderr)
        return 2
    target = Path(args.target).resolve()
    project_name = args.project_name or target.name
    mode = "lean-core" if args.mode == "lean" else args.mode
    today = dt.date.today().isoformat()
    replacements = {
        "PROJECT_NAME": project_name,
        "MODE": mode,
        "DATE": today,
        "VERIFY_COMMAND": display_verify_commands(verify_argvs),
        "OPERATIONAL_PAIN": readiness_value(args.operational_pain),
        "CURRENT_WORKAROUND": readiness_value(args.current_workaround),
        "FIRST_PROOF_METRIC": readiness_value(args.first_proof_metric),
        "PYTHON_VERSION": "3.12",
        "APP_DIR": "app",
        "APP_MODULE": "app.main",
        "ENV_VAR_1": "TEST_ENV",
        "TEST_VALUE_1": "test",
        "ENV_VAR_2": "TEST_MODE",
        "TEST_VALUE_2": "true",
        "MAX_TOTAL_COST_USD": "25",
        "MAX_RUN_COST_USD": "2",
    }

    result = CopyResult(created=[], skipped=[])
    if not args.dry_run:
        target.mkdir(parents=True, exist_ok=True)

    hook_messages: list[str] = []
    hook_failed = False
    if mode == "lean-core":
        add_lean_core_files(args, target, replacements, result)
    else:
        add_common_files(args, target, replacements, result)
    if args.mode == "lean":
        add_lean_files(args, target, replacements, result)
    elif mode != "lean-core":
        add_standard_files(args, target, replacements, result)
        if mode == "strict":
            args.with_cost_architecture = True
    add_optional_files(args, target, replacements, result)
    write_text_file(
        target / ".playbook/project_verification.json",
        project_verification_config(verify_argvs),
        force=args.force,
        dry_run=args.dry_run,
        result=result,
    )
    write_text_file(
        target / ".playbook/readiness_state.json",
        readiness_state_config(mode),
        force=args.force,
        dry_run=args.dry_run,
        result=result,
    )
    write_text_file(
        target / ".playbook/delivery_execution_model.json",
        delivery_execution_model_config(),
        force=args.force,
        dry_run=args.dry_run,
        result=result,
    )
    if args.install_claude_hooks:
        hook_messages, hook_failed = install_claude_hooks(args, target, result)

    print(f"init_playbook_project: target={target}")
    print(f"init_playbook_project: mode={mode}")
    for path in result.created:
        print(f"  create: {path}")
    for path in result.skipped:
        print(f"  skip existing: {path}")
    for message in hook_messages:
        print(f"  hooks: {message}")
    print(f"init_playbook_project: created={len(result.created)} skipped={len(result.skipped)}")
    return 1 if args.install_claude_hooks and hook_failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
