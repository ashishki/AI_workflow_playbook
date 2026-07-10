from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .receipts import artifact_ref, sha256_file


def manifest_hash(bundle: dict[str, Any]) -> str:
    cloned = dict(bundle)
    cloned["manifest_hash"] = ""
    payload = json.dumps(cloned, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def write_bundle(
    *,
    output_dir: Path,
    repository: str,
    task_id: str,
    task_spec_version: str,
    condition: str,
    adapter_version: str,
    environment_digest: str,
    commit_before: str,
    commit_after: str,
    receipt_paths: list[Path],
    trace_paths: list[Path],
    post_state_manifest: Path,
    scorer_outputs: list[Path],
    failure_records: list[dict[str, Any]],
    report_path: Path,
) -> Path:
    bundle = {
        "schema_version": "playbook.evidence_bundle.v1",
        "bundle_id": f"{task_id}-{condition}-{output_dir.name}",
        "manifest_hash": "",
        "repository": repository,
        "task_id": task_id,
        "commit_before": commit_before,
        "commit_after": commit_after,
        "task_spec_version": task_spec_version,
        "condition": condition,
        "adapter_version": adapter_version,
        "environment_digest": environment_digest,
        "command_receipts": [artifact_ref(path, output_dir, "command_receipt") for path in receipt_paths],
        "trace_refs": [artifact_ref(path, output_dir, "trace") for path in trace_paths],
        "post_state_manifest": artifact_ref(post_state_manifest, output_dir, "post_state_manifest"),
        "scorer_outputs": [artifact_ref(path, output_dir, "scorer_output") for path in scorer_outputs],
        "failure_records": failure_records,
        "cost_record": {"cost_usd": "unknown", "tokens": "unknown"},
        "generated_report_ref": artifact_ref(report_path, output_dir, "generated_report"),
        "verifier_identity": "ai_workflow_harness_lab",
        "verification_timestamp": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }
    bundle["manifest_hash"] = manifest_hash(bundle)
    path = output_dir / "bundle.json"
    path.write_text(json.dumps(bundle, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def verify_bundle(bundle_path: Path) -> list[str]:
    bundle_path = bundle_path.resolve()
    bundle_dir = bundle_path.parent
    errors: list[str] = []
    try:
        bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"bundle json invalid: {exc}"]
    if bundle.get("manifest_hash") != manifest_hash(bundle):
        errors.append("manifest_hash mismatch")
    if not bundle.get("environment_digest"):
        errors.append("environment_digest missing")
    for ref in bundle.get("command_receipts", []):
        ref_errors = check_ref(bundle_dir, ref)
        errors.extend(ref_errors)
        if not ref_errors:
            errors.extend(check_receipt_artifacts(bundle_dir, ref))
    for key in ("trace_refs", "scorer_outputs"):
        for ref in bundle.get(key, []):
            errors.extend(check_ref(bundle_dir, ref))
    for key in ("post_state_manifest", "generated_report_ref"):
        ref = bundle.get(key)
        if isinstance(ref, dict):
            errors.extend(check_ref(bundle_dir, ref))
    return errors


def resolve_artifact_path(bundle_dir: Path, raw_path: str) -> Path | None:
    path = Path(raw_path)
    if path.is_absolute() or ".." in path.parts:
        return None
    resolved = (bundle_dir / path).resolve()
    try:
        resolved.relative_to(bundle_dir.resolve())
    except ValueError:
        return None
    return resolved


def check_ref(bundle_dir: Path, ref: dict[str, Any]) -> list[str]:
    path = resolve_artifact_path(bundle_dir, str(ref["path"]))
    if path is None:
        return [f"path escape forbidden: {ref['path']}"]
    if not path.exists():
        return [f"missing artifact: {path}"]
    actual = sha256_file(path)
    if actual != ref.get("sha256"):
        return [f"hash mismatch: {path}"]
    return []


def check_receipt_artifacts(bundle_dir: Path, ref: dict[str, Any]) -> list[str]:
    receipt_path = resolve_artifact_path(bundle_dir, str(ref["path"]))
    if receipt_path is None:
        return [f"path escape forbidden: {ref['path']}"]
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"receipt json invalid: {receipt_path}: {exc}"]
    errors: list[str] = []
    for artifact_key, hash_key in (
        ("stdout_artifact_path", "stdout_sha256"),
        ("stderr_artifact_path", "stderr_sha256"),
        ("diff_stat_artifact_path", "diff_stat_sha256"),
    ):
        artifact = Path(str(receipt.get(artifact_key, "")))
        if artifact.is_absolute() or ".." in artifact.parts:
            errors.append(f"receipt path escape forbidden: {artifact}")
            continue
        path = (receipt_path.parent / artifact).resolve()
        try:
            path.relative_to(receipt_path.parent.resolve())
        except ValueError:
            errors.append(f"receipt path escape forbidden: {path}")
            continue
        if not path.exists():
            errors.append(f"missing receipt artifact: {path}")
            continue
        actual = sha256_file(path)
        if actual != receipt.get(hash_key):
            errors.append(f"receipt hash mismatch: {path}")
    return errors
