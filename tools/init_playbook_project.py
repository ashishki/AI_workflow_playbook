#!/usr/bin/env python3
"""Initialize a downstream repository with a proportional playbook kit."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
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
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    checks = [
        [
            sys.executable,
            "tools/playbook_validate.py",
            "--root",
            str(root),
            "--check",
            "tasks",
            "--check",
            "placeholders",
        ],
    ]
    failures = 0
    for cmd in checks:
        result = subprocess.run(cmd, cwd=root)
        if result.returncode:
            failures += 1
    return 1 if failures else 0


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
        PLAYBOOK_ROOT / "tools/playbook_validate.py",
        target / "tools/playbook_validate.py",
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
    parser.add_argument("--verify-command", default="python3 tools/verify_project.py --root .")
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
    readiness_errors = validate_required_readiness(args)
    if readiness_errors:
        for error in readiness_errors:
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
        "VERIFY_COMMAND": args.verify_command,
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
