#!/usr/bin/env python3
"""Guarded, replayable execution for bounded Codex reviewer roles.

The main interactive Codex session may request a review, but this module owns the
execution contract: policy preflight, exact prompt materialization, fresh
``codex exec`` invocation, read-only drift detection, marker parsing, durable
artifacts, and a hash-chained event ledger.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


SCHEMA_VERSION = "playbook.codex_role_run.v1"
EVENT_SCHEMA_VERSION = "playbook.role_run_event.v1"
SAFE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
SUPPORTED_VERDICTS = {"PASS", "ADVISORY", "STOP_SHIP"}
PARENT_CODEX_ENV_KEYS = {
    "CODEX_THREAD_ID",
    "CODEX_MANAGED_BY_NPM",
    "CODEX_MANAGED_PACKAGE_ROOT",
}


class RoleRunError(RuntimeError):
    """Raised when a role run cannot produce trustworthy evidence."""


@dataclass(frozen=True)
class RoleSpec:
    role: str
    marker: str
    sandbox: str = "read-only"
    max_attempts: int = 1
    independent: bool = True


ROLE_SPECS: dict[str, RoleSpec] = {
    "product_design_review": RoleSpec(
        role="product_design_review",
        marker="PRODUCT_DESIGN_REVIEW",
    ),
    "program_design_review": RoleSpec(
        role="program_design_review",
        marker="PROGRAM_DESIGN_REVIEW",
    ),
    "slice_review": RoleSpec(
        role="slice_review",
        marker="SLICE_REVIEW",
    ),
    "maintainability_review": RoleSpec(
        role="maintainability_review",
        marker="MAINTAINABILITY_REVIEW",
    ),
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_write_bytes(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def atomic_write_text(path: Path, content: str) -> None:
    atomic_write_bytes(path, content.encode("utf-8"))


def atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    atomic_write_text(
        path,
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )


def ensure_safe_id(value: str, *, label: str) -> str:
    if not SAFE_ID_RE.fullmatch(value):
        raise RoleRunError(f"{label} must match {SAFE_ID_RE.pattern}: {value!r}")
    return value


def resolve_root(root: Path) -> Path:
    resolved = root.expanduser().resolve()
    if not resolved.is_dir():
        raise RoleRunError(f"repository root does not exist: {resolved}")
    if not (resolved / ".git").exists():
        raise RoleRunError(f"repository root is not a Git checkout: {resolved}")
    return resolved


def resolve_inside(root: Path, candidate: Path | str, *, must_exist: bool = False) -> Path:
    raw = Path(candidate)
    resolved = raw.resolve(strict=must_exist) if raw.is_absolute() else (root / raw).resolve(strict=must_exist)
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise RoleRunError(f"path escapes repository root: {candidate}") from exc
    return resolved


def relative_path(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root).as_posix()


def run_command(
    argv: Sequence[str],
    *,
    cwd: Path,
    env: Mapping[str, str] | None = None,
    timeout: int | None = None,
    input_text: str | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(argv),
        cwd=cwd,
        env=dict(env) if env is not None else None,
        text=True,
        input=input_text,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )


def git_output(root: Path, *args: str) -> str:
    result = run_command(["git", *args], cwd=root)
    if result.returncode != 0:
        raise RoleRunError(
            f"git {' '.join(args)} failed ({result.returncode}): {result.stderr.strip()}"
        )
    return result.stdout.strip()


def current_head(root: Path) -> str:
    value = git_output(root, "rev-parse", "HEAD")
    if not re.fullmatch(r"[0-9a-f]{40}", value):
        raise RoleRunError(f"unexpected Git HEAD: {value!r}")
    return value


def generated_run_id(role: str) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{timestamp}-{role}-{secrets.token_hex(4)}"


def _snapshot_entry(path: Path) -> dict[str, Any]:
    stat_result = path.lstat()
    if path.is_symlink():
        return {
            "kind": "symlink",
            "target": os.readlink(path),
            "mode": stat_result.st_mode,
        }
    if path.is_file():
        return {
            "kind": "file",
            "sha256": sha256_file(path),
            "size": stat_result.st_size,
            "mode": stat_result.st_mode,
        }
    return {"kind": "other", "mode": stat_result.st_mode}


def workspace_snapshot(root: Path, *, excluded_prefixes: Iterable[str]) -> dict[str, dict[str, Any]]:
    """Hash tracked and untracked files while excluding runner-owned artifacts."""
    result = run_command(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        cwd=root,
    )
    if result.returncode != 0:
        raise RoleRunError(f"git ls-files failed: {result.stderr.strip()}")
    excluded = tuple(prefix.rstrip("/") + "/" for prefix in excluded_prefixes)
    snapshot: dict[str, dict[str, Any]] = {}
    for item in result.stdout.split("\0"):
        if not item:
            continue
        normalized = Path(item).as_posix()
        if normalized == ".git" or normalized.startswith(".git/"):
            continue
        if any(normalized == prefix[:-1] or normalized.startswith(prefix) for prefix in excluded):
            continue
        path = resolve_inside(root, normalized)
        if not path.exists() and not path.is_symlink():
            continue
        snapshot[normalized] = _snapshot_entry(path)
    return dict(sorted(snapshot.items()))


def changed_snapshot_paths(
    before: Mapping[str, Mapping[str, Any]],
    after: Mapping[str, Mapping[str, Any]],
) -> list[str]:
    return sorted(key for key in set(before) | set(after) if before.get(key) != after.get(key))


def _event_payload_for_hash(event: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in event.items() if key != "event_sha256"}


def validate_event_ledger(path: Path) -> tuple[int, str | None]:
    if not path.exists():
        return 0, None
    previous: str | None = None
    expected_sequence = 1
    count = 0
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw_line.strip():
            continue
        try:
            event = json.loads(raw_line)
        except json.JSONDecodeError as exc:
            raise RoleRunError(f"invalid ledger JSON at line {line_number}: {exc}") from exc
        if not isinstance(event, dict):
            raise RoleRunError(f"ledger event at line {line_number} must be an object")
        if event.get("schema_version") != EVENT_SCHEMA_VERSION:
            raise RoleRunError(f"unexpected ledger schema at line {line_number}")
        if event.get("sequence") != expected_sequence:
            raise RoleRunError(f"ledger sequence break at line {line_number}")
        if event.get("previous_event_sha256") != previous:
            raise RoleRunError(f"ledger hash-chain break at line {line_number}")
        observed_hash = event.get("event_sha256")
        expected_hash = sha256_bytes(canonical_json_bytes(_event_payload_for_hash(event)))
        if observed_hash != expected_hash:
            raise RoleRunError(f"ledger event hash mismatch at line {line_number}")
        previous = observed_hash
        expected_sequence += 1
        count += 1
    return count, previous


def append_event(
    ledger_path: Path,
    *,
    run_id: str,
    event_type: str,
    details: Mapping[str, Any],
) -> dict[str, Any]:
    count, previous = validate_event_ledger(ledger_path)
    event: dict[str, Any] = {
        "schema_version": EVENT_SCHEMA_VERSION,
        "sequence": count + 1,
        "run_id": run_id,
        "event_type": event_type,
        "occurred_at": utc_now(),
        "previous_event_sha256": previous,
        "details": dict(details),
    }
    event["event_sha256"] = sha256_bytes(canonical_json_bytes(event))
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    with ledger_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    return event


def discover_instruction_files(root: Path) -> list[dict[str, Any]]:
    candidates: list[tuple[str, Path]] = [
        ("repository", root / "AGENTS.md"),
        ("repository_codex", root / ".codex" / "AGENTS.md"),
        ("user_codex", Path.home() / ".codex" / "AGENTS.md"),
    ]
    records: list[dict[str, Any]] = []
    for source, candidate in candidates:
        if candidate.is_file():
            records.append(
                {
                    "source": source,
                    "path": candidate.as_posix(),
                    "sha256": sha256_file(candidate),
                    "size": candidate.stat().st_size,
                }
            )
    return records


def _known_context_files(root: Path, *, feature_id: str | None) -> list[Path]:
    candidates = [
        root / "docs" / "tasks.md",
        root / "docs" / "PROJECT_BRIEF.md",
        root / "docs" / "ARCHITECTURE.md",
        root / "docs" / "REVIEW_POLICY.md",
        root / ".playbook" / "delivery_execution_model.json",
        root / ".playbook" / "project_verification.json",
    ]
    if feature_id:
        candidates.extend(
            [
                root / "docs" / "design" / f"{feature_id}.md",
                root / "docs" / "design" / f"{feature_id}.design.json",
            ]
        )
    return [path for path in candidates if path.is_file()]


def context_manifest(
    *,
    root: Path,
    role: str,
    task_id: str,
    feature_id: str | None,
    slice_id: str | None,
    prompt_path: Path,
    renderer_argv: Sequence[str],
    base_commit: str,
) -> dict[str, Any]:
    files = [
        {
            "path": relative_path(root, path),
            "sha256": sha256_file(path),
            "size": path.stat().st_size,
        }
        for path in _known_context_files(root, feature_id=feature_id)
    ]
    return {
        "schema_version": "playbook.codex_role_context.v1",
        "role": role,
        "task_id": task_id,
        "feature_id": feature_id,
        "slice_id": slice_id,
        "base_commit": base_commit,
        "prompt": {
            "path": relative_path(root, prompt_path),
            "sha256": sha256_file(prompt_path),
            "size": prompt_path.stat().st_size,
        },
        "renderer_argv_sha256": sha256_bytes(canonical_json_bytes(list(renderer_argv))),
        "known_context_files": files,
        "instruction_files": discover_instruction_files(root),
        "capture_boundary": {
            "playbook_prompt_exact": True,
            "known_repository_context_hashed": True,
            "codex_internal_system_prompt_captured": False,
            "codex_internal_tool_schema_captured": False,
        },
    }


def renderer_help(root: Path) -> str:
    renderer = root / "tools" / "render_codex_exec_prompt.py"
    if not renderer.is_file():
        raise RoleRunError(f"missing prompt renderer: {renderer}")
    result = run_command([sys.executable, str(renderer), "--help"], cwd=root)
    if result.returncode != 0:
        raise RoleRunError(f"prompt renderer --help failed: {result.stderr.strip()}")
    return result.stdout


def render_role_prompt(
    *,
    root: Path,
    task_id: str,
    role: str,
    feature_id: str | None,
    slice_id: str | None,
) -> tuple[str, list[str]]:
    renderer = root / "tools" / "render_codex_exec_prompt.py"
    help_text = renderer_help(root)
    argv = [
        sys.executable,
        str(renderer),
        "--root",
        str(root),
        "--task",
        task_id,
        "--role",
        role,
    ]
    if feature_id and "--feature-id" in help_text:
        argv.extend(["--feature-id", feature_id])
    if slice_id and "--slice-id" in help_text:
        argv.extend(["--slice-id", slice_id])
    result = run_command(argv, cwd=root)
    if result.returncode != 0:
        raise RoleRunError(
            f"prompt renderer failed ({result.returncode}): {result.stderr.strip()}"
        )
    if not result.stdout.strip():
        raise RoleRunError("prompt renderer produced an empty prompt")
    return result.stdout, argv


def parse_review_report(*, root: Path, role: str, report_path: Path) -> dict[str, Any]:
    renderer = root / "tools" / "render_codex_exec_prompt.py"
    result = run_command(
        [
            sys.executable,
            str(renderer),
            "--role",
            role,
            "--parse-report",
            str(report_path),
        ],
        cwd=root,
    )
    if result.returncode != 0:
        raise RoleRunError(f"review marker parsing failed: {result.stderr.strip()}")
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RoleRunError("review marker parser did not return JSON") from exc
    verdict = payload.get("verdict")
    if verdict not in SUPPORTED_VERDICTS:
        raise RoleRunError(f"unsupported review verdict: {verdict!r}")
    return payload


def validate_trace(path: Path) -> int:
    if not path.is_file():
        raise RoleRunError("Codex JSONL trace is missing")
    count = 0
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw_line.strip():
            continue
        try:
            event = json.loads(raw_line)
        except json.JSONDecodeError as exc:
            raise RoleRunError(f"invalid Codex JSONL at line {line_number}: {exc}") from exc
        if not isinstance(event, dict):
            raise RoleRunError(f"Codex event at line {line_number} must be an object")
        count += 1
    if count == 0:
        raise RoleRunError("Codex JSONL trace contains no events")
    return count


def sanitized_codex_environment() -> tuple[dict[str, str], bool]:
    env = dict(os.environ)
    scrubbed = any(key in env for key in PARENT_CODEX_ENV_KEYS)
    for key in PARENT_CODEX_ENV_KEYS:
        env.pop(key, None)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env, scrubbed


def resolve_codex_binary(value: str | None) -> str:
    if value:
        candidate = Path(value).expanduser()
        if candidate.is_absolute() or candidate.parent != Path("."):
            resolved = candidate.resolve()
            if not resolved.is_file():
                raise RoleRunError(f"Codex binary does not exist: {resolved}")
            return str(resolved)
        discovered = shutil.which(value)
    else:
        discovered = shutil.which("codex")
    if not discovered:
        raise RoleRunError("Codex executable is unavailable")
    return str(Path(discovered).resolve())


def codex_cli_version(codex_binary: str, *, root: Path, env: Mapping[str, str]) -> str:
    result = run_command([codex_binary, "--version"], cwd=root, env=env, timeout=30)
    if result.returncode != 0:
        raise RoleRunError(f"codex --version failed: {result.stderr.strip()}")
    version = result.stdout.strip()
    if not version:
        raise RoleRunError("codex --version returned empty output")
    return version


def default_published_report(*, root: Path, feature_id: str, role: str) -> Path:
    return root / ".playbook-artifacts" / "reports" / feature_id / f"{role}.md"


def publish_report(*, root: Path, report_path: Path, destination: Path) -> tuple[str, str]:
    safe_destination = resolve_inside(root, destination)
    atomic_write_bytes(safe_destination, report_path.read_bytes())
    return relative_path(root, safe_destination), sha256_file(safe_destination)


def write_design_review_record_if_supported(
    *,
    root: Path,
    feature_id: str,
    role: str,
    report_relative_path: str,
    reviewer_binding: str,
) -> str | None:
    if role not in {"product_design_review", "program_design_review"}:
        return None
    registry_path = root / "docs" / "design" / f"{feature_id}.design.json"
    if not registry_path.is_file():
        raise RoleRunError(f"missing Feature Design registry: {registry_path}")
    payload = json.loads(registry_path.read_text(encoding="utf-8"))
    tools_dir = root / "tools"
    if str(tools_dir) not in sys.path:
        sys.path.insert(0, str(tools_dir))
    try:
        import approve_feature_design  # type: ignore
    except ImportError as exc:
        raise RoleRunError("approve_feature_design helper is unavailable") from exc
    approve_feature_design.write_design_review_record(
        root=root,
        feature_id=feature_id,
        role=role,
        report_path=report_relative_path,
        reviewed_design=payload,
        reviewer_binding=reviewer_binding,
    )
    expected = (
        root
        / ".playbook-artifacts"
        / "reviews"
        / feature_id
        / "design"
        / f"{role}.review.json"
    )
    return relative_path(root, expected) if expected.exists() else None


def _nullable_hash(path: Path | None) -> str | None:
    return sha256_file(path) if path is not None and path.is_file() else None


def validate_role_result(
    *,
    root: Path,
    result_path: Path,
    require_current_head: bool = True,
) -> dict[str, Any]:
    root = resolve_root(root)
    result_path = resolve_inside(root, result_path, must_exist=True)
    payload = json.loads(result_path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise RoleRunError("unsupported role result schema")
    if payload.get("status") != "validated":
        raise RoleRunError(f"role result is not validated: {payload.get('status')}")
    if payload.get("role") not in ROLE_SPECS:
        raise RoleRunError(f"unsupported role in result: {payload.get('role')!r}")
    sidecar = result_path.with_suffix(result_path.suffix + ".sha256")
    if not sidecar.is_file():
        raise RoleRunError("role result SHA-256 sidecar is missing")
    if sidecar.read_text(encoding="utf-8").strip() != sha256_file(result_path):
        raise RoleRunError("role result SHA-256 mismatch")
    if require_current_head and payload.get("base_commit") != current_head(root):
        raise RoleRunError("role result was produced for a different Git HEAD")

    hash_fields = [
        (payload["inputs"]["prompt_path"], payload["inputs"]["prompt_sha256"]),
        (payload["inputs"]["context_manifest_path"], payload["inputs"]["context_manifest_sha256"]),
        (payload["outputs"]["trace_path"], payload["outputs"]["trace_sha256"]),
        (payload["outputs"]["stderr_path"], payload["outputs"]["stderr_sha256"]),
    ]
    if payload["outputs"].get("report_path"):
        hash_fields.append((payload["outputs"]["report_path"], payload["outputs"]["report_sha256"]))
    if payload["outputs"].get("published_report_path"):
        hash_fields.append(
            (
                payload["outputs"]["published_report_path"],
                payload["outputs"]["published_report_sha256"],
            )
        )
    for relative, expected_hash in hash_fields:
        path = resolve_inside(root, relative, must_exist=True)
        if sha256_file(path) != expected_hash:
            raise RoleRunError(f"artifact hash mismatch: {relative}")

    ledger_path = result_path.parent / "events.jsonl"
    _, ledger_head = validate_event_ledger(ledger_path)
    if ledger_head is None:
        raise RoleRunError("role event ledger is empty")
    expected_result_hash = sha256_file(result_path)
    linked = any(
        event.get("event_type") == "role.result.written"
        and event.get("details", {}).get("result_sha256") == expected_result_hash
        for event in (
            json.loads(line)
            for line in ledger_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
    )
    if not linked:
        raise RoleRunError("role result is not linked from the event ledger")
    return payload


def execute_role_run(
    *,
    root: Path,
    task_id: str,
    role: str,
    feature_id: str | None,
    slice_id: str | None,
    codex_binary: str | None,
    model: str | None,
    timeout_seconds: int,
    run_id: str | None,
    output_report: Path | None,
    publish: bool,
) -> tuple[dict[str, Any], Path]:
    root = resolve_root(root)
    ensure_safe_id(task_id, label="task_id")
    if role not in ROLE_SPECS:
        raise RoleRunError(f"unsupported Codex role: {role}")
    spec = ROLE_SPECS[role]
    if role in {"product_design_review", "program_design_review"} and not feature_id:
        raise RoleRunError(f"{role} requires --feature-id")
    if role in {"slice_review", "maintainability_review"} and (not feature_id or not slice_id):
        raise RoleRunError(f"{role} requires --feature-id and --slice-id")
    if feature_id:
        ensure_safe_id(feature_id, label="feature_id")
    if slice_id:
        ensure_safe_id(slice_id, label="slice_id")
    if timeout_seconds < 1:
        raise RoleRunError("timeout_seconds must be positive")

    run_id = ensure_safe_id(run_id or generated_run_id(role), label="run_id")
    run_root = root / ".playbook-artifacts" / "runs" / run_id
    if run_root.exists():
        raise RoleRunError(f"role run already exists: {run_id}")
    run_root.mkdir(parents=True)
    ledger_path = run_root / "events.jsonl"
    prompt_path = run_root / "prompt.md"
    context_path = run_root / "context_manifest.json"
    trace_path = run_root / "codex_events.jsonl"
    stderr_path = run_root / "codex_stderr.txt"
    report_path = run_root / "report.md"
    result_path = run_root / "result.json"
    started_at = utc_now()
    base_commit = current_head(root)
    excluded = [relative_path(root, run_root)]

    append_event(
        ledger_path,
        run_id=run_id,
        event_type="role.requested",
        details={
            "role": role,
            "task_id": task_id,
            "feature_id": feature_id,
            "slice_id": slice_id,
            "base_commit": base_commit,
            "sandbox": spec.sandbox,
        },
    )
    before = workspace_snapshot(root, excluded_prefixes=excluded)
    prompt, renderer_argv = render_role_prompt(
        root=root,
        task_id=task_id,
        role=role,
        feature_id=feature_id,
        slice_id=slice_id,
    )
    atomic_write_text(prompt_path, prompt)
    context = context_manifest(
        root=root,
        role=role,
        task_id=task_id,
        feature_id=feature_id,
        slice_id=slice_id,
        prompt_path=prompt_path,
        renderer_argv=renderer_argv,
        base_commit=base_commit,
    )
    atomic_write_json(context_path, context)
    append_event(
        ledger_path,
        run_id=run_id,
        event_type="context.materialized",
        details={
            "prompt_sha256": sha256_file(prompt_path),
            "context_manifest_sha256": sha256_file(context_path),
            "renderer_argv_sha256": context["renderer_argv_sha256"],
        },
    )

    env, parent_scrubbed = sanitized_codex_environment()
    binary = resolve_codex_binary(codex_binary)
    version = codex_cli_version(binary, root=root, env=env)
    codex_argv = [
        binary,
        "exec",
        "--json",
        "--sandbox",
        spec.sandbox,
        "--output-last-message",
        str(report_path),
    ]
    if model:
        codex_argv.extend(["--model", model])
    codex_argv.append(prompt)
    argv_hash = sha256_bytes(canonical_json_bytes(codex_argv[1:]))
    append_event(
        ledger_path,
        run_id=run_id,
        event_type="codex.exec.started",
        details={
            "cli_version": version,
            "model": model,
            "sandbox": spec.sandbox,
            "argv_sha256": argv_hash,
            "parent_codex_context_scrubbed": parent_scrubbed,
        },
    )

    execution_exit: int | None = None
    execution_stdout = ""
    execution_stderr = ""
    timed_out = False
    try:
        execution = run_command(codex_argv, cwd=root, env=env, timeout=timeout_seconds)
        execution_exit = execution.returncode
        execution_stdout = execution.stdout
        execution_stderr = execution.stderr
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        execution_stdout = (
            exc.stdout.decode("utf-8", errors="replace")
            if isinstance(exc.stdout, bytes)
            else exc.stdout or ""
        )
        execution_stderr = (
            exc.stderr.decode("utf-8", errors="replace")
            if isinstance(exc.stderr, bytes)
            else exc.stderr or ""
        )
    atomic_write_text(trace_path, execution_stdout)
    atomic_write_text(stderr_path, execution_stderr)
    append_event(
        ledger_path,
        run_id=run_id,
        event_type="codex.exec.finished",
        details={
            "exit_code": execution_exit,
            "timed_out": timed_out,
            "trace_sha256": sha256_file(trace_path),
            "stderr_sha256": sha256_file(stderr_path),
        },
    )

    after = workspace_snapshot(root, excluded_prefixes=excluded)
    changed_paths = changed_snapshot_paths(before, after)
    errors: list[str] = []
    trace_valid = False
    marker_valid = False
    event_count = 0
    verdict: str | None = None
    if timed_out:
        errors.append("Codex role execution timed out")
    elif execution_exit != 0:
        errors.append(f"codex exec exited with {execution_exit}")
    if changed_paths:
        errors.append("read-only reviewer changed repository files")
    try:
        event_count = validate_trace(trace_path)
        trace_valid = True
    except RoleRunError as exc:
        errors.append(str(exc))
    if not report_path.is_file() or not report_path.read_text(encoding="utf-8").strip():
        errors.append("review report is missing or empty")
    else:
        try:
            parsed = parse_review_report(root=root, role=role, report_path=report_path)
            verdict = parsed["verdict"]
            marker_valid = True
        except RoleRunError as exc:
            errors.append(str(exc))

    published_path: str | None = None
    published_hash: str | None = None
    review_record_path: str | None = None
    status = "timeout" if timed_out else "execution_failed" if execution_exit != 0 else "postflight_failed"
    if not errors:
        status = "validated"
        if publish:
            if not feature_id:
                raise RoleRunError("publishing requires feature_id")
            destination = output_report or default_published_report(
                root=root,
                feature_id=feature_id,
                role=role,
            )
            published_path, published_hash = publish_report(
                root=root,
                report_path=report_path,
                destination=destination,
            )
            review_record_path = write_design_review_record_if_supported(
                root=root,
                feature_id=feature_id,
                role=role,
                report_relative_path=published_path,
                reviewer_binding=f"codex-role-run:{run_id}:{version}:{model or 'default'}",
            )
            append_event(
                ledger_path,
                run_id=run_id,
                event_type="review.published",
                details={
                    "report_path": published_path,
                    "report_sha256": published_hash,
                    "review_record_path": review_record_path,
                },
            )

    result: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "role": role,
        "task_id": task_id,
        "feature_id": feature_id,
        "slice_id": slice_id,
        "base_commit": base_commit,
        "sandbox": spec.sandbox,
        "status": status,
        "verdict": verdict,
        "started_at": started_at,
        "finished_at": utc_now(),
        "codex": {
            "binary": binary,
            "cli_version": version,
            "model": model,
            "argv_sha256": argv_hash,
            "exit_code": execution_exit,
            "parent_codex_context_scrubbed": parent_scrubbed,
        },
        "inputs": {
            "prompt_path": relative_path(root, prompt_path),
            "prompt_sha256": sha256_file(prompt_path),
            "context_manifest_path": relative_path(root, context_path),
            "context_manifest_sha256": sha256_file(context_path),
            "renderer_argv_sha256": context["renderer_argv_sha256"],
        },
        "outputs": {
            "report_path": relative_path(root, report_path) if report_path.is_file() else None,
            "report_sha256": _nullable_hash(report_path),
            "trace_path": relative_path(root, trace_path),
            "trace_sha256": sha256_file(trace_path),
            "stderr_path": relative_path(root, stderr_path),
            "stderr_sha256": sha256_file(stderr_path),
            "published_report_path": published_path,
            "published_report_sha256": published_hash,
        },
        "postflight": {
            "trace_valid": trace_valid,
            "marker_valid": marker_valid,
            "workspace_unchanged": not changed_paths,
            "changed_paths": changed_paths,
            "event_count": event_count,
            "errors": errors,
        },
    }
    atomic_write_json(result_path, result)
    result_hash = sha256_file(result_path)
    atomic_write_text(result_path.with_suffix(".json.sha256"), result_hash + "\n")
    append_event(
        ledger_path,
        run_id=run_id,
        event_type="role.result.written",
        details={
            "status": status,
            "verdict": verdict,
            "result_path": relative_path(root, result_path),
            "result_sha256": result_hash,
        },
    )
    return result, result_path
