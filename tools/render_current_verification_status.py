#!/usr/bin/env python3
"""Render current verification status from a verify_playbook machine report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def render(report: dict[str, object]) -> str:
    summary = report.get("summary", {})
    if not isinstance(summary, dict):
        summary = {}
    checks = report.get("checks", [])
    if not isinstance(checks, list):
        checks = []
    lines = [
        "# Current Verification Status",
        "",
        "This file is generated from `tools/verify_playbook.py` output. It is a current-status artifact, not a historical implementation report.",
        "",
        f"- Valid for commit: `{report.get('valid_for_commit', 'unknown')}`",
        f"- Generated at: `{report.get('generated_at', 'unknown')}`",
        f"- Required checks: `{summary.get('required', 'unknown')}`",
        f"- Required failures: `{summary.get('required_failures', 'unknown')}`",
        f"- Optional failures: `{summary.get('optional_failures', 'unknown')}`",
        "",
        "| Check | Required | Exit | Status |",
        "|---|---:|---:|---|",
    ]
    for check in checks:
        if not isinstance(check, dict):
            continue
        status = "PASS" if check.get("passed") else "FAIL"
        lines.append(
            f"| `{check.get('check_id', 'unknown')}` | `{check.get('required', 'unknown')}` | `{check.get('exit_code', 'unknown')}` | {status} |"
        )
    lines.append("")
    dirty = report.get("dirty_state", [])
    if isinstance(dirty, list) and dirty:
        lines.extend(["## Dirty State", ""])
        lines.extend(f"- `{item}`" for item in dirty)
        lines.append("")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default=".playbook-artifacts/playbook_verification.json")
    parser.add_argument("--output", default=".playbook-artifacts/CURRENT_VERIFICATION_STATUS.md")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    input_path = Path(args.input)
    output_path = Path(args.output)
    report = json.loads(input_path.read_text(encoding="utf-8"))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render(report), encoding="utf-8")
    print(f"wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
