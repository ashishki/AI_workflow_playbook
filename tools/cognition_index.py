#!/usr/bin/env python3
"""Build a deterministic retrieval manifest for playbook cognition artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "1.0"
DEFAULT_DIRS = ("docs", "prompts", "templates", "reference", "ci", "schemas")
DEFAULT_FILES = ("README.md", "PLAYBOOK.md")
DEFAULT_SUFFIXES = {".md", ".txt", ".json", ".yml", ".yaml"}
EXCLUDED_PARTS = {
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
    "dist",
    "build",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Repository root to index.")
    parser.add_argument("--project-id", help="Stable project id. Defaults to root directory name.")
    parser.add_argument("--output", help="Write JSON manifest to this path.")
    parser.add_argument(
        "--include-code",
        action="store_true",
        help="Also index source/test files with common code suffixes.",
    )
    return parser.parse_args()


def is_excluded(path: Path) -> bool:
    return any(part in EXCLUDED_PARTS for part in path.parts)


def candidate_paths(root: Path, include_code: bool) -> list[Path]:
    suffixes = set(DEFAULT_SUFFIXES)
    if include_code:
        suffixes.update({".py", ".js", ".ts", ".tsx", ".jsx", ".sql"})

    paths: list[Path] = []
    for file_name in DEFAULT_FILES:
        path = root / file_name
        if path.exists():
            paths.append(path)

    for directory in DEFAULT_DIRS:
        base = root / directory
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if path.is_file() and path.suffix.lower() in suffixes and not is_excluded(path):
                paths.append(path)

    if include_code:
        for directory in ("src", "app", "tests", "scripts"):
            base = root / directory
            if not base.exists():
                continue
            for path in base.rglob("*"):
                if path.is_file() and path.suffix.lower() in suffixes and not is_excluded(path):
                    paths.append(path)

    return sorted(set(paths), key=lambda path: path.relative_to(root).as_posix())


def parse_frontmatter(text: str) -> dict[str, Any]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}

    end = None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end = index
            break
    if end is None:
        return {}

    result: dict[str, Any] = {}
    current_list_key: str | None = None
    for raw_line in lines[1:end]:
        line = raw_line.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith("  - ") and current_list_key:
            result.setdefault(current_list_key, []).append(line[4:].strip())
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        current_list_key = None
        if value == "":
            result[key] = []
            current_list_key = key
        elif value in {"true", "false"}:
            result[key] = value == "true"
        elif value.startswith("[") and value.endswith("]"):
            inner = value[1:-1].strip()
            result[key] = [item.strip().strip("\"'") for item in inner.split(",") if item.strip()]
        else:
            result[key] = value.strip("\"'")
    return result


def extract_headings(text: str) -> list[str]:
    headings: list[str] = []
    for line in text.splitlines():
        match = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if match:
            headings.append(match.group(2).strip())
    return headings


def extract_links(text: str) -> list[str]:
    links: set[str] = set()
    for match in re.finditer(r"\[[^\]]+\]\(([^)]+)\)", text):
        links.add(match.group(1).strip())
    for match in re.finditer(r"\[\[([^\]]+)\]\]", text):
        links.add(match.group(1).strip())
    return sorted(links)


def classify(path: Path, frontmatter: dict[str, Any]) -> str:
    if isinstance(frontmatter.get("artifact_kind"), str):
        return str(frontmatter["artifact_kind"])

    lower = path.as_posix().lower()
    name = path.name.lower()
    if name == "architecture.md":
        return "architecture"
    if name == "implementation_contract.md":
        return "contract"
    if name.startswith("tasks") and name.endswith(".md"):
        return "task_graph"
    if name == "codex_prompt.md":
        return "session_state"
    if name == "decision_log.md" or name == "decisions.md":
        return "decision_log"
    if name == "implementation_journal.md":
        return "journal"
    if name == "evidence_index.md":
        return "evidence_index"
    if name.endswith("_eval.md") or name in {"evaluation.md", "eval_cases.md"}:
        return "eval"
    if "/adr/" in lower or "/adrs/" in lower:
        return "adr"
    if "/audit/" in lower or "/archive/" in lower or "review" in name:
        return "review"
    if "/postmortem" in lower:
        return "postmortem"
    if "/hypoth" in lower:
        return "hypothesis"
    if "/research/" in lower or "research" in name:
        return "research"
    if "runbook" in name or "operator_workflow" in name:
        return "runbook"
    if name == "cognition_manifest.md":
        return "retrieval_manifest"
    if name == "readme.md":
        return "project_map"
    return "reference"


def is_canonical(path: Path, artifact_kind: str, frontmatter: dict[str, Any]) -> bool:
    if isinstance(frontmatter.get("canonical"), bool):
        return bool(frontmatter["canonical"])
    if artifact_kind in {
        "architecture",
        "contract",
        "task_graph",
        "session_state",
        "decision_log",
        "adr",
        "journal",
        "evidence_index",
        "eval",
        "review",
        "postmortem",
        "hypothesis",
        "runbook",
    }:
        return True
    return False


def is_generated(path: Path, frontmatter: dict[str, Any]) -> bool:
    if isinstance(frontmatter.get("generated"), bool):
        return bool(frontmatter["generated"])
    return "generated" in path.parts or path.name.startswith("PHASE_REPORT_LATEST")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def build_manifest(root: Path, project_id: str, include_code: bool) -> dict[str, Any]:
    artifacts: list[dict[str, Any]] = []
    for path in candidate_paths(root, include_code):
        text = read_text(path)
        rel = path.relative_to(root).as_posix()
        frontmatter = parse_frontmatter(text)
        artifact_kind = classify(Path(rel), frontmatter)
        headings = extract_headings(text)
        title = headings[0] if headings else path.stem.replace("_", " ").replace("-", " ").title()
        artifacts.append(
            {
                "path": rel,
                "artifact_kind": artifact_kind,
                "title": title,
                "canonical": is_canonical(Path(rel), artifact_kind, frontmatter),
                "generated": is_generated(Path(rel), frontmatter),
                "frontmatter": frontmatter,
                "headings": headings,
                "links": extract_links(text),
                "sha256": hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest(),
            }
        )

    return {
        "schema_version": SCHEMA_VERSION,
        "project_id": project_id,
        "root": root.as_posix(),
        "artifacts": artifacts,
    }


def main() -> int:
    args = parse_args()
    root = Path(args.root).expanduser().resolve()
    project_id = args.project_id or root.name
    manifest = build_manifest(root, project_id, args.include_code)
    output = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    if args.output:
        output_path = Path(args.output)
        if not output_path.is_absolute():
            output_path = root / output_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output, encoding="utf-8")
    else:
        print(output, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
