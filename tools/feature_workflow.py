#!/usr/bin/env python3
"""Thin coordinator for Feature Design and vertical slice workflow."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
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
SLICE_CANDIDATE_RESULT_SCHEMA = "playbook.slice_candidate_result.v1"


def json_write(path: Path, payload: dict[str, Any]) -> None:
    feature_design_lib.atomic_write_json(path, payload)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def now_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_json(payload: dict[str, Any]) -> str:
    return feature_design_lib.sha256_bytes(
        json.dumps(payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True).encode("utf-8")
    )


def git(root: Path, args: list[str]) -> tuple[int, str]:
    result = subprocess.run(["git", *args], cwd=root, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    return result.returncode, result.stdout.strip()


def git_commit(root: Path) -> str:
    code, stdout = git(root, ["rev-parse", "HEAD"])
    return stdout if code == 0 and stdout else "not-a-git-repository"


def git_status(root: Path) -> list[str]:
    code, stdout = git(root, ["status", "--short"])
    return stdout.splitlines() if code == 0 and stdout else []


def dirty_paths(root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "status", "--porcelain=v1", "-z"],
        cwd=root,
        text=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0 or not result.stdout:
        return []
    paths: list[str] = []
    for raw in result.stdout.split(b"\0"):
        if not raw:
            continue
        entry = raw.decode("utf-8", errors="replace")
        if len(entry) < 4:
            continue
        path = entry[3:]
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        paths.append(path)
    return sorted(set(paths))


def require_clean_tree(root: Path, *, allow_playbook_artifacts: bool = True) -> None:
    dirty = [
        path
        for path in dirty_paths(root)
        if not (allow_playbook_artifacts and path.startswith(".playbook-artifacts/"))
    ]
    if dirty:
        raise SystemExit("clean Git working tree is required; dirty paths: " + ", ".join(dirty))


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


def rel_or_none(root: Path, path: Path) -> str:
    try:
        return feature_design_lib.repo_rel(root, path)
    except ValueError:
        return ""


def task_block(root: Path, task_id: str) -> playbook_validate.TaskBlock:
    for block in playbook_validate.parse_task_blocks(root / "docs/tasks.md"):
        if block.task_id == task_id:
            return block
    raise SystemExit(f"feature_workflow: task {task_id} not found")


def task_record(root: Path, task_id: str) -> tuple[playbook_validate.TaskBlock, dict[str, Any]]:
    block = task_block(root, task_id)
    return block, block.to_record()


def task_block_text(root: Path, task_id: str) -> str:
    return render_codex_exec_prompt.task_section(root / "docs/tasks.md", task_id)


def file_sha256_or_empty(path: Path) -> str:
    return feature_design_lib.sha256_file(path) if path.exists() else ""


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


def planning_hash_inputs(root: Path, task_id: str, record: dict[str, Any]) -> dict[str, str]:
    inventory = repo_inventory(root, record)
    return {
        "task_block_sha256": feature_design_lib.sha256_text(task_block_text(root, task_id)),
        "brief_sha256": file_sha256_or_empty(root / "docs/PROJECT_BRIEF.md"),
        "repository_inventory_sha256": sha256_json(inventory),
    }


def decision_payload_sha256(decision: dict[str, Any]) -> str:
    payload = {
        key: value
        for key, value in decision.items()
        if key
        not in {
            "selected_planning_depth",
            "selected_by",
            "selection_method",
            "selected_at",
            "override_reason",
            "decision_payload_sha256",
        }
    }
    return sha256_json(payload)


def planning_decision_state(root: Path, task_id: str, record: dict[str, Any] | None = None) -> tuple[dict[str, Any] | None, list[str]]:
    path, _ = planning_decision_paths(root, task_id)
    if not path.exists():
        return None, ["planning decision is missing"]
    try:
        decision = read_json(path)
    except json.JSONDecodeError as exc:
        return None, [f"planning decision is invalid JSON: {exc.msg}"]
    record = record or task_record(root, task_id)[1]
    current = planning_hash_inputs(root, task_id, record)
    stale = [key for key, value in current.items() if str(decision.get(key, "")) != value]
    expected_payload = decision_payload_sha256(decision)
    if str(decision.get("decision_payload_sha256", "")) != expected_payload:
        stale.append("decision_payload_sha256")
    reasons = [f"planning decision stale: {', '.join(sorted(set(stale)))}"] if stale else []
    return decision, reasons


def require_selected_planning(root: Path, task_id: str, record: dict[str, Any]) -> dict[str, Any]:
    decision, problems = planning_decision_state(root, task_id, record)
    if decision is None:
        raise SystemExit("; ".join(problems))
    if decision.get("status") == "needs_input":
        raise SystemExit("planning decision needs_input blocks workflow draft/start/check")
    if problems:
        raise SystemExit("; ".join(problems))
    selected = str(decision.get("selected_planning_depth") or "").strip()
    if not selected:
        raise SystemExit("planning decision has no human-selected Planning Depth")
    if not str(decision.get("selected_by", "")).startswith("human:") and decision.get("selection_method") != "test_harness":
        raise SystemExit("planning decision selection requires human:<identity> provenance")
    task_depth = str(record.get("planning_depth", "")).strip()
    if task_depth and task_depth != selected and not str(decision.get("override_reason", "")).strip():
        raise SystemExit(
            f"task Planning-Depth {task_depth} conflicts with selected planning decision {selected} without override reason"
        )
    return decision


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
    hash_inputs = planning_hash_inputs(root, args.task, record)
    decision = {
        "schema_version": PLANNING_SCHEMA,
        "task_id": args.task,
        "status": status,
        "facts": facts,
        "unknown_facts": unknown + ([] if brief_is_approved(root) else ["approved_brief"]),
        "repository_inventory": repo_inventory(root, record),
        "recommended_planning_depth": recommendation["recommended_planning_depth"],
        "reasons": recommendation["reasons"],
        "selected_planning_depth": None,
        "selected_by": None,
        "selection_method": None,
        "selected_at": None,
        "override_reason": None,
        "override_allowed": recommendation["override_allowed"],
        "override_requires_reason": recommendation["override_requires_reason"],
        **hash_inputs,
    }
    decision["decision_payload_sha256"] = decision_payload_sha256(decision)
    json_path, md_path = planning_decision_paths(root, args.task)
    json_write(json_path, decision)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(render_planning_markdown(decision), encoding="utf-8")
    print(f"feature_workflow plan: status={status} recommendation={decision['recommended_planning_depth']}")
    print(f"planning_decision={json_path.relative_to(root)}")
    return 1 if status == "needs_input" else 0


def select_planning_decision(
    *,
    root: Path,
    task_id: str,
    selected_planning_depth: str,
    selected_by: str,
    selection_method: str,
    override_reason: str | None,
    selected_at: str | None = None,
) -> dict[str, Any]:
    block, record = task_record(root, task_id)
    del block
    decision, problems = planning_decision_state(root, task_id, record)
    if decision is None:
        raise ValueError("; ".join(problems))
    if decision.get("status") == "needs_input":
        raise ValueError("cannot select Planning Depth while decision status is needs_input")
    if problems:
        raise ValueError("; ".join(problems))
    selected = selected_planning_depth.strip()
    if selected not in planning_depth.PLANNING_DEPTHS:
        raise ValueError(f"unsupported Planning Depth: {selected}")
    recommended = str(decision.get("recommended_planning_depth", "")).strip()
    override = selected != recommended
    reason = (override_reason or "").strip()
    if override and not reason:
        raise ValueError("Planning Depth override requires a reason")
    if selection_method != "test_harness" and not selected_by.startswith("human:"):
        raise ValueError("production Planning Depth selection requires human:<identity>")
    decision.update(
        {
            "selected_planning_depth": selected,
            "selected_by": selected_by,
            "selection_method": "override" if override and selection_method != "test_harness" else selection_method,
            "selected_at": selected_at or now_utc(),
            "override_reason": reason or None,
        }
    )
    decision["decision_payload_sha256"] = decision_payload_sha256(decision)
    json_path, md_path = planning_decision_paths(root, task_id)
    json_write(json_path, decision)
    md_path.write_text(render_planning_markdown(decision), encoding="utf-8")
    return decision


def cmd_select_plan(args: argparse.Namespace) -> int:
    root = args.root.resolve()
    decision_path, _ = planning_decision_paths(root, args.task)
    if not decision_path.exists():
        print("feature_workflow select-plan: run plan first", file=sys.stderr)
        return 1
    decision = read_json(decision_path)
    if decision.get("status") == "needs_input":
        print("feature_workflow select-plan: planning decision needs_input", file=sys.stderr)
        return 1
    if not sys.stdin.isatty():
        print("feature_workflow select-plan: interactive TTY is required", file=sys.stderr)
        return 2
    print(f"Recommended: {decision['recommended_planning_depth']}")
    print("Reasons:")
    for reason in decision.get("reasons", []):
        print(f"- {reason}")
    print("")
    print("1. Accept recommendation")
    print("2. Override")
    print("3. Cancel")
    choice = input("Select: ").strip()
    if choice == "3":
        print("feature_workflow select-plan: cancelled")
        return 1
    selected = str(decision["recommended_planning_depth"])
    method = "accepted_recommendation"
    reason = None
    if choice == "2":
        selected = input("Planning Depth override (oneshot|compact_design|designed_slices): ").strip()
        reason = input("Override reason: ").strip()
        method = "override"
    elif choice != "1":
        print("feature_workflow select-plan: invalid choice", file=sys.stderr)
        return 1
    human = input("Human identity (example: human:artem): ").strip()
    try:
        selected_decision = select_planning_decision(
            root=root,
            task_id=args.task,
            selected_planning_depth=selected,
            selected_by=human,
            selection_method=method,
            override_reason=reason,
        )
    except ValueError as exc:
        print(f"feature_workflow select-plan: {exc}", file=sys.stderr)
        return 1
    print(f"feature_workflow select-plan: selected={selected_decision['selected_planning_depth']}")
    return 0


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
    try:
        _block, record, _decision = validate_task_feature_slice_binding(root, task_id=args.task, feature_id=args.feature_id)
        require_clean_tree(root, allow_playbook_artifacts=True)
    except SystemExit as exc:
        print(f"feature_workflow draft: {exc}", file=sys.stderr)
        return 1
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


def validate_task_feature_slice_binding(
    root: Path,
    *,
    task_id: str,
    feature_id: str,
    slice_id: str = "",
) -> tuple[playbook_validate.TaskBlock, dict[str, Any], dict[str, Any]]:
    block, record = task_record(root, task_id)
    decision = require_selected_planning(root, task_id, record)
    registry_ref = f"docs/design/{feature_id}.design.json"
    refs = [str(ref).strip().strip("`") for ref in record.get("design_refs", [])]
    if registry_ref not in refs:
        raise SystemExit(f"task {task_id} Design-Refs must include {registry_ref}")
    selected_depth = str(decision.get("selected_planning_depth", "")).strip()
    task_depth = str(record.get("planning_depth", "")).strip()
    if task_depth != selected_depth and not str(decision.get("override_reason", "")).strip():
        raise SystemExit(f"task {task_id} Planning-Depth {task_depth} conflicts with selected decision {selected_depth}")
    declared_slice = str(record.get("slice_id", "")).strip()
    if slice_id and declared_slice and declared_slice != slice_id:
        raise SystemExit(f"task {task_id} Slice-ID {declared_slice} conflicts with requested slice {slice_id}")
    return block, record, decision


def approval_is_fresh(root: Path, feature_id: str) -> tuple[bool, dict[str, Any], Path]:
    registry, design, _findings = load_design(root, feature_id)
    return feature_design_lib.design_is_approved(design, root, registry), design, registry


def required_reviews_path(root: Path, feature_id: str, phase: str, slice_id: str = "") -> Path:
    if phase == "slice":
        if not slice_id:
            raise ValueError("slice_id is required for slice review projection")
        return root / ".playbook-artifacts/workflows" / feature_id / "slices" / slice_id / "required_reviews.json"
    return root / ".playbook-artifacts/workflows" / feature_id / "design" / "required_reviews.json"


def legacy_required_reviews_path(root: Path, feature_id: str) -> Path:
    return root / ".playbook-artifacts/workflows" / feature_id / "required_reviews.json"


def read_required_reviews_projection(root: Path, feature_id: str, phase: str, slice_id: str = "") -> dict[str, Any]:
    path = required_reviews_path(root, feature_id, phase, slice_id)
    if path.exists():
        return read_json(path)
    legacy = legacy_required_reviews_path(root, feature_id)
    if legacy.exists():
        data = read_json(legacy)
        if str(data.get("phase", "")) == phase and (phase != "slice" or str(data.get("slice_id", "")) == slice_id):
            return data
    return {"reviews": []}


def parse_review_if_present(root: Path, feature_id: str, review: dict[str, Any], design: dict[str, Any] | None = None) -> dict[str, Any]:
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
    parsed_review = {**review, "status": status, "verdict": verdict, "report_sha256": feature_design_lib.sha256_file(path)}
    if design is not None and review.get("phase") == "design":
        try:
            record = approve_feature_design.write_design_review_record(
                root=root,
                feature_id=feature_id,
                role=str(review["role"]),
                report_path=feature_design_lib.repo_rel(root, path),
                reviewed_design=design,
                reviewer_binding=f"codex_exec:{review['role']}",
                read_only=True,
            )
            record_path = approve_feature_design.design_review_record_path(root, feature_id, str(review["role"]))
            parsed_review["review_record_path"] = feature_design_lib.repo_rel(root, record_path)
            parsed_review["review_record_sha256"] = feature_design_lib.sha256_file(record_path)
            parsed_review["reviewed_markdown_sha256"] = record["reviewed_markdown_sha256"]
            parsed_review["reviewed_registry_payload_sha256"] = record["reviewed_registry_payload_sha256"]
        except Exception as exc:
            return {**parsed_review, "status": "blocked", "blocker": str(exc)}
    return parsed_review


def write_required_reviews(root: Path, feature_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    phase = str(payload.get("phase", "design"))
    slice_id = str(payload.get("slice_id") or "")
    design: dict[str, Any] | None = None
    if phase == "design":
        try:
            _registry, design, _findings = load_design(root, feature_id)
        except SystemExit:
            design = None
    parsed_reviews = [parse_review_if_present(root, feature_id, review, design) for review in payload["reviews"]]
    payload = {**payload, "reviews": parsed_reviews}
    path = required_reviews_path(root, feature_id, phase, slice_id)
    feature_review_policy.write_report(path, payload)
    return payload


def role_runner_command(root: Path, task_id: str, feature_id: str, review: dict[str, Any]) -> str:
    """Return the governed default command for supported review roles.

    Model selection remains explicit at invocation time because it is a
    repository policy decision, not a Feature Workflow default.
    """
    parts = [
        "python3 tools/run_codex_role.py run",
        f"--root {json.dumps(str(root))}",
        f"--task {json.dumps(task_id)}",
        f"--feature-id {json.dumps(feature_id)}",
    ]
    slice_id = str(review.get("slice_id") or "")
    if slice_id:
        parts.append(f"--slice-id {json.dumps(slice_id)}")
    parts.extend(
        [
            f"--role {json.dumps(str(review['role']))}",
            f"--output-report {json.dumps(str(review['report_path']))}",
        ]
    )
    return " ".join(parts)


def cmd_review(args: argparse.Namespace) -> int:
    root = args.root.resolve()
    try:
        validate_task_feature_slice_binding(root, task_id=args.task, feature_id=args.feature_id, slice_id=args.slice_id)
    except SystemExit as exc:
        print(f"feature_workflow review: {exc}", file=sys.stderr)
        return 1
    _registry, design, _findings = load_design(root, args.feature_id)
    slice_item = feature_design_lib.find_slice(design, args.slice_id) if args.slice_id else None
    report = feature_review_policy.report(feature_id=args.feature_id, design=design, slice_item=slice_item)
    phase = "slice" if slice_item is not None else "design"
    roles = {str(item.get("role")) for item in report["reviews"]}
    if args.role != "auto":
        allowed = (
            {feature_review_policy.SLICE_REVIEW_ROLE, feature_review_policy.MAINTAINABILITY_REVIEW_ROLE}
            if phase == "slice"
            else set(feature_review_policy.DESIGN_REVIEW_ROLES)
        )
        if args.role not in allowed:
            print(f"feature_workflow review: role {args.role} is not valid for {phase} phase", file=sys.stderr)
            return 1
        if args.role not in roles:
            print(f"feature_workflow review: role {args.role} is not required or optional for current {phase} policy", file=sys.stderr)
            return 1
        report["reviews"] = [item for item in report["reviews"] if item.get("role") == args.role]
    for review in report["reviews"]:
        prompt_path = root / review["prompt_path"]
        prompt_path.parent.mkdir(parents=True, exist_ok=True)
        prompt_path.write_text(
            render_prompt(root, args.task, review["role"], review["report_path"], args.feature_id),
            encoding="utf-8",
        )
        review["suggested_command"] = role_runner_command(root, args.task, args.feature_id, review)
    report = write_required_reviews(root, args.feature_id, report)
    blockers = [review for review in report["reviews"] if review.get("status") == "blocked"]
    print(f"feature_workflow review: required={sum(1 for r in report['reviews'] if r.get('required'))} blockers={len(blockers)}")
    for review in report["reviews"]:
        print(f"{review['role']}: {review['status']} prompt={review['prompt_path']} report={review['report_path']}")
    return 1 if blockers else 0


def slice_artifact_dir(root: Path, feature_id: str, slice_id: str) -> Path:
    return root / ".playbook-artifacts/workflows" / feature_id / "slices" / slice_id


def legacy_slice_artifact_dir(root: Path, feature_id: str, slice_id: str) -> Path:
    return root / ".playbook-artifacts/workflows" / feature_id / slice_id


def slice_acceptance_path(root: Path, feature_id: str, slice_id: str) -> Path:
    return slice_artifact_dir(root, feature_id, slice_id) / "acceptance.json"


def candidate_result_path(root: Path, feature_id: str, slice_id: str) -> Path:
    return slice_artifact_dir(root, feature_id, slice_id) / "candidate_result.json"


def post_state_manifest_path(root: Path, feature_id: str, slice_id: str) -> Path:
    return slice_artifact_dir(root, feature_id, slice_id) / "post_state_manifest.json"


def read_start_artifact(root: Path, feature_id: str, slice_id: str) -> dict[str, Any]:
    path = slice_artifact_dir(root, feature_id, slice_id) / "start.json"
    legacy = legacy_slice_artifact_dir(root, feature_id, slice_id) / "start.json"
    if path.exists():
        return read_json(path)
    if legacy.exists():
        return read_json(legacy)
    return {}


def manifest_files_current(root: Path, manifest: dict[str, Any]) -> tuple[bool, list[str]]:
    problems: list[str] = []
    for item in manifest.get("files", []):
        if not isinstance(item, dict):
            problems.append("invalid manifest file entry")
            continue
        raw_path = str(item.get("path", "")).strip()
        path = feature_design_lib.safe_repo_path(root, raw_path)
        if path is None:
            problems.append(f"unsafe manifest path: {raw_path}")
            continue
        state = str(item.get("state", "present"))
        if state == "deleted":
            if path.exists():
                problems.append(f"manifest expected deleted file still exists: {raw_path}")
            continue
        if not path.exists():
            problems.append(f"manifest file missing: {raw_path}")
            continue
        if path.is_symlink():
            resolved = path.resolve()
            try:
                resolved.relative_to(root.resolve())
            except ValueError:
                problems.append(f"manifest symlink escapes repository: {raw_path}")
                continue
        if not path.is_file():
            problems.append(f"manifest path is not a regular file: {raw_path}")
            continue
        expected = str(item.get("sha256", "")).strip()
        actual = feature_design_lib.sha256_file(path)
        if expected != actual:
            problems.append(f"manifest hash mismatch: {raw_path}")
    return not problems, problems


def slice_acceptance_is_fresh(root: Path, feature_id: str, slice_id: str, slice_item: dict[str, Any] | None = None) -> tuple[bool, list[str]]:
    problems: list[str] = []
    if slice_item is not None and feature_design_lib.normalize_slice_status(slice_item.get("status")) != "accepted":
        problems.append("slice status is not accepted")
    acceptance_file = slice_acceptance_path(root, feature_id, slice_id)
    if not acceptance_file.exists():
        problems.append("acceptance file is missing")
        return False, problems
    try:
        acceptance = read_json(acceptance_file)
    except json.JSONDecodeError as exc:
        return False, [f"acceptance file is invalid JSON: {exc.msg}"]
    candidate_file = candidate_result_path(root, feature_id, slice_id)
    if not candidate_file.exists():
        problems.append("candidate result is missing")
    else:
        expected_candidate = str(acceptance.get("candidate_result_sha256", "")).strip()
        actual_candidate = feature_design_lib.sha256_file(candidate_file)
        if expected_candidate != actual_candidate:
            problems.append("candidate result hash mismatch")
        try:
            candidate = read_json(candidate_file)
        except json.JSONDecodeError as exc:
            candidate = {}
            problems.append(f"candidate result invalid JSON: {exc.msg}")
        manifest_ref = str(candidate.get("post_state_manifest_ref", "")).strip()
        manifest_sha = str(candidate.get("post_state_manifest_sha256", "")).strip()
        manifest_path = feature_design_lib.safe_repo_path(root, manifest_ref) if manifest_ref else None
        if manifest_path is None or not manifest_path.exists():
            problems.append("post-state manifest is missing")
        else:
            if feature_design_lib.sha256_file(manifest_path) != manifest_sha:
                problems.append("post-state manifest hash mismatch")
            try:
                manifest = read_json(manifest_path)
            except json.JSONDecodeError as exc:
                manifest = {}
                problems.append(f"post-state manifest invalid JSON: {exc.msg}")
            ok, manifest_problems = manifest_files_current(root, manifest)
            if not ok:
                problems.extend(manifest_problems)
    accepted_commit = str(acceptance.get("accepted_commit", "")).strip()
    if accepted_commit and accepted_commit != "not-a-git-repository":
        code, _stdout = git(root, ["merge-base", "--is-ancestor", accepted_commit, "HEAD"])
        if code != 0:
            problems.append("accepted commit is not an ancestor of current HEAD")
    return not problems, problems


def dependency_ids_ready(root: Path, feature_id: str, design: dict[str, Any], slice_item: dict[str, Any]) -> list[str]:
    by_id = feature_design_lib.slice_registry(design)
    missing: list[str] = []
    for dep in slice_item.get("dependencies", []):
        dep_item = by_id.get(str(dep))
        if not dep_item:
            missing.append(str(dep))
            continue
        accepted, _problems = slice_acceptance_is_fresh(root, feature_id, str(dep), dep_item)
        if not accepted:
            missing.append(str(dep))
    return missing


def blocking_design_reviews(root: Path, feature_id: str) -> list[dict[str, Any]]:
    data = read_required_reviews_projection(root, feature_id, "design")
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
        missing = dependency_ids_ready(root, feature_id, design, item)
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
    try:
        validate_task_feature_slice_binding(root, task_id=args.task, feature_id=args.feature_id, slice_id=args.slice_id)
    except SystemExit as exc:
        print(f"feature_workflow start: {exc}", file=sys.stderr)
        return 1
    fresh, design, registry = approval_is_fresh(root, args.feature_id)
    if not fresh:
        print("feature_workflow start: fresh approved design is required", file=sys.stderr)
        return 1
    slice_item = feature_design_lib.find_slice(design, args.slice_id)
    if slice_item is None:
        print(f"feature_workflow start: slice {args.slice_id} not found", file=sys.stderr)
        return 1
    if feature_design_lib.normalize_slice_status(slice_item.get("status")) != "planned":
        print("feature_workflow start: slice status must be planned", file=sys.stderr)
        return 1
    try:
        require_clean_tree(root, allow_playbook_artifacts=True)
    except SystemExit as exc:
        print(f"feature_workflow start: {exc}", file=sys.stderr)
        return 1
    missing = dependency_ids_ready(root, args.feature_id, design, slice_item)
    if missing:
        print(f"feature_workflow start: dependencies not accepted: {', '.join(missing)}", file=sys.stderr)
        return 1
    in_progress = [item.get("slice_id") for item in design.get("slices", []) if isinstance(item, dict) and item.get("status") == "in_progress" and item.get("slice_id") != args.slice_id]
    if in_progress and not args.allow_parallel:
        print(f"feature_workflow start: conflicting in_progress slice(s): {', '.join(in_progress)}", file=sys.stderr)
        return 1
    try:
        context_output = render_workflow_context(root, args.feature_id, args.slice_id, args.task)
    except SystemExit as exc:
        print(f"feature_workflow start: {exc}", file=sys.stderr)
        return 1
    print(f"feature_workflow context: output={context_output.relative_to(root)}")
    audited_run_ref = ""
    if args.execution_profile == "audited_rounds":
        audited_run_ref = create_audited_run_for_slice(
            root=root,
            task_id=args.task,
            feature_id=args.feature_id,
            slice_id=args.slice_id,
            context_ref=feature_design_lib.repo_rel(root, context_output),
            slice_item=slice_item,
        )
    start_path = slice_artifact_dir(root, args.feature_id, args.slice_id) / "start.json"
    json_write(
        start_path,
        {
            "schema_version": "playbook.slice_start.v1",
            "feature_id": args.feature_id,
            "slice_id": args.slice_id,
            "task_id": args.task,
            "execution_profile": args.execution_profile,
            "audited_run_ref": audited_run_ref,
            "base_commit": git_commit(root),
            "dirty_state": git_status(root),
            "started_at": now_utc(),
        },
    )
    design = update_slice(root, registry, design, args.slice_id, {"status": "in_progress"})
    print(f"feature_workflow start: slice={args.slice_id}")
    print("Allowed files: " + ", ".join(slice_item.get("allowed_files", [])))
    print("Forbidden files: " + ", ".join(slice_item.get("forbidden_files", [])))
    print("Verification: " + json.dumps(slice_item.get("verification", []), sort_keys=True))
    return 0


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
    start = read_start_artifact(root, feature_id, slice_id)
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
    if getattr(args, "task", ""):
        try:
            validate_task_feature_slice_binding(root, task_id=args.task, feature_id=args.feature_id, slice_id=args.slice_id)
        except SystemExit as exc:
            print(f"feature_workflow context: {exc}", file=sys.stderr)
            return 1
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


def post_state_manifest(root: Path, feature_id: str, slice_id: str, base_commit: str) -> dict[str, Any]:
    files: list[dict[str, Any]] = []
    for raw_path in changed_files_since(root, base_commit):
        if (
            raw_path.startswith(".playbook-artifacts/")
            or raw_path == f"docs/design/{feature_id}.design.json"
            or raw_path == f"docs/design/{feature_id}.md"
            or raw_path.startswith(".git/")
            or "/.git/" in raw_path
            or "__pycache__/" in raw_path
            or raw_path.startswith(".pytest_cache/")
            or raw_path.startswith(".venv/")
        ):
            continue
        path = feature_design_lib.safe_repo_path(root, raw_path)
        if path is None:
            raise SystemExit(f"unsafe changed path: {raw_path}")
        if path.is_symlink():
            resolved = path.resolve()
            try:
                resolved.relative_to(root.resolve())
            except ValueError as exc:
                raise SystemExit(f"symlink changed path escapes repository: {raw_path}") from exc
        if not path.exists():
            files.append({"path": raw_path, "state": "deleted"})
            continue
        if not path.is_file():
            continue
        files.append(
            {
                "path": raw_path,
                "state": "present",
                "sha256": feature_design_lib.sha256_file(path),
                "size_bytes": path.stat().st_size,
            }
        )
    return {
        "schema_version": "playbook.slice_post_state_manifest.v1",
        "feature_id": feature_id,
        "slice_id": slice_id,
        "base_commit": base_commit,
        "files": sorted(files, key=lambda item: item["path"]),
        "generated_at": now_utc(),
    }


def candidate_diff_sha256(manifest: dict[str, Any]) -> str:
    return sha256_json(
        {
            "base_commit": manifest.get("base_commit"),
            "files": manifest.get("files", []),
        }
    )


def verification_hash_refs(root: Path, verification: list[dict[str, Any]]) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    for item in verification:
        receipt = str(item.get("receipt", "")).strip()
        if not receipt:
            continue
        path = feature_design_lib.safe_repo_path(root, receipt)
        if path is None or not path.exists():
            continue
        refs.append(
            {
                "id": item.get("id"),
                "required": bool(item.get("required", True)),
                "status": item.get("status"),
                "receipt": receipt,
                "sha256": feature_design_lib.sha256_file(path),
            }
        )
    return refs


def review_hash_refs(root: Path, reviews: list[dict[str, Any]]) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    for item in reviews:
        for path_key, sha_key in (("report_path", "report_sha256"), ("review_record_path", "review_record_sha256")):
            raw_path = str(item.get(path_key, "")).strip()
            if not raw_path:
                continue
            path = feature_design_lib.safe_repo_path(root, raw_path)
            if path is None or not path.exists():
                continue
            refs.append(
                {
                    "role": item.get("role"),
                    "verdict": item.get("verdict"),
                    "path": raw_path,
                    "sha256": str(item.get(sha_key) or feature_design_lib.sha256_file(path)),
                }
            )
    return refs


def write_candidate_result(
    *,
    root: Path,
    task_id: str,
    feature_id: str,
    slice_id: str,
    base_commit: str,
    manifest: dict[str, Any],
    verification: list[dict[str, Any]],
    maintainability_ref: str,
    reviews: list[dict[str, Any]],
    status: str,
) -> dict[str, Any]:
    manifest_path = post_state_manifest_path(root, feature_id, slice_id)
    json_write(manifest_path, manifest)
    maintainability_path = feature_design_lib.safe_repo_path(root, maintainability_ref) if maintainability_ref else None
    candidate = {
        "schema_version": SLICE_CANDIDATE_RESULT_SCHEMA,
        "feature_id": feature_id,
        "slice_id": slice_id,
        "task_id": task_id,
        "base_commit": base_commit,
        "candidate_commit": git_commit(root),
        "diff_sha256": candidate_diff_sha256(manifest),
        "post_state_manifest_ref": feature_design_lib.repo_rel(root, manifest_path),
        "post_state_manifest_sha256": feature_design_lib.sha256_file(manifest_path),
        "verification_refs": verification_hash_refs(root, verification),
        "maintainability_ref": maintainability_ref,
        "maintainability_sha256": feature_design_lib.sha256_file(maintainability_path) if maintainability_path and maintainability_path.exists() else "",
        "review_records": review_hash_refs(root, reviews),
        "status": status,
    }
    json_write(candidate_result_path(root, feature_id, slice_id), candidate)
    return candidate


def advisory_verdicts(reviews: list[dict[str, Any]]) -> list[str]:
    return [str(item.get("role")) for item in reviews if item.get("verdict") == "ADVISORY"]


def write_policy_auto_acceptance(
    *,
    root: Path,
    task_id: str,
    feature_id: str,
    slice_id: str,
    candidate: dict[str, Any],
) -> dict[str, Any]:
    candidate_path = candidate_result_path(root, feature_id, slice_id)
    acceptance = {
        "schema_version": "playbook.slice_acceptance.v1",
        "feature_id": feature_id,
        "slice_id": slice_id,
        "task_id": task_id,
        "accepted_by": "policy:feature_review_policy",
        "accepted_at": now_utc(),
        "acceptance_method": "policy_auto",
        "policy_ref": "feature_review_policy.slice_acceptance.v1",
        "accepted_commit": git_commit(root),
        "candidate_result_sha256": feature_design_lib.sha256_file(candidate_path),
        "diff_sha256": candidate["diff_sha256"],
        "verification_hashes": candidate.get("verification_refs", []),
        "review_record_hashes": candidate.get("review_records", []),
        "advisory_acknowledgement": "",
        "evidence_hashes": {},
    }
    json_write(slice_acceptance_path(root, feature_id, slice_id), acceptance)
    return acceptance


def create_audited_run_for_slice(
    *,
    root: Path,
    task_id: str,
    feature_id: str,
    slice_id: str,
    context_ref: str,
    slice_item: dict[str, Any],
) -> str:
    base_run_id = f"{feature_id}-{slice_id}"
    run_id = base_run_id
    base = root / ".playbook-artifacts/audited-runs" / run_id
    if base.exists():
        run_id = f"{base_run_id}-{dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
        base = root / ".playbook-artifacts/audited-runs" / run_id
    budgets = {
        "max_rounds": 5,
        "max_wall_clock_seconds": 7200,
        "max_repeated_failure_count": 2,
        "max_no_progress_rounds": 2,
        "max_tool_calls_per_round": 40,
        "max_total_cost_usd": "unknown",
        "human_escalation_policy": "stop_and_request_human_input",
    }
    requirements = [
        {
            "id": "REQ-1",
            "description": str(slice_item.get("user_visible_outcome", "slice acceptance criteria")),
            "status": "open",
            "evidence_refs": [],
        }
    ]
    if slice_item.get("expected_interfaces"):
        requirements.append(
            {
                "id": "REQ-2",
                "description": "Expected interfaces: " + ", ".join(str(item) for item in slice_item.get("expected_interfaces", [])),
                "status": "open",
                "evidence_refs": [],
            }
        )
    manifest = {
        "schema_version": "playbook.audited_run_manifest.v1",
        "run_id": run_id,
        "execution_profile": "audited_rounds",
        "task_id": task_id,
        "feature_id": feature_id,
        "slice_id": slice_id,
        "original_goal_ref": context_ref,
        **budgets,
        "created_at": now_utc(),
        "status": "active",
    }
    state = {
        "schema_version": "playbook.audited_state.v1",
        "run_id": run_id,
        "original_goal_ref": context_ref,
        "requirements": requirements,
        "facts": [],
        "blockers": [],
        "verified_artifacts": [],
        "open_requirements": [item["id"] for item in requirements],
        "audit_refs": [],
        "round_counters": {
            "completed_rounds": 0,
            "next_round": 1,
            "consecutive_failures": 0,
            "consecutive_no_progress": 0,
        },
        "budgets": budgets,
        "status": "active",
    }
    result = {
        "schema_version": "playbook.audited_run_result.v1",
        "run_id": run_id,
        "status": "active",
        "stop_reason": None,
        "generated_at": now_utc(),
    }
    json_write(base / "manifest.json", manifest)
    json_write(base / "audited_state.json", state)
    json_write(base / "result.json", result)
    return f".playbook-artifacts/audited-runs/{run_id}/manifest.json"


def validate_audited_run_result(root: Path, start: dict[str, Any]) -> tuple[bool, str]:
    manifest_ref = str(start.get("audited_run_ref", "")).strip()
    manifest_path = feature_design_lib.safe_repo_path(root, manifest_ref)
    if manifest_path is None or not manifest_path.exists():
        return False, "audited run manifest is missing"
    run_base = manifest_path.parent
    result_file = run_base / "result.json"
    state_file = run_base / "audited_state.json"
    if not result_file.exists() or not state_file.exists():
        return False, "audited run result/state is missing"
    try:
        result = read_json(result_file)
        state = read_json(state_file)
    except json.JSONDecodeError as exc:
        return False, f"audited run artifact invalid JSON: {exc.msg}"
    if result.get("schema_version") != "playbook.audited_run_result.v1":
        return False, "audited run result schema_version is invalid"
    if state.get("schema_version") != "playbook.audited_state.v1":
        return False, "audited state schema_version is invalid"
    if result.get("status") != "complete" or state.get("status") != "complete":
        return False, "audited run is not complete"
    open_requirements = state.get("open_requirements", [])
    if open_requirements:
        return False, "audited run has open requirements: " + ", ".join(str(item) for item in open_requirements)
    if not all(item.get("status") == "verified" for item in state.get("requirements", [])):
        return False, "audited run has unverified requirements"
    return True, ""


def validate_candidate_fresh(root: Path, feature_id: str, slice_id: str) -> tuple[dict[str, Any], list[str]]:
    problems: list[str] = []
    candidate_file = candidate_result_path(root, feature_id, slice_id)
    if not candidate_file.exists():
        return {}, ["candidate result is missing"]
    try:
        candidate = read_json(candidate_file)
    except json.JSONDecodeError as exc:
        return {}, [f"candidate result invalid JSON: {exc.msg}"]
    if candidate.get("schema_version") != SLICE_CANDIDATE_RESULT_SCHEMA:
        problems.append("candidate result has unsupported schema_version")
    if candidate.get("feature_id") != feature_id or candidate.get("slice_id") != slice_id:
        problems.append("candidate result feature/slice mismatch")
    manifest_ref = str(candidate.get("post_state_manifest_ref", "")).strip()
    manifest_path = feature_design_lib.safe_repo_path(root, manifest_ref) if manifest_ref else None
    if manifest_path is None or not manifest_path.exists():
        problems.append("post-state manifest is missing")
        manifest = {}
    else:
        if feature_design_lib.sha256_file(manifest_path) != str(candidate.get("post_state_manifest_sha256", "")).strip():
            problems.append("post-state manifest hash mismatch")
        try:
            manifest = read_json(manifest_path)
        except json.JSONDecodeError as exc:
            manifest = {}
            problems.append(f"post-state manifest invalid JSON: {exc.msg}")
        ok, manifest_problems = manifest_files_current(root, manifest)
        if not ok:
            problems.extend(manifest_problems)
    base_commit = str(candidate.get("base_commit", "")).strip()
    current_manifest = post_state_manifest(root, feature_id, slice_id, base_commit) if base_commit else {}
    if current_manifest and candidate_diff_sha256(current_manifest) != str(candidate.get("diff_sha256", "")).strip():
        problems.append("current repository state does not match candidate diff hash")
    for ref in candidate.get("verification_refs", []):
        if not isinstance(ref, dict):
            problems.append("invalid verification ref")
            continue
        raw_path = str(ref.get("receipt", "")).strip()
        path = feature_design_lib.safe_repo_path(root, raw_path)
        if path is None or not path.exists():
            problems.append(f"verification receipt missing: {raw_path}")
            continue
        if feature_design_lib.sha256_file(path) != str(ref.get("sha256", "")).strip():
            problems.append(f"verification receipt hash mismatch: {raw_path}")
    for ref in candidate.get("review_records", []):
        if not isinstance(ref, dict):
            problems.append("invalid review ref")
            continue
        raw_path = str(ref.get("path", "")).strip()
        path = feature_design_lib.safe_repo_path(root, raw_path)
        if path is None or not path.exists():
            problems.append(f"review evidence missing: {raw_path}")
            continue
        if feature_design_lib.sha256_file(path) != str(ref.get("sha256", "")).strip():
            problems.append(f"review evidence hash mismatch: {raw_path}")
    return candidate, problems


def accept_slice(
    *,
    root: Path,
    task_id: str,
    feature_id: str,
    slice_id: str,
    accepted_by: str,
    advisory_acknowledgement: str,
    acceptance_method: str,
    accepted_at: str | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    validate_task_feature_slice_binding(root, task_id=task_id, feature_id=feature_id, slice_id=slice_id)
    fresh, design, registry = approval_is_fresh(root, feature_id)
    if not fresh:
        raise SystemExit("fresh approved design is required")
    slice_item = feature_design_lib.find_slice(design, slice_id)
    if slice_item is None:
        raise SystemExit(f"slice {slice_id} not found")
    if feature_design_lib.normalize_slice_status(slice_item.get("status")) != "awaiting_human_acceptance":
        raise SystemExit("slice must be awaiting_human_acceptance")
    require_clean_tree(root, allow_playbook_artifacts=True)
    if git_commit(root) == "not-a-git-repository":
        raise SystemExit("Git repository is required for slice acceptance")
    candidate, problems = validate_candidate_fresh(root, feature_id, slice_id)
    if problems:
        raise SystemExit("; ".join(problems))
    base_commit = str(candidate.get("base_commit", "")).strip()
    current_commit = git_commit(root)
    if current_commit == base_commit:
        raise SystemExit("current HEAD must differ from base commit before acceptance")
    if not accepted_by.startswith("human:"):
        raise SystemExit("slice acceptance requires human:<identity>")
    advisory_roles = [str(ref.get("role")) for ref in candidate.get("review_records", []) if ref.get("verdict") == "ADVISORY"]
    if advisory_roles and not advisory_acknowledgement.strip():
        raise SystemExit("ADVISORY slice review findings require recorded acknowledgement")
    candidate_file = candidate_result_path(root, feature_id, slice_id)
    acceptance = {
        "schema_version": "playbook.slice_acceptance.v1",
        "feature_id": feature_id,
        "slice_id": slice_id,
        "task_id": task_id,
        "accepted_by": accepted_by,
        "accepted_at": accepted_at or now_utc(),
        "acceptance_method": acceptance_method,
        "accepted_commit": current_commit,
        "candidate_result_sha256": feature_design_lib.sha256_file(candidate_file),
        "diff_sha256": candidate["diff_sha256"],
        "verification_hashes": candidate.get("verification_refs", []),
        "review_record_hashes": candidate.get("review_records", []),
        "advisory_acknowledgement": advisory_acknowledgement.strip(),
    }
    json_write(slice_acceptance_path(root, feature_id, slice_id), acceptance)
    update_slice(root, registry, design, slice_id, {"status": "accepted"})
    return acceptance


def run_structured_verification(root: Path, feature_id: str, slice_id: str, checks: list[Any]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for index, check in enumerate(checks):
        if isinstance(check, str):
            results.append({"id": f"legacy_{index}", "status": "legacy_skipped", "required": False, "warning": "LEGACY_SLICE_VERIFICATION_STRING", "command": check})
            continue
        if not isinstance(check, dict):
            results.append({"id": f"invalid_{index}", "status": "invalid", "required": True, "exit_code": 2})
            continue
        required = bool(check.get("required", True))
        argv = [sys.executable if item == "{python}" else str(item) for item in check.get("argv", [])]
        cwd_raw = str(check.get("cwd", "."))
        cwd = feature_design_lib.safe_repo_path(root, cwd_raw)
        if cwd is None:
            results.append({"id": check.get("id", f"check_{index}"), "status": "invalid", "required": required, "exit_code": 2, "error": "unsafe cwd"})
            continue
        receipt_dir = slice_artifact_dir(root, feature_id, slice_id) / "receipts" / str(check.get("id", f"check_{index}"))
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
                "required": required,
                "exit_code": exit_code,
                "expected_exit_code": expected,
                "receipt": str(receipt_path.relative_to(root)) if receipt_path.exists() else "",
                "receipt_sha256": feature_design_lib.sha256_file(receipt_path) if receipt_path.exists() else "",
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


def reports_acceptable(root: Path, feature_id: str, reviews: list[dict[str, Any]]) -> tuple[bool, bool, bool, list[dict[str, Any]]]:
    parsed = [parse_review_if_present(root, feature_id, review) for review in reviews]
    blocked = any(item.get("status") == "blocked" for item in parsed)
    pending = any(item.get("required") and item.get("status") == "pending" for item in parsed)
    acceptable = not blocked and not pending
    return acceptable, pending, blocked, parsed


def cmd_check(args: argparse.Namespace) -> int:
    root = args.root.resolve()
    try:
        validate_task_feature_slice_binding(root, task_id=args.task, feature_id=args.feature_id, slice_id=args.slice_id)
    except SystemExit as exc:
        print(f"feature_workflow check: {exc}", file=sys.stderr)
        return 1
    fresh, design, registry = approval_is_fresh(root, args.feature_id)
    if not fresh:
        print("feature_workflow check: fresh approved design is required", file=sys.stderr)
        return 1
    slice_item = feature_design_lib.find_slice(design, args.slice_id)
    if slice_item is None:
        print(f"feature_workflow check: slice {args.slice_id} not found", file=sys.stderr)
        return 1
    start = read_start_artifact(root, args.feature_id, args.slice_id)
    if not start:
        print("feature_workflow check: slice must be started first", file=sys.stderr)
        return 1
    if start.get("execution_profile") == "audited_rounds":
        audited_ok, audited_problem = validate_audited_run_result(root, start)
        if not audited_ok:
            print(f"feature_workflow check: {audited_problem}", file=sys.stderr)
            return 1
    base_commit = str(start.get("base_commit", ""))
    scope = scope_findings(root, base_commit, slice_item, args.feature_id)
    verification = run_structured_verification(root, args.feature_id, args.slice_id, list(slice_item.get("verification", [])))
    maintainability = normalized_maintainability(root, args.task, args.feature_id)
    maintainability_path = slice_artifact_dir(root, args.feature_id, args.slice_id) / "maintainability.json"
    json_write(maintainability_path, maintainability)
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
    acceptable, pending, blocked_review, parsed_reviews = reports_acceptable(root, args.feature_id, review_policy["reviews"])
    review_policy["reviews"] = parsed_reviews
    write_required_reviews(root, args.feature_id, review_policy)
    deterministic_blocked = any(item.get("severity") == "stop_ship" for item in scope)
    required_structured = [
        item
        for item in verification
        if item.get("required") is True and item.get("status") in {"pass", "fail", "invalid"} and item.get("receipt")
    ]
    required_failed = any(item.get("required") is True and item.get("status") in {"fail", "invalid"} for item in verification)
    optional_failed = any(item.get("required") is False and item.get("status") in {"fail", "invalid"} for item in verification)
    zero_real_required = design.get("planning_depth") == "designed_slices" and not required_structured
    if deterministic_blocked:
        status = "blocked"
        next_slice_status = "blocked"
    elif required_failed or zero_real_required or maintainability.get("status") == "stop_ship":
        status = "verification_failed"
        next_slice_status = "verification_failed"
    elif blocked_review:
        status = "blocked"
        next_slice_status = "blocked"
    elif pending:
        status = "review_required"
        next_slice_status = "review_required"
    else:
        status = "review_passed"
        next_slice_status = "review_passed"
    manifest = post_state_manifest(root, args.feature_id, args.slice_id, base_commit)
    candidate = write_candidate_result(
        root=root,
        task_id=args.task,
        feature_id=args.feature_id,
        slice_id=args.slice_id,
        base_commit=base_commit,
        manifest=manifest,
        verification=verification,
        maintainability_ref=feature_design_lib.repo_rel(root, maintainability_path),
        reviews=parsed_reviews,
        status=status,
    )
    if status == "review_passed":
        advisories = advisory_verdicts(parsed_reviews)
        if design.get("risk_level") in {"high", "critical"} or advisories or optional_failed:
            status = "awaiting_human_acceptance"
            next_slice_status = "awaiting_human_acceptance"
        else:
            write_policy_auto_acceptance(
                root=root,
                task_id=args.task,
                feature_id=args.feature_id,
                slice_id=args.slice_id,
                candidate=candidate,
            )
            status = "accepted"
            next_slice_status = "accepted"
    update_slice(root, registry, design, args.slice_id, {"status": next_slice_status})
    result = {
        "schema_version": SLICE_RESULT_SCHEMA,
        "feature_id": args.feature_id,
        "slice_id": args.slice_id,
        "task_id": args.task,
        "base_commit": base_commit,
        "current_commit": git_commit(root),
        "changed_files": changed_files_since(root, base_commit),
        "scope_findings": scope,
        "verification": verification,
        "optional_verification_advisory": optional_failed,
        "zero_real_required_structured_checks": zero_real_required,
        "maintainability_status": maintainability.get("status"),
        "maintainability": maintainability,
        "required_reviews": parsed_reviews,
        "candidate_result": feature_design_lib.repo_rel(root, candidate_result_path(root, args.feature_id, args.slice_id)),
        "candidate_result_sha256": feature_design_lib.sha256_file(candidate_result_path(root, args.feature_id, args.slice_id)),
        "review_status": "accepted" if status in {"awaiting_human_acceptance", "accepted"} else "pending" if pending else "blocked" if not acceptable else "not_required",
        "status": status,
    }
    output = slice_artifact_dir(root, args.feature_id, args.slice_id) / "slice_result.json"
    json_write(output, result)
    print(f"feature_workflow check: status={status} result={output.relative_to(root)}")
    if status == "awaiting_human_acceptance":
        print("AWAITING_HUMAN_ACCEPTANCE")
    return 0 if status in {"awaiting_human_acceptance", "accepted"} else 1


def cmd_accept_slice(args: argparse.Namespace) -> int:
    root = args.root.resolve()
    if not sys.stdin.isatty():
        print("feature_workflow accept-slice: interactive TTY is required", file=sys.stderr)
        return 2
    try:
        candidate, problems = validate_candidate_fresh(root, args.feature_id, args.slice_id)
    except SystemExit as exc:
        print(f"feature_workflow accept-slice: {exc}", file=sys.stderr)
        return 1
    if problems:
        print("feature_workflow accept-slice: " + "; ".join(problems), file=sys.stderr)
        return 1
    manifest_ref = str(candidate.get("post_state_manifest_ref", ""))
    manifest_path = feature_design_lib.safe_repo_path(root, manifest_ref) if manifest_ref else None
    manifest = read_json(manifest_path) if manifest_path and manifest_path.exists() else {"files": []}
    print(f"Slice: {args.slice_id}")
    print(f"Base commit: {candidate.get('base_commit')}")
    print(f"Candidate commit at check: {candidate.get('candidate_commit')}")
    print(f"Current commit: {git_commit(root)}")
    print("Changed files:")
    for item in manifest.get("files", []):
        print(f"- {item.get('path')} {item.get('state')}")
    print("Verification:")
    for item in candidate.get("verification_refs", []):
        print(f"- {item.get('id')}: {item.get('status')} required={item.get('required')}")
    print("Reviews:")
    for item in candidate.get("review_records", []):
        print(f"- {item.get('role')}: {item.get('verdict')} {item.get('path')}")
    confirmation = input("Type exact slice ID to accept: ").strip()
    if confirmation != args.slice_id:
        print("feature_workflow accept-slice: slice ID confirmation mismatch", file=sys.stderr)
        return 1
    human = input("Human identity (example: human:artem): ").strip()
    advisory_ack = input("Advisory acknowledgement or 'none': ").strip()
    if advisory_ack.lower() == "none":
        advisory_ack = ""
    try:
        acceptance = accept_slice(
            root=root,
            task_id=args.task,
            feature_id=args.feature_id,
            slice_id=args.slice_id,
            accepted_by=human,
            advisory_acknowledgement=advisory_ack,
            acceptance_method="interactive_tty",
        )
    except SystemExit as exc:
        print(f"feature_workflow accept-slice: {exc}", file=sys.stderr)
        return 1
    print(f"feature_workflow accept-slice: accepted {args.slice_id} at {acceptance['accepted_commit']}")
    return 0


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
            elif all(isinstance(item, dict) and feature_design_lib.normalize_slice_status(item.get("status")) == "accepted" for item in design.get("slices", [])):
                state = "all_slices_accepted"
                next_action = "existing release resolver"
            else:
                state = "slice_blocked"
                next_action = "; ".join(reasons) if reasons else "inspect slice dependencies"
            required = read_required_reviews_projection(root, args.feature_id, "design")
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
    select_plan = sub.add_parser("select-plan")
    select_plan.add_argument("--task", required=True)
    draft = sub.add_parser("draft")
    draft.add_argument("--task", required=True)
    draft.add_argument("--feature-id", required=True)
    review = sub.add_parser("review")
    review.add_argument("--task", required=True)
    review.add_argument("--feature-id", required=True)
    review.add_argument("--slice-id", default="")
    review.add_argument("--role", default="auto")
    status = sub.add_parser("status")
    status.add_argument("--feature-id", required=True)
    approve = sub.add_parser("approve")
    approve.add_argument("--feature-id", required=True)
    next_cmd = sub.add_parser("next")
    next_cmd.add_argument("--feature-id", required=True)
    start = sub.add_parser("start")
    start.add_argument("--feature-id", required=True)
    start.add_argument("--slice-id", required=True)
    start.add_argument("--task", required=True)
    start.add_argument("--execution-profile", choices=("direct_codex", "audited_rounds"), default="direct_codex")
    start.add_argument("--allow-parallel", action="store_true")
    context = sub.add_parser("context")
    context.add_argument("--feature-id", required=True)
    context.add_argument("--slice-id", required=True)
    context.add_argument("--task", default="")
    check = sub.add_parser("check")
    check.add_argument("--task", required=True)
    check.add_argument("--feature-id", required=True)
    check.add_argument("--slice-id", required=True)
    accept = sub.add_parser("accept-slice")
    accept.add_argument("--task", required=True)
    accept.add_argument("--feature-id", required=True)
    accept.add_argument("--slice-id", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return {
        "plan": cmd_plan,
        "select-plan": cmd_select_plan,
        "draft": cmd_draft,
        "review": cmd_review,
        "status": cmd_status,
        "approve": cmd_approve,
        "next": cmd_next,
        "start": cmd_start,
        "context": cmd_context,
        "check": cmd_check,
        "accept-slice": cmd_accept_slice,
    }[args.command](args)


if __name__ == "__main__":
    raise SystemExit(main())
