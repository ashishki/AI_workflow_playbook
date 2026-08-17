#!/usr/bin/env python3
"""Aggregate LOC deltas for paired harness runs and print a short report block."""

from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DOC_EXTENSIONS = {".md", ".rst", ".txt", ".toml", ".yml", ".yaml"}
CODE_EXTENSIONS = {
    ".py",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".go",
    ".rs",
    ".java",
    ".kt",
    ".rb",
    ".cpp",
    ".c",
    ".h",
    ".cs",
}

TRANSIENT_PARTS = {".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".tox", ".nox"}
TRANSIENT_FILES = {".coverage", "coverage.xml"}


def is_transient_path(path: str) -> bool:
    value = Path(path)
    return any(part in TRANSIENT_PARTS for part in value.parts) or value.name in TRANSIENT_FILES


@dataclass
class LocationTotals:
    code: int = 0
    docs: int = 0
    tests: int = 0
    other: int = 0

    def add(self, category: str, amount: int) -> None:
        if category == "code":
            self.code += amount
        elif category == "docs":
            self.docs += amount
        elif category == "tests":
            self.tests += amount
        else:
            self.other += amount

    def merge(self, other: "LocationTotals") -> None:
        self.code += other.code
        self.docs += other.docs
        self.tests += other.tests
        self.other += other.other

    @property
    def total(self) -> int:
        return self.code + self.docs + self.tests + self.other


def command_output(cmd: list[str], cwd: Path) -> tuple[int, str]:
    result = subprocess.run(
        cmd,
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout


def parse_trial_index(name: str) -> int | None:
    if not name.startswith("trial-"):
        return None
    try:
        return int(name.split("-", 1)[1])
    except ValueError:
        return None


def load_post_state_workspace(bundle_path: Path) -> Path | None:
    manifest_path = bundle_path.parent / "post_state_manifest.json"
    if not manifest_path.exists():
        return None
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None

    workspace = payload.get("workspace")
    if not isinstance(workspace, str):
        return None

    workspace_path = Path(workspace)
    if not workspace_path.is_absolute():
        workspace_path = manifest_path.parent / workspace_path
    return workspace_path


def find_runs(root: Path) -> dict[tuple[str, int], Path]:
    index_path = root / "run_index.json"
    if index_path.exists():
        payload = json.loads(index_path.read_text(encoding="utf-8"))
        raw = payload.get("bundles", [])
        mapping: dict[tuple[str, int], Path] = {}
        for raw_path in raw:
            if not isinstance(raw_path, str):
                continue
            bundle = (root / raw_path).resolve()
            if not bundle.name == "bundle.json":
                bundle = bundle / "bundle.json"
            task = bundle.parent.parent.name
            trial = parse_trial_index(bundle.parent.name)
            if trial is None:
                continue
            mapping[(task, trial)] = bundle
        if mapping:
            return mapping

    mapping = {}
    for bundle in root.rglob("bundle.json"):
        task = bundle.parent.parent.name
        trial = parse_trial_index(bundle.parent.name)
        if trial is None:
            continue
        mapping[(task, trial)] = bundle
    return mapping


def resolve_workspace(bundle_path: Path) -> Path:
    candidate = bundle_path.parent / "workspace"
    if candidate.exists():
        return candidate
    manifest_workspace = load_post_state_workspace(bundle_path)
    if manifest_workspace is not None and manifest_workspace.exists():
        return manifest_workspace
    return candidate


def classify_path(path: str) -> str:
    normalized = Path(path)
    text = normalized.as_posix()
    stem = normalized.name
    parts = normalized.parts
    if text.startswith("tests/") or any(part == "tests" for part in parts):
        return "tests"
    if stem.startswith("test_") or stem.endswith("_test.py") or stem.endswith("_test.md"):
        return "tests"
    if normalized.suffix in DOC_EXTENSIONS:
        return "docs"
    if normalized.suffix in CODE_EXTENSIONS:
        return "code"
    if normalized.suffix == ".py" and "test" in parts:
        return "tests"
    return "other"


def count_lines(path: Path) -> int:
    try:
        return len(path.read_text(encoding="utf-8").splitlines())
    except (UnicodeDecodeError, OSError):
        return 0


def numstat_deltas(workspace: Path) -> LocationTotals:
    rc, out = command_output(
        ["git", "-C", str(workspace), "diff", "--numstat", "HEAD"],
        workspace,
    )
    if rc != 0:
        return LocationTotals()

    deltas = LocationTotals()
    for raw_line in out.splitlines():
        parts = raw_line.split("\t")
        if len(parts) < 3:
            continue
        added, removed, changed_file = parts[0], parts[1], parts[2]
        if is_transient_path(changed_file):
            continue
        try:
            added_int = int(added)
        except ValueError:
            added_int = 0
        try:
            removed_int = int(removed)
        except ValueError:
            removed_int = 0
        deltas.add(classify_path(changed_file), added_int + removed_int)

    # Include untracked file adds as additions (for completeness).
    _, status_out = command_output(
        [
            "git",
            "-C",
            str(workspace),
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
        ],
        workspace,
    )
    for line in status_out.splitlines():
        if not line.startswith("?? "):
            continue
        file_path = line[3:]
        if is_transient_path(file_path):
            continue
        absolute = workspace / file_path
        deltas.add(classify_path(file_path), count_lines(absolute))
    return deltas


def summarize(condition_dir: Path, trials: dict[tuple[str, int], Path]) -> tuple[LocationTotals, list[str], dict[str, Any]]:
    totals = LocationTotals()
    used_trials: list[str] = []
    trial_records: dict[str, dict[str, int]] = {}
    for key, bundle_path in sorted(trials.items()):
        workspace = bundle_path.parent / "workspace"
        workspace = resolve_workspace(bundle_path)
        trial_path = f"{key[0]}/trial-{key[1]}"
        if not workspace.exists():
            used_trials.append(f"missing workspace for {trial_path}")
            continue
        delta = numstat_deltas(workspace)
        totals.merge(delta)
        trial_records[trial_path] = {"code": delta.code, "docs": delta.docs, "tests": delta.tests, "other": delta.other}
    return totals, used_trials, trial_records


def format_summary(
    baseline_count: int,
    candidate_count: int,
    baseline_totals: LocationTotals,
    candidate_totals: LocationTotals,
) -> str:
    delta_code = candidate_totals.code - baseline_totals.code
    delta_docs = candidate_totals.docs - baseline_totals.docs
    delta_tests = candidate_totals.tests - baseline_totals.tests
    delta_other = candidate_totals.other - baseline_totals.other
    delta_total = candidate_totals.total - baseline_totals.total

    def mean(total: int, count: int) -> float:
        return total / count if count else 0.0

    lines = [
        "## Harness LOC Delta (paired trials)",
        "",
        f"- Paired baseline trials: {baseline_count}",
        f"- Paired candidate trials: {candidate_count}",
        "",
        "| Location | Baseline LOC | Candidate LOC | Candidate - Baseline |",
        "|---|---:|---:|---:|",
        f"| Code | {baseline_totals.code} | {candidate_totals.code} | {delta_code:+} |",
        f"| Docs | {baseline_totals.docs} | {candidate_totals.docs} | {delta_docs:+} |",
        f"| Tests | {baseline_totals.tests} | {candidate_totals.tests} | {delta_tests:+} |",
        f"| Other | {baseline_totals.other} | {candidate_totals.other} | {delta_other:+} |",
        f"| Total | {baseline_totals.total} | {candidate_totals.total} | {delta_total:+} |",
        "",
        f"- Baseline per-trial mean LOC: {mean(baseline_totals.total, baseline_count):.2f}",
        f"- Candidate per-trial mean LOC: {mean(candidate_totals.total, candidate_count):.2f}",
    ]
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate LOC summary for paired harness trials")
    parser.add_argument("--baseline", required=True, type=Path, help="Baseline run directory")
    parser.add_argument("--candidate", required=True, type=Path, help="Candidate run directory")
    parser.add_argument(
        "--markdown",
        type=Path,
        default=None,
        help="Optional path to write Markdown report block",
    )
    parser.add_argument(
        "--json",
        type=Path,
        default=None,
        help="Optional path to write machine-readable JSON",
    )
    parser.add_argument(
        "--append-report",
        type=Path,
        default=None,
        help="Optional comparison_report.md to append report block to",
    )
    parser.add_argument(
        "--expect-trials",
        type=int,
        default=None,
        help="Optional expected paired trial count",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    baseline_runs = find_runs(args.baseline)
    candidate_runs = find_runs(args.candidate)

    paired_keys = sorted(set(baseline_runs) & set(candidate_runs))
    if not paired_keys:
        raise SystemExit("no paired trials found; baseline and candidate task/trial sets do not overlap")

    baseline_map = {key: baseline_runs[key] for key in paired_keys}
    candidate_map = {key: candidate_runs[key] for key in paired_keys}

    baseline_totals, baseline_warnings, _ = summarize(args.baseline, baseline_map)
    candidate_totals, candidate_warnings, _ = summarize(args.candidate, candidate_map)

    paired_count = len(paired_keys)
    block = format_summary(
        paired_count,
        paired_count,
        baseline_totals,
        candidate_totals,
    )

    print(block)
    if args.expect_trials is not None and paired_count != args.expect_trials:
        print(f"WARNING: expected {args.expect_trials} paired trials, observed {paired_count}")

    if baseline_warnings or candidate_warnings:
        print("Warnings:")
        for message in (*baseline_warnings, *candidate_warnings):
            print(f"- {message}")

    payload = {
        "paired_trials": paired_count,
        "baseline": baseline_totals.__dict__,
        "candidate": candidate_totals.__dict__,
        "delta": {
            "code": candidate_totals.code - baseline_totals.code,
            "docs": candidate_totals.docs - baseline_totals.docs,
            "tests": candidate_totals.tests - baseline_totals.tests,
            "other": candidate_totals.other - baseline_totals.other,
            "total": candidate_totals.total - baseline_totals.total,
        },
    }

    if args.json is not None:
        args.json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if args.markdown is not None:
        args.markdown.write_text(block + "\n", encoding="utf-8")

    if args.append_report is not None:
        existing = args.append_report.read_text(encoding="utf-8") if args.append_report.exists() else ""
        if "## Harness LOC Delta (paired trials)" not in existing:
            args.append_report.write_text(existing.rstrip() + "\n\n" + block + "\n", encoding="utf-8")
        else:
            print(
                f"append skipped: marker already present in {args.append_report}",
            )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
