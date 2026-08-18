#!/usr/bin/env python3
"""Deterministic review policy for Feature Design and slice workflow."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DESIGN_REVIEW_ROLES = ("product_design_review", "program_design_review")
SLICE_REVIEW_ROLE = "slice_review"
MAINTAINABILITY_REVIEW_ROLE = "maintainability_review"
GUARDED_CODEX_ROLES = {
    "product_design_review",
    "program_design_review",
    "slice_review",
    "maintainability_review",
}


def design_reviews(design: dict[str, Any]) -> list[dict[str, Any]]:
    depth = str(design.get("planning_depth", "oneshot"))
    risk = str(design.get("risk_level", "medium"))
    if depth == "oneshot":
        return []
    if depth == "compact_design":
        return [
            {
                "role": "program_design_review",
                "phase": "design",
                "required": risk != "low",
                "reason": "compact design requires program design challenge for medium+ risk",
            }
        ]
    reviews = [
        {
            "role": "product_design_review",
            "phase": "design",
            "required": risk in {"high", "critical"},
            "reason": "designed_slices requires product outcome challenge before approval",
        },
        {
            "role": "program_design_review",
            "phase": "design",
            "required": risk in {"high", "critical"},
            "reason": "designed_slices requires program design challenge before approval",
        },
    ]
    if risk in {"low", "medium"}:
        for item in reviews:
            item["required"] = True
            item["reason"] = "designed_slices defaults to design review before approval"
    return reviews


def maintainability_required(
    design: dict[str, Any],
    maintainability_report: dict[str, Any] | None = None,
    scope_findings: list[dict[str, Any]] | None = None,
) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    if str(design.get("risk_level", "medium")) in {"medium", "high", "critical"}:
        reasons.append("medium/high/critical risk")
    if maintainability_report and maintainability_report.get("status") in {"advisory", "stop_ship"}:
        reasons.append("maintainability checker produced signals")
    for finding in scope_findings or []:
        check_id = str(finding.get("check_id", ""))
        if check_id in {"SLICE_CHANGE_BUDGET_EXCEEDED", "SLICE_OUTSIDE_ALLOWED_FILES", "SLICE_FORBIDDEN_FILE"}:
            reasons.append(check_id)
    return bool(reasons), sorted(set(reasons))


def slice_reviews(
    design: dict[str, Any],
    slice_item: dict[str, Any],
    maintainability_report: dict[str, Any] | None = None,
    scope_findings: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    reviews = [
        {
            "role": SLICE_REVIEW_ROLE,
            "phase": "slice",
            "slice_id": slice_item.get("slice_id"),
            "required": True,
            "reason": "implemented slice requires independent slice review",
        }
    ]
    required, reasons = maintainability_required(design, maintainability_report, scope_findings)
    if required:
        reviews.append(
            {
                "role": MAINTAINABILITY_REVIEW_ROLE,
                "phase": "slice",
                "slice_id": slice_item.get("slice_id"),
                "required": True,
                "reason": "; ".join(reasons),
            }
        )
    return reviews


def report(
    *,
    feature_id: str,
    design: dict[str, Any],
    slice_item: dict[str, Any] | None = None,
    maintainability_report: dict[str, Any] | None = None,
    scope_findings: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    reviews = design_reviews(design) if slice_item is None else slice_reviews(design, slice_item, maintainability_report, scope_findings)
    for item in reviews:
        role = item["role"]
        if item.get("phase") == "slice" and item.get("slice_id"):
            item["prompt_path"] = f".playbook-artifacts/prompts/{feature_id}/{item['slice_id']}_{role}.md"
            item["report_path"] = f".playbook-artifacts/reports/{feature_id}/{item['slice_id']}_{role}.md"
        else:
            item["prompt_path"] = f".playbook-artifacts/prompts/{feature_id}/{role}.md"
            item["report_path"] = f".playbook-artifacts/reports/{feature_id}/{role}.md"
        item.setdefault("status", "pending")
        item["runner_required"] = role in GUARDED_CODEX_ROLES
        item["execution_surface"] = "codex_role_runner" if role in GUARDED_CODEX_ROLES else "external_or_manual"
        item["runner_tool"] = "tools/run_codex_role.py" if role in GUARDED_CODEX_ROLES else None
    return {
        "schema_version": "playbook.required_reviews.v1",
        "feature_id": feature_id,
        "phase": "slice" if slice_item is not None else "design",
        "slice_id": slice_item.get("slice_id") if slice_item else None,
        "reviews": reviews,
    }


def write_report(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
