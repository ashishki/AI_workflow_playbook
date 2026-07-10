#!/usr/bin/env python3
"""Validate an EvidenceBundle and its referenced machine artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from jsonschema import Draft202012Validator
except ImportError:  # pragma: no cover - covered by CI dependency installation.
    Draft202012Validator = None  # type: ignore[assignment]


FORBIDDEN_AGENT_VERDICT_FIELDS = {
    "passed",
    "verified",
    "accepted",
    "release_ready",
    "final_verdict",
}

BUNDLE_REQUIRED = {
    "schema_version",
    "bundle_id",
    "manifest_hash",
    "repository",
    "task_id",
    "commit_before",
    "commit_after",
    "task_spec_version",
    "condition",
    "adapter_version",
    "environment_digest",
    "command_receipts",
    "trace_refs",
    "post_state_manifest",
    "scorer_outputs",
    "failure_records",
    "cost_record",
    "generated_report_ref",
    "verifier_identity",
    "verification_timestamp",
}

RECEIPT_REQUIRED = {
    "schema_version",
    "receipt_id",
    "task_id",
    "producer",
    "command_argv",
    "working_directory",
    "start_timestamp",
    "end_timestamp",
    "exit_code",
    "stdout_artifact_path",
    "stdout_sha256",
    "stderr_artifact_path",
    "stderr_sha256",
    "repo_commit_before",
    "repo_commit_after",
    "dirty_state_before",
    "dirty_state_after",
    "diff_stat_artifact_path",
    "diff_stat_sha256",
    "environment_summary",
    "redaction_status",
}

FAILURE_REQUIRED = {
    "schema_version",
    "failure_id",
    "run_id",
    "task_id",
    "stage",
    "failure_class",
    "owner_class",
    "retryable",
    "retry_count",
    "terminal",
    "message",
    "evidence_refs",
    "score_treatment",
    "invalid_run",
}

SCHEMA_ROOT = Path(__file__).resolve().parents[1] / "schemas"
SCHEMA_FILES = {
    "bundle": "evidence_bundle.schema.json",
    "receipt": "command_receipt.schema.json",
    "failure": "failure_record.schema.json",
    "run_result": "run_result.schema.json",
}


@dataclass
class Finding:
    severity: str
    check_id: str
    message: str
    path: str = ""

    def as_dict(self) -> dict[str, str]:
        return {
            "severity": self.severity,
            "check_id": self.check_id,
            "message": self.message,
            "path": self.path,
        }


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json_hash(data: dict[str, Any]) -> str:
    cloned = dict(data)
    cloned["manifest_hash"] = ""
    payload = json.dumps(cloned, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def load_json(path: Path) -> tuple[dict[str, Any] | None, list[Finding]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, [Finding("error", "JSON_INVALID", f"{exc.msg} at line {exc.lineno}", str(path))]
    if not isinstance(data, dict):
        return None, [Finding("error", "JSON_OBJECT_REQUIRED", "artifact must be a JSON object", str(path))]
    return data, []


def schema_validator(name: str) -> Any | None:
    if Draft202012Validator is None:
        return None
    schema = json.loads((SCHEMA_ROOT / SCHEMA_FILES[name]).read_text(encoding="utf-8"))
    return Draft202012Validator(schema)


def validate_schema(data: dict[str, Any], name: str, path: Path) -> list[Finding]:
    validator = schema_validator(name)
    if validator is None:
        return [
            Finding(
                "error",
                "SCHEMA_VALIDATOR_MISSING",
                "jsonschema is required to validate evidence contracts",
                str(path),
            )
        ]
    findings: list[Finding] = []
    for error in sorted(validator.iter_errors(data), key=lambda item: list(item.path)):
        location = ".".join(str(part) for part in error.path)
        suffix = f" at {location}" if location else ""
        findings.append(
            Finding(
                "error",
                f"{name.upper()}_SCHEMA",
                f"{error.message}{suffix}",
                str(path),
            )
        )
    return findings


def resolve_ref(bundle_dir: Path, artifact_ref: dict[str, Any]) -> Path:
    path = Path(str(artifact_ref.get("path", "")))
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"path escape forbidden: {path}")
    resolved = (bundle_dir / path).resolve()
    resolved.relative_to(bundle_dir.resolve())
    return resolved


def validate_artifact_ref(bundle_dir: Path, artifact_ref: dict[str, Any], check_id: str) -> list[Finding]:
    findings: list[Finding] = []
    if not isinstance(artifact_ref, dict):
        return [Finding("error", check_id, "artifact ref must be an object")]
    try:
        path = resolve_ref(bundle_dir, artifact_ref)
    except ValueError as exc:
        return [Finding("error", "ARTIFACT_PATH_ESCAPE", str(exc))]
    expected = artifact_ref.get("sha256")
    if not path.exists():
        findings.append(Finding("error", check_id, f"referenced artifact missing: {path}", str(path)))
        return findings
    actual = sha256_file(path)
    if expected != actual:
        findings.append(
            Finding(
                "error",
                check_id,
                f"sha256 mismatch for {path}: expected {expected}, actual {actual}",
                str(path),
            )
        )
    return findings


def validate_required(data: dict[str, Any], required: set[str], check_id: str, path: Path) -> list[Finding]:
    missing = sorted(required - set(data))
    if not missing:
        return []
    return [Finding("error", check_id, "missing required fields: " + ", ".join(missing), str(path))]


def validate_no_forbidden_verdict(data: dict[str, Any], path: Path, *, allow_final_verdict: bool = False) -> list[Finding]:
    forbidden = set(FORBIDDEN_AGENT_VERDICT_FIELDS)
    if allow_final_verdict:
        forbidden.discard("final_verdict")
    present = sorted(forbidden & set(data))
    if present:
        return [
            Finding(
                "error",
                "EVIDENCE_MANUAL_VERDICT",
                "manual verdict/status fields are not allowed here: " + ", ".join(present),
                str(path),
            )
        ]
    return []


def validate_receipt(bundle_dir: Path, ref: dict[str, Any], bundle_task_id: str) -> tuple[list[Finding], dict[str, Any] | None]:
    findings = validate_artifact_ref(bundle_dir, ref, "ARTIFACT_HASH")
    if findings:
        return findings, None
    path = resolve_ref(bundle_dir, ref)
    receipt, load_findings = load_json(path)
    findings.extend(load_findings)
    if receipt is None:
        return findings, None
    findings.extend(validate_required(receipt, RECEIPT_REQUIRED, "RECEIPT_SCHEMA", path))
    findings.extend(validate_schema(receipt, "receipt", path))
    findings.extend(validate_no_forbidden_verdict(receipt, path))
    if receipt.get("schema_version") != "playbook.command_receipt.v1":
        findings.append(Finding("error", "RECEIPT_SCHEMA", "unsupported receipt schema_version", str(path)))
    if receipt.get("task_id") != bundle_task_id:
        findings.append(
            Finding(
                "error",
                "BUNDLE_TASK_MISMATCH",
                f"receipt task_id {receipt.get('task_id')} does not match bundle task_id {bundle_task_id}",
                str(path),
            )
        )
    for artifact_path_key, hash_key in (
        ("stdout_artifact_path", "stdout_sha256"),
        ("stderr_artifact_path", "stderr_sha256"),
        ("diff_stat_artifact_path", "diff_stat_sha256"),
    ):
        artifact_path = Path(str(receipt.get(artifact_path_key, "")))
        if artifact_path.is_absolute() or ".." in artifact_path.parts:
            findings.append(
                Finding(
                    "error",
                    "RECEIPT_ARTIFACT_PATH_ESCAPE",
                    f"receipt artifact path escapes receipt directory: {artifact_path}",
                    str(path),
                )
            )
            continue
        artifact_path = (path.parent / artifact_path).resolve()
        try:
            artifact_path.relative_to(path.parent.resolve())
        except ValueError:
            findings.append(
                Finding(
                    "error",
                    "RECEIPT_ARTIFACT_PATH_ESCAPE",
                    f"receipt artifact path escapes receipt directory: {artifact_path}",
                    str(path),
                )
            )
            continue
        if not artifact_path.exists():
            findings.append(
                Finding("error", "RECEIPT_ARTIFACT_MISSING", f"receipt artifact missing: {artifact_path}", str(path))
            )
            continue
        actual = sha256_file(artifact_path)
        if actual != receipt.get(hash_key):
            findings.append(
                Finding(
                    "error",
                    "RECEIPT_ARTIFACT_HASH",
                    f"{artifact_path_key} hash mismatch: expected {receipt.get(hash_key)}, actual {actual}",
                    str(artifact_path),
                )
            )
    return findings, receipt


def validate_failure_record(record: dict[str, Any], bundle_task_id: str, source: str) -> list[Finding]:
    findings: list[Finding] = []
    missing = sorted(FAILURE_REQUIRED - set(record))
    if missing:
        findings.append(Finding("error", "FAILURE_RECORD_SCHEMA", "missing required fields: " + ", ".join(missing), source))
        return findings
    findings.extend(validate_schema(record, "failure", Path(source)))
    if record.get("task_id") != bundle_task_id:
        findings.append(
            Finding(
                "error",
                "BUNDLE_TASK_MISMATCH",
                f"failure task_id {record.get('task_id')} does not match bundle task_id {bundle_task_id}",
                source,
            )
        )
    if record.get("failure_class") == "environment_failure":
        if record.get("owner_class") != "environment":
            findings.append(
                Finding(
                    "error",
                    "FAILURE_OWNER_MISCLASSIFIED",
                    "environment_failure must have owner_class=environment",
                    source,
                )
            )
        if record.get("score_treatment") != "invalid_run_exclude_from_capability_score" or record.get("invalid_run") is not True:
            findings.append(
                Finding(
                    "error",
                    "FAILURE_INVALID_RUN_TREATMENT",
                    "environment_failure must be invalid_run and excluded from capability score",
                    source,
                )
            )
    if record.get("failure_class") == "policy_failure":
        if record.get("score_treatment") != "policy_gate_failure" or record.get("terminal") is not True:
            findings.append(
                Finding(
                    "error",
                    "POLICY_GATE_TREATMENT",
                    "policy_failure must be terminal and use score_treatment=policy_gate_failure",
                    source,
                )
            )
    return findings


def validate_scorer_output(path: Path) -> tuple[list[Finding], dict[str, Any] | None]:
    if path.suffix.lower() != ".json":
        return [], None
    data, findings = load_json(path)
    if data is None:
        return findings, None
    if "scorer_id" not in data or "scorer_version" not in data:
        findings.append(
            Finding("error", "SCORER_PROVENANCE", "scorer output must include scorer_id and scorer_version", str(path))
        )
    return findings, data


def validate_bundle(bundle_path: Path, baseline_path: Path | None = None) -> dict[str, Any]:
    bundle_path = bundle_path.resolve()
    bundle_dir = bundle_path.parent
    findings: list[Finding] = []
    bundle, load_findings = load_json(bundle_path)
    findings.extend(load_findings)
    receipts: list[dict[str, Any]] = []
    scorer_outputs: list[dict[str, Any]] = []
    terminal_policy_failure = False
    if bundle is None:
        return report(bundle_path, findings, receipts)

    findings.extend(validate_required(bundle, BUNDLE_REQUIRED, "BUNDLE_SCHEMA", bundle_path))
    findings.extend(validate_schema(bundle, "bundle", bundle_path))
    findings.extend(validate_no_forbidden_verdict(bundle, bundle_path))
    if bundle.get("schema_version") != "playbook.evidence_bundle.v1":
        findings.append(Finding("error", "BUNDLE_SCHEMA", "unsupported evidence bundle schema_version", str(bundle_path)))
    if not bundle.get("environment_digest"):
        findings.append(Finding("error", "BUNDLE_ENVIRONMENT_DIGEST", "environment_digest is required", str(bundle_path)))
    expected_hash = bundle.get("manifest_hash")
    actual_hash = canonical_json_hash(bundle)
    if expected_hash != actual_hash:
        findings.append(
            Finding(
                "error",
                "BUNDLE_MANIFEST_HASH",
                f"manifest_hash mismatch: expected {expected_hash}, actual {actual_hash}",
                str(bundle_path),
            )
        )

    task_id = str(bundle.get("task_id", ""))
    for ref in bundle.get("command_receipts", []) if isinstance(bundle.get("command_receipts"), list) else []:
        receipt_findings, receipt = validate_receipt(bundle_dir, ref, task_id)
        findings.extend(receipt_findings)
        if receipt is not None:
            receipts.append(receipt)

    for key in ("trace_refs", "scorer_outputs"):
        refs = bundle.get(key, [])
        if not isinstance(refs, list):
            findings.append(Finding("error", "BUNDLE_SCHEMA", f"{key} must be a list", str(bundle_path)))
            continue
        for ref in refs:
            ref_findings = validate_artifact_ref(bundle_dir, ref, "ARTIFACT_HASH")
            findings.extend(ref_findings)
            if key == "trace_refs" and isinstance(ref, dict) and not ref_findings:
                trace_path = resolve_ref(bundle_dir, ref)
                if trace_path.name == "run_result.json":
                    run_result, load = load_json(trace_path)
                    findings.extend(load)
                    if run_result is not None:
                        findings.extend(validate_schema(run_result, "run_result", trace_path))
            if key == "scorer_outputs" and isinstance(ref, dict) and not ref_findings:
                scorer_findings, scorer_data = validate_scorer_output(resolve_ref(bundle_dir, ref))
                findings.extend(scorer_findings)
                if scorer_data is not None:
                    scorer_outputs.append(scorer_data)

    if isinstance(bundle.get("post_state_manifest"), dict):
        findings.extend(validate_artifact_ref(bundle_dir, bundle["post_state_manifest"], "ARTIFACT_HASH"))
    else:
        findings.append(Finding("error", "BUNDLE_SCHEMA", "post_state_manifest must be an artifact ref", str(bundle_path)))

    generated_report_ref = bundle.get("generated_report_ref")
    if isinstance(generated_report_ref, dict):
        findings.extend(validate_artifact_ref(bundle_dir, generated_report_ref, "ARTIFACT_HASH"))
    elif generated_report_ref is not None:
        findings.append(Finding("error", "BUNDLE_SCHEMA", "generated_report_ref must be null or artifact ref", str(bundle_path)))

    for item in bundle.get("failure_records", []) if isinstance(bundle.get("failure_records"), list) else []:
        if isinstance(item, dict) and "path" in item and "sha256" in item:
            ref_findings = validate_artifact_ref(bundle_dir, item, "ARTIFACT_HASH")
            findings.extend(ref_findings)
            if ref_findings:
                continue
            data, load = load_json(resolve_ref(bundle_dir, item))
            findings.extend(load)
            if data is not None:
                findings.extend(validate_failure_record(data, task_id, str(resolve_ref(bundle_dir, item))))
                if data.get("failure_class") == "policy_failure" and data.get("terminal") is True:
                    terminal_policy_failure = True
        elif isinstance(item, dict):
            findings.extend(validate_failure_record(item, task_id, str(bundle_path)))
            if item.get("failure_class") == "policy_failure" and item.get("terminal") is True:
                terminal_policy_failure = True
        else:
            findings.append(Finding("error", "FAILURE_RECORD_SCHEMA", "failure record must be object or artifact ref", str(bundle_path)))

    if terminal_policy_failure:
        passing = [output.get("scorer_id", "unknown") for output in scorer_outputs if output.get("verdict") == "passed"]
        if passing:
            findings.append(
                Finding(
                    "error",
                    "POLICY_GATE_CONFLICT",
                    "terminal policy failure cannot coexist with passing scorer verdict(s): " + ", ".join(passing),
                    str(bundle_path),
                )
            )

    if baseline_path:
        baseline, load = load_json(baseline_path.resolve())
        findings.extend(load)
        if baseline is not None:
            for key in ("task_id", "task_spec_version", "repository"):
                if baseline.get(key) != bundle.get(key):
                    findings.append(
                        Finding(
                            "error",
                            "BASELINE_INCOMPATIBLE",
                            f"baseline {key}={baseline.get(key)} does not match candidate {key}={bundle.get(key)}",
                            str(baseline_path),
                        )
                    )
            if baseline.get("adapter_version") != bundle.get("adapter_version"):
                findings.append(
                    Finding(
                        "error",
                        "BASELINE_INCOMPATIBLE",
                        "adapter_version changed between baseline and candidate",
                        str(baseline_path),
                    )
                )

    return report(bundle_path, findings, receipts)


def report(bundle_path: Path, findings: list[Finding], receipts: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema_version": "playbook.evidence_validation_report.v1",
        "bundle_path": str(bundle_path),
        "validated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "findings": [finding.as_dict() for finding in findings],
        "summary": {
            "errors": sum(1 for finding in findings if finding.severity == "error"),
            "warnings": sum(1 for finding in findings if finding.severity == "warning"),
            "receipts": len(receipts),
        },
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle_path")
    parser.add_argument("--json", dest="json_path")
    parser.add_argument("--baseline", dest="baseline_path")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    validation = validate_bundle(
        Path(args.bundle_path),
        Path(args.baseline_path) if args.baseline_path else None,
    )
    if args.json_path:
        output = Path(args.json_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(validation, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    for finding in validation["findings"]:
        print(
            "{severity}: {check_id}: {message}".format(**finding),
            file=sys.stderr if finding["severity"] == "error" else sys.stdout,
        )
    summary = validation["summary"]
    print(f"validate_harness_evidence: errors={summary['errors']} warnings={summary['warnings']} receipts={summary['receipts']}")
    return 1 if summary["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
