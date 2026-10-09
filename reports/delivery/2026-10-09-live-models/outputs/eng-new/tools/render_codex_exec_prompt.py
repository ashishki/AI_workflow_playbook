#!/usr/bin/env python3
"""Render task-scoped prompts for isolated codex exec subagents."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

TOOL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_ROOT / "tools"))

try:
    import playbook_validate
except ImportError as exc:  # pragma: no cover
    raise SystemExit(f"failed to import playbook_validate: {exc}") from exc

try:
    import feature_design_lib
except ImportError as exc:  # pragma: no cover
    raise SystemExit(f"failed to import feature_design_lib: {exc}") from exc


ROLE_PROMPTS = {
    "meta_review": [
        "docs/audit/PROMPT_0_META.md",
        "prompts/audit/PROMPT_0_META.md",
    ],
    "arch_review": [
        "docs/audit/PROMPT_1_ARCH.md",
        "prompts/audit/PROMPT_1_ARCH.md",
    ],
    "code_review": [
        "docs/audit/PROMPT_2_CODE.md",
        "prompts/audit/PROMPT_2_CODE.md",
    ],
    "test_critic": [
        "docs/audit/PROMPT_TEST_CRITIC.md",
        "prompts/audit/PROMPT_TEST_CRITIC.md",
    ],
    "privacy_review": [
        "docs/audit/PROMPT_PRIVACY_REVIEW.md",
        "prompts/audit/PROMPT_PRIVACY_REVIEW.md",
    ],
    "fix_from_review": [
        "docs/prompts/PROMPT_FIX_FROM_REVIEW.md",
        "prompts/PROMPT_FIX_FROM_REVIEW.md",
    ],
    "doc_sync": [
        "docs/prompts/PROMPT_DOC_SYNC_AFTER_TASK.md",
        "prompts/PROMPT_DOC_SYNC_AFTER_TASK.md",
    ],
    "consolidated_review": [
        "docs/audit/PROMPT_3_CONSOLIDATED.md",
        "prompts/audit/PROMPT_3_CONSOLIDATED.md",
    ],
    "product_design_review": [],
    "program_design_review": [],
    "slice_review": [],
    "maintainability_review": [],
    "design_author": [],
}

READ_ONLY_ROLES = {
    "meta_review",
    "arch_review",
    "code_review",
    "test_critic",
    "privacy_review",
    "consolidated_review",
    "product_design_review",
    "program_design_review",
    "slice_review",
    "maintainability_review",
}

DESIGN_REVIEW_ROLES = {
    "product_design_review",
    "program_design_review",
    "slice_review",
    "maintainability_review",
}

DESIGN_AUTHOR_ROLES = {"design_author"}

ROLE_MARKERS = {
    "test_critic": "TEST_CRITIC_RESULT: NO_FINDING | ADVISORY | STOP_SHIP",
    "privacy_review": "PRIVACY_REVIEW_RESULT: PASS | ADVISORY | STOP_SHIP",
    "fix_from_review": "FIX_RESULT: APPLIED | BLOCKED",
    "doc_sync": "DOC_SYNC_RESULT: UPDATED | BLOCKED",
    "product_design_review": "PRODUCT_DESIGN_REVIEW: PASS | ADVISORY | STOP_SHIP",
    "program_design_review": "PROGRAM_DESIGN_REVIEW: PASS | ADVISORY | STOP_SHIP",
    "slice_review": "SLICE_REVIEW: PASS | ADVISORY | STOP_SHIP",
    "maintainability_review": "MAINTAINABILITY_REVIEW: PASS | ADVISORY | STOP_SHIP",
    "design_author": "DESIGN_AUTHOR_RESULT: DRAFTED | BLOCKED",
}


def read_text_if_exists(path: Path, limit: int | None = None) -> str:
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8", errors="replace")
    if limit is not None and len(text) > limit:
        return text[:limit] + "\n\n[truncated by render_codex_exec_prompt.py]\n"
    return text


def find_prompt(root: Path, role: str) -> tuple[str, str]:
    for rel in ROLE_PROMPTS[role]:
        for base in (root, TOOL_ROOT):
            path = base / rel
            if path.exists():
                return str(path.relative_to(base)), path.read_text(encoding="utf-8")
    return "", ""


def task_section(tasks_path: Path, task_id: str) -> str:
    lines = tasks_path.read_text(encoding="utf-8", errors="replace").splitlines()
    start: int | None = None
    for index, line in enumerate(lines):
        if line.startswith(f"### {task_id}:"):
            start = index
            break
    if start is None:
        raise SystemExit(f"task {task_id} not found in {tasks_path}")
    end = len(lines)
    for index in range(start + 1, len(lines)):
        if lines[index].startswith("### "):
            end = index
            break
    return "\n".join(lines[start:end]).strip()


def load_task(root: Path, task_id: str) -> tuple[dict[str, Any], str]:
    tasks_path = root / "docs" / "tasks.md"
    if not tasks_path.exists():
        raise SystemExit(f"missing task file: {tasks_path}")
    for block in playbook_validate.parse_task_blocks(tasks_path):
        if block.task_id == task_id:
            return block.to_record(), task_section(tasks_path, task_id)
    raise SystemExit(f"task {task_id} not found in {tasks_path}")


def default_output_path(task_id: str, role: str) -> str:
    suffix = {
        "meta_review": "meta_review",
        "arch_review": "arch_review",
        "code_review": "code_review",
        "test_critic": "test_critic",
        "privacy_review": "privacy_review",
        "fix_from_review": "fix_result",
        "doc_sync": "doc_sync_result",
        "consolidated_review": "consolidated_review",
        "product_design_review": "product_design_review",
        "program_design_review": "program_design_review",
        "slice_review": "slice_review",
        "maintainability_review": "maintainability_review",
        "design_author": "design_author",
    }[role]
    return f"docs/verification/{task_id}_{suffix}.md"


def marker_prefix(role: str) -> str | None:
    marker = ROLE_MARKERS.get(role)
    return marker.split(":", 1)[0] if marker else None


def parse_required_marker(role: str, text: str) -> dict[str, str]:
    prefix = marker_prefix(role)
    if prefix is None:
        return {"role": role, "verdict": "NOT_REQUIRED"}
    for line in text.splitlines():
        if not line.startswith(prefix + ":"):
            continue
        verdict = line.split(":", 1)[1].strip().split()[0]
        allowed = [part.strip() for part in ROLE_MARKERS[role].split(":", 1)[1].split("|")]
        if verdict not in allowed:
            raise ValueError(f"invalid marker verdict {verdict}; expected one of {', '.join(allowed)}")
        return {"role": role, "marker": prefix, "verdict": verdict}
    raise ValueError(f"missing required marker {prefix}:")


def review_report_block(root: Path, reports: list[str]) -> str:
    if not reports:
        return "No review reports supplied."
    parts = []
    for report in reports:
        path = root / report
        content = read_text_if_exists(path, limit=12000)
        if content:
            parts.append(f"### {report}\n\n{content.strip()}")
        else:
            parts.append(f"### {report}\n\n[missing or unreadable]")
    return "\n\n".join(parts)


def design_context_block(root: Path, task_record: dict[str, Any]) -> str:
    parts: list[str] = []
    for ref in task_record.get("design_refs", []):
        path, raw = playbook_validate.design_registry_path(root, ref)
        if path is None or not path.exists():
            parts.append(f"### {raw}\n\n[missing or unsafe design ref]")
            continue
        findings, design = feature_design_lib.validate_design_file(root, path)
        if findings:
            rendered_findings = "\n".join(
                f"- {finding.severity}: {finding.check_id}: {finding.message}" for finding in findings
            )
            parts.append(f"### {raw} Validation Findings\n\n{rendered_findings}")
        if design is None:
            continue
        feature_id = str(design.get("feature_id", path.stem.replace(".design", "")))
        markdown = root / "docs/design" / f"{feature_id}.md"
        brief_path = feature_design_lib.safe_repo_path(root, str(design.get("brief_ref", "")))
        parts.extend(
            [
                f"### Design Registry: {raw}",
                "",
                "```json",
                json.dumps(design, indent=2, sort_keys=True),
                "```",
                "",
                f"### Feature Design Markdown: docs/design/{feature_id}.md",
                "",
                "```markdown",
                read_text_if_exists(markdown, limit=20000) or "[feature design markdown not present]",
                "```",
                "",
                f"### Brief Ref: {design.get('brief_ref')}",
                "",
                "```markdown",
                read_text_if_exists(brief_path, limit=8000) if brief_path else "[unsafe or missing brief ref]",
                "```",
            ]
        )
        slice_id = str(task_record.get("slice_id", "")).strip()
        if slice_id:
            slice_item = feature_design_lib.find_slice(design, slice_id)
            parts.extend(
                [
                    f"### Current Slice: {slice_id}",
                    "",
                    "```json",
                    json.dumps(slice_item or {"missing_slice": slice_id}, indent=2, sort_keys=True),
                    "```",
                ]
            )
    return "\n\n".join(parts) if parts else "[No Design-Refs declared on this task.]"


def feature_id_from_task_or_args(task_record: dict[str, Any], requested: str) -> str:
    if requested:
        return requested
    for ref in task_record.get("design_refs", []):
        raw = str(ref).strip().strip("`")
        name = Path(raw).name
        if name.endswith(".design.json"):
            return name.removesuffix(".design.json")
    return "F01"


def read_planning_decision(root: Path, task_id: str, explicit_path: str) -> str:
    path = Path(explicit_path) if explicit_path else root / ".playbook-artifacts/planning" / task_id / "planning_decision.json"
    if not path.is_absolute():
        path = root / path
    return read_text_if_exists(path, limit=16000) or "[planning decision not present]"


def repository_inventory_block(root: Path, feature_id: str) -> str:
    candidates = [
        root / ".playbook-artifacts/planning" / feature_id / "repository_inventory.json",
        root / ".playbook/repository_inventory.json",
    ]
    for path in candidates:
        text = read_text_if_exists(path, limit=16000)
        if text:
            return text
    return "[repository inventory not present]"


def existing_patterns_block(root: Path, task_record: dict[str, Any]) -> str:
    refs = ["docs/ARCHITECTURE.md", "templates/ARCHITECTURE.md", "templates/AGENTS.md"]
    parts: list[str] = []
    for ref in refs + list(task_record.get("context_refs", [])):
        raw = str(ref).strip().strip("`")
        path = feature_design_lib.safe_repo_path(root, raw)
        if path is None or not path.exists():
            continue
        parts.append(f"### {raw}\n\n{read_text_if_exists(path, limit=10000)}")
    return "\n\n".join(parts) if parts else "[no existing pattern refs found]"


def output_contract(role: str) -> str:
    marker = ROLE_MARKERS.get(role)
    if not marker:
        return "Use the role prompt's existing output contract."
    return (
        f"The first non-empty line of the report must start with:\n\n`{marker}`\n\n"
        "Use `STOP_SHIP` only for blockers grounded in the provided task, design, "
        "slice, contracts, or evidence. Advisory findings must not be presented as completion authority."
    )


def command_hint(args: argparse.Namespace, output_path: str) -> str:
    sandbox = "read-only" if args.role in READ_ONLY_ROLES else "workspace-write"
    reviews = " ".join(f"--review {path}" for path in args.review)
    approval = (
        f" --human-approval-ref {args.human_approval_ref}"
        if args.human_approval_ref
        else ""
    )
    feature = f" --feature-id {args.feature_id}" if args.feature_id else ""
    planning = f" --planning-decision {args.planning_decision}" if args.planning_decision else ""
    return (
        "codex exec \\\n"
        f"  --cd {json.dumps(str(args.root))} \\\n"
        f"  --sandbox {sandbox} \\\n"
        f"  --output-last-message {json.dumps(output_path)} \\\n"
        "  \"$(python3 tools/render_codex_exec_prompt.py "
        f"--root . --task {args.task} --role {args.role}"
        + (f" {reviews}" if reviews else "")
        + approval
        + feature
        + planning
        + f" --output-path {output_path})\""
    )


def render(args: argparse.Namespace) -> str:
    root = args.root.resolve()
    task_record, raw_task = load_task(root, args.task)
    output_path = args.output_path or default_output_path(args.task, args.role)
    prompt_ref, prompt_text = find_prompt(root, args.role)
    review_policy = read_text_if_exists(root / "docs" / "REVIEW_POLICY.md", limit=16000)
    delivery_model = read_text_if_exists(root / ".playbook" / "delivery_execution_model.json", limit=12000)
    verification = read_text_if_exists(root / ".playbook" / "project_verification.json", limit=12000)
    current_state = read_text_if_exists(root / "docs" / "CODEX_PROMPT.md", limit=16000)
    evidence_index = read_text_if_exists(root / "docs" / "EVIDENCE_INDEX.md", limit=12000)
    review_reports = review_report_block(root, args.review)

    access_rule = (
        "READ-ONLY: do not modify files. Your final answer is the report."
        if args.role in READ_ONLY_ROLES
        else "WRITE-SCOPED: modify only files allowed by this role and task scope."
    )
    if args.role in DESIGN_AUTHOR_ROLES:
        feature_id = feature_id_from_task_or_args(task_record, args.feature_id)
        template = read_text_if_exists(root / "templates/FEATURE_DESIGN.md", limit=24000)
        planning_decision = read_planning_decision(root, args.task, args.planning_decision)
        current_registry = read_text_if_exists(root / "docs/design" / f"{feature_id}.design.json", limit=20000)
        current_markdown = read_text_if_exists(root / "docs/design" / f"{feature_id}.md", limit=24000)
        brief = read_text_if_exists(root / "docs/PROJECT_BRIEF.md", limit=12000)
        return f"""# Codex Design Author Prompt

Project root: {root}
Task: {args.task}
Feature: {feature_id}
Role: design_author
Expected report path: {output_path}

## Access Rule

WRITE-SCOPED: modify only:

- `docs/design/{feature_id}.md`
- `docs/design/{feature_id}.design.json`
- `docs/tasks.md`

Do not write application code. Do not edit migrations, CI, security policy,
production dependencies, release approval artifacts, or runtime code. Do not
approve the design. Do not set `status=approved`, `approved_by`, `approved_at`,
approval hashes, or release/completion authority.

## Suggested Invocation

```bash
{command_hint(args, output_path)}
```

## Output Contract

{output_contract(args.role)}

Allowed final design statuses after your draft work:

- `draft`
- `review_required`

## Approved Brief

```markdown
{brief.strip() if brief else "[docs/PROJECT_BRIEF.md not present]"}
```

## Canonical Task Section

```markdown
{raw_task}
```

## Machine Task Record

```json
{json.dumps(task_record, indent=2, sort_keys=True)}
```

## Planning Decision

```json
{planning_decision.strip()}
```

## Repository Inventory

```json
{repository_inventory_block(root, feature_id).strip()}
```

## Existing Architecture Refs And Patterns

```markdown
{existing_patterns_block(root, task_record).strip()}
```

## Feature Design Template

```markdown
{template.strip() if template else "[templates/FEATURE_DESIGN.md not present]"}
```

## Current Feature Design Registry

```json
{current_registry.strip() if current_registry else "[registry not present]"}
```

## Current Feature Design Markdown

```markdown
{current_markdown.strip() if current_markdown else "[markdown not present]"}
```

## Required Design Content

Fill or update:

- Product Outcome
- Existing System Context
- System Impact
- File Tree Diff
- Key Types
- Interfaces And Signatures
- Control Flow
- Invariants
- Failure Paths
- Patterns To Reuse
- Patterns Not To Introduce
- Maintainability Risks
- Verification Strategy
- Vertical Slices

Vertical slices must be vertical user-visible increments, not horizontal layer
batches.
"""
    if args.role in DESIGN_REVIEW_ROLES:
        return f"""# Codex Exec Design Review Prompt

Project root: {root}
Task: {args.task}
Role: {args.role}
Expected report path: {output_path}
Prompt source: inline renderer fallback

## Access Rule

{access_rule}

Do not modify files. Do not approve the design. Do not approve completion or release.

## Suggested Invocation

```bash
{command_hint(args, output_path)}
```

## Output Contract

{output_contract(args.role)}

## Review Focus

- Product fit and observable outcome for product design review.
- Reuse of existing patterns, module boundaries, signatures, invariants, failure paths, migration, and rollback for program design review.
- Slice verticality, allowed/forbidden files, acceptance criteria, verification, and review checkpoint for slice review.
- Coupling, duplicate domain logic, new dependencies, interface drift, hidden global state, file-tree drift, and disproportionate diff risk for maintainability review.

## Canonical Task Section

```markdown
{raw_task}
```

## Machine Task Record

```json
{json.dumps(task_record, indent=2, sort_keys=True)}
```

## Feature Design Context

{design_context_block(root, task_record)}

## Review Policy

```markdown
{review_policy.strip() if review_policy else "[docs/REVIEW_POLICY.md not present]"}
```
"""

    return f"""# Codex Exec Subagent Prompt

Project root: {root}
Task: {args.task}
Role: {args.role}
Expected report path: {output_path}
Prompt source: {prompt_ref or "inline renderer fallback"}

## Access Rule

{access_rule}

Do not commit. Do not push. Do not approve completion. Human approval remains
external when the delivery model or review policy requires it.

## Suggested Invocation

```bash
{command_hint(args, output_path)}
```

## Role Instructions

{prompt_text.strip() if prompt_text else "[No role prompt found. Use the access rule and task scope only.]"}

## Output Contract

{output_contract(args.role)}

## Canonical Task Section

```markdown
{raw_task}
```

## Machine Task Record

```json
{json.dumps(task_record, indent=2, sort_keys=True)}
```

## Review Policy

```markdown
{review_policy.strip() if review_policy else "[docs/REVIEW_POLICY.md not present]"}
```

## Delivery Execution Model

```json
{delivery_model.strip() if delivery_model else "[.playbook/delivery_execution_model.json not present]"}
```

## Project Verification Config

```json
{verification.strip() if verification else "[.playbook/project_verification.json not present]"}
```

## Existing Review Reports

{review_reports}

## Evidence Index

```markdown
{evidence_index.strip() if evidence_index else "[docs/EVIDENCE_INDEX.md not present]"}
```

## Current Session State

```markdown
{current_state.strip() if current_state else "[docs/CODEX_PROMPT.md not present]"}
```
"""


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--task", default="")
    parser.add_argument("--role", required=True, choices=sorted(ROLE_PROMPTS))
    parser.add_argument("--review", action="append", default=[])
    parser.add_argument("--human-approval-ref", default="")
    parser.add_argument("--feature-id", default="")
    parser.add_argument("--planning-decision", default="")
    parser.add_argument("--output-path", default="")
    parser.add_argument("--parse-report", type=Path, default=None)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    if args.parse_report is not None:
        try:
            parsed = parse_required_marker(
                args.role,
                args.parse_report.read_text(encoding="utf-8", errors="replace"),
            )
        except (OSError, ValueError) as exc:
            print(f"render_codex_exec_prompt: {exc}", file=sys.stderr)
            return 1
        print(json.dumps(parsed, indent=2, sort_keys=True))
        return 0
    if not args.task:
        print("render_codex_exec_prompt: --task is required unless --parse-report is used", file=sys.stderr)
        return 2
    sys.stdout.write(render(args))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
