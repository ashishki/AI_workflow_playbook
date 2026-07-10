from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .models import ExecutionResult


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git(args: list[str], cwd: Path) -> str:
    result = subprocess.run(["git", *args], cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    return result.stdout.strip() if result.returncode == 0 else "git-unavailable"


def dirty(cwd: Path) -> list[str]:
    result = subprocess.run(["git", "status", "--short"], cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if result.returncode != 0:
        return ["git-unavailable"]
    return result.stdout.splitlines() if result.stdout else []


def run_command_receipt(
    task_id: str,
    output_dir: Path,
    argv: list[str],
    cwd: Path,
    timeout: float | None = None,
) -> ExecutionResult:
    output_dir.mkdir(parents=True, exist_ok=True)
    commit_before = git(["rev-parse", "HEAD"], cwd)
    dirty_before = dirty(cwd)
    start = utc_now()
    try:
        completed = subprocess.run(argv, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, check=False)
        exit_code = completed.returncode
        stdout = completed.stdout
        stderr = completed.stderr
        timed_out = False
    except FileNotFoundError as exc:
        exit_code = 127
        stdout = b""
        stderr = f"command not found: {exc.filename}\n".encode("utf-8")
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        exit_code = 124
        stdout = exc.stdout or b""
        stderr = (exc.stderr or b"") + b"\ntimeout\n"
        timed_out = True
    end = utc_now()
    stdout_path = output_dir / "stdout.txt"
    stderr_path = output_dir / "stderr.txt"
    diff_path = output_dir / "diff_stat.txt"
    stdout_path.write_bytes(stdout)
    stderr_path.write_bytes(stderr)
    diff = subprocess.run(["git", "diff", "--stat"], cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    diff_path.write_text(diff.stdout if diff.returncode == 0 else "", encoding="utf-8")
    receipt = {
        "schema_version": "playbook.command_receipt.v1",
        "receipt_id": f"{task_id}-{int(time.time())}-{uuid.uuid4().hex[:8]}",
        "task_id": task_id,
        "producer": "ai_workflow_harness_lab.receipts",
        "command_argv": argv,
        "working_directory": str(cwd),
        "start_timestamp": start,
        "end_timestamp": end,
        "exit_code": int(exit_code),
        "stdout_artifact_path": "stdout.txt",
        "stdout_sha256": sha256_file(stdout_path),
        "stderr_artifact_path": "stderr.txt",
        "stderr_sha256": sha256_file(stderr_path),
        "repo_commit_before": commit_before,
        "repo_commit_after": git(["rev-parse", "HEAD"], cwd),
        "dirty_state_before": dirty_before,
        "dirty_state_after": dirty(cwd),
        "diff_stat_artifact_path": "diff_stat.txt",
        "diff_stat_sha256": sha256_file(diff_path),
        "environment_summary": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "timeout": timeout,
            "timed_out": timed_out,
        },
        "parent_receipt_id": None,
        "redaction_status": "not_requested",
    }
    receipt_path = output_dir / "receipt.json"
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return ExecutionResult(
        receipt_path=receipt_path,
        exit_code=int(exit_code),
        start_timestamp=start,
        end_timestamp=end,
        timed_out=timed_out,
        command_argv=argv,
    )


def artifact_ref(path: Path, base: Path, kind: str, artifact_id: str | None = None) -> dict[str, Any]:
    ref: dict[str, Any] = {
        "path": str(path.relative_to(base)),
        "sha256": sha256_file(path),
        "kind": kind,
    }
    if artifact_id:
        ref["id"] = artifact_id
    return ref
