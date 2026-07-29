#!/usr/bin/env python3
"""Deterministic AI Workflow Playbook validator.

The validator intentionally avoids LLMs and third-party dependencies. JSON
Schema files remain the versioned contract; this tool is the executable
consumer for the parts of the contract that the playbook itself needs in CI.
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    from jsonschema import Draft202012Validator
except ImportError:  # pragma: no cover - exercised by environments without dev deps.
    Draft202012Validator = None  # type: ignore[assignment]

try:
    import feature_design_lib
except ImportError:  # pragma: no cover - script execution path.
    from tools import feature_design_lib  # type: ignore


FIELD_RE = re.compile(r"^([A-Za-z][A-Za-z0-9_-]*):(?:\s*(.*))?$")
TASK_HEADING_RE = re.compile(r"^###\s+([A-Za-z][A-Za-z0-9._-]*):\s*(.+?)\s*$")
FENCE_RE = re.compile(r"^\s*(```|~~~)")
PLACEHOLDER_RE = re.compile(r"\{\{[^{}\n]+\}\}")
BACKTICK_RE = re.compile(r"`([^`]+)`")
PATH_LIKE_RE = re.compile(r"[/\\]|(?:\.(?:md|py|json|ya?ml|toml|txt|sh)$)")

FIELD_ALIASES = {
    "acceptance-criteria": "acceptance_criteria",
    "acceptance_criteria": "acceptance_criteria",
    "context-refs": "context_refs",
    "context_refs": "context_refs",
    "correction-budget": "correction_budget",
    "correction_budget": "correction_budget",
    "cost-budget": "cost_budget",
    "cost_budget": "cost_budget",
    "critic-required": "critic_required",
    "critic_required": "critic_required",
    "design-refs": "design_refs",
    "design_refs": "design_refs",
    "depends-on": "dependencies",
    "depends_on": "dependencies",
    "evidence": "evidence",
    "files": "files",
    "heavy-mode": "heavy_mode",
    "heavy_mode": "heavy_mode",
    "holdout-required": "holdout_required",
    "holdout_required": "holdout_required",
    "integration-points": "files",
    "integration_points": "files",
    "notes": "notes",
    "objective": "objective",
    "owner": "owner",
    "phase": "phase",
    "planning-depth": "planning_depth",
    "planning_depth": "planning_depth",
    "property-required": "property_required",
    "property_required": "property_required",
    "public-tests-required": "public_tests_required",
    "public_tests_required": "public_tests_required",
    "mutation-required": "mutation_required",
    "mutation_required": "mutation_required",
    "risk-level": "risk_level",
    "risk_level": "risk_level",
    "runtime-verification": "runtime_verification",
    "runtime_verification": "runtime_verification",
    "review-checkpoint": "review_checkpoint",
    "review_checkpoint": "review_checkpoint",
    "slice-id": "slice_id",
    "slice_id": "slice_id",
    "status": "status",
    "test": "test",
    "type": "type_tags",
    "user-touchpoint": "user_touchpoint",
    "user_touchpoint": "user_touchpoint",
    "verification": "verify",
    "verify": "verify",
    "visual-contract": "visual_contract",
    "visual_contract": "visual_contract",
    "change-budget": "change_budget",
    "change_budget": "change_budget",
    "maintainability-risk": "maintainability_risk",
    "maintainability_risk": "maintainability_risk",
}

TEST_GOVERNANCE_DEFAULTS = {
    "risk_level": "medium",
    "public_tests_required": "conditional",
    "critic_required": "conditional",
    "holdout_required": "conditional",
    "mutation_required": "conditional",
    "property_required": "conditional",
    "visual_contract": "optional",
}

GOVERNANCE_FIELD_KEYS = tuple(
    sorted(
        key
        for key, canonical in FIELD_ALIASES.items()
        if canonical in TEST_GOVERNANCE_DEFAULTS
    )
)

CONTROLLED_FIELD_KEYS = tuple(sorted(FIELD_ALIASES))

LIST_FIELDS = {
    "acceptance_criteria",
    "context_refs",
    "dependencies",
    "design_refs",
    "evidence",
    "files",
    "test",
    "type_tags",
    "verify",
}

PATH_SKIP_PARTS = {
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    "node_modules",
}

PLACEHOLDER_SKIP_DIRS = {
    "templates",
    "prompts",
    "examples",
    "domain_packs",
    "reference",
    "reports",
}

ACTIVE_PLACEHOLDER_FILES = {
    "README.md",
    "PLAYBOOK.md",
    ".github/workflows/playbook-checks.yml",
    "docs/tasks.md",
    "docs/architecture_layers.md",
    "docs/runtime_verification_protocol.md",
    "docs/agent_harness/HARNESS_EVALUATION_PROTOCOL.md",
    "docs/evaluation/PLAYBOOK_EMPIRICAL_VALIDATION.md",
}

IMPLEMENTATION_STARTED_STATUSES = {
    "in_progress",
    "review_pending",
    "implemented",
    "done",
    "done_pending_review",
    "completed",
    "release_candidate",
}

COMPLETED_STATUSES = {
    "done",
    "implemented",
    "completed",
    "release_candidate",
}


@dataclass
class Finding:
    severity: str
    path: str
    line: int
    check_id: str
    message: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "severity": self.severity,
            "path": self.path,
            "line": self.line,
            "check_id": self.check_id,
            "message": self.message,
        }


@dataclass
class TaskBlock:
    task_id: str
    title: str
    path: Path
    line: int
    phase_context: str = ""
    fields: dict[str, Any] = field(default_factory=dict)
    field_lines: dict[str, int] = field(default_factory=dict)
    parse_findings: list[tuple[int, str, str]] = field(default_factory=list)

    def to_record(self) -> dict[str, Any]:
        status = str(self.fields.get("status", "")).strip()
        verify = listify(self.fields.get("verify"))
        test = listify(self.fields.get("test"))
        evidence = listify(self.fields.get("evidence"))
        record: dict[str, Any] = {
            "schema_version": "playbook.task.v1",
            "task_id": self.task_id,
            "title": self.title,
            "owner": str(self.fields.get("owner", "")).strip(),
            "phase": str(self.fields.get("phase") or self.phase_context).strip(),
            "status": status,
            "type_tags": split_tags(self.fields.get("type_tags")),
            "dependencies": parse_dependencies(self.fields.get("dependencies")),
            "objective": str(self.fields.get("objective", "")).strip(),
            "acceptance_criteria": listify(self.fields.get("acceptance_criteria")),
            "files": listify(self.fields.get("files")),
            "context_refs": listify(self.fields.get("context_refs")),
            "heavy_mode": normalize_heavy_mode(self.fields.get("heavy_mode")),
            "runtime_verification": normalize_runtime_verification(
                self.fields.get("runtime_verification")
            ),
            "planning_depth": normalize_planning_depth(self.fields.get("planning_depth")),
            "planning_depth_source": "declared"
            if self.fields.get("planning_depth") not in (None, "")
            else "legacy_default",
            "design_refs": listify(self.fields.get("design_refs")),
        }
        for optional_string in (
            "slice_id",
            "user_touchpoint",
            "review_checkpoint",
            "change_budget",
            "maintainability_risk",
        ):
            value = self.fields.get(optional_string)
            if value not in (None, ""):
                record[optional_string] = str(value).strip().lower().replace("-", "_") if optional_string == "maintainability_risk" else str(value).strip()
        for field_name, default in TEST_GOVERNANCE_DEFAULTS.items():
            record[field_name] = normalize_governance_value(
                self.fields.get(field_name), default
            )
        if verify:
            record["verify"] = verify
        elif status.startswith("done") and evidence:
            # Historical framework tasks used Evidence before the executable
            # schema existed. Keep them valid while new tasks use Verification.
            record["verify"] = evidence
        if test:
            record["test"] = test
        correction_budget = self.fields.get("correction_budget")
        if correction_budget not in (None, ""):
            try:
                record["correction_budget"] = int(str(correction_budget).strip())
            except ValueError:
                record["correction_budget"] = correction_budget
        cost_budget = self.fields.get("cost_budget")
        if cost_budget not in (None, ""):
            record["cost_budget"] = str(cost_budget).strip()
        return record


def relative(root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def canonical_field(raw: str) -> str | None:
    return FIELD_ALIASES.get(raw.strip().lower().replace(" ", "-"))


def governance_field_suggestion(raw: str) -> str | None:
    normalized = raw.strip().lower().replace(" ", "-")
    matches = difflib.get_close_matches(
        normalized,
        GOVERNANCE_FIELD_KEYS,
        n=1,
        cutoff=0.8,
    )
    return matches[0] if matches else None


def controlled_field_suggestion(raw: str) -> str | None:
    normalized = raw.strip().lower().replace(" ", "-")
    matches = difflib.get_close_matches(
        normalized,
        CONTROLLED_FIELD_KEYS,
        n=1,
        cutoff=0.8,
    )
    return matches[0] if matches else None


def listify(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    if not text or text.lower() in {"none", "n/a", "not applicable"}:
        return []
    return [text]


def split_tags(value: Any) -> list[str]:
    values = listify(value)
    tags: list[str] = []
    for item in values:
        tags.extend(part.strip() for part in re.split(r"[, ]+", item) if part.strip())
    return tags


def parse_dependencies(value: Any) -> list[str]:
    deps: list[str] = []
    for item in listify(value):
        if item.strip().lower() in {"none", "n/a", "no", "-"}:
            continue
        deps.extend(part.strip() for part in re.split(r"[, ]+", item) if part.strip())
    return deps


def normalize_heavy_mode(value: Any) -> str:
    raw = str(value or "").strip().lower().replace("-", "_")
    if raw in {"required", "yes", "true"}:
        return "required"
    if raw in {"optional", "conditional"}:
        return "optional"
    return "none"


def normalize_runtime_verification(value: Any) -> str:
    raw = str(value or "").strip().lower().replace("-", "_")
    if raw in {"required", "yes", "true"}:
        return "required"
    if raw in {"not_required", "none", "no", "false"}:
        return "not_required"
    return "conditional"


def normalize_planning_depth(value: Any) -> str:
    raw = str(value or "").strip().lower().replace("-", "_")
    if raw in {"compact", "compactdesign", "compact_design"}:
        return "compact_design"
    if raw in {"designed", "designed_slice", "designed_slices", "sliced", "vertical_slices"}:
        return "designed_slices"
    if raw in {"oneshot", "one_shot", "none", "not_required", ""}:
        return "oneshot"
    return raw or "oneshot"


def normalize_governance_value(value: Any, default: str) -> str:
    raw = (
        str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    )
    return raw or default


def parse_list_item(line: str) -> str | None:
    stripped = line.strip()
    if stripped.startswith("- "):
        return stripped[2:].strip()
    return None


def parse_task_blocks(path: Path) -> list[TaskBlock]:
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    tasks: list[TaskBlock] = []
    current: TaskBlock | None = None
    current_phase = ""
    active_field: str | None = None
    multiline_field: str | None = None
    multiline_indent: int | None = None

    for line_no, line in enumerate(lines, 1):
        if line.startswith("## Phase "):
            current_phase = line[3:].strip()
            active_field = None
            multiline_field = None
            multiline_indent = None
            continue
        heading = TASK_HEADING_RE.match(line)
        if heading:
            current = TaskBlock(
                task_id=heading.group(1).strip(),
                title=heading.group(2).strip(),
                path=path,
                line=line_no,
                phase_context=current_phase,
            )
            tasks.append(current)
            active_field = None
            multiline_field = None
            multiline_indent = None
            continue
        if current is None:
            continue
        if line.startswith("## "):
            active_field = None
            multiline_field = None
            multiline_indent = None
            continue
        field_match = FIELD_RE.match(line.strip())
        if field_match:
            raw_field_name = field_match.group(1)
            field_name = canonical_field(raw_field_name)
            if field_name is None:
                governance_suggestion = governance_field_suggestion(raw_field_name)
                suggestion = governance_suggestion or controlled_field_suggestion(raw_field_name)
                if suggestion is not None:
                    current.parse_findings.append(
                        (
                            line_no,
                            "TASK_GOVERNANCE_FIELD_UNKNOWN"
                            if governance_suggestion
                            else "TASK_CONTROLLED_FIELD_UNKNOWN",
                            f"task {current.task_id} has unknown "
                            f"{'governance' if governance_suggestion else 'controlled'} field "
                            f"{raw_field_name}; did you mean {suggestion}?",
                        )
                    )
                active_field = None
                multiline_field = None
                multiline_indent = None
                continue
            if field_name in current.fields:
                current.parse_findings.append(
                    (
                        line_no,
                        "TASK_FIELD_DUPLICATE",
                        f"task {current.task_id} repeats field {raw_field_name}; "
                        f"first declaration is line {current.field_lines[field_name]}",
                    )
                )
                active_field = None
                multiline_field = None
                multiline_indent = None
                continue
            raw_value = (field_match.group(2) or "").rstrip()
            current.field_lines.setdefault(field_name, line_no)
            if raw_value == "|":
                current.fields[field_name] = ""
                active_field = field_name
                multiline_field = field_name
                multiline_indent = None
            elif field_name in LIST_FIELDS:
                current.fields[field_name] = listify(raw_value)
                active_field = field_name
                multiline_field = None
                multiline_indent = None
            else:
                current.fields[field_name] = raw_value.strip()
                active_field = field_name
                multiline_field = None
                multiline_indent = None
            continue
        if multiline_field is not None:
            if not line.strip():
                current.fields[multiline_field] = (
                    str(current.fields.get(multiline_field, "")) + "\n"
                )
                continue
            indent = len(line) - len(line.lstrip(" "))
            if multiline_indent is None:
                multiline_indent = indent
            trimmed = line[multiline_indent:] if len(line) >= multiline_indent else line.strip()
            current.fields[multiline_field] = (
                str(current.fields.get(multiline_field, "")) + trimmed.rstrip() + "\n"
            )
            continue
        if active_field in LIST_FIELDS:
            item = parse_list_item(line)
            if item is not None:
                current.fields.setdefault(active_field, [])
                current.fields[active_field].append(item)
                continue
            if active_field and line.startswith("    ") and current.fields.get(active_field):
                current.fields[active_field][-1] = (
                    current.fields[active_field][-1] + " " + line.strip()
                ).strip()

    return tasks


def validate_task_record(task: TaskBlock, root: Path, schema_validator: Any | None = None) -> list[Finding]:
    findings = [
        Finding(
            "error",
            relative(root, task.path),
            line,
            check_id,
            message,
        )
        for line, check_id, message in task.parse_findings
    ]
    record = task.to_record()
    if not record.get("verify") and not record.get("test"):
        findings.append(
            Finding(
                "error",
                relative(root, task.path),
                task.line,
                "TASK_VERIFIER_REQUIRED",
                f"task {task.task_id} must declare Verification/Verify or Test",
            )
        )
    if record.get("change_budget") and not feature_design_lib.validate_change_budget(record.get("change_budget")):
        findings.append(
            Finding(
                "error",
                relative(root, task.path),
                task.field_lines.get("change_budget", task.line),
                "TASK_CHANGE_BUDGET_INVALID",
                f"task {task.task_id} Change-Budget must use entries like files<=4, lines<=200",
            )
        )
    if schema_validator is not None:
        for error in sorted(schema_validator.iter_errors(record), key=lambda item: list(item.path)):
            field_path = ".".join(str(part) for part in error.path)
            field_name = field_path.split(".", 1)[0] if field_path else ""
            findings.append(
                Finding(
                    "error",
                    relative(root, task.path),
                    task.field_lines.get(field_name, task.line),
                    "TASK_SCHEMA",
                    f"task {task.task_id} schema violation"
                    + (f" at {field_path}" if field_path else "")
                    + f": {error.message}",
                )
            )
        return findings
    findings.append(
        Finding(
            "error",
            relative(root, task.path),
            task.line,
            "SCHEMA_VALIDATOR_MISSING",
            "jsonschema is required to validate task.schema.json",
        )
    )
    return findings

def validate_dependency_graph(tasks: list[TaskBlock], root: Path) -> list[Finding]:
    findings: list[Finding] = []
    by_id = {task.task_id: task for task in tasks}
    graph = {task.task_id: task.to_record().get("dependencies", []) for task in tasks}
    for task_id, deps in graph.items():
        for dep in deps:
            if dep not in by_id:
                task = by_id[task_id]
                findings.append(
                    Finding(
                        "error",
                        relative(root, task.path),
                        task.field_lines.get("dependencies", task.line),
                        "TASK_UNKNOWN_DEPENDENCY",
                        f"task {task_id} depends on unknown task {dep}",
                    )
                )

    visiting: set[str] = set()
    visited: set[str] = set()

    def walk(task_id: str, stack: list[str]) -> None:
        if task_id in visiting:
            cycle = stack[stack.index(task_id) :] + [task_id]
            task = by_id[task_id]
            findings.append(
                Finding(
                    "error",
                    relative(root, task.path),
                    task.field_lines.get("dependencies", task.line),
                    "TASK_CYCLIC_DEPENDENCY",
                    "cyclic dependency: " + " -> ".join(cycle),
                )
            )
            return
        if task_id in visited or task_id not in graph:
            return
        visiting.add(task_id)
        for dep in graph[task_id]:
            walk(dep, stack + [dep])
        visiting.remove(task_id)
        visited.add(task_id)

    for task_id in graph:
        walk(task_id, [task_id])
    return findings


def looks_like_path(value: str) -> bool:
    value = value.strip().split("#", 1)[0].split("::", 1)[0].rstrip("/")
    if not value or value.startswith(("http://", "https://")):
        return False
    if value.startswith("{{") and value.endswith("}}"):
        return False
    return bool(PATH_LIKE_RE.search(value)) or value in {"README.md", "PLAYBOOK.md"}


def referenced_paths(value: str) -> list[str]:
    refs = [match.group(1).strip() for match in BACKTICK_RE.finditer(value)]
    if not refs and looks_like_path(value):
        refs.append(value.strip())
    return [ref.split("#", 1)[0].split("::", 1)[0].rstrip("/") for ref in refs]


def backticked_path_refs(value: str) -> list[str]:
    refs: list[str] = []
    for match in BACKTICK_RE.finditer(value):
        raw = match.group(1).strip()
        if " " in raw:
            continue
        if looks_like_path(raw):
            refs.append(raw.split("#", 1)[0].split("::", 1)[0].rstrip("/"))
    return refs


def validate_context_refs(tasks: list[TaskBlock], root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for task in tasks:
        for ref in task.to_record().get("context_refs", []):
            for path_text in referenced_paths(ref):
                if looks_like_path(path_text) and not (root / path_text).exists():
                    findings.append(
                        Finding(
                            "error",
                            relative(root, task.path),
                            task.field_lines.get("context_refs", task.line),
                            "REFERENCE_MISSING_CONTEXT",
                            f"task {task.task_id} Context-Refs path missing: {path_text}",
                        )
                    )
    return findings


def task_status_key(record: dict[str, Any]) -> str:
    return str(record.get("status", "")).strip().lower().replace("-", "_").replace(" ", "_")


def is_completed_status(record: dict[str, Any]) -> bool:
    status = task_status_key(record)
    return status in COMPLETED_STATUSES or status.startswith("done")


def is_implementation_started(record: dict[str, Any]) -> bool:
    status = task_status_key(record)
    return status in IMPLEMENTATION_STARTED_STATUSES or status.startswith("done")


def design_registry_path(root: Path, ref: str) -> tuple[Path | None, str]:
    refs = referenced_paths(ref)
    raw = refs[0] if refs else ref
    path = feature_design_lib.safe_repo_path(root, raw)
    return path, raw.strip().strip("`")


def design_finding_to_task_finding(root: Path, finding: feature_design_lib.DesignFinding) -> Finding:
    return Finding(finding.severity, finding.path, finding.line, finding.check_id, finding.message)


def review_checkpoint_closed(root: Path, value: str) -> bool:
    raw = value.strip().strip("`")
    normalized = raw.lower().replace("-", "_").replace(" ", "_")
    if normalized in {"closed", "complete", "completed", "passed", "review_closed"}:
        return True
    path = feature_design_lib.safe_repo_path(root, raw)
    if path and path.is_file():
        text = path.read_text(encoding="utf-8", errors="replace")
        return any(
            marker in text
            for marker in (
                "SLICE_REVIEW: PASS",
                "PROGRAM_DESIGN_REVIEW: PASS",
                "MAINTAINABILITY_REVIEW: PASS",
                "TEST_CRITIC_RESULT: NO_FINDING",
                "PRIVACY_REVIEW_RESULT: PASS",
            )
        )
    return False


def has_real_verification_evidence(record: dict[str, Any]) -> bool:
    commands = listify(record.get("verify")) + listify(record.get("test"))
    if not commands:
        return False
    weak = {"manual review", "manual", "tbd", "todo", "unknown", "n/a"}
    for command in commands:
        raw = command.strip().strip("`").lower()
        if raw in weak:
            return False
        if any(token in raw for token in ("python", "pytest", "tools/", "git ", "npm ", "pnpm ", "uv ", "make ", "harness", "verify")):
            return True
    return False


def validate_task_design_requirements(tasks: list[TaskBlock], root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for task in tasks:
        record = task.to_record()
        depth = record.get("planning_depth", "oneshot")
        if depth == "oneshot":
            continue
        design_refs = record.get("design_refs", [])
        if not design_refs:
            findings.append(
                Finding(
                    "error",
                    relative(root, task.path),
                    task.field_lines.get("design_refs", task.line),
                    "TASK_DESIGN_REF_REQUIRED",
                    f"task {task.task_id} with Planning-Depth {depth} requires Design-Refs",
                )
            )
            continue
        loaded_designs: list[dict[str, Any]] = []
        approved_designs: list[dict[str, Any]] = []
        for ref in design_refs:
            registry_path, raw = design_registry_path(root, ref)
            if registry_path is None:
                findings.append(
                    Finding(
                        "error",
                        relative(root, task.path),
                        task.field_lines.get("design_refs", task.line),
                        "TASK_DESIGN_REF_UNSAFE",
                        f"task {task.task_id} Design-Ref must stay inside repository: {raw}",
                    )
                )
                continue
            if not registry_path.exists():
                findings.append(
                    Finding(
                        "error",
                        relative(root, task.path),
                        task.field_lines.get("design_refs", task.line),
                        "TASK_DESIGN_REF_MISSING",
                        f"task {task.task_id} Design-Ref missing: {raw}",
                    )
                )
                continue
            design_findings, design = feature_design_lib.validate_design_file(root, registry_path)
            findings.extend(design_finding_to_task_finding(root, finding) for finding in design_findings)
            if design is None:
                continue
            loaded_designs.append(design)
            if feature_design_lib.design_is_approved(design, root, registry_path):
                approved_designs.append(design)
        if not loaded_designs:
            continue
        if not approved_designs:
            findings.append(
                Finding(
                    "error",
                    relative(root, task.path),
                    task.field_lines.get("design_refs", task.line),
                    "TASK_DESIGN_APPROVAL_REQUIRED",
                    f"task {task.task_id} requires an approved design before implementation",
                )
            )
            continue
        design = approved_designs[0]
        if depth == "designed_slices":
            slice_id = str(record.get("slice_id", "")).strip()
            if not slice_id:
                findings.append(
                    Finding(
                        "error",
                        relative(root, task.path),
                        task.field_lines.get("slice_id", task.line),
                        "TASK_SLICE_ID_REQUIRED",
                        f"task {task.task_id} with designed_slices requires Slice-ID",
                    )
                )
                continue
            slice_item = feature_design_lib.find_slice(design, slice_id)
            if slice_item is None:
                findings.append(
                    Finding(
                        "error",
                        relative(root, task.path),
                        task.field_lines.get("slice_id", task.line),
                        "TASK_SLICE_MISSING",
                        f"task {task.task_id} references missing slice {slice_id}",
                    )
                )
                continue
            for required_field, check_id in (
                ("user_touchpoint", "TASK_USER_TOUCHPOINT_REQUIRED"),
                ("review_checkpoint", "TASK_REVIEW_CHECKPOINT_REQUIRED"),
                ("change_budget", "TASK_CHANGE_BUDGET_REQUIRED"),
            ):
                if not record.get(required_field):
                    findings.append(
                        Finding(
                            "error",
                            relative(root, task.path),
                            task.field_lines.get(required_field, task.line),
                            check_id,
                            f"task {task.task_id} with designed_slices requires {required_field}",
                        )
                    )
            missing_deps = feature_design_lib.slice_dependencies_satisfied(design, slice_item)
            for dep in missing_deps:
                findings.append(
                    Finding(
                        "error",
                        relative(root, task.path),
                        task.field_lines.get("slice_id", task.line),
                        "TASK_SLICE_DEPENDENCY_UNSATISFIED",
                        f"task {task.task_id} slice {slice_id} dependency {dep} is not implemented/reviewed",
                    )
                )
            outside_allowed, forbidden_hits = feature_design_lib.task_files_within_slice(
                listify(record.get("files")),
                slice_item,
            )
            for path in outside_allowed:
                findings.append(
                    Finding(
                        "error",
                        relative(root, task.path),
                        task.field_lines.get("files", task.line),
                        "TASK_SLICE_SCOPE_MISMATCH",
                        f"task {task.task_id} file outside slice allowed files: {path}",
                    )
                )
            for path in forbidden_hits:
                findings.append(
                    Finding(
                        "error",
                        relative(root, task.path),
                        task.field_lines.get("files", task.line),
                        "TASK_SLICE_FORBIDDEN_FILE",
                        f"task {task.task_id} file is forbidden by slice {slice_id}: {path}",
                    )
                )
        if is_completed_status(record):
            if not feature_design_lib.design_is_approved(design, root, registry_path):
                findings.append(
                    Finding(
                        "error",
                        relative(root, task.path),
                        task.field_lines.get("design_refs", task.line),
                        "TASK_COMPLETED_DESIGN_NOT_APPROVED",
                        f"completed task {task.task_id} cannot reference an unapproved design",
                    )
                )
            checkpoint = str(record.get("review_checkpoint", "")).strip()
            if checkpoint and not review_checkpoint_closed(root, checkpoint):
                findings.append(
                    Finding(
                        "error",
                        relative(root, task.path),
                        task.field_lines.get("review_checkpoint", task.line),
                        "TASK_REVIEW_CHECKPOINT_OPEN",
                        f"completed task {task.task_id} required review checkpoint is not closed",
                    )
                )
            if not has_real_verification_evidence(record):
                findings.append(
                    Finding(
                        "error",
                        relative(root, task.path),
                        task.field_lines.get("verify", task.line),
                        "TASK_COMPLETED_VERIFICATION_WEAK",
                        f"completed task {task.task_id} requires concrete verification evidence",
                    )
                )
    return findings


def validate_tasks(root: Path) -> tuple[list[Finding], list[dict[str, Any]]]:
    tasks_path = root / "docs" / "tasks.md"
    if not tasks_path.exists():
        return [
            Finding(
                "error",
                "docs/tasks.md",
                1,
                "TASK_FILE_MISSING",
                "docs/tasks.md is required",
            )
        ], []
    tasks = parse_task_blocks(tasks_path)
    findings: list[Finding] = []
    if not tasks:
        findings.append(
            Finding("error", "docs/tasks.md", 1, "TASK_NONE_FOUND", "no task blocks found")
        )
    schema_validator = task_schema_validator(root)
    for task in tasks:
        findings.extend(validate_task_record(task, root, schema_validator))
    findings.extend(validate_dependency_graph(tasks, root))
    findings.extend(validate_context_refs(tasks, root))
    findings.extend(validate_task_design_requirements(tasks, root))
    return findings, [task.to_record() for task in tasks]


def task_schema_validator(root: Path) -> Any | None:
    if Draft202012Validator is None:
        return None
    schema_path = root / "schemas" / "task.schema.json"
    if not schema_path.exists():
        schema_path = Path(__file__).resolve().parents[1] / "schemas" / "task.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    return Draft202012Validator(schema)


def should_skip_path(path: Path) -> bool:
    return any(part in PATH_SKIP_PARTS for part in path.parts)


def active_placeholder_paths(root: Path) -> list[Path]:
    paths: list[Path] = []
    for rel in ACTIVE_PLACEHOLDER_FILES:
        path = root / rel
        if path.exists():
            paths.append(path)
    for path in sorted((root / "docs").rglob("*.md")) if (root / "docs").exists() else []:
        rel_parts = set(path.relative_to(root).parts)
        if rel_parts & PLACEHOLDER_SKIP_DIRS:
            continue
        if path not in paths:
            paths.append(path)
    return paths


def validate_placeholders(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for path in active_placeholder_paths(root):
        if should_skip_path(path):
            continue
        in_fence = False
        for line_no, line in enumerate(
            path.read_text(encoding="utf-8", errors="replace").splitlines(),
            1,
        ):
            if FENCE_RE.match(line):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            if "placeholder" in line.lower() or "replace `" in line.lower():
                continue
            for match in PLACEHOLDER_RE.finditer(line):
                findings.append(
                    Finding(
                        "error",
                        relative(root, path),
                        line_no,
                        "PLACEHOLDER_UNRESOLVED",
                        f"unresolved placeholder {match.group(0)}",
                    )
                )
    return findings


def active_scaffold_placeholder_findings(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for path in active_placeholder_paths(root):
        if should_skip_path(path):
            continue
        for line_no, line in enumerate(
            path.read_text(encoding="utf-8", errors="replace").splitlines(),
            1,
        ):
            if "scaffold placeholder" in line.lower():
                findings.append(
                    Finding(
                        "error",
                        relative(root, path),
                        line_no,
                        "READINESS_SCAFFOLD_PLACEHOLDER_ACTIVE",
                        "scaffold placeholder remains in an active artifact",
                    )
                )
    return findings


def validate_readiness(root: Path) -> list[Finding]:
    path = root / ".playbook/readiness_state.json"
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [
            Finding(
                "error",
                ".playbook/readiness_state.json",
                1,
                "READINESS_JSON_INVALID",
                f"readiness state is invalid JSON: {exc}",
            )
        ]
    schema_path = root / "schemas/readiness_state.schema.json"
    if schema_path.exists() and Draft202012Validator is not None:
        validator = Draft202012Validator(json.loads(schema_path.read_text(encoding="utf-8")))
        errors = sorted(validator.iter_errors(data), key=lambda error: list(error.path))
        if errors:
            return [
                Finding(
                    "error",
                    ".playbook/readiness_state.json",
                    1,
                    "READINESS_SCHEMA_INVALID",
                    f"readiness state schema violation: {error.message}",
                )
                for error in errors
            ]
    state = data.get("state")
    if state in {"implementation_ready", "release_candidate", "release_ready"} and data.get(
        "implementation_ready_requires_no_scaffold_placeholders", True
    ):
        findings = active_scaffold_placeholder_findings(root)
    else:
        findings = []
    planning_depth = data.get("planning_depth", "oneshot")
    if state in {"implementation_ready", "release_candidate", "release_ready"} and planning_depth in {"compact_design", "designed_slices"}:
        refs = data.get("required_design_refs", [])
        if not isinstance(refs, list) or not refs:
            findings.append(
                Finding(
                    "error",
                    ".playbook/readiness_state.json",
                    1,
                    "READINESS_DESIGN_REF_REQUIRED",
                    "implementation_ready requires required_design_refs when planning depth requires design",
                )
            )
            return findings
        approved = False
        for ref in refs:
            if not isinstance(ref, str):
                continue
            design_path = feature_design_lib.safe_repo_path(root, ref)
            if design_path is None:
                findings.append(
                    Finding(
                        "error",
                        ".playbook/readiness_state.json",
                        1,
                        "READINESS_DESIGN_REF_UNSAFE",
                        f"required design ref must stay inside repository: {ref}",
                    )
                )
                continue
            design_findings, design = feature_design_lib.validate_design_file(root, design_path)
            findings.extend(design_finding_to_task_finding(root, finding) for finding in design_findings)
            if feature_design_lib.design_is_approved(design, root, design_path):
                approved = True
        if not approved:
            findings.append(
                Finding(
                    "error",
                    ".playbook/readiness_state.json",
                    1,
                    "READINESS_DESIGN_APPROVAL_REQUIRED",
                    "implementation_ready requires an approved feature design",
                )
            )
    return findings


def git_text(root: Path, args: list[str]) -> tuple[int, str]:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return result.returncode, result.stdout.strip()


def current_commit(root: Path) -> str:
    code, stdout = git_text(root, ["rev-parse", "HEAD"])
    return stdout if code == 0 and stdout else "not-a-git-repository"


def current_dirty_state(root: Path) -> list[str]:
    code, stdout = git_text(root, ["status", "--short"])
    if code != 0:
        return []
    if not stdout:
        return []
    return [
        line
        for line in stdout.splitlines()
        if ".playbook-artifacts/" not in line and not line.endswith(".playbook-artifacts")
    ]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def artifact_ref_findings(root: Path, ref: Any, ref_label: str) -> list[Finding]:
    findings: list[Finding] = []
    if not isinstance(ref, dict):
        return [
            Finding(
                "error",
                ".playbook-artifacts/project_verification.json",
                1,
                "READINESS_RELEASE_ARTIFACT_REF_INVALID",
                f"{ref_label} must be an artifact ref object",
            )
        ]
    raw_path = ref.get("path")
    expected_hash = ref.get("sha256")
    if not isinstance(raw_path, str) or not raw_path:
        findings.append(
            Finding(
                "error",
                ".playbook-artifacts/project_verification.json",
                1,
                "READINESS_RELEASE_ARTIFACT_REF_INVALID",
                f"{ref_label} path is missing",
            )
        )
        return findings
    path = Path(raw_path)
    if path.is_absolute() or ".." in path.parts:
        findings.append(
            Finding(
                "error",
                ".playbook-artifacts/project_verification.json",
                1,
                "READINESS_RELEASE_ARTIFACT_REF_INVALID",
                f"{ref_label} path must stay inside the project root",
            )
        )
        return findings
    resolved = (root / path).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError:
        findings.append(
            Finding(
                "error",
                ".playbook-artifacts/project_verification.json",
                1,
                "READINESS_RELEASE_ARTIFACT_REF_INVALID",
                f"{ref_label} path escapes the project root",
            )
        )
        return findings
    if not resolved.is_file():
        findings.append(
            Finding(
                "error",
                raw_path,
                1,
                "READINESS_RELEASE_ARTIFACT_REF_MISSING",
                f"{ref_label} artifact is missing",
            )
        )
        return findings
    if not isinstance(expected_hash, str) or not re.fullmatch(r"[a-f0-9]{64}", expected_hash):
        findings.append(
            Finding(
                "error",
                ".playbook-artifacts/project_verification.json",
                1,
                "READINESS_RELEASE_ARTIFACT_HASH_INVALID",
                f"{ref_label} sha256 is invalid",
            )
        )
        return findings
    actual_hash = sha256_file(resolved)
    if actual_hash != expected_hash:
        findings.append(
            Finding(
                "error",
                raw_path,
                1,
                "READINESS_RELEASE_ARTIFACT_HASH_MISMATCH",
                f"{ref_label} artifact hash does not match project verification result",
            )
        )
    return findings


def validate_release_verification(root: Path) -> list[Finding]:
    result_path = root / ".playbook-artifacts/project_verification.json"
    if not result_path.is_file():
        return [
            Finding(
                "error",
                ".playbook-artifacts/project_verification.json",
                1,
                "READINESS_RELEASE_VERIFICATION_MISSING",
                "release_ready requires current project verification result",
            )
        ]
    try:
        result = json.loads(result_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [
            Finding(
                "error",
                ".playbook-artifacts/project_verification.json",
                exc.lineno,
                "READINESS_RELEASE_VERIFICATION_INVALID",
                f"project verification result is invalid JSON: {exc.msg}",
            )
        ]
    findings: list[Finding] = []
    schema_path = root / "schemas/project_verification_result.schema.json"
    if not schema_path.is_file():
        findings.append(
            Finding(
                "error",
                "schemas/project_verification_result.schema.json",
                1,
                "READINESS_RELEASE_RESULT_SCHEMA_MISSING",
                "release readiness requires project verification result schema",
            )
        )
    elif Draft202012Validator is None:
        findings.append(
            Finding(
                "error",
                "schemas/project_verification_result.schema.json",
                1,
                "READINESS_RELEASE_SCHEMA_VALIDATOR_UNAVAILABLE",
                "release readiness requires jsonschema Draft202012Validator",
            )
        )
    else:
        try:
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            findings.append(
                Finding(
                    "error",
                    "schemas/project_verification_result.schema.json",
                    exc.lineno,
                    "READINESS_RELEASE_RESULT_SCHEMA_INVALID",
                    f"project verification result schema is invalid JSON: {exc.msg}",
                )
            )
        else:
            validator = Draft202012Validator(schema)
            for error in sorted(validator.iter_errors(result), key=lambda item: list(item.path)):
                findings.append(
                    Finding(
                        "error",
                        ".playbook-artifacts/project_verification.json",
                        1,
                        "READINESS_RELEASE_VERIFICATION_SCHEMA",
                        f"project verification result schema violation: {error.message}",
                    )
                )
    if result.get("schema_version") != "playbook.project_verification_result.v1":
        findings.append(
            Finding(
                "error",
                ".playbook-artifacts/project_verification.json",
                1,
                "READINESS_RELEASE_VERIFICATION_SCHEMA",
                "project verification result has unsupported schema_version",
            )
        )
    configuration_errors = result.get("configuration_errors")
    if configuration_errors:
        findings.append(
            Finding(
                "error",
                ".playbook-artifacts/project_verification.json",
                1,
                "READINESS_RELEASE_CONFIGURATION_ERRORS",
                "release_ready requires empty project verification configuration_errors",
            )
        )
    checks = result.get("checks")
    missing_project_check_reported = False
    if not isinstance(checks, list) or not checks:
        checks = []
        missing_project_check_reported = True
        findings.append(
            Finding(
                "error",
                ".playbook-artifacts/project_verification.json",
                1,
                "READINESS_RELEASE_PROJECT_CHECK_MISSING",
                "release_ready requires at least one executed non-contract project verification check",
            )
        )
    recomputed_required_failures = 0
    executed_project_checks = 0
    for check in checks:
        if not isinstance(check, dict):
            continue
        required = check.get("required") is True
        passed = check.get("passed") is True
        skipped = check.get("skipped") is True
        if required and not passed:
            recomputed_required_failures += 1
        if required and skipped:
            findings.append(
                Finding(
                    "error",
                    ".playbook-artifacts/project_verification.json",
                    1,
                    "READINESS_RELEASE_REQUIRED_CHECK_SKIPPED",
                    f"required project verification check {check.get('id', '<unknown>')} was skipped",
                )
            )
        if required and check.get("id") != "playbook_contract" and not skipped and check.get("exit_code") is not None:
            executed_project_checks += 1
        findings.extend(artifact_ref_findings(root, check.get("stdout_ref"), f"{check.get('id', '<unknown>')}.stdout_ref"))
        findings.extend(artifact_ref_findings(root, check.get("stderr_ref"), f"{check.get('id', '<unknown>')}.stderr_ref"))
    if executed_project_checks == 0 and not missing_project_check_reported:
        findings.append(
            Finding(
                "error",
                ".playbook-artifacts/project_verification.json",
                1,
                "READINESS_RELEASE_PROJECT_CHECK_MISSING",
                "release_ready requires at least one executed non-contract project verification check",
            )
        )
    if result.get("required_failures") != recomputed_required_failures:
        findings.append(
            Finding(
                "error",
                ".playbook-artifacts/project_verification.json",
                1,
                "READINESS_RELEASE_FAILURE_COUNT_MISMATCH",
                "project verification required_failures does not match required check results",
            )
        )
    if result.get("required_failures") != 0:
        findings.append(
            Finding(
                "error",
                ".playbook-artifacts/project_verification.json",
                1,
                "READINESS_RELEASE_VERIFICATION_FAILED",
                "release_ready requires project verification required_failures=0",
            )
        )
    expected_commit = current_commit(root)
    if expected_commit == "not-a-git-repository":
        findings.append(
            Finding(
                "error",
                ".",
                1,
                "READINESS_RELEASE_GIT_REQUIRED",
                "release_ready exact-HEAD claims require a Git repository",
            )
        )
    elif result.get("project_commit") != expected_commit:
        findings.append(
            Finding(
                "error",
                ".playbook-artifacts/project_verification.json",
                1,
                "READINESS_RELEASE_VERIFICATION_STALE",
                "project verification result project_commit does not match current HEAD",
            )
        )
    dirty = current_dirty_state(root)
    if dirty:
        findings.append(
            Finding(
                "error",
                ".",
                1,
                "READINESS_RELEASE_DIRTY_STATE",
                "release_ready requires a clean Git working tree after verification",
            )
        )
    return findings


def valid_project_verifier_argv(value: Any) -> bool:
    if not isinstance(value, list) or len(value) < 2:
        return False
    if not all(isinstance(item, str) and item for item in value):
        return False
    python_tokens = {"{python}", "python", "python3", "python.exe", "python3.exe"}
    for index, item in enumerate(value):
        if item != "tools/verify_project.py" or index == 0:
            continue
        runner = Path(value[index - 1]).name
        if value[index - 1] in python_tokens or runner in python_tokens:
            return "--root" in value
    return False


def validate_delivery(root: Path) -> list[Finding]:
    path = root / ".playbook/delivery_execution_model.json"
    if not path.exists():
        if (root / ".playbook/readiness_state.json").exists() or (root / ".playbook/project_verification.json").exists():
            return [
                Finding(
                    "error",
                    ".playbook/delivery_execution_model.json",
                    1,
                    "DELIVERY_CONTRACT_MISSING",
                    "generated Playbook projects must include delivery_execution_model.json",
                )
            ]
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [
            Finding(
                "error",
                ".playbook/delivery_execution_model.json",
                exc.lineno,
                "DELIVERY_JSON_INVALID",
                f"delivery execution model is invalid JSON: {exc.msg}",
            )
        ]
    findings: list[Finding] = []
    schema_path = root / "schemas/delivery_execution_model.schema.json"
    if schema_path.exists() and Draft202012Validator is not None:
        validator = Draft202012Validator(json.loads(schema_path.read_text(encoding="utf-8")))
        for error in sorted(validator.iter_errors(data), key=lambda item: list(item.path)):
            findings.append(
                Finding(
                    "error",
                    ".playbook/delivery_execution_model.json",
                    1,
                    "DELIVERY_SCHEMA_INVALID",
                    f"delivery execution model schema violation: {error.message}",
                )
            )
        if findings:
            return findings
    implementer = data.get("implementer", {})
    reviewer = data.get("reviewer", {})
    verifier = data.get("verifier", {})
    completion = data.get("completion_authority", {})
    if not isinstance(implementer, dict) or not isinstance(reviewer, dict) or not isinstance(verifier, dict) or not isinstance(completion, dict):
        return findings
    if completion.get("kind") == implementer.get("kind") or completion.get("kind") == "active_codex_session":
        findings.append(
            Finding(
                "error",
                ".playbook/delivery_execution_model.json",
                1,
                "DELIVERY_SELF_COMPLETION_AUTHORITY",
                "implementer must not be the completion authority",
            )
        )
    if not reviewer.get("kind"):
        findings.append(
            Finding(
                "error",
                ".playbook/delivery_execution_model.json",
                1,
                "DELIVERY_REVIEWER_MISSING",
                "delivery model must name reviewer authority",
            )
        )
    verifier_argv = verifier.get("argv")
    if verifier.get("binding_id") != "project_verifier" or not valid_project_verifier_argv(verifier_argv):
        findings.append(
            Finding(
                "error",
                ".playbook/delivery_execution_model.json",
                1,
                "DELIVERY_VERIFIER_MISSING",
                "delivery model verifier must use structured project_verifier argv binding",
            )
        )
    triggers = data.get("independent_review_triggers")
    if not isinstance(triggers, list) or not triggers:
        findings.append(
            Finding(
                "error",
                ".playbook/delivery_execution_model.json",
                1,
                "DELIVERY_REVIEW_TRIGGERS_MISSING",
                "delivery model must define independent review triggers",
            )
        )
    bindings = data.get("cli_bindings")
    if not isinstance(bindings, dict) or not bindings.get("codex_direct"):
        findings.append(
            Finding(
                "error",
                ".playbook/delivery_execution_model.json",
                1,
                "DELIVERY_CLI_BINDING_MISSING",
                "delivery model must define Codex Direct CLI binding",
            )
        )
    return findings


def validate_json_schemas(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    schema_dir = root / "schemas"
    if not schema_dir.exists():
        return [Finding("error", "schemas", 1, "SCHEMA_DIR_MISSING", "schemas/ missing")]
    for path in sorted(schema_dir.glob("*.schema.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            findings.append(
                Finding(
                    "error",
                    relative(root, path),
                    exc.lineno,
                    "SCHEMA_JSON_INVALID",
                    exc.msg,
                )
            )
            continue
        if not isinstance(data, dict) or "$schema" not in data:
            findings.append(
                Finding(
                    "error",
                    relative(root, path),
                    1,
                    "SCHEMA_META_MISSING",
                    "schema file must contain a $schema field",
                )
            )
            continue
        if Draft202012Validator is None:
            findings.append(
                Finding(
                    "error",
                    relative(root, path),
                    1,
                    "SCHEMA_VALIDATOR_MISSING",
                    "jsonschema is required to validate JSON Schema contracts",
                )
            )
            continue
        try:
            Draft202012Validator.check_schema(data)
        except Exception as exc:
            findings.append(
                Finding(
                    "error",
                    relative(root, path),
                    1,
                    "SCHEMA_META_INVALID",
                    str(exc),
                )
            )
    return findings


def validate_reference_integrity(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    docs = [
        root / "docs" / "COGNITION_MANIFEST.md",
        root / "docs" / "EVIDENCE_INDEX.md",
        root / "docs" / "tasks.md",
    ]
    for path in docs:
        if not path.exists():
            continue
        in_fence = False
        for line_no, line in enumerate(
            path.read_text(encoding="utf-8", errors="replace").splitlines(),
            1,
        ):
            if FENCE_RE.match(line):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            for ref in backticked_path_refs(line):
                if not looks_like_path(ref):
                    continue
                normalized = ref.split("#", 1)[0].split("::", 1)[0].rstrip("/")
                if normalized in {"docs/context-packets"} or normalized.startswith("generated/"):
                    severity = "warning"
                else:
                    severity = "error"
                if not (root / normalized).exists():
                    findings.append(
                        Finding(
                            severity,
                            relative(root, path),
                            line_no,
                            "REFERENCE_MISSING",
                            f"missing referenced path {normalized}",
                        )
                    )
    return findings


def validate_modes(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    init_tool = root / "tools" / "init_playbook_project.py"
    if not init_tool.exists():
        return [
            Finding(
                "error",
                "tools/init_playbook_project.py",
                1,
                "MODE_INITIALIZER_MISSING",
                "initializer tool missing",
            )
        ]
    with tempfile.TemporaryDirectory(prefix="playbook-modes-") as tmp:
        tmp_path = Path(tmp)
        import subprocess

        modes = ["lean-core", "standard", "strict"]
        for mode in modes:
            target = tmp_path / mode
            cmd = [
                sys.executable,
                str(init_tool),
                str(target),
                "--mode",
                mode,
                "--project-name",
                f"Mode {mode}",
                "--verify-argv",
                json.dumps(["{python}", "-c", "raise SystemExit(0)"]),
                "--operational-pain",
                f"Mode {mode} smoke validation needs reproducible project bootstrap.",
                "--current-workaround",
                "Manual fixture generation during validator tests.",
                "--first-proof-metric",
                "Generated project validator exits zero.",
            ]
            result = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if result.returncode != 0:
                findings.append(
                    Finding(
                        "error",
                        "tools/init_playbook_project.py",
                        1,
                        "MODE_INITIALIZER_FAILED",
                        f"initializer failed for {mode}: {result.stderr.strip() or result.stdout.strip()}",
                    )
                )
                continue
            mode_findings, _ = validate_tasks(target)
            for finding in mode_findings:
                finding.path = f"generated:{mode}/{finding.path}"
            findings.extend(mode_findings)
            findings.extend(
                Finding(
                    finding.severity,
                    f"generated:{mode}/{finding.path}",
                    finding.line,
                    finding.check_id,
                    finding.message,
                )
                for finding in validate_placeholders(target)
            )
            if mode == "lean-core":
                unexpected = [
                    "PLAYBOOK.md",
                    "docs/ARCHITECTURE.md",
                    "docs/EVIDENCE_INDEX.md",
                    "docs/ai_cost_architecture.md",
                    "docs/router_eval.md",
                ]
                for rel in unexpected:
                    if (target / rel).exists():
                        findings.append(
                            Finding(
                                "error",
                                f"generated:{mode}/{rel}",
                                1,
                                "MODE_LEAN_CORE_TOO_HEAVY",
                                f"Lean-Core generated unexpected Strict/Standard artifact {rel}",
                            )
                        )
    return findings


def validate_rag(root: Path) -> list[Finding]:
    manifest_path = root / ".playbook" / "rag_eval_manifest.json"
    if not manifest_path.exists():
        return []
    try:
        from tools.rag_eval_lib import validate_contract
    except ImportError:  # pragma: no cover - script execution path.
        from rag_eval_lib import validate_contract  # type: ignore

    findings: list[Finding] = []
    for rag_finding in validate_contract(root, manifest_path):
        findings.append(
            Finding(
                rag_finding.severity,
                rag_finding.path or relative(root, manifest_path),
                1,
                rag_finding.check_id,
                rag_finding.message,
            )
        )
    return findings


def validate_designs(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    design_dir = root / "docs/design"
    if not design_dir.exists():
        task_findings, _ = validate_tasks(root)
        return [finding for finding in task_findings if finding.check_id.startswith(("TASK_DESIGN", "TASK_SLICE"))]
    for registry_path in sorted(design_dir.glob("*.design.json")):
        design_findings, _ = feature_design_lib.validate_design_file(root, registry_path)
        findings.extend(design_finding_to_task_finding(root, finding) for finding in design_findings)
    task_findings, _ = validate_tasks(root)
    findings.extend(
        finding
        for finding in task_findings
        if finding.check_id.startswith(("TASK_DESIGN", "TASK_SLICE", "TASK_USER_TOUCHPOINT", "TASK_REVIEW_CHECKPOINT", "TASK_CHANGE_BUDGET"))
    )
    return findings


def validate_instruction_manifest(root: Path) -> list[Finding]:
    path = root / ".playbook/instruction_manifest.json"
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [
            Finding(
                "error",
                ".playbook/instruction_manifest.json",
                exc.lineno,
                "INSTRUCTION_MANIFEST_JSON_INVALID",
                f"instruction manifest is invalid JSON: {exc.msg}",
            )
        ]
    findings: list[Finding] = []
    schema_path = root / "schemas/instruction_manifest.schema.json"
    if schema_path.exists() and Draft202012Validator is not None:
        validator = Draft202012Validator(json.loads(schema_path.read_text(encoding="utf-8")))
        for error in sorted(validator.iter_errors(data), key=lambda item: list(item.path)):
            findings.append(
                Finding(
                    "error",
                    ".playbook/instruction_manifest.json",
                    1,
                    "INSTRUCTION_MANIFEST_SCHEMA",
                    f"instruction manifest schema violation: {error.message}",
                )
            )
    seen: set[str] = set()
    for artifact in data.get("artifacts", []) if isinstance(data, dict) else []:
        if not isinstance(artifact, dict):
            continue
        raw = str(artifact.get("path", ""))
        if raw in seen:
            findings.append(
                Finding(
                    "error",
                    ".playbook/instruction_manifest.json",
                    1,
                    "INSTRUCTION_MANIFEST_DUPLICATE_PATH",
                    f"duplicate artifact path {raw}",
                )
            )
        seen.add(raw)
        resolved = feature_design_lib.safe_repo_path(root, raw)
        if resolved is None:
            findings.append(
                Finding(
                    "error",
                    ".playbook/instruction_manifest.json",
                    1,
                    "INSTRUCTION_MANIFEST_REF_UNSAFE",
                    f"artifact path must stay inside repository: {raw}",
                )
            )
        elif not resolved.exists() and artifact.get("load_policy") == "always":
            findings.append(
                Finding(
                    "warning",
                    ".playbook/instruction_manifest.json",
                    1,
                    "INSTRUCTION_MANIFEST_REF_MISSING",
                    f"manifest artifact does not exist yet: {raw}",
                )
            )
    return findings


def run_checks(root: Path, checks: list[str]) -> dict[str, Any]:
    findings: list[Finding] = []
    tasks: list[dict[str, Any]] = []
    expanded = checks if checks != ["all"] else ["schemas", "tasks", "design", "instructions", "placeholders", "readiness", "delivery", "references", "modes", "rag"]
    for check in expanded:
        if check == "schemas":
            findings.extend(validate_json_schemas(root))
        elif check == "tasks":
            task_findings, tasks = validate_tasks(root)
            findings.extend(task_findings)
        elif check == "placeholders":
            findings.extend(validate_placeholders(root))
        elif check == "readiness":
            findings.extend(validate_readiness(root))
        elif check == "delivery":
            findings.extend(validate_delivery(root))
        elif check == "references":
            findings.extend(validate_reference_integrity(root))
        elif check == "modes":
            findings.extend(validate_modes(root))
        elif check == "rag":
            findings.extend(validate_rag(root))
        elif check == "design":
            findings.extend(validate_designs(root))
        elif check == "instructions":
            findings.extend(validate_instruction_manifest(root))
        else:
            findings.append(
                Finding("error", ".", 1, "CHECK_UNKNOWN", f"unknown check {check}")
            )
    return {
        "schema_version": "playbook.validation.v1",
        "root": str(root),
        "checks": expanded,
        "tasks": tasks,
        "findings": [finding.as_dict() for finding in findings],
        "summary": {
            "errors": sum(1 for finding in findings if finding.severity == "error"),
            "warnings": sum(1 for finding in findings if finding.severity == "warning"),
        },
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Playbook or generated project root.")
    parser.add_argument(
        "--check",
        action="append",
        choices=("all", "schemas", "tasks", "design", "instructions", "placeholders", "readiness", "delivery", "references", "modes", "rag"),
        default=None,
        help="Run only this check. Repeatable. Defaults to all checks.",
    )
    parser.add_argument("--json", dest="json_path", help="Write machine-readable report.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.root).resolve()
    checks = args.check or ["all"]
    report = run_checks(root, checks)
    if args.json_path:
        json_path = Path(args.json_path)
        if not json_path.is_absolute():
            json_path = root / json_path
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    for finding in report["findings"]:
        print(
            "{severity}: {path}:{line}: {check_id}: {message}".format(**finding),
            file=sys.stderr if finding["severity"] == "error" else sys.stdout,
        )
    summary = report["summary"]
    print(
        f"playbook_validate: errors={summary['errors']} warnings={summary['warnings']}"
    )
    return 1 if summary["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
