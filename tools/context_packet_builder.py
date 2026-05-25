#!/usr/bin/env python3
"""Build a bounded markdown context packet from a cognition manifest."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from pathlib import Path
from typing import Any


ROLE_ESSENTIALS: dict[str, set[str]] = {
    "strategist": {"architecture", "decision_log", "adr", "evidence_index", "eval"},
    "orchestrator": {"session_state", "task_graph", "decision_log", "journal", "evidence_index"},
    "implementer": {"session_state", "task_graph", "contract", "decision_log", "evidence_index"},
    "reviewer": {"contract", "task_graph", "decision_log", "adr", "evidence_index", "eval", "review"},
    "researcher": {"architecture", "decision_log", "research", "adr"},
    "postmortem-writer": {"session_state", "decision_log", "adr", "evidence_index", "eval", "review"},
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, help="Path to generated cognition index JSON.")
    parser.add_argument("--role", required=True, choices=sorted(ROLE_ESSENTIALS))
    parser.add_argument("--scope", action="append", default=[], help="Scope term. Repeatable.")
    parser.add_argument("--max-files", type=int, default=12)
    parser.add_argument("--max-chars-per-file", type=int, default=1200)
    parser.add_argument("--output", help="Write packet to this markdown path.")
    return parser.parse_args()


def slug(value: str) -> str:
    clean = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return clean or "scope"


def load_manifest(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def allow_template_context(project_id: str, scopes: list[str]) -> bool:
    if project_id == "ai-workflow-playbook":
        return True
    return any("template" in scope.lower() or "prompt" in scope.lower() for scope in scopes)


def score_artifact(artifact: dict[str, Any], role: str, scopes: list[str], project_id: str) -> tuple[int, str]:
    score = 0
    kind = artifact.get("artifact_kind", "")
    path = artifact.get("path", "")
    if path.startswith("templates/") and not allow_template_context(project_id, scopes):
        return -100, path
    if path.startswith("prompts/audit/") and not allow_template_context(project_id, scopes):
        return -100, path

    haystack = " ".join(
        [
            str(path),
            str(artifact.get("title", "")),
            " ".join(artifact.get("headings", [])),
            " ".join(artifact.get("links", [])),
            json.dumps(artifact.get("frontmatter", {}), sort_keys=True),
        ]
    ).lower()

    if kind in ROLE_ESSENTIALS[role]:
        score += 50
    if artifact.get("canonical"):
        score += 10
    if artifact.get("generated"):
        score -= 20
    if path.startswith("docs/"):
        score += 5
    if path.startswith("templates/"):
        score -= 12
    if "/archive/" in path or "/audit/" in path:
        score -= 8
    if path.endswith("CODEX_PROMPT.md") or path.endswith("tasks.md"):
        score += 8
    for scope in scopes:
        terms = [term for term in re.split(r"\s+", scope.lower()) if len(term) > 2]
        if scope.lower() in haystack:
            score += 40
        score += sum(8 for term in terms if term in haystack)
    return score, path


def select_artifacts(manifest: dict[str, Any], role: str, scopes: list[str], max_files: int) -> list[dict[str, Any]]:
    project_id = str(manifest.get("project_id", ""))
    scored = [
        (score_artifact(artifact, role, scopes, project_id), artifact)
        for artifact in manifest.get("artifacts", [])
    ]
    scored.sort(key=lambda item: (-item[0][0], item[0][1]))
    return [artifact for (score, _path), artifact in scored if score > 0][:max_files]


def excerpt(root: Path, artifact: dict[str, Any], max_chars: int) -> str:
    path = root / artifact["path"]
    if not path.exists():
        return "_Missing source file._"
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            if lines and lines[-1] != "":
                lines.append("")
            continue
        lines.append(line.rstrip())
        if sum(len(item) + 1 for item in lines) >= max_chars:
            break
    result = "\n".join(lines).strip()
    if len(result) > max_chars:
        result = result[:max_chars].rstrip() + "\n..."
    return result or "_No text excerpt available._"


def render_packet(
    manifest_path: Path,
    manifest: dict[str, Any],
    role: str,
    scopes: list[str],
    artifacts: list[dict[str, Any]],
    max_chars_per_file: int,
) -> str:
    project_id = manifest["project_id"]
    scope_text = "; ".join(scopes) if scopes else "general"
    created = dt.date.today().isoformat()
    root = Path(manifest["root"])
    lines = [
        "---",
        "artifact_kind: context_packet",
        f"project: {project_id}",
        f"role: {role}",
        f"scope: {scope_text}",
        f"source_manifest: {manifest_path.as_posix()}",
        "generated: true",
        "canonical: false",
        f"created: {created}",
        "---",
        "",
        f"# Context Packet - {project_id} - {role}",
        "",
        "## Scope",
        "",
        scope_text,
        "",
        "## Canonical Artifacts",
        "",
        "| Artifact | Kind | Canonical | Why included |",
        "|----------|------|-----------|--------------|",
    ]

    for artifact in artifacts:
        reason = "role essential"
        if scopes and any(scope.lower() in json.dumps(artifact, sort_keys=True).lower() for scope in scopes):
            reason = "scope match"
        lines.append(
            f"| `{artifact['path']}` | {artifact['artifact_kind']} | {artifact['canonical']} | {reason} |"
        )

    lines.extend(["", "## Included Context", ""])
    for artifact in artifacts:
        lines.extend(
            [
                f"### {artifact['title']}",
                "",
                f"- Path: `{artifact['path']}`",
                f"- Kind: `{artifact['artifact_kind']}`",
                f"- SHA-256: `{artifact['sha256']}`",
                "",
                "```text",
                excerpt(root, artifact, max_chars_per_file),
                "```",
                "",
            ]
        )

    lines.extend(
        [
            "## Excluded Context",
            "",
            "Older archives, generated notes, and unrelated project material were excluded unless they matched the role or scope.",
            "",
            "## Evidence",
            "",
            "Use the cited canonical paths above. Do not treat this generated packet as authority.",
            "",
            "## Next Action",
            "",
            "Proceed only within the declared role and scope. If required evidence is missing, update `Context-Refs`, the evidence index, or the decision log before acting.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    manifest_path = Path(args.manifest).expanduser().resolve()
    manifest = load_manifest(manifest_path)
    artifacts = select_artifacts(manifest, args.role, args.scope, args.max_files)
    packet = render_packet(
        manifest_path=manifest_path,
        manifest=manifest,
        role=args.role,
        scopes=args.scope,
        artifacts=artifacts,
        max_chars_per_file=args.max_chars_per_file,
    )
    if args.output:
        output_path = Path(args.output)
        if not output_path.is_absolute():
            output_path = Path(manifest["root"]) / output_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(packet, encoding="utf-8")
    else:
        print(packet)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
