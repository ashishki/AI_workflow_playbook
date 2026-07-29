#!/usr/bin/env python3
"""Shared helpers for Feature Design validation and slice lookup."""

from __future__ import annotations

import fnmatch
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from jsonschema import Draft202012Validator
except ImportError:  # pragma: no cover - environments without dev deps.
    Draft202012Validator = None  # type: ignore[assignment]


APPROVED_STATUSES = {"approved", "implemented"}
SELF_APPROVERS = {"ai", "agent", "assistant", "codex", "llm", "model", "self"}
SLICE_DONE_STATUSES = {"implemented", "reviewed", "closed", "complete", "completed"}
CHANGE_BUDGET_RE = re.compile(
    r"^(files|lines|public_interfaces|dependencies|tool_calls|tokens|latency_ms|cost_usd)\s*<=\s*([0-9]+(?:\.[0-9]+)?)$"
)


@dataclass
class DesignFinding:
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


def relative(root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def safe_repo_path(root: Path, raw: str) -> Path | None:
    clean = raw.strip().strip("`")
    clean = clean.split("#", 1)[0].split("::", 1)[0].rstrip("/")
    if not clean:
        return None
    path = Path(clean)
    if path.is_absolute() or ".." in path.parts:
        return None
    resolved = (root / path).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError:
        return None
    return resolved


def repo_rel(root: Path, path: Path) -> str:
    return str(path.resolve().relative_to(root.resolve()))


def schema_validator(root: Path) -> Any | None:
    if Draft202012Validator is None:
        return None
    schema_path = root / "schemas/feature_design.schema.json"
    if not schema_path.exists():
        schema_path = Path(__file__).resolve().parents[1] / "schemas/feature_design.schema.json"
    return Draft202012Validator(json.loads(schema_path.read_text(encoding="utf-8")))


def load_json(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, f"invalid JSON: {exc.msg}"
    except OSError as exc:
        return None, str(exc)
    if not isinstance(data, dict):
        return None, "feature design registry must be a JSON object"
    return data, None


def validate_change_budget(value: Any) -> bool:
    if value in (None, ""):
        return False
    if isinstance(value, dict):
        return all(
            key in {"files", "lines", "public_interfaces", "dependencies", "tool_calls", "tokens", "latency_ms", "cost_usd"}
            and isinstance(amount, (int, float))
            and amount >= 0
            for key, amount in value.items()
        )
    raw = str(value).strip()
    if not raw:
        return False
    parts = [part.strip() for part in re.split(r"[,;]", raw) if part.strip()]
    return bool(parts) and all(CHANGE_BUDGET_RE.match(part) for part in parts)


def parse_change_budget(value: Any) -> dict[str, float]:
    if isinstance(value, dict):
        return {
            str(key): float(amount)
            for key, amount in value.items()
            if isinstance(amount, (int, float)) and amount >= 0
        }
    if not validate_change_budget(value):
        return {}
    budget: dict[str, float] = {}
    for part in [item.strip() for item in re.split(r"[,;]", str(value)) if item.strip()]:
        match = CHANGE_BUDGET_RE.match(part)
        if match:
            amount = float(match.group(2))
            budget[match.group(1)] = int(amount) if amount.is_integer() else amount
    return budget


def validate_refs(root: Path, registry_path: Path, data: dict[str, Any]) -> list[DesignFinding]:
    findings: list[DesignFinding] = []
    ref_fields = [("brief_ref", data.get("brief_ref"))]
    ref_fields.extend(("architecture_refs", ref) for ref in data.get("architecture_refs", []) if isinstance(ref, str))
    for field, raw in ref_fields:
        if not isinstance(raw, str) or not raw:
            continue
        resolved = safe_repo_path(root, raw)
        if resolved is None:
            findings.append(
                DesignFinding(
                    "error",
                    relative(root, registry_path),
                    1,
                    "DESIGN_REF_UNSAFE",
                    f"{field} must stay inside repository: {raw}",
                )
            )
        elif not resolved.exists():
            findings.append(
                DesignFinding(
                    "error",
                    relative(root, registry_path),
                    1,
                    "DESIGN_REF_MISSING",
                    f"{field} path does not exist: {raw}",
                )
            )
    return findings


def validate_approval(root: Path, registry_path: Path, data: dict[str, Any]) -> list[DesignFinding]:
    findings: list[DesignFinding] = []
    status = str(data.get("status", "")).strip().lower()
    if status not in APPROVED_STATUSES:
        return findings
    approved_by = str(data.get("approved_by", "")).strip()
    approved_at = str(data.get("approved_at", "")).strip()
    if not approved_by or not approved_at:
        findings.append(
            DesignFinding(
                "error",
                relative(root, registry_path),
                1,
                "DESIGN_APPROVAL_MISSING",
                "approved design requires approved_by and approved_at provenance",
            )
        )
        return findings
    if approved_by.lower() in SELF_APPROVERS or "codex" in approved_by.lower():
        findings.append(
            DesignFinding(
                "error",
                relative(root, registry_path),
                1,
                "DESIGN_SELF_APPROVAL",
                "model/agent self-approval is not valid design approval",
            )
        )
    policy = str(data.get("approval_policy", "")).strip()
    if policy == "human_required" and approved_by.lower() != "human" and not approved_by.lower().startswith("human:"):
        findings.append(
            DesignFinding(
                "error",
                relative(root, registry_path),
                1,
                "DESIGN_HUMAN_APPROVAL_REQUIRED",
                "human_required design approval must cite human provenance",
            )
        )
    if data.get("planning_depth") == "designed_slices" and data.get("risk_level") in {"high", "critical"} and policy != "human_required":
        findings.append(
            DesignFinding(
                "error",
                relative(root, registry_path),
                1,
                "DESIGN_HUMAN_APPROVAL_REQUIRED",
                "high-risk designed_slices requires approval_policy=human_required",
            )
        )
    return findings


def slice_registry(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    registry: dict[str, dict[str, Any]] = {}
    for item in data.get("slices", []):
        if isinstance(item, dict) and isinstance(item.get("slice_id"), str):
            registry[item["slice_id"]] = item
    return registry


def validate_slices(root: Path, registry_path: Path, data: dict[str, Any]) -> list[DesignFinding]:
    findings: list[DesignFinding] = []
    seen: set[str] = set()
    slices = [item for item in data.get("slices", []) if isinstance(item, dict)]
    for item in slices:
        slice_id = str(item.get("slice_id", "")).strip()
        if not slice_id:
            continue
        if slice_id in seen:
            findings.append(
                DesignFinding(
                    "error",
                    relative(root, registry_path),
                    1,
                    "DESIGN_SLICE_DUPLICATE",
                    f"duplicate slice_id {slice_id}",
                )
            )
        seen.add(slice_id)
        if not validate_change_budget(item.get("change_budget")):
            findings.append(
                DesignFinding(
                    "error",
                    relative(root, registry_path),
                    1,
                    "DESIGN_CHANGE_BUDGET_INVALID",
                    f"slice {slice_id} change_budget must use entries like files<=4, lines<=200",
                )
            )
        if data.get("planning_depth") == "designed_slices" and not item.get("verification"):
            findings.append(
                DesignFinding(
                    "error",
                    relative(root, registry_path),
                    1,
                    "DESIGN_SLICE_VERIFICATION_REQUIRED",
                    f"slice {slice_id} must declare verification",
                )
            )
    by_id = slice_registry(data)
    for item in slices:
        slice_id = str(item.get("slice_id", "")).strip()
        for dep in item.get("dependencies", []):
            if dep not in by_id:
                findings.append(
                    DesignFinding(
                        "error",
                        relative(root, registry_path),
                        1,
                        "DESIGN_SLICE_UNKNOWN_DEPENDENCY",
                        f"slice {slice_id} depends on unknown slice {dep}",
                    )
                )

    visiting: set[str] = set()
    visited: set[str] = set()

    def walk(slice_id: str, stack: list[str]) -> None:
        if slice_id in visiting:
            cycle = stack[stack.index(slice_id) :] + [slice_id]
            findings.append(
                DesignFinding(
                    "error",
                    relative(root, registry_path),
                    1,
                    "DESIGN_SLICE_CYCLIC_DEPENDENCY",
                    "cyclic slice dependency: " + " -> ".join(cycle),
                )
            )
            return
        if slice_id in visited or slice_id not in by_id:
            return
        visiting.add(slice_id)
        for dep in by_id[slice_id].get("dependencies", []):
            walk(str(dep), stack + [str(dep)])
        visiting.remove(slice_id)
        visited.add(slice_id)

    for slice_id in by_id:
        walk(slice_id, [slice_id])
    return findings


def validate_design_file(root: Path, registry_path: Path) -> tuple[list[DesignFinding], dict[str, Any] | None]:
    registry_path = registry_path if registry_path.is_absolute() else root / registry_path
    if not registry_path.exists():
        return [
            DesignFinding(
                "error",
                relative(root, registry_path),
                1,
                "DESIGN_REGISTRY_MISSING",
                "feature design registry is missing",
            )
        ], None
    data, error = load_json(registry_path)
    if error or data is None:
        return [
            DesignFinding(
                "error",
                relative(root, registry_path),
                1,
                "DESIGN_JSON_INVALID",
                error or "invalid JSON",
            )
        ], None
    findings: list[DesignFinding] = []
    validator = schema_validator(root)
    if validator is None:
        findings.append(
            DesignFinding(
                "error",
                relative(root, registry_path),
                1,
                "DESIGN_SCHEMA_VALIDATOR_MISSING",
                "jsonschema is required to validate feature_design.schema.json",
            )
        )
    else:
        for schema_error in sorted(validator.iter_errors(data), key=lambda item: list(item.path)):
            field_path = ".".join(str(part) for part in schema_error.path)
            findings.append(
                DesignFinding(
                    "error",
                    relative(root, registry_path),
                    1,
                    "DESIGN_SCHEMA",
                    f"schema violation"
                    + (f" at {field_path}" if field_path else "")
                    + f": {schema_error.message}",
                )
            )
    findings.extend(validate_refs(root, registry_path, data))
    findings.extend(validate_approval(root, registry_path, data))
    findings.extend(validate_slices(root, registry_path, data))
    if (
        data.get("planning_depth") == "designed_slices"
        and data.get("status") in {"review_required", "approved", "implemented"}
        and not data.get("slices")
    ):
        findings.append(
            DesignFinding(
                "error",
                relative(root, registry_path),
                1,
                "DESIGN_SLICE_REQUIRED",
                "designed_slices design requires at least one vertical slice",
            )
        )
    return findings, data


def design_is_approved(data: dict[str, Any] | None) -> bool:
    return bool(data and data.get("status") in APPROVED_STATUSES)


def find_slice(data: dict[str, Any], slice_id: str) -> dict[str, Any] | None:
    return slice_registry(data).get(slice_id)


def slice_dependencies_satisfied(data: dict[str, Any], slice_item: dict[str, Any]) -> list[str]:
    by_id = slice_registry(data)
    missing: list[str] = []
    for dep in slice_item.get("dependencies", []):
        dep_item = by_id.get(str(dep))
        if not dep_item or str(dep_item.get("status", "")).strip().lower() not in SLICE_DONE_STATUSES:
            missing.append(str(dep))
    return missing


def path_matches_any(path: str, patterns: list[str]) -> bool:
    clean = path.strip().strip("`")
    return any(fnmatch.fnmatch(clean, pattern) or clean.startswith(pattern.rstrip("/") + "/") for pattern in patterns)


def task_files_within_slice(files: list[str], slice_item: dict[str, Any]) -> tuple[list[str], list[str]]:
    allowed = [str(item) for item in slice_item.get("allowed_files", [])]
    forbidden = [str(item) for item in slice_item.get("forbidden_files", [])]
    outside_allowed: list[str] = []
    forbidden_hits: list[str] = []
    for raw in files:
        path = raw.strip().strip("`")
        if forbidden and path_matches_any(path, forbidden):
            forbidden_hits.append(path)
        if allowed and not path_matches_any(path, allowed):
            outside_allowed.append(path)
    return outside_allowed, forbidden_hits
