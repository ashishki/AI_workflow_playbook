#!/usr/bin/env python3
"""Deterministic Planning Depth recommendation rules."""

from __future__ import annotations

import argparse
import json
from typing import Any


PLANNING_DEPTHS = ("oneshot", "compact_design", "designed_slices")


def normalize_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    raw = str(value or "").strip().lower()
    return raw in {"1", "true", "yes", "y", "on"}


def recommend_planning_depth(
    *,
    risk_level: str = "medium",
    task_tags: list[str] | None = None,
    estimated_components: int = 1,
    expected_file_count: int = 1,
    api_change: bool = False,
    persistence_change: bool = False,
    security_change: bool = False,
    destructive_or_external_write: bool = False,
    rag_or_agentic: bool = False,
    migration_required: bool = False,
    user_visible_feature: bool = False,
    new_internal_interface: bool = False,
    nontrivial_control_flow: bool = False,
    local_refactor: bool = False,
    expected_large_diff: bool = False,
) -> dict[str, Any]:
    tags = {tag.strip().lower() for tag in (task_tags or []) if tag.strip()}
    risk = risk_level.strip().lower().replace("-", "_") or "medium"
    reasons: list[str] = []

    designed_triggers = [
        (risk in {"high", "critical"}, f"{risk} risk" if risk in {"high", "critical"} else ""),
        (user_visible_feature, "new user-visible capability"),
        (estimated_components >= 3, "touches multiple architectural components"),
        (api_change and persistence_change, "touches API and persistence"),
        (security_change, "touches security or privacy boundary"),
        (destructive_or_external_write, "destructive or external write behavior"),
        (rag_or_agentic or any(tag.startswith(("rag:", "agent:", "tool:")) for tag in tags), "RAG/tool-use/agentic behavior"),
        (migration_required, "migration required"),
        (expected_file_count >= 8 or expected_large_diff, "expected large diff"),
    ]
    for active, reason in designed_triggers:
        if active and reason:
            reasons.append(reason)
    if reasons:
        return {
            "recommended_planning_depth": "designed_slices",
            "reasons": sorted(set(reasons)),
            "override_allowed": True,
            "override_requires_reason": True,
        }

    compact_triggers = [
        (risk == "medium", "medium risk"),
        (expected_file_count >= 3, "multiple files or modules"),
        (estimated_components == 2, "touches more than one component"),
        (new_internal_interface, "new internal interface"),
        (nontrivial_control_flow, "nontrivial control flow"),
        (local_refactor, "local refactor"),
    ]
    for active, reason in compact_triggers:
        if active:
            reasons.append(reason)
    if reasons:
        return {
            "recommended_planning_depth": "compact_design",
            "reasons": sorted(set(reasons)),
            "override_allowed": True,
            "override_requires_reason": True,
        }

    oneshot_reasons = ["low risk or local change", "no API/schema/persistence/security boundary"]
    if tags & {"docs", "documentation", "config"}:
        oneshot_reasons.append("docs/config-only task")
    return {
        "recommended_planning_depth": "oneshot",
        "reasons": sorted(set(oneshot_reasons)),
        "override_allowed": True,
        "override_requires_reason": False,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--risk-level", default="medium", choices=("low", "medium", "high", "critical"))
    parser.add_argument("--task-tag", action="append", default=[])
    parser.add_argument("--estimated-components", type=int, default=1)
    parser.add_argument("--expected-file-count", type=int, default=1)
    parser.add_argument("--api-change", action="store_true")
    parser.add_argument("--persistence-change", action="store_true")
    parser.add_argument("--security-change", action="store_true")
    parser.add_argument("--destructive-or-external-write", action="store_true")
    parser.add_argument("--rag-or-agentic", action="store_true")
    parser.add_argument("--migration-required", action="store_true")
    parser.add_argument("--user-visible-feature", action="store_true")
    parser.add_argument("--new-internal-interface", action="store_true")
    parser.add_argument("--nontrivial-control-flow", action="store_true")
    parser.add_argument("--local-refactor", action="store_true")
    parser.add_argument("--expected-large-diff", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = recommend_planning_depth(
        risk_level=args.risk_level,
        task_tags=args.task_tag,
        estimated_components=args.estimated_components,
        expected_file_count=args.expected_file_count,
        api_change=args.api_change,
        persistence_change=args.persistence_change,
        security_change=args.security_change,
        destructive_or_external_write=args.destructive_or_external_write,
        rag_or_agentic=args.rag_or_agentic,
        migration_required=args.migration_required,
        user_visible_feature=args.user_visible_feature,
        new_internal_interface=args.new_internal_interface,
        nontrivial_control_flow=args.nontrivial_control_flow,
        local_refactor=args.local_refactor,
        expected_large_diff=args.expected_large_diff,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
