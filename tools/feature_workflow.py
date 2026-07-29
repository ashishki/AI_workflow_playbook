#!/usr/bin/env python3
"""Thin coordinator for Feature Design and vertical slice workflow."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    import approve_feature_design
    import check_maintainability
    import create_feature_design
    import feature_design_lib
    import feature_review_policy
    import planning_depth
    import playbook_validate
    import render_codex_exec_prompt
    import render_slice_context
except ImportError:  # pragma: no cover
    from tools import (  # type: ignore
        approve_feature_design,
        check_maintainability,
        create_feature_design,
        feature_design_lib,
        feature_review_policy,
        planning_depth,
        playbook_validate,
        render_codex_exec_prompt,
        render_slice_context,
    )


PLAYBOOK_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_SCHEMA = "playbook.feature_workflow.v1"
PLANNING_SCHEMA = "playbook.planning_decision.v1"
SLICE_RESULT_SCHEMA = "playbook.slice_result.v1"


def json_write(path: Path, payload: dict[str, Any]) -> None:
    feature_design_lib.atomic_write_json(path, payload)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def git(root: Path, args: list[str]) -> tuple[int, str]:
    result = subprocess.run(["git", *args], cwd=root, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    return result.returncode, result.stdout.strip()


def git_commit(root: Path) -> str:
    code, stdout = git(root, ["rev-parse", "HEAD"])
    return stdout if code == 0 and stdout else "not-a-git-repository"


def git_status(root: Path) -> list[str]:
    code, stdout = git(root, ["status", "--short"])
    return stdout.splitlines() if code == 0 and stdout else []


def changed_files_since(root: Path, base_commit: str) -> list[str]:
    files: set[str] = set()
    code, stdout = git(root, ["diff", "--name-only", base_commit, "--"])
    if code == 0:
        files.update(line.strip() for line in stdout.splitlines() if line.strip())
    other_code, other_stdout = git(root, ["ls-files", "--others", "--exclude-standard"])
    if other_code == 0:
        files.update(line.strip() for line in other_stdout.splitlines() if line.strip())
    return sorted(files)


def changed_lines_since(root: Path, base_commit: str) -> int:
    code, stdout = git(root, ["diff", "--numstat", base_commit, "--"])
    if code != 0:
        return 0
    total = 0
    for line in stdout.splitlines():
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        for value in parts[:2]:
            if value.isdigit():
                total += int(value)
    return total


def task_block(root: Path, task_id: str) -> playbook_validate.TaskBlock:
    for block in playbook_validate.parse_task_blocks(root / "docs/tasks.md"):
        if block.task_id == task_id:
            return block
    raise SystemExit(f"feature_workflow: task {task_id} not found")


def task_record(root: Path, task_id: str) -> tuple[playbook_validate.TaskBlock, dict[str, Any]]:
    block = task_block(root, task_id)
    return block, block.to_record()


def brief_is_approved(root: Path) -> bool:
    brief = root / "docs/PROJECT_BRIEF.md"
    if not brief.exists():
        return False
    text = brief.read_text(encoding="utf-8", errors="replace").lower()
    return "approved:" in text or "status: approved" in text or "brief approved" in text


def repo_inventory(root: Path, record: dict[str, Any]) -> dict[str, Any]:
    code, stdout = git(root, ["ls-files"])
    files = stdout.splitlines() if code == 0 and stdout else []
    suffixes = {Path(path).suffix for path in files if Path(path).suffix}
    languages = []
    if ".py" in suffixes:
        languages.append("python")
    if suffixes & {".ts", ".tsx", ".js", ".jsx"}:
        languages.append("javascript/typescript")
    if suffixes & {".go"}:
        languages.append("go")
    test_framework = []
    if any(path.startswith("tests/") for path in files) or (root / "pyproject.toml").exists():
        test_framework.append("pytest")
    ci = sorted(path for path in files if path.startswith(".github/workflows/"))
    declared_files = [item.strip("`") for item in record.get("files", [])]
    return {
        "languages": sorted(set(languages)),
        "test_framework": sorted(set(test_framework)),
        "ci": ci,
        "task_declared_files": declared_files,
        "task_tags": record.get("type_tags", []),
        "risk_level": record.get("risk_level", "medium"),
    }


def fact(value: Any, source: str) -> dict[str, Any]:
    return {"value": value, "source": source}


def planning_facts(root: Path, block: playbook_validate.TaskBlock, record: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    tags = {tag.lower() for tag in record.get("type_tags", [])}
    files = [item.strip("`") for item in record.get("files", [])]
    joined = "\n".join(files).lower()
    risk_declared = "risk_level" in block.fields
    facts: dict[str, Any] = {
        "risk_level": fact(record.get("risk_level", "medium"), "declared" if risk_declared else "default"),
        "task_tags": fact(sorted(tags), "declared" if tags else "unknown"),
        "expected_file_count": fact(len(files), "declared" if files else "unknown"),
        "estimated_components": fact(max(1, len({Path(path).parts[0] for path in files if Path(path).parts})), "detected" if files else "unknown"),
        "api_change": fact("api" in tags or "/api/" in joined or joined.startswith("api/") or "routes" in joined, "declared" if "api" in tags else "detected"),
        "persistence_change": fact("persistence" in tags or "migration" in joined or "models" in joined or "repository" in joined, "declared" if "persistence" in tags else "detected"),
        "security_change": fact("security" in tags or "auth" in joined or "permission" in joined, "declared" if "security" in tags else "detected"),
        "migration_required": fact("migration" in tags or "migrations/" in joined, "declared" if "migration" in tags else "detected"),
        "rag_or_agentic": fact(bool(tags & {"rag", "agent", "agentic", "tool", "tool-use"}), "declared" if tags & {"rag", "agent", "agentic", "tool", "tool-use"} else "detected"),
        "user_visible_feature": fact("feature" in tags or bool(record.get("user_touchpoint")), "declared" if "feature" in tags or record.get("user_touchpoint") else "unknown"),
    }
    unknown: list[str] = []
    if not risk_declared:
        unknown.append("risk_level")
    if not files:
        unknown.extend(["expected_file_count", "estimated_components", "api_change", "persistence_change", "security_change"])
    if facts["user_visible_feature"]["source"] == "unknown":
        unknown.append("user_visible_feature")
    return facts, sorted(set(unknown))


def planning_decision_paths(root: Path, task_id: str) -> tuple[Path, Path]:
    base = root / ".playbook-artifacts/planning" / task_id
    return base / "planning_decision.json", base / "planning_decision.md"


def cmd_plan(args: argparse.Namespace) -> int:
    root = args.root.resolve()
    block, record = task_record(root, args.task)
    facts, unknown = planning_facts(root, block, record)
    recommendation = planning_depth.recommend_planning_depth(
        risk_level=str(facts["risk_level"]["value"]),
        task_tags=list(facts["task_tags"]["value"] or []),
        estimated_components=int(facts["estimated_components"]["value"] or 1),
        expected_file_count=int(facts["expected_file_count"]["value"] or 0),
        api_change=bool(facts["api_change"]["value"]),
        persistence_change=bool(facts["persistence_change"]["value"]),
        security_change=bool(facts["security_change"]["value"]),
        rag_or_agentic=bool(facts["rag_or_agentic"]["value"]),
        migration_required=bool(facts["migration_required"]["value"]),
        user_visible_feature=bool(facts["user_visible_feature"]["value"]),
    )
    status = "ready"
    if not brief_is_approved(root) or (unknown and record.get("planning_depth_source") == "legacy_default"):
        status = "needs_input"
    selected = record.get("planning_depth") if record.get("planning_depth_source") == "declared" else None
    decision = {
        "schema_version": PLANNING_SCHEMA,
        "task_id": args.task,
        "status": status,
        "facts": facts,
        "unknown_facts": unknown + ([] if brief_is_approved(root) else ["approved_brief"]),
        "repository_inventory": repo_inventory(root, record),
        "recommended_planning_depth": recommendation["recommended_planning_depth"],
        "reasons": recommendation["reasons"],
        "selected_planning_depth": selected,
        "override_reason": None,
        "override_allowed": recommendation["override_allowed"],
        "override_requires_reason": recommendation["override_requires_reason"],
    }
    json_path, md_path = planning_decision_paths(root, args.task)
    json_write(json_path, decision)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(render_planning_markdown(decision), encoding="utf-8")
    print(f"feature_workflow plan: status={status} recommendation={decision['recommended_planning_depth']}")
    print(f"planning_decision={json_path.relative_to(root)}")
    return 1 if status == "needs_input" else 0


def render_planning_markdown(decision: dict[str, Any]) -> str:
    lines = [
        f"# Planning Decision - {decision['task_id']}",
        "",
        f"Status: {decision['status']}",
        f"Recommended planning depth: {decision['recommended_planning_depth']}",
        f"Selected planning depth: {decision['selected_planning_depth'] or '[human pending]'}",
        "",
        "## Reasons",
        "",
    ]
    lines.extend(f"- {reason}" for reason in decision["reasons"])
    lines.extend(["", "## Unknown Facts", ""])
    lines.extend(f"- {item}" for item in decision["unknown_facts"] or ["none"])
    lines.extend(["", "## Facts", "", "```json", json.dumps(decision["facts"], indent=2, sort_keys=True), "```", ""])
    return "\n".join(lines)


def design_paths(root: Path, feature_id: str) -> tuple[Path, Path]:
    return root / "docs/design" / f"{feature_id}.md", root / "docs/design" / f"{feature_id}.design.json"


def ensure_design_scaffold(root: Path, feature_id: str, record: dict[str, Any]) -> None:
    markdown, registry = design_paths(root, feature_id)
    if markdown.exists() and registry.exists():
        return
    markdown.parent.mkdir(parents=True, exist_ok=True)
    depth = record.get("planning_depth") if record.get("planning_depth") in {"compact_design", "designed_slices"} else "compact_design"
    today = dt.date.today().isoformat()
    markdown.write_text(
        create_feature_design.render_template(feature_id, str(depth), "codex-design-author", str(record.get("risk_level", "medium")), today),
        encoding="utf-8",
    )
    approval_policy = (
        "human_required"
        if depth == "designed_slices" and record.get("risk_level") in {"high", "critical"}
        else "human_or_authorized_reviewer"
    )
    json_write(
        registry,
        {
            "schema_version": "playbook.feature_design.v1",
            "feature_id": feature_id,
            "status": "draft",
            "planning_depth": depth,
            "risk_level": record.get("risk_level", "medium"),
            "brief_ref": "docs/PROJECT_BRIEF.md",
            "architecture_refs": ["docs/ARCHITECTURE.md"] if (root / "docs/ARCHITECTURE.md").exists() else [],
            "approval_policy": approval_policy,
            "slices": [],
        },
    )


def write_design_session(root: Path, feature_id: str) -> Path:
    path = root / ".playbook-artifacts/workflows" / feature_id / "design_session.json"
    payload = {
        "schema_version": WORKFLOW_SCHEMA,
        "feature_id": feature_id,
        "phase": "design",
        "base_commit": git_commit(root),
        "dirty_state": git_status(root),
        "allowed_design_paths": [
            f"docs/design/{feature_id}.md",
            f"docs/design/{feature_id}.design.json",
            "docs/tasks.md",
        ],
        "allowed_artifact_prefixes": [".playbook-artifacts/"],
    }
    json_write(path, payload)
    return path


def render_prompt(root: Path, task_id: str, role: str, output_path: str, feature_id: str = "", planning_path: str = "", reviews: list[str] | None = None) -> str:
    namespace = argparse.Namespace(
        root=root,
        task=task_id,
        role=role,
        review=reviews or [],
        human_approval_ref="",
        feature_id=feature_id,
        planning_decision=planning_path,
        output_path=output_path,
    )
    return render_codex_exec_prompt.render(namespace)


def cmd_draft(args: argparse.Namespace) -> int:
    root = args.root.resolve()
    _block, record = task_record(root, args.task)
    ensure_design_scaffold(root, args.feature_id, record)
    session_path = write_design_session(root, args.feature_id)
    planning_path, _ = planning_decision_paths(root, args.task)
    prompt_path = root / ".playbook-artifacts/prompts" / args.feature_id / "design_author.md"
    prompt_path.parent.mkdir(parents=True, exist_ok=True)
    output_path = f".playbook-artifacts/reports/{args.feature_id}_design_author.md"
    prompt_path.write_text(
        render_prompt(root, args.task, "design_author", output_path, args.feature_id, str(planning_path.relative_to(root)) if planning_path.exists() else ""),
        encoding="utf-8",
    )
    print("DESIGN AUTHOR PROMPT READY")
    print(f"prompt={prompt_path.relative_to(root)}")
    print(f"design_session={session_path.relative_to(root)}")
    print("Suggested external command:")
    print(
        "codex exec \\\n"
        f"  --cd {json.dumps(str(root))} \\\n"
        "  --sandbox workspace-write \\\n"
        f"  --output-last-message {json.dumps(output_path)} \\\n"
        f"  \"$(cat {prompt_path.relative_to(root)})\""
    )
    return 0


def load_design(root: Path, feature_id: str) -> tuple[Path, dict[str, Any], list[feature_design_lib.DesignFinding]]:
    _markdown, registry = design_paths(root, feature_id)
    findings, design = feature_design_lib.validate_design_file(root, registry)
    if design is None:
        raise SystemExit(f"feature_workflow: design missing or invalid for {feature_id}")
    return registry, design, findings


def approval_is_fresh(root: Path, feature_id: str) -> tuple[bool, dict[str, Any], Path]:
    registry, design, _findings = load_design(root, feature_id)
    return feature_design_lib.design_is_approved(design, root, registry), design, registry


def parse_review_if_present(root: Path, review: dict[str, Any]) -> dict[str, Any]:
    path = feature_design_lib.safe_repo_path(root, str(review.get("report_path", "")))
    if path is None:
        return {**review, "status": "blocked", "blocker": "unsafe report path"}
    if not path.exists():
        return {**review, "status": "pending"}
    try:
        parsed = render_codex_exec_prompt.parse_required_marker(str(review["role"]), path.read_text(encoding="utf-8", errors="replace"))
    except ValueError as exc:
        return {**review, "status": "blocked", "blocker": str(exc)}
    verdict = parsed["verdict"]
    status = "blocked" if verdict == "STOP_SHIP" else "acceptable"
    return {**review, "status": status, "verdict": verdict, "report_sha256": feature_design_lib.sha256_file(path)}


def write_required_reviews(root: Path, feature_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    parsed_reviews = [parse_review_if_present(root, review) for review in payload["reviews"]]
    payload = {**payload, "reviews": parsed_reviews}
    path = root / ".playbook-artifacts/workflows" / feature_id / "required_reviews.json"
    feature_review_policy.write_report(path, payload)
    return payload


def cmd_review(args: argparse.Namespace) -> int:
    root = args.root.resolve()
    _registry, design, _findings = load_design(root, args.feature_id)
    slice_item = feature_design_lib.find_slice(design, args.slice_id) if args.slice_id else None
    report = feature_review_policy.report(feature_id=args.feature_id, design=design, slice_item=slice_item)
    for review in report["reviews"]:
        prompt_path = root / review["prompt_path"]
        prompt_path.parent.mkdir(parents=True, exist_ok=True)
        prompt_path.write_text(
            render_prompt(root, args.task, review["role"], review["report_path"], args.feature_id),
            encoding="utf-8",
        )
        review["suggested_command"] = (
            "codex exec "
            f"--cd {json.dumps(str(root))} "
            "--sandbox read-only "
            f"--output-last-message {json.dumps(review['report_path'])} "
            f"\"$(cat {review['prompt_path']})\""
        )
    report = write_required_reviews(root, args.feature_id, report)
    blockers = [review for review in report["reviews"] if review.get("status") == "blocked"]
    print(f"feature_workflow review: required={sum(1 for r in report['reviews'] if r.get('required'))} blockers={len(blockers)}")
    for review in report["reviews"]:
        print(f"{review['role']}: {review['status']} prompt={review['prompt_path']} report={review['report_path']}")
    return 1 if blockers else 0


def dependency_ids_ready(design: dict[str, Any], slice_item: dict[str, Any]) -> list[str]:
    by_id = feature_design_lib.slice_registry(design)
    missing: list[str] = []
    for dep in slice_item.get("dependencies", []):
        dep_item = by_id.get(str(dep))
        if not dep_item or str(dep_item.get("status", "")) not in feature_design_lib.SLICE_WORKFLOW_DONE_STATUSES:
            missing.append(str(dep))
    return missing


def blocking_design_reviews(root: Path, feature_id: str) -> list[dict[str, Any]]:
    path = root / ".playbook-artifacts/workflows" / feature_id / "required_reviews.json"
    if not path.exists():
        return []
    data = read_json(path)
    return [item for item in data.get("reviews", []) if item.get("required") and item.get("status") == "blocked"]


def choose_next_slice(root: Path, feature_id: str) -> tuple[dict[str, Any] | None, list[str], dict[str, Any]]:
    fresh, design, _registry = approval_is_fresh(root, feature_id)
    reasons: list[str] = []
    if not fresh:
        return None, ["fresh approved design is required"], design
    blockers = blocking_design_reviews(root, feature_id)
    if blockers:
        return None, [f"blocking design review: {item['role']}" for item in blockers], design
    for item in design.get("slices", []):
        if not isinstance(item, dict) or item.get("status") != "planned":
            continue
        missing = dependency_ids_ready(design, item)
        if missing:
            reasons.append(f"{item.get('slice_id')} waits for dependencies: {', '.join(missing)}")
            continue
        return item, [], design
    if not reasons:
        reasons.append("no planned slice is ready")
    return None, reasons, design


def cmd_next(args: argparse.Namespace) -> int:
    root = args.root.resolve()
    item, reasons, _design = choose_next_slice(root, args.feature_id)
    if item:
        print(f"Ready slice: {item['slice_id']}")
        print(json.dumps(item, indent=2, sort_keys=True))
        return 0
    print("No ready slice.")
    for reason in reasons:
        print(f"- {reason}")
    return 1


def update_slice(root: Path, registry: Path, design: dict[str, Any], slice_id: str, updates: dict[str, Any]) -> dict[str, Any]:
    updated = json.loads(json.dumps(design))
    for item in updated.get("slices", []):
        if isinstance(item, dict) and item.get("slice_id") == slice_id:
            item.update(updates)
            break
    json_write(registry, updated)
    return updated


def cmd_start(args: argparse.Namespace) -> int:
    root = args.root.resolve()
    fresh, design, registry = approval_is_fresh(root, args.feature_id)
    if not fresh:
        print("feature_workflow start: fresh approved design is required", file=sys.stderr)
        return 1
    slice_item = feature_design_lib.find_slice(design, args.slice_id)
    if slice_item is None:
        print(f"feature_workflow start: slice {args.slice_id} not found", file=sys.stderr)
        return 1
    missing = dependency_ids_ready(design, slice_item)
    if missing:
        print(f"feature_workflow start: dependencies not reviewed: {', '.join(missing)}", file=sys.stderr)
        return 1
    in_progress = [item.get("slice_id") for item in design.get("slices", []) if isinstance(item, dict) and item.get("status") == "in_progress" and item.get("slice_id") != args.slice_id]
    if in_progress and not args.allow_parallel:
        print(f"feature_workflow start: conflicting in_progress slice(s): {', '.join(in_progress)}", file=sys.stderr)
        return 1
    start_path = root / ".playbook-artifacts/workflows" / args.feature_id / args.slice_id / "start.json"
    json_write(
        start_path,
        {
            "schema_version": "playbook.slice_start.v1",
            "feature_id": args.feature_id,
            "slice_id": args.slice_id,
            "base_commit": git_commit(root),
            "dirty_state": git_status(root),
            "started_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        },
    )
    design = update_slice(root, registry, design, args.slice_id, {"status": "in_progress"})
    context_code = cmd_context(args)
    print(f"feature_workflow start: slice={args.slice_id}")
    print("Allowed files: " + ", ".join(slice_item.get("allowed_files", [])))
    print("Forbidden files: " + ", ".join(slice_item.get("forbidden_files", [])))
    print("Verification: " + json.dumps(slice_item.get("verification", []), sort_keys=True))
    return context_code


def render_workflow_context(root: Path, feature_id: str, slice_id: str, task_id: str = "") -> Path:
    registry, design, findings = load_design(root, feature_id)
    errors = [finding for finding in findings if finding.severity == "error"]
    if errors or not feature_design_lib.design_is_approved(design, root, registry):
        raise SystemExit("feature_workflow context: fresh approved design is required")
    slice_item = feature_design_lib.find_slice(design, slice_id)
    if slice_item is None:
        raise SystemExit(f"feature_workflow context: slice {slice_id} not found")
    manifest_path = root / ".playbook/instruction_manifest.json"
    manifest_errors, manifest = render_slice_context.load_manifest(root, manifest_path)
    if manifest_errors or manifest is None:
        raise SystemExit("; ".join(manifest_errors))
    packet = render_slice_context.render_packet(root, feature_id, slice_id, design, slice_item, manifest, manifest_path)
    start_path = root / ".playbook-artifacts/workflows" / feature_id / slice_id / "start.json"
    start = read_json(start_path) if start_path.exists() else {}
    planning_ref = f".playbook-artifacts/planning/{task_id}/planning_decision.json" if task_id else "[not supplied]"
    required = feature_review_policy.report(feature_id=feature_id, design=design, slice_item=slice_item)
    packet += "\n".join(
        [
            "",
            "## Workflow Execution Contract",
            "",
            f"- Planning decision ref: `{planning_ref}`",
            f"- Approved Markdown SHA-256: `{design.get('approved_markdown_sha256', '')}`",
            f"- Approved registry payload SHA-256: `{design.get('approved_registry_payload_sha256', '')}`",
            f"- Base commit: `{start.get('base_commit', '[not started]')}`",
            f"- Current task: `{task_id or '[not supplied]'}`",
            "- Required slice review roles: "
            + ", ".join(item["role"] for item in required["reviews"] if item.get("required")),
            "",
            "### Exact Structured Verification",
            "",
            "```json",
            json.dumps(slice_item.get("verification", []), indent=2, sort_keys=True),
            "```",
            "",
            "Implement only this slice. Do not approve completion. Do not modify design content.",
            "",
        ]
    )
    output = root / ".playbook-artifacts/context" / feature_id / f"{slice_id}.md"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(packet, encoding="utf-8")
    return output


def cmd_context(args: argparse.Namespace) -> int:
    root = args.root.resolve()
    try:
        output = render_workflow_context(root, args.feature_id, args.slice_id, getattr(args, "task", ""))
    except SystemExit as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(f"feature_workflow context: output={output.relative_to(root)}")
    return 0


def scope_findings(root: Path, base_commit: str, slice_item: dict[str, Any], feature_id: str) -> list[dict[str, Any]]:
    files = [
        path
        for path in changed_files_since(root, base_commit)
        if not path.startswith(".playbook-artifacts/")
        and path != f"docs/design/{feature_id}.design.json"
        and path != f"docs/design/{feature_id}.md"
        and "__pycache__/" not in path
    ]
    findings: list[dict[str, Any]] = []
    outside, forbidden = feature_design_lib.task_files_within_slice(files, slice_item)
    for path in forbidden:
        findings.append({"severity": "stop_ship", "check_id": "SLICE_FORBIDDEN_FILE", "path": path, "message": f"changed forbidden file {path}"})
    for path in outside:
        findings.append({"severity": "stop_ship", "check_id": "SLICE_OUTSIDE_ALLOWED_FILES", "path": path, "message": f"changed file outside slice allowed files {path}"})
    budget = feature_design_lib.parse_change_budget(slice_item.get("change_budget"))
    line_delta = changed_lines_since(root, base_commit)
    if "files" in budget and len(files) > budget["files"]:
        findings.append({"severity": "advisory", "check_id": "SLICE_CHANGE_BUDGET_EXCEEDED", "metric": "files", "actual": len(files), "budget": budget["files"]})
    if "lines" in budget and line_delta > budget["lines"]:
        findings.append({"severity": "advisory", "check_id": "SLICE_CHANGE_BUDGET_EXCEEDED", "metric": "lines", "actual": line_delta, "budget": budget["lines"]})
    return findings


def run_structured_verification(root: Path, feature_id: str, slice_id: str, checks: list[Any]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for index, check in enumerate(checks):
        if isinstance(check, str):
            results.append({"id": f"legacy_{index}", "status": "legacy_skipped", "warning": "LEGACY_SLICE_VERIFICATION_STRING", "command": check})
            continue
        if not isinstance(check, dict):
            results.append({"id": f"invalid_{index}", "status": "invalid", "exit_code": 2})
            continue
        argv = [sys.executable if item == "{python}" else str(item) for item in check.get("argv", [])]
        cwd_raw = str(check.get("cwd", "."))
        cwd = feature_design_lib.safe_repo_path(root, cwd_raw)
        if cwd is None:
            results.append({"id": check.get("id", f"check_{index}"), "status": "invalid", "exit_code": 2, "error": "unsafe cwd"})
            continue
        receipt_dir = root / ".playbook-artifacts/workflows" / feature_id / slice_id / "receipts" / str(check.get("id", f"check_{index}"))
        command = [
            sys.executable,
            str(PLAYBOOK_ROOT / "tools/receipt_run.py"),
            "--task-id",
            f"{feature_id}-{slice_id}-{check.get('id', index)}",
            "--output-dir",
            str(receipt_dir),
        ]
        if check.get("timeout_seconds"):
            command.extend(["--timeout", str(check["timeout_seconds"])])
        command.extend(["--", *argv])
        completed = subprocess.run(command, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        receipt_path = receipt_dir / "receipt.json"
        receipt = read_json(receipt_path) if receipt_path.exists() else {}
        expected = int(check.get("expected_exit_code", 0))
        exit_code = int(receipt.get("exit_code", completed.returncode))
        status = "pass" if exit_code == expected else "fail"
        results.append(
            {
                "id": check.get("id", f"check_{index}"),
                "status": status,
                "exit_code": exit_code,
                "expected_exit_code": expected,
                "receipt": str(receipt_path.relative_to(root)) if receipt_path.exists() else "",
            }
        )
    return results


def normalized_maintainability(root: Path, task_id: str, feature_id: str) -> dict[str, Any]:
    report = check_maintainability.evaluate(root, task_id)
    implementation_files = [
        path
        for path in report.get("changed_files", [])
        if not str(path).startswith(".playbook-artifacts/")
        and f"docs/design/{feature_id}.design.json" not in str(path)
        and f"docs/design/{feature_id}.md" not in str(path)
        and "__pycache__" not in str(path)
    ]
    task = check_maintainability.load_task(root, task_id)
    budget = feature_design_lib.parse_change_budget(task.get("change_budget"))
    filtered = []
    for signal in report.get("signals", []):
        message = str(signal.get("message", ""))
        if (
            f"docs/design/{feature_id}.design.json" in message
            or f"docs/design/{feature_id}.md" in message
            or ".playbook-artifacts/" in message
            or "__pycache__" in message
        ):
            continue
        if (
            signal.get("check_id") == "MAINTAINABILITY_CHANGE_BUDGET_FILES"
            and "files" in budget
            and len(implementation_files) <= budget["files"]
        ):
            continue
        filtered.append(signal)
    report["signals"] = filtered
    report["status"] = "stop_ship" if any(s.get("severity") == "stop_ship" for s in filtered) else "advisory" if filtered else "pass"
    return report


def reports_acceptable(root: Path, reviews: list[dict[str, Any]]) -> tuple[bool, bool, bool, list[dict[str, Any]]]:
    parsed = [parse_review_if_present(root, review) for review in reviews]
    blocked = any(item.get("status") == "blocked" for item in parsed)
    pending = any(item.get("required") and item.get("status") == "pending" for item in parsed)
    acceptable = not blocked and not pending
    return acceptable, pending, blocked, parsed


def cmd_check(args: argparse.Namespace) -> int:
    root = args.root.resolve()
    fresh, design, registry = approval_is_fresh(root, args.feature_id)
    if not fresh:
        print("feature_workflow check: fresh approved design is required", file=sys.stderr)
        return 1
    slice_item = feature_design_lib.find_slice(design, args.slice_id)
    if slice_item is None:
        print(f"feature_workflow check: slice {args.slice_id} not found", file=sys.stderr)
        return 1
    start_path = root / ".playbook-artifacts/workflows" / args.feature_id / args.slice_id / "start.json"
    if not start_path.exists():
        print("feature_workflow check: slice must be started first", file=sys.stderr)
        return 1
    start = read_json(start_path)
    base_commit = str(start.get("base_commit", ""))
    scope = scope_findings(root, base_commit, slice_item, args.feature_id)
    verification = run_structured_verification(root, args.feature_id, args.slice_id, list(slice_item.get("verification", [])))
    maintainability = normalized_maintainability(root, args.task, args.feature_id)
    review_policy = feature_review_policy.report(
        feature_id=args.feature_id,
        design=design,
        slice_item=slice_item,
        maintainability_report=maintainability,
        scope_findings=scope,
    )
    for review in review_policy["reviews"]:
        prompt_path = root / review["prompt_path"]
        prompt_path.parent.mkdir(parents=True, exist_ok=True)
        prompt_path.write_text(render_prompt(root, args.task, review["role"], review["report_path"], args.feature_id), encoding="utf-8")
    acceptable, pending, blocked_review, parsed_reviews = reports_acceptable(root, review_policy["reviews"])
    review_policy["reviews"] = parsed_reviews
    write_required_reviews(root, args.feature_id, review_policy)
    deterministic_blocked = any(item.get("severity") == "stop_ship" for item in scope)
    verification_failed = any(item.get("status") in {"fail", "invalid"} for item in verification if item.get("status") != "legacy_skipped")
    if deterministic_blocked:
        status = "blocked"
    elif verification_failed or maintainability.get("status") == "stop_ship":
        status = "fail"
    elif blocked_review:
        status = "blocked"
    elif pending:
        status = "review_required"
    else:
        status = "eligible_for_human_acceptance"
        update_slice(root, registry, design, args.slice_id, {"status": "reviewed"})
    result = {
        "schema_version": SLICE_RESULT_SCHEMA,
        "feature_id": args.feature_id,
        "slice_id": args.slice_id,
        "base_commit": base_commit,
        "current_commit": git_commit(root),
        "changed_files": changed_files_since(root, base_commit),
        "scope_findings": scope,
        "verification": verification,
        "maintainability_status": maintainability.get("status"),
        "maintainability": maintainability,
        "required_reviews": parsed_reviews,
        "review_status": "accepted" if status == "eligible_for_human_acceptance" else "pending" if pending else "blocked" if not acceptable else "not_required",
        "status": status,
    }
    output = root / ".playbook-artifacts/workflows" / args.feature_id / args.slice_id / "slice_result.json"
    json_write(output, result)
    print(f"feature_workflow check: status={status} result={output.relative_to(root)}")
    if status == "eligible_for_human_acceptance" and design.get("risk_level") in {"high", "critical"}:
        print("ELIGIBLE_FOR_HUMAN_ACCEPTANCE")
    return 0 if status == "eligible_for_human_acceptance" else 1


def cmd_status(args: argparse.Namespace) -> int:
    root = args.root.resolve()
    markdown, registry = design_paths(root, args.feature_id)
    if not registry.exists():
        state = "design_missing"
        summary = {"feature_id": args.feature_id, "state": state, "next_action": "draft design"}
    else:
        findings, design = feature_design_lib.validate_design_file(root, registry)
        if design is None:
            state = "design_missing"
            summary = {"feature_id": args.feature_id, "state": state, "findings": [f.as_dict() for f in findings]}
        else:
            approval = feature_design_lib.approval_state(root, registry, design)
            blockers = blocking_design_reviews(root, args.feature_id)
            in_progress = [item.get("slice_id") for item in design.get("slices", []) if isinstance(item, dict) and item.get("status") == "in_progress"]
            ready, reasons, _ = choose_next_slice(root, args.feature_id) if approval.get("fresh") else (None, [], design)
            if design.get("status") == "draft":
                state = "design_draft"
                next_action = "review design"
            elif blockers:
                state = "design_stop_ship"
                next_action = "resolve design blockers"
            elif not approval.get("fresh") and design.get("status") in {"approved", "implemented"}:
                state = "approval_stale"
                next_action = "re-approve design"
            elif not approval.get("fresh"):
                state = "human_approval_required"
                next_action = "approve design"
            elif in_progress:
                state = "slice_in_progress"
                next_action = f"check {in_progress[0]}"
            elif ready:
                state = "ready_for_slice"
                next_action = f"start {ready['slice_id']}"
            elif all(isinstance(item, dict) and item.get("status") == "reviewed" for item in design.get("slices", [])):
                state = "all_slices_reviewed"
                next_action = "existing release resolver"
            else:
                state = "slice_blocked"
                next_action = "; ".join(reasons) if reasons else "inspect slice dependencies"
            required_path = root / ".playbook-artifacts/workflows" / args.feature_id / "required_reviews.json"
            required = read_json(required_path) if required_path.exists() else {"reviews": []}
            required_total = sum(1 for item in required.get("reviews", []) if item.get("required"))
            required_ok = sum(1 for item in required.get("reviews", []) if item.get("required") and item.get("status") == "acceptable")
            summary = {
                "schema_version": "playbook.feature_workflow_status.v1",
                "feature_id": args.feature_id,
                "planning_depth": design.get("planning_depth"),
                "design_status": design.get("status"),
                "approval": approval.get("status"),
                "required_design_reviews": {"acceptable": required_ok, "total": required_total},
                "slices": len(design.get("slices", [])),
                "ready_slice": ready.get("slice_id") if ready else None,
                "blocked_reasons": reasons,
                "current_implementation_diff": git_status(root),
                "state": state,
                "next_action": next_action,
            }
    output = root / ".playbook-artifacts/workflows" / args.feature_id / "status.json"
    json_write(output, summary)
    print(f"Feature: {args.feature_id}")
    print(f"Planning depth: {summary.get('planning_depth', '[unknown]')}")
    print(f"Design status: {summary.get('design_status', '[missing]')}")
    print(f"Approval: {summary.get('approval', '[none]')}")
    if "required_design_reviews" in summary:
        reviews = summary["required_design_reviews"]
        print(f"Required design reviews: {reviews['acceptable']}/{reviews['total']} acceptable")
    print(f"Slices: {summary.get('slices', 0)}")
    print(f"Ready slice: {summary.get('ready_slice') or '[none]'}")
    print(f"Current implementation diff: {'none' if not summary.get('current_implementation_diff') else 'present'}")
    print(f"Next action: {summary.get('next_action')}")
    return 0


def cmd_approve(args: argparse.Namespace) -> int:
    return approve_feature_design.main(["--root", str(args.root.resolve()), "--feature-id", args.feature_id])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    sub = parser.add_subparsers(dest="command", required=True)
    plan = sub.add_parser("plan")
    plan.add_argument("--task", required=True)
    draft = sub.add_parser("draft")
    draft.add_argument("--task", required=True)
    draft.add_argument("--feature-id", required=True)
    review = sub.add_parser("review")
    review.add_argument("--task", required=True)
    review.add_argument("--feature-id", required=True)
    review.add_argument("--slice-id", default="")
    review.add_argument("--role", default="auto")
    review.add_argument("--execute", action="store_true")
    status = sub.add_parser("status")
    status.add_argument("--feature-id", required=True)
    approve = sub.add_parser("approve")
    approve.add_argument("--feature-id", required=True)
    next_cmd = sub.add_parser("next")
    next_cmd.add_argument("--feature-id", required=True)
    start = sub.add_parser("start")
    start.add_argument("--feature-id", required=True)
    start.add_argument("--slice-id", required=True)
    start.add_argument("--task", default="")
    start.add_argument("--allow-parallel", action="store_true")
    context = sub.add_parser("context")
    context.add_argument("--feature-id", required=True)
    context.add_argument("--slice-id", required=True)
    context.add_argument("--task", default="")
    check = sub.add_parser("check")
    check.add_argument("--task", required=True)
    check.add_argument("--feature-id", required=True)
    check.add_argument("--slice-id", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return {
        "plan": cmd_plan,
        "draft": cmd_draft,
        "review": cmd_review,
        "status": cmd_status,
        "approve": cmd_approve,
        "next": cmd_next,
        "start": cmd_start,
        "context": cmd_context,
        "check": cmd_check,
    }[args.command](args)


if __name__ == "__main__":
    raise SystemExit(main())
