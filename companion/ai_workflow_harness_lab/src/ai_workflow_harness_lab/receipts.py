from __future__ import annotations

import hashlib
import json
import os
import platform
import signal
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .environment import git as run_git
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
    result = run_git(args, cwd)
    return result.stdout.strip() if result.returncode == 0 else "git-unavailable"


def dirty(cwd: Path) -> list[str]:
    result = run_git(["status", "--short"], cwd)
    if result.returncode != 0:
        return ["git-unavailable"]
    return result.stdout.splitlines() if result.stdout else []


def linux_descendants(root_pid: int) -> set[int]:
    """Return the current Linux descendant set, including new sessions."""
    if sys.platform != "linux":
        return set()
    parents: dict[int, int] = {}
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        try:
            status = (entry / "status").read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for line in status.splitlines():
            if line.startswith("PPid:"):
                parents[int(entry.name)] = int(line.split()[1])
                break
    descendants: set[int] = set()
    changed = True
    while changed:
        changed = False
        for pid, parent in parents.items():
            if pid not in descendants and (parent == root_pid or parent in descendants):
                descendants.add(pid)
                changed = True
    return descendants


def kill_process_tree(process: subprocess.Popen[bytes]) -> None:
    """Stop and kill the command plus descendants that escaped its process group."""
    if process.poll() is not None:
        return
    if sys.platform == "linux":
        targets = {process.pid}
        try:
            os.kill(process.pid, signal.SIGSTOP)
        except ProcessLookupError:
            return
        for _ in range(2):
            discovered = linux_descendants(process.pid) - targets
            for pid in discovered:
                try:
                    os.kill(pid, signal.SIGSTOP)
                except ProcessLookupError:
                    pass
            targets.update(discovered)
        for pid in sorted(targets, reverse=True):
            try:
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        return
    if os.name == "posix":
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    else:
        process.kill()


def run_command_receipt(
    task_id: str,
    output_dir: Path,
    argv: list[str],
    cwd: Path,
    timeout: float | None = None,
    *,
    inspect_git: bool = True,
) -> ExecutionResult:
    output_dir.mkdir(parents=True, exist_ok=True)
    commit_before = git(["rev-parse", "HEAD"], cwd) if inspect_git else "not_inspected"
    dirty_before = dirty(cwd) if inspect_git else ["not_inspected"]
    start = utc_now()
    start_monotonic_ns = time.monotonic_ns()
    try:
        process = subprocess.Popen(
            argv,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=os.name == "posix",
        )
        try:
            stdout, stderr = process.communicate(timeout=timeout)
            exit_code = process.returncode
            timed_out = False
        except subprocess.TimeoutExpired as initial_timeout:
            kill_process_tree(process)
            try:
                stdout, stderr = process.communicate(timeout=2)
            except subprocess.TimeoutExpired as lingering_pipe:
                stdout = lingering_pipe.output or initial_timeout.output or b""
                stderr = lingering_pipe.stderr or initial_timeout.stderr or b""
                if process.stdout is not None:
                    process.stdout.close()
                if process.stderr is not None:
                    process.stderr.close()
                process.wait(timeout=1)
            exit_code = 124
            stderr = (stderr or b"") + b"\ntimeout\n"
            timed_out = True
    except FileNotFoundError as exc:
        exit_code = 127
        stdout = b""
        stderr = f"command not found: {exc.filename}\n".encode("utf-8")
        timed_out = False
    end = utc_now()
    end_monotonic_ns = time.monotonic_ns()
    stdout_path = output_dir / "stdout.txt"
    stderr_path = output_dir / "stderr.txt"
    diff_path = output_dir / "diff_stat.txt"
    stdout_path.write_bytes(stdout)
    stderr_path.write_bytes(stderr)
    if inspect_git:
        diff = run_git(["diff", "--stat"], cwd)
        diff_path.write_text(diff.stdout if diff.returncode == 0 else "", encoding="utf-8")
        commit_after = git(["rev-parse", "HEAD"], cwd)
        dirty_after = dirty(cwd)
    else:
        diff_path.write_text("", encoding="utf-8")
        commit_after = "not_inspected"
        dirty_after = ["not_inspected"]
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
        "repo_commit_after": commit_after,
        "dirty_state_before": dirty_before,
        "dirty_state_after": dirty_after,
        "diff_stat_artifact_path": "diff_stat.txt",
        "diff_stat_sha256": sha256_file(diff_path),
        "environment_summary": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "timeout": timeout,
            "timed_out": timed_out,
            "git_inspection": inspect_git,
            "start_monotonic_ns": start_monotonic_ns,
            "end_monotonic_ns": end_monotonic_ns,
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
