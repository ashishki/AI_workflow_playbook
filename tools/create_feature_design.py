#!/usr/bin/env python3
"""Create a draft Feature Design Markdown file and companion registry."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import tempfile
from pathlib import Path

try:
    import feature_design_lib
except ImportError:  # pragma: no cover
    from tools import feature_design_lib  # type: ignore


PLAYBOOK_ROOT = Path(__file__).resolve().parents[1]


def atomic_write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        tmp_name = handle.name
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
    os.replace(tmp_name, path)


def render_template(feature_id: str, planning_depth: str, owner: str, risk_level: str, today: str) -> str:
    template = (PLAYBOOK_ROOT / "templates/FEATURE_DESIGN.md").read_text(encoding="utf-8")
    return (
        template.replace("{{DATE}}", today)
        .replace("Feature-ID:\n", f"Feature-ID: {feature_id}\n")
        .replace("Planning-Depth:\n", f"Planning-Depth: {planning_depth}\n")
        .replace("Owner:\n", f"Owner: {owner}\n")
        .replace("Risk-Level:\n", f"Risk-Level: {risk_level}\n")
    )


def initial_registry(args: argparse.Namespace, today: str) -> dict[str, object]:
    approval_policy = (
        "human_required"
        if args.planning_depth == "designed_slices" and args.risk_level in {"high", "critical"}
        else args.approval_policy
    )
    return {
        "schema_version": "playbook.feature_design.v1",
        "feature_id": args.feature_id,
        "status": "draft",
        "planning_depth": args.planning_depth,
        "risk_level": args.risk_level,
        "brief_ref": args.brief_ref,
        "architecture_refs": args.architecture_ref,
        "approval_policy": approval_policy,
        "slices": [],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Project root.")
    parser.add_argument("--feature-id", required=True)
    parser.add_argument("--planning-depth", choices=("compact_design", "designed_slices"), required=True)
    parser.add_argument("--owner", default="human")
    parser.add_argument("--risk-level", choices=("low", "medium", "high", "critical"), default="medium")
    parser.add_argument("--brief-ref", default="docs/PROJECT_BRIEF.md")
    parser.add_argument("--architecture-ref", action="append", default=[])
    parser.add_argument(
        "--approval-policy",
        choices=("human_required", "human_or_authorized_reviewer", "not_required"),
        default="human_or_authorized_reviewer",
    )
    parser.add_argument("--force", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.root).resolve()
    design_dir = root / "docs/design"
    markdown_path = design_dir / f"{args.feature_id}.md"
    registry_path = design_dir / f"{args.feature_id}.design.json"
    if not args.force and (markdown_path.exists() or registry_path.exists()):
        print(f"create_feature_design: design already exists for {args.feature_id}")
        return 1
    if feature_design_lib.safe_repo_path(root, args.brief_ref) is None:
        print(f"create_feature_design: unsafe brief ref: {args.brief_ref}")
        return 2
    for ref in args.architecture_ref:
        if feature_design_lib.safe_repo_path(root, ref) is None:
            print(f"create_feature_design: unsafe architecture ref: {ref}")
            return 2
    today = dt.date.today().isoformat()
    design_dir.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text(
        render_template(args.feature_id, args.planning_depth, args.owner, args.risk_level, today),
        encoding="utf-8",
    )
    atomic_write_json(registry_path, initial_registry(args, today))
    print(f"create_feature_design: markdown={markdown_path.relative_to(root)}")
    print(f"create_feature_design: registry={registry_path.relative_to(root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
