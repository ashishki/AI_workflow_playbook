#!/usr/bin/env python3
"""Shared helpers for guarded, evidence-bearing Codex review-role runs."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any, Iterable

ROLE_RUN_SCHEMA_VERSION = "playbook.role_run.v1"
ROLE_RUN_PRODUCER = "tools/run_codex_role.py"
SUPPORTED_ROLES = {
    "product_design_review": {"phase": "design", "sandbox": "read-only"},
    "program_design_review": {"phase": "design", "sandbox": "read-only"},
    "slice_review": {"phase": "slice", "sandbox": "read-only"},
    "maintainability_review": {"phase": "slice", "sandbox": "read-only"},
}
SAFE_ID_RE = re.compile(r"[^A-Za-z0-9._-]+")


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json_bytes(payload: Any) -> bytes:
    return json.dumps(payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True).encode("utf-8")


def canonical_json_sha256(payload: Any) -> str:
    return sha256_bytes(canonical_json_bytes(payload))


def atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def atomic_write_json(path: Path, payload: Any) -> None:
    atomic_write_text(path, json.dumps(payload, indent=2, sort_keys=True) + "\n")


def safe_id(value: str) -> str:
    normalized = SAFE_ID_RE.sub("-", value.strip()).strip("-._")
    return normalized or "run"


def safe_repo_path(root: Path, raw: str) -> Path | None:
    value = str(raw).strip().strip("`")
    if not value:
        return None
    candidate = Path(value)
    if candidate.is_absolute() or ".." in candidate.parts:
        return None
    resolved_root = root.resolve()
    resolved = (resolved_root / candidate).resolve()
    try:
        resolved.relative_to(resolved_root)
    except ValueError:
        return None
    return resolved


def repo_rel(root: Path, path: Path) -> str:
    return str(path.resolve().relative_to(root.resolve()))


def run_git(root: Path, args: list[str], *, binary: bool = False) -> tuple[int, bytes | str]:
    completed = subprocess.run(
        ["git", *args],
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=not binary,
        check=False,
    )
    return completed.returncode, completed.stdout


def git_commit(root: Path) -> str:
    code, stdout = run_git(root, ["rev-parse", "HEAD"])
    value = str(stdout).strip()
    return value if code == 0 and value else "not-a-git-repository"


def git_diff_stat(root: Path) -> str:
    code, stdout = run_git(root, ["diff", "--stat", "HEAD", "--"])
    if code != 0:
        return "not-a-git-repository\n"
    value = str(stdout)
    return value + ("\n" if value and not value.endswith("\n") else "")


def _parse_porcelain_paths(raw: bytes) -> list[tuple[str, str]]:
    entries: list[tuple[str, str]] = []
    parts = raw.split(b"\0")
    index = 0
    while index < len(parts):
        item = parts[index]
        index += 1
        if not item:
            continue
        decoded = item.decode("utf-8", errors="replace")
        if len(decoded) < 4:
            continue
        status = decoded[:2]
        path = decoded[3:]
        if status.startswith(("R", "C")) and index < len(parts):
            target = parts[index].decode("utf-8", errors="replace")
            index += 1
            path = target
        entries.append((status, path))
    return entries


def workspace_state(root: Path) -> dict[str, Any]:
    code, raw = run_git(root, ["status", "--porcelain=v1", "-z", "--untracked-files=all"], binary=True)
    if code != 0 or not isinstance(raw, bytes):
        raise RuntimeError("Codex role execution requires a Git repository")
    entries = [
        (status, path)
        for status, path in _parse_porcelain_paths(raw)
        if not path.startswith(".playbook-artifacts/")
    ]
    file_hashes: dict[str, str] = {}
    for _status, raw_path in entries:
        path = safe_repo_path(root, raw_path)
        if path is None or not path.exists() or not path.is_file() or path.is_symlink():
            continue
        file_hashes[raw_path] = sha256_file(path)
    diff_code, tracked_diff = run_git(root, ["diff", "--binary", "HEAD", "--"], binary=True)
    cached_code, cached_diff = run_git(root, ["diff", "--cached", "--binary", "HEAD", "--"], binary=True)
    if diff_code != 0 or cached_code != 0 or not isinstance(tracked_diff, bytes) or not isinstance(cached_diff, bytes):
        raise RuntimeError("failed to capture Git workspace state")
    payload = {
        "commit": git_commit(root),
        "status_entries": [f"{status} {path}" for status, path in entries],
        "dirty_file_sha256": dict(sorted(file_hashes.items())),
        "tracked_diff_sha256": sha256_bytes(tracked_diff),
        "cached_diff_sha256": sha256_bytes(cached_diff),
    }
    payload["state_sha256"] = canonical_json_sha256(payload)
    return payload


def append_event(path: Path, event_type: str, **fields: Any) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    event = {"timestamp": utc_now(), "type": event_type, **fields}
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")
    return event


def role_spec(role: str, marker: str) -> dict[str, Any]:
    if role not in SUPPORTED_ROLES:
        raise ValueError(f"unsupported role: {role}")
    prefix, raw_values = marker.split(":", 1)
    values = [value.strip() for value in raw_values.split("|")]
    return {
        "schema_version": "playbook.role_spec.v1",
        "role": role,
        "phase": SUPPORTED_ROLES[role]["phase"],
        "sandbox": SUPPORTED_ROLES[role]["sandbox"],
        "fresh_process_required": True,
        "write_access": False,
        "completion_authority": False,
        "expected_marker": prefix,
        "allowed_verdicts": values,
        "max_attempts": 1,
    }


def role_result_sidecar_path(report_path: Path) -> Path:
    return report_path.with_suffix(".role_run.json")


def _unique_paths(paths: Iterable[Path]) -> list[Path]:
    seen: set[str] = set()
    result: list[Path] = []
    for path in paths:
        key = str(path.resolve())
        if key in seen:
            continue
        seen.add(key)
        result.append(path)
    return result


def context_source_paths(
    root: Path,
    *,
    task_record: dict[str, Any],
    feature_id: str,
) -> list[Path]:
    candidates: list[Path] = [
        root / "docs/tasks.md",
        root / "docs/PROJECT_BRIEF.md",
        root / "docs/REVIEW_POLICY.md",
        root / "docs/ARCHITECTURE.md",
        root / "templates/AGENTS.md",
        root / "docs/design" / f"{feature_id}.md",
        root / "docs/design" / f"{feature_id}.design.json",
    ]
    for raw in task_record.get("context_refs", []):
        path = safe_repo_path(root, str(raw))
        if path is not None:
            candidates.append(path)
    return [path for path in _unique_paths(candidates) if path.exists() and path.is_file()]


def build_context_manifest(
    root: Path,
    *,
    task_id: str,
    raw_task: str,
    task_record: dict[str, Any],
    feature_id: str,
    slice_id: str,
    role: str,
    prompt_path: Path,
    prompt_sha256: str,
    spec: dict[str, Any],
) -> dict[str, Any]:
    sources = []
    for path in context_source_paths(root, task_record=task_record, feature_id=feature_id):
        sources.append(
            {
                "path": repo_rel(root, path),
                "sha256": sha256_file(path),
                "size_bytes": path.stat().st_size,
            }
        )
    payload = {
        "schema_version": "playbook.role_context_manifest.v1",
        "task_id": task_id,
        "feature_id": feature_id,
        "slice_id": slice_id or None,
        "role": role,
        "base_commit": git_commit(root),
        "task_section_sha256": sha256_text(raw_task),
        "prompt_path": repo_rel(root, prompt_path),
        "prompt_sha256": prompt_sha256,
        "model_visible_prompt_sha256": prompt_sha256,
        "role_spec_sha256": canonical_json_sha256(spec),
        "sources": sorted(sources, key=lambda item: item["path"]),
    }
    payload["manifest_sha256"] = canonical_json_sha256(payload)
    return payload


def parse_jsonl_objects(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    events: list[dict[str, Any]] = []
    problems: list[str] = []
    if not path.exists():
        return events, [f"trace missing: {path}"]
    for line_number, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            problems.append(f"trace line {line_number} is invalid JSON: {exc.msg}")
            continue
        if not isinstance(value, dict):
            problems.append(f"trace line {line_number} must be a JSON object")
            continue
        events.append(value)
    if not events and not problems:
        problems.append("trace contains no JSON events")
    return events, problems


def observed_model(events: list[dict[str, Any]]) -> str:
    def walk(value: Any) -> str:
        if isinstance(value, dict):
            model = value.get("model")
            if isinstance(model, str) and model.strip():
                return model.strip()
            for child in value.values():
                found = walk(child)
                if found:
                    return found
        elif isinstance(value, list):
            for child in value:
                found = walk(child)
                if found:
                    return found
        return ""

    for event in events:
        found = walk(event)
        if found:
            return found
    return "unknown"


def validate_role_result(
    root: Path,
    result_path: Path,
    *,
    expected_role: str = "",
    expected_task_id: str = "",
    expected_feature_id: str = "",
    expected_slice_id: str = "",
) -> tuple[dict[str, Any] | None, list[str]]:
    problems: list[str] = []
    try:
        raw_result = repo_rel(root, result_path) if result_path.is_absolute() else str(result_path)
    except ValueError:
        return None, ["role result is outside repository"]
    safe_result = safe_repo_path(root, raw_result)
    if safe_result is None or not safe_result.exists():
        return None, ["role result is missing or outside repository"]
    try:
        payload = json.loads(safe_result.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return None, [f"role result is unreadable: {exc}"]
    if payload.get("schema_version") != ROLE_RUN_SCHEMA_VERSION:
        problems.append("invalid role result schema_version")
    if payload.get("status") != "validated":
        problems.append(f"role result is not validated: {payload.get('status')}")
    expected = {
        "role": expected_role,
        "task_id": expected_task_id,
        "feature_id": expected_feature_id,
        "slice_id": expected_slice_id or None,
    }
    for key, value in expected.items():
        if value not in {"", None} and payload.get(key) != value:
            problems.append(f"role result {key} mismatch")
    artifact_pairs = (
        ("prompt_path", "prompt_sha256"),
        ("context_manifest_path", "context_manifest_sha256"),
        ("report_path", "report_sha256"),
        ("trace_path", "trace_sha256"),
        ("stderr_path", "stderr_sha256"),
        ("receipt_path", "receipt_sha256"),
        ("event_ledger_path", "event_ledger_sha256"),
    )
    for path_key, hash_key in artifact_pairs:
        raw_path = str(payload.get(path_key, ""))
        artifact = safe_repo_path(root, raw_path)
        if artifact is None or not artifact.exists() or not artifact.is_file():
            problems.append(f"role result artifact missing or unsafe: {path_key}")
            continue
        if sha256_file(artifact) != str(payload.get(hash_key, "")):
            problems.append(f"role result artifact hash mismatch: {path_key}")
    report = safe_repo_path(root, str(payload.get("report_path", "")))
    if report is not None and report.exists():
        marker = str(payload.get("marker", ""))
        verdict = str(payload.get("verdict", ""))
        matched = False
        for line in report.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.startswith(marker + ":"):
                observed = line.split(":", 1)[1].strip().split()[0]
                matched = observed == verdict
                break
        if not matched:
            problems.append("role result verdict does not match report marker")
    if payload.get("write_drift"):
        problems.append("role result records workspace write drift")
    context_path = safe_repo_path(root, str(payload.get("context_manifest_path", "")))
    if context_path is not None and context_path.exists():
        try:
            context = json.loads(context_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            problems.append("context manifest is invalid JSON")
        else:
            if context.get("prompt_sha256") != payload.get("prompt_sha256"):
                problems.append("context manifest prompt hash mismatch")
            if context.get("model_visible_prompt_sha256") != payload.get("prompt_sha256"):
                problems.append("model-visible prompt provenance mismatch")
    return payload, sorted(set(problems))
