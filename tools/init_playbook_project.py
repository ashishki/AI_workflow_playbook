#!/usr/bin/env python3
"""Initialize a downstream repository with a proportional playbook kit."""

from __future__ import annotations

import argparse
import datetime as dt
import os
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path


PLAYBOOK_ROOT = Path(__file__).resolve().parents[1]


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
    return rendered


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


def copy_prompt_files(destination: Path, force: bool, dry_run: bool, result: CopyResult) -> None:
    source = PLAYBOOK_ROOT / "prompts"
    for item in sorted(source.glob("*.md")):
        copy_binary_or_text_file(item, destination / item.name, force=force, dry_run=dry_run, result=result)


def chmod_executable(path: Path) -> None:
    if not path.exists():
        return
    mode = path.stat().st_mode
    path.chmod(mode | 0o111)


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
        PLAYBOOK_ROOT / "schemas/cost_telemetry_entry.schema.json",
        target / "schemas/cost_telemetry_entry.schema.json",
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
    copy_prompt_files(target / "docs/prompts", args.force, args.dry_run, result)
    copy_tree("prompts/audit", target / "docs/audit", args.force, args.dry_run, result)
    copy_tree("hooks", target / "hooks", args.force, args.dry_run, result)
    if not args.dry_run:
        for hook in (target / "hooks").glob("*.sh"):
            chmod_executable(hook)


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
    parser.add_argument("--mode", choices=("lean", "standard", "strict"), default="standard")
    parser.add_argument("--project-name", default="")
    parser.add_argument("--verify-command", default="TODO: add project verification command")
    parser.add_argument("--with-cost-architecture", action="store_true")
    parser.add_argument("--with-router-eval", action="store_true")
    parser.add_argument("--with-cost-adapter", action="store_true")
    parser.add_argument("--external-skill", action="append", default=[], help="Create trust record for this external skill.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing files.")
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    target = Path(args.target).resolve()
    project_name = args.project_name or target.name
    today = dt.date.today().isoformat()
    replacements = {
        "PROJECT_NAME": project_name,
        "MODE": args.mode,
        "DATE": today,
        "VERIFY_COMMAND": args.verify_command,
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

    add_common_files(args, target, replacements, result)
    if args.mode == "lean":
        add_lean_files(args, target, replacements, result)
    else:
        add_standard_files(args, target, replacements, result)
        if args.mode == "strict":
            args.with_cost_architecture = True
    add_optional_files(args, target, replacements, result)

    print(f"init_playbook_project: target={target}")
    print(f"init_playbook_project: mode={args.mode}")
    for path in result.created:
        print(f"  create: {path}")
    for path in result.skipped:
        print(f"  skip existing: {path}")
    print(f"init_playbook_project: created={len(result.created)} skipped={len(result.skipped)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
