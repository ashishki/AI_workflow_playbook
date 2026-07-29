#!/usr/bin/env python3
"""Human-only approval for exact Feature Design versions."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    import feature_design_lib
    import render_codex_exec_prompt
except ImportError:  # pragma: no cover
    from tools import feature_design_lib, render_codex_exec_prompt  # type: ignore


class ApprovalError(ValueError):
    pass


def git_status(root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "status", "--short"],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return result.stdout.splitlines() if result.returncode == 0 and result.stdout else []


def git_commit(root: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 and result.stdout.strip() else "not-a-git-repository"


def parse_review_ref(root: Path, ref: dict[str, str]) -> dict[str, str]:
    role = str(ref.get("role", "")).strip()
    raw_path = str(ref.get("path", "")).strip()
    if role not in render_codex_exec_prompt.DESIGN_REVIEW_ROLES:
        raise ApprovalError(f"unsupported review role for design approval: {role}")
    path = feature_design_lib.safe_repo_path(root, raw_path)
    if path is None:
        raise ApprovalError(f"review report path must stay inside repository: {raw_path}")
    if not path.exists():
        raise ApprovalError(f"required review report is missing: {raw_path}")
    try:
        parsed = render_codex_exec_prompt.parse_required_marker(role, path.read_text(encoding="utf-8", errors="replace"))
    except ValueError as exc:
        raise ApprovalError(str(exc)) from exc
    verdict = str(parsed["verdict"])
    if verdict == "STOP_SHIP":
        raise ApprovalError(f"STOP_SHIP review blocks approval: {role} {raw_path}")
    return {
        "role": role,
        "path": feature_design_lib.repo_rel(root, path),
        "sha256": feature_design_lib.sha256_file(path),
        "verdict": verdict,
        "marker": str(parsed.get("marker", "")),
    }


def load_required_review_refs(root: Path, feature_id: str) -> list[dict[str, str]]:
    required_path = root / ".playbook-artifacts/workflows" / feature_id / "required_reviews.json"
    if not required_path.exists():
        return []
    data = json.loads(required_path.read_text(encoding="utf-8"))
    refs: list[dict[str, str]] = []
    for item in data.get("reviews", []):
        if not isinstance(item, dict) or not item.get("required"):
            continue
        path = str(item.get("report_path", "")).strip()
        role = str(item.get("role", "")).strip()
        if not path:
            raise ApprovalError(f"required review {role} has no report_path")
        refs.append({"role": role, "path": path})
    return refs


def validate_design_session_boundary(root: Path, feature_id: str) -> list[str]:
    session_path = root / ".playbook-artifacts/workflows" / feature_id / "design_session.json"
    if not session_path.exists():
        return []
    session = json.loads(session_path.read_text(encoding="utf-8"))
    allowed = set(str(path) for path in session.get("allowed_design_paths", []))
    allowed_prefixes = [".playbook-artifacts/"]
    initial_dirty = set(str(line) for line in session.get("dirty_state", []))
    current_dirty = set(git_status(root))
    new_dirty = current_dirty - initial_dirty
    violations: list[str] = []
    for line in sorted(new_dirty):
        path = line[3:].strip() if len(line) > 3 else line.strip()
        if path in allowed or any(path.startswith(prefix) for prefix in allowed_prefixes):
            continue
        violations.append(path)
    base_commit = str(session.get("base_commit", "")).strip()
    if base_commit and base_commit != git_commit(root):
        result = subprocess.run(
            ["git", "diff", "--name-only", base_commit, "HEAD", "--"],
            cwd=root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if result.returncode == 0:
            for path in result.stdout.splitlines():
                if path in allowed or any(path.startswith(prefix) for prefix in allowed_prefixes):
                    continue
                violations.append(path)
    return sorted(set(violations))


def approve_registry_payload(
    *,
    root: Path,
    registry_path: Path,
    payload: dict[str, Any],
    human_id: str,
    approval_method: str,
    approval_ref: str,
    approved_at: str,
    review_refs: list[dict[str, str]] | None,
    advisory_acknowledgement: str,
) -> dict[str, Any]:
    root = root.resolve()
    registry_path = registry_path if registry_path.is_absolute() else root / registry_path
    findings, design = feature_design_lib.validate_design_file(root, registry_path)
    errors = [finding for finding in findings if finding.severity == "error"]
    if errors:
        raise ApprovalError("; ".join(f"{finding.check_id}: {finding.message}" for finding in errors))
    if design is None:
        raise ApprovalError("feature design registry is invalid")
    payload = dict(payload)
    if str(payload.get("feature_id")) != str(design.get("feature_id")):
        raise ApprovalError("approval payload feature_id disagrees with registry")
    human = human_id.strip()
    if not human or human.lower() in feature_design_lib.SELF_APPROVERS or "codex" in human.lower():
        raise ApprovalError("model/agent self-approval is not valid")
    if payload.get("approval_policy") == "human_required" and human.lower() != "human" and not human.lower().startswith("human:"):
        raise ApprovalError("human_required design requires human:<identity> provenance")
    parsed_refs = [parse_review_ref(root, ref) for ref in (review_refs or [])]
    advisories = [ref for ref in parsed_refs if ref["verdict"] == "ADVISORY"]
    if advisories and not advisory_acknowledgement.strip():
        raise ApprovalError("ADVISORY review findings require recorded human acknowledgement")
    updated = dict(payload)
    updated["status"] = "approved"
    updated["approved_by"] = human
    updated["approved_at"] = approved_at
    updated["approval_method"] = approval_method
    updated["approval_ref"] = approval_ref
    updated["approved_review_refs"] = parsed_refs
    if advisory_acknowledgement.strip():
        updated["advisory_acknowledgement"] = advisory_acknowledgement.strip()
    updated["approved_markdown_sha256"] = feature_design_lib.markdown_sha256(root, updated) or ""
    updated["approved_registry_payload_sha256"] = feature_design_lib.registry_payload_sha256(updated)
    post_findings = feature_design_lib.validate_approval(root, registry_path, updated)
    post_errors = [finding for finding in post_findings if finding.severity == "error"]
    if post_errors:
        raise ApprovalError("; ".join(f"{finding.check_id}: {finding.message}" for finding in post_errors))
    return updated


def approve_design(
    *,
    root: Path,
    feature_id: str,
    human_id: str,
    review_refs: list[dict[str, str]] | None,
    advisory_acknowledgement: str,
    approval_method: str,
    approval_ref: str,
    approved_at: str | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    registry_path = root / "docs/design" / f"{feature_id}.design.json"
    payload, error = feature_design_lib.load_json(registry_path)
    if error or payload is None:
        raise ApprovalError(error or "missing feature design registry")
    drift = validate_design_session_boundary(root, feature_id)
    if drift:
        raise ApprovalError("DESIGN_PHASE_CODE_DRIFT: " + ", ".join(drift))
    refs = review_refs if review_refs is not None else load_required_review_refs(root, feature_id)
    approved = approve_registry_payload(
        root=root,
        registry_path=registry_path,
        payload=payload,
        human_id=human_id,
        approval_method=approval_method,
        approval_ref=approval_ref,
        approved_at=approved_at or dt.date.today().isoformat(),
        review_refs=refs,
        advisory_acknowledgement=advisory_acknowledgement,
    )
    feature_design_lib.atomic_write_json(registry_path, approved)
    approval_artifact = root / approval_ref
    if not approval_artifact.is_absolute():
        approval_artifact = root / approval_ref
    approval_artifact.parent.mkdir(parents=True, exist_ok=True)
    approval_artifact.write_text(
        json.dumps(
            {
                "schema_version": "playbook.feature_design_approval.v1",
                "feature_id": feature_id,
                "approved_by": approved["approved_by"],
                "approved_at": approved["approved_at"],
                "approved_markdown_sha256": approved["approved_markdown_sha256"],
                "approved_registry_payload_sha256": approved["approved_registry_payload_sha256"],
                "approved_review_refs": approved.get("approved_review_refs", []),
                "advisory_acknowledgement": approved.get("advisory_acknowledgement", ""),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return approved


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".")
    parser.add_argument("--feature-id", required=True)
    parser.add_argument("--review-ref", action="append", default=[], help="Required review as role=path.")
    return parser


def parse_cli_review_refs(values: list[str]) -> list[dict[str, str]]:
    refs: list[dict[str, str]] = []
    for value in values:
        if "=" not in value:
            raise ApprovalError(f"review ref must use role=path: {value}")
        role, path = value.split("=", 1)
        refs.append({"role": role.strip(), "path": path.strip()})
    return refs


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.root).resolve()
    if not sys.stdin.isatty():
        print("approve_feature_design: interactive TTY is required for human approval", file=sys.stderr)
        return 2
    print(f"About to approve exact Feature Design: {args.feature_id}")
    confirmation = input("Type the exact feature ID to continue: ").strip()
    if confirmation != args.feature_id:
        print("approve_feature_design: feature ID confirmation mismatch", file=sys.stderr)
        return 1
    human_id = input("Human identity (example: human:artem): ").strip()
    if not human_id:
        print("approve_feature_design: human identity is required", file=sys.stderr)
        return 1
    review_refs = parse_cli_review_refs(args.review_ref) if args.review_ref else None
    advisories_ack = input("Advisory acknowledgement or 'none': ").strip()
    if advisories_ack.lower() == "none":
        advisories_ack = ""
    approval_ref = f".playbook-artifacts/workflows/{args.feature_id}/approval.json"
    try:
        approve_design(
            root=root,
            feature_id=args.feature_id,
            human_id=human_id,
            review_refs=review_refs,
            advisory_acknowledgement=advisories_ack,
            approval_method="interactive_tty",
            approval_ref=approval_ref,
        )
    except ApprovalError as exc:
        print(f"approve_feature_design: {exc}", file=sys.stderr)
        return 1
    print(f"approve_feature_design: approved {args.feature_id} approval_ref={approval_ref}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
