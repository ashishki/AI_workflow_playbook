#!/usr/bin/env python3
"""Render a bounded context packet for one approved feature slice."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any

try:
    from jsonschema import Draft202012Validator
except ImportError:  # pragma: no cover
    Draft202012Validator = None  # type: ignore[assignment]

try:
    import feature_design_lib
except ImportError:  # pragma: no cover
    from tools import feature_design_lib  # type: ignore


INCLUDED_POLICIES = {"always", "current_feature", "current_slice"}


def read_text(path: Path, limit: int = 20000) -> str:
    if not path.exists():
        return "[missing]"
    text = path.read_text(encoding="utf-8", errors="replace")
    if len(text) > limit:
        return text[:limit].rstrip() + "\n[truncated by render_slice_context.py]"
    return text


def load_manifest(root: Path, manifest_path: Path) -> tuple[list[str], dict[str, Any] | None]:
    if not manifest_path.exists():
        return [], {"schema_version": "playbook.instruction_manifest.v1", "artifacts": []}
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"instruction manifest invalid JSON: {exc.msg}"], None
    errors: list[str] = []
    schema_path = root / "schemas/instruction_manifest.schema.json"
    if schema_path.exists() and Draft202012Validator is not None:
        validator = Draft202012Validator(json.loads(schema_path.read_text(encoding="utf-8")))
        for error in sorted(validator.iter_errors(data), key=lambda item: list(item.path)):
            errors.append(f"instruction manifest schema violation: {error.message}")
    if errors:
        return errors, None
    return [], data


def manifest_artifacts(root: Path, manifest: dict[str, Any]) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    for artifact in manifest.get("artifacts", []):
        if not isinstance(artifact, dict):
            continue
        if artifact.get("load_policy") not in INCLUDED_POLICIES:
            continue
        raw_path = str(artifact.get("path", ""))
        path = feature_design_lib.safe_repo_path(root, raw_path)
        if path is None or not path.exists():
            continue
        selected.append({**artifact, "resolved_path": path})
    selected.sort(key=lambda item: (str(item.get("authority")), str(item.get("path"))))
    return selected


def design_markdown_path(root: Path, feature_id: str) -> Path:
    return root / "docs/design" / f"{feature_id}.md"


def render_packet(
    root: Path,
    feature_id: str,
    slice_id: str,
    design: dict[str, Any],
    slice_item: dict[str, Any],
    manifest: dict[str, Any],
    manifest_path: Path,
) -> str:
    brief_path = feature_design_lib.safe_repo_path(root, str(design["brief_ref"]))
    design_md = design_markdown_path(root, feature_id)
    created = dt.date.today().isoformat()
    lines = [
        f"# Slice Context - {feature_id}/{slice_id}",
        "",
        f"Generated-At: {created}",
        f"Feature-ID: {feature_id}",
        f"Slice-ID: {slice_id}",
        f"Planning-Depth: {design['planning_depth']}",
        f"Risk-Level: {design['risk_level']}",
        f"Instruction-Manifest: {manifest_path.relative_to(root) if manifest_path.exists() else '[none]'}",
        "",
        "## Brief Subset",
        "",
        f"Path: `{design['brief_ref']}`",
        "",
        "```markdown",
        read_text(brief_path, 8000) if brief_path else "[unsafe brief ref]",
        "```",
        "",
        "## Approved Feature Design",
        "",
        f"Markdown: `docs/design/{feature_id}.md`",
        f"Registry: `docs/design/{feature_id}.design.json`",
        "",
        "```markdown",
        read_text(design_md, 20000),
        "```",
        "",
        "## Current Slice",
        "",
        "```json",
        json.dumps(slice_item, indent=2, sort_keys=True),
        "```",
        "",
        "## Slice Boundaries",
        "",
        "- Allowed files: " + ", ".join(f"`{item}`" for item in slice_item.get("allowed_files", [])),
        "- Forbidden files: " + ", ".join(f"`{item}`" for item in slice_item.get("forbidden_files", [])),
        "- Expected interfaces: " + ", ".join(f"`{item}`" for item in slice_item.get("expected_interfaces", [])),
        "- Change budget: " + str(slice_item.get("change_budget", "")),
        "- Review checkpoint: " + str(slice_item.get("review_checkpoint", "")),
        "- Rollback: " + str(slice_item.get("rollback", "")),
        "",
        "## Verification Commands",
        "",
    ]
    lines.extend(f"- `{command}`" for command in slice_item.get("verification", []))
    lines.extend(
        [
            "",
            "## Architecture Refs",
            "",
        ]
    )
    for ref in design.get("architecture_refs", []):
        lines.append(f"- `{ref}`")
    lines.extend(["", "## Authoritative Contract Excerpts", ""])
    for artifact in manifest_artifacts(root, manifest):
        path = artifact["resolved_path"]
        lines.extend(
            [
                f"### {artifact['path']}",
                "",
                f"- Authority: {artifact['authority']}",
                f"- Stability: {artifact['stability']}",
                f"- Load policy: {artifact['load_policy']}",
                "",
                "```text",
                read_text(path, 6000),
                "```",
                "",
            ]
        )
    lines.extend(
        [
            "## Known Findings",
            "",
            "Use current task/review artifacts only. Historical completed-task logs and never-by-default artifacts are intentionally excluded.",
            "",
        ]
    )
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".")
    parser.add_argument("--feature-id", required=True)
    parser.add_argument("--slice-id", required=True)
    parser.add_argument("--manifest", default=".playbook/instruction_manifest.json")
    parser.add_argument("--output", help="Output path. Defaults to .playbook-artifacts/context/<feature>/<slice>.md")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.root).resolve()
    registry_path = root / "docs/design" / f"{args.feature_id}.design.json"
    findings, design = feature_design_lib.validate_design_file(root, registry_path)
    errors = [finding for finding in findings if finding.severity == "error"]
    if errors:
        for finding in errors:
            print(f"{finding.path}: {finding.check_id}: {finding.message}", file=sys.stderr)
        return 1
    if not feature_design_lib.design_is_approved(design):
        print("render_slice_context: approved feature design is required", file=sys.stderr)
        return 1
    assert design is not None
    slice_item = feature_design_lib.find_slice(design, args.slice_id)
    if slice_item is None:
        print(f"render_slice_context: slice {args.slice_id} not found in design {args.feature_id}", file=sys.stderr)
        return 1
    manifest_path = Path(args.manifest)
    if not manifest_path.is_absolute():
        manifest_path = root / manifest_path
    manifest_errors, manifest = load_manifest(root, manifest_path)
    if manifest_errors or manifest is None:
        for error in manifest_errors:
            print(f"render_slice_context: {error}", file=sys.stderr)
        return 1
    packet = render_packet(root, args.feature_id, args.slice_id, design, slice_item, manifest, manifest_path)
    output_path = Path(args.output) if args.output else root / ".playbook-artifacts/context" / args.feature_id / f"{args.slice_id}.md"
    if not output_path.is_absolute():
        output_path = root / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(packet, encoding="utf-8")
    print(f"render_slice_context: output={output_path.relative_to(root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
