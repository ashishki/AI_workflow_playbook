#!/usr/bin/env python3
"""Validate Feature Design companion JSON registries."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    import feature_design_lib
except ImportError:  # pragma: no cover
    from tools import feature_design_lib  # type: ignore


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Project root.")
    parser.add_argument(
        "--design",
        action="append",
        default=[],
        help="Feature design registry path. Defaults to docs/design/*.design.json.",
    )
    parser.add_argument("--json", dest="json_path", help="Write machine-readable validation report.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.root).resolve()
    if args.design:
        raw_paths = args.design
    elif (root / "docs/design").exists():
        raw_paths = [str(path.relative_to(root)) for path in sorted((root / "docs/design").glob("*.design.json"))]
    else:
        raw_paths = []
    findings: list[feature_design_lib.DesignFinding] = []
    for raw in raw_paths:
        path = feature_design_lib.safe_repo_path(root, raw)
        if path is None:
            findings.append(
                feature_design_lib.DesignFinding(
                    "error",
                    raw,
                    1,
                    "DESIGN_REF_UNSAFE",
                    f"design path must stay inside repository: {raw}",
                )
            )
            continue
        design_findings, _ = feature_design_lib.validate_design_file(root, path)
        findings.extend(design_findings)
    report = {
        "schema_version": "playbook.feature_design_validation.v1",
        "root": str(root),
        "designs": raw_paths,
        "findings": [finding.as_dict() for finding in findings],
        "summary": {
            "errors": sum(1 for finding in findings if finding.severity == "error"),
            "warnings": sum(1 for finding in findings if finding.severity == "warning"),
        },
    }
    if args.json_path:
        output_path = Path(args.json_path)
        if not output_path.is_absolute():
            output_path = root / output_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    for finding in findings:
        print(f"{finding.severity}: {finding.path}:{finding.line}: {finding.check_id}: {finding.message}")
    summary = report["summary"]
    print(f"validate_feature_design: errors={summary['errors']} warnings={summary['warnings']}")
    return 1 if summary["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
