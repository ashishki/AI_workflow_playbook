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
    import feature_review_policy
    import render_codex_exec_prompt
except ImportError:  # pragma: no cover
    from tools import feature_design_lib, feature_review_policy, render_codex_exec_prompt  # type: ignore


class ApprovalError(ValueError):
    pass


DESIGN_REVIEW_RECORD_SCHEMA = "playbook.design_review_record.v1"


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


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


def design_review_record_path(root: Path, feature_id: str, role: str) -> Path:
    return root / ".playbook-artifacts/reviews" / feature_id / "design" / f"{role}.review.json"


def write_design_review_record(
    *,
    root: Path,
    feature_id: str,
    role: str,
    report_path: str,
    reviewed_design: dict[str, Any],
    reviewer_binding: str,
    read_only: bool = True,
    generated_at: str | None = None,
) -> dict[str, Any]:
    if role not in feature_review_policy.DESIGN_REVIEW_ROLES:
        raise ApprovalError(f"unsupported design review role: {role}")
    path = feature_design_lib.safe_repo_path(root, report_path)
    if path is None:
        raise ApprovalError(f"review report path must stay inside repository: {report_path}")
    if not path.exists():
        raise ApprovalError(f"required review report is missing: {report_path}")
    parsed = render_codex_exec_prompt.parse_required_marker(role, path.read_text(encoding="utf-8", errors="replace"))
    hashes = feature_design_lib.design_hashes(root, reviewed_design)
    record = {
        "schema_version": DESIGN_REVIEW_RECORD_SCHEMA,
        "feature_id": feature_id,
        "role": role,
        "verdict": parsed["verdict"],
        "report_path": feature_design_lib.repo_rel(root, path),
        "report_sha256": feature_design_lib.sha256_file(path),
        "reviewed_markdown_sha256": hashes["markdown_sha256"],
        "reviewed_registry_payload_sha256": hashes["registry_payload_sha256"],
        "generated_at": generated_at or utc_now(),
        "reviewer_binding": reviewer_binding,
        "read_only": read_only,
    }
    feature_design_lib.atomic_write_json(design_review_record_path(root, feature_id, role), record)
    return record


def parse_design_review_record(
    *,
    root: Path,
    feature_id: str,
    role: str,
    current_design: dict[str, Any],
    required: bool,
) -> dict[str, str]:
    record_path = design_review_record_path(root, feature_id, role)
    if not record_path.exists():
        label = "required" if required else "optional"
        raise ApprovalError(f"missing {label} design review record: {feature_id} {role}")
    try:
        record = json.loads(record_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ApprovalError(f"invalid design review record {feature_design_lib.relative(root, record_path)}: {exc.msg}") from exc
    if not isinstance(record, dict):
        raise ApprovalError(f"design review record must be an object: {feature_design_lib.relative(root, record_path)}")
    expected = {
        "schema_version": DESIGN_REVIEW_RECORD_SCHEMA,
        "feature_id": feature_id,
        "role": role,
    }
    for key, value in expected.items():
        if record.get(key) != value:
            raise ApprovalError(f"design review record {role} has invalid {key}")
    if record.get("read_only") is not True:
        raise ApprovalError(f"design review record {role} must declare read_only=true")
    if not str(record.get("reviewer_binding", "")).strip():
        raise ApprovalError(f"design review record {role} missing reviewer_binding")
    verdict = str(record.get("verdict", "")).strip()
    if verdict == "STOP_SHIP":
        raise ApprovalError(f"STOP_SHIP review blocks approval: {role}")
    if verdict not in {"PASS", "ADVISORY"}:
        raise ApprovalError(f"design review record {role} has unacceptable verdict: {verdict or '[missing]'}")
    report_path_raw = str(record.get("report_path", "")).strip()
    report_path = feature_design_lib.safe_repo_path(root, report_path_raw)
    if report_path is None:
        raise ApprovalError(f"review report path must stay inside repository: {report_path_raw}")
    if not report_path.exists():
        raise ApprovalError(f"required review report is missing: {report_path_raw}")
    expected_report_sha = str(record.get("report_sha256", "")).strip()
    actual_report_sha = feature_design_lib.sha256_file(report_path)
    if expected_report_sha != actual_report_sha:
        raise ApprovalError(f"design review record {role} is stale: report hash changed")
    try:
        parsed = render_codex_exec_prompt.parse_required_marker(role, report_path.read_text(encoding="utf-8", errors="replace"))
    except ValueError as exc:
        raise ApprovalError(str(exc)) from exc
    if parsed["verdict"] != verdict:
        raise ApprovalError(f"design review record {role} verdict disagrees with report marker")
    hashes = feature_design_lib.design_hashes(root, current_design)
    if str(record.get("reviewed_markdown_sha256", "")).strip() != hashes["markdown_sha256"]:
        raise ApprovalError(f"design review record {role} is stale: Feature Design Markdown changed")
    if str(record.get("reviewed_registry_payload_sha256", "")).strip() != hashes["registry_payload_sha256"]:
        raise ApprovalError(f"design review record {role} is stale: Feature Design registry payload changed")
    return {
        "role": role,
        "path": feature_design_lib.repo_rel(root, report_path),
        "sha256": actual_report_sha,
        "verdict": verdict,
        "marker": str(parsed.get("marker", "")),
        "record_path": feature_design_lib.repo_rel(root, record_path),
        "record_sha256": feature_design_lib.sha256_file(record_path),
        "reviewed_markdown_sha256": hashes["markdown_sha256"],
        "reviewed_registry_payload_sha256": hashes["registry_payload_sha256"],
    }


def required_design_review_refs(root: Path, feature_id: str, design: dict[str, Any]) -> list[dict[str, str]]:
    refs: list[dict[str, str]] = []
    for item in feature_review_policy.design_reviews(design):
        if not item.get("required"):
            continue
        role = str(item.get("role", "")).strip()
        refs.append(
            parse_design_review_record(
                root=root,
                feature_id=feature_id,
                role=role,
                current_design=design,
                required=True,
            )
        )
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
    feature_id = str(design.get("feature_id", payload.get("feature_id", ""))).strip()
    required_refs = required_design_review_refs(root, feature_id, payload)
    explicit_refs = [parse_review_ref(root, ref) for ref in (review_refs or [])]
    by_role: dict[str, dict[str, str]] = {ref["role"]: ref for ref in explicit_refs}
    by_role.update({ref["role"]: ref for ref in required_refs})
    parsed_refs = list(by_role.values())
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
    approved = approve_registry_payload(
        root=root,
        registry_path=registry_path,
        payload=payload,
        human_id=human_id,
        approval_method=approval_method,
        approval_ref=approval_ref,
        approved_at=approved_at or dt.date.today().isoformat(),
        review_refs=review_refs,
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
