#!/usr/bin/env python3
"""External-only Codex adapter for the frozen test-first pilot."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shlex
import shutil
import signal
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, BinaryIO


MODEL = "gpt-5.6-sol"
REASONING_EFFORT = "medium"
SERVICE_TIER = "default"
CODEX_CLI_VERSION = "codex-cli 0.144.4"
PERMISSION_PROFILE = "test_first_pilot"
TRACE_FILE = "codex_events.jsonl"
STDERR_FILE = "codex_stderr.txt"
FINAL_MESSAGE_FILE = "final_message.txt"
LEDGER_FILE = "event_ledger.jsonl"
SUMMARY_FILE = "adapter_summary.json"
SAFE_ENVIRONMENT_KEYS = {
    "CODEX_HOME",
    "HOME",
    "LANG",
    "LC_ALL",
    "PATH",
    "SSL_CERT_DIR",
    "SSL_CERT_FILE",
}
DISABLED_FEATURES = (
    "apps",
    "plugins",
    "remote_plugin",
    "enable_mcp_apps",
    "browser_use",
    "browser_use_external",
    "browser_use_full_cdp_access",
    "in_app_browser",
    "computer_use",
    "multi_agent",
    "multi_agent_v2",
    "enable_fanout",
)
VERIFIER_COMMANDS = {
    "pin_ci_actions": ("python", "-m", "pytest", "-q", "pilot_tests/test_ci_pins.py"),
    "reject_unapproved_ci_actions": (
        "python",
        "-m",
        "pytest",
        "-q",
        "tests/test_ci_supply_chain.py",
        "pilot_tests/test_unapproved_action.py",
    ),
}
IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}")
EVENT_APPEND_LOCK = threading.Lock()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def append_event(path: Path, event: dict[str, object]) -> None:
    with EVENT_APPEND_LOCK:
        recorded_event = {**event, "monotonic_ns": time.monotonic_ns()}
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(recorded_event, sort_keys=True) + "\n")


def safe_environment(source: dict[str, str], python_executable: Path | None = None) -> dict[str, str]:
    environment = {key: value for key, value in source.items() if key in SAFE_ENVIRONMENT_KEYS}
    python_bin = (python_executable or Path(sys.executable)).parent
    inherited_path = environment.get("PATH", "")
    environment["PATH"] = os.pathsep.join(part for part in (str(python_bin), inherited_path) if part)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["PYTHONNOUSERSITE"] = "1"
    environment["PYTHONPYCACHEPREFIX"] = "/dev/null/test-first-pilot-pycache"
    environment["PYTEST_ADDOPTS"] = "-p no:cacheprovider"
    environment["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    return environment


def toml_string(value: str) -> str:
    return json.dumps(value)


def codex_runtime_root(codex_bin: str) -> Path:
    resolved = Path(codex_bin).resolve()
    if resolved.name == "codex.js" and resolved.parent.name == "bin":
        return resolved.parent.parent
    return resolved


def permission_config(venv_root: Path, codex_runtime: Path) -> str:
    read_roots = "".join(
        f',{toml_string(str(path))}="read"'
        for path in dict.fromkeys((venv_root, codex_runtime))
    )
    return (
        f'permissions.{PERMISSION_PROFILE}.filesystem='
        f'{{":minimal"="read",":workspace_roots"={{"."="write"}}{read_roots}}}'
    )


def build_command(
    codex_bin: str,
    workspace: Path,
    output: Path,
    venv_root: Path,
    codex_runtime: Path,
) -> list[str]:
    command = [
        codex_bin,
        "exec",
        "--ephemeral",
        "--ignore-user-config",
        "--ignore-rules",
        "--strict-config",
        "--model",
        MODEL,
        "--cd",
        str(workspace),
        "--color",
        "never",
        "--json",
        "--output-last-message",
        str(output / FINAL_MESSAGE_FILE),
    ]
    for feature in DISABLED_FEATURES:
        command.extend(("--disable", feature))
    command.extend(
        (
            "-c",
            f'default_permissions="{PERMISSION_PROFILE}"',
            "-c",
            permission_config(venv_root, codex_runtime),
            "-c",
            f"permissions.{PERMISSION_PROFILE}.network.enabled=false",
            "-c",
            f'model_reasoning_effort="{REASONING_EFFORT}"',
            "-c",
            f'service_tier="{SERVICE_TIER}"',
            "-c",
            'approval_policy="never"',
            "-c",
            'web_search="disabled"',
            "-c",
            "include_apps_instructions=false",
            "-c",
            "include_collaboration_mode_instructions=false",
            "-c",
            (
                'shell_environment_policy.include_only=["PATH","HOME","LANG","LC_ALL",'
                '"PYTHONDONTWRITEBYTECODE","PYTHONNOUSERSITE","PYTHONPYCACHEPREFIX",'
                '"PYTEST_ADDOPTS","PYTEST_DISABLE_PLUGIN_AUTOLOAD"]'
            ),
            "-",
        )
    )
    return command


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--pilot-id", required=True)
    parser.add_argument("--attempt-id", required=True)
    parser.add_argument("--task", required=True)
    parser.add_argument("--condition", choices=("baseline", "playbook"), required=True)
    parser.add_argument("--trial", type=int, required=True)
    parser.add_argument("--manifest-digest", required=True)
    parser.add_argument("--approval-id", required=True)
    parser.add_argument("--timeout", type=float, default=1200.0)
    parser.add_argument("--codex-bin", default="codex", help=argparse.SUPPRESS)
    return parser.parse_args(argv)


def command_text(item: dict[str, Any]) -> str:
    command = item.get("command", "")
    if isinstance(command, list):
        return " ".join(str(part) for part in command)
    return str(command)


def is_verifier(task_id: str, command: str) -> bool:
    expected = VERIFIER_COMMANDS.get(task_id)
    if expected is None:
        return False
    try:
        tokens = shlex.split(command)
        if (
            len(tokens) == 3
            and Path(tokens[0]).name in {"bash", "sh"}
            and tokens[1] in {"-c", "-lc"}
        ):
            tokens = shlex.split(tokens[2])
    except ValueError:
        return False
    return tuple(tokens) == expected


def command_result(item: dict[str, Any]) -> tuple[int | None, str]:
    raw_exit = item.get("exit_code")
    exit_code = raw_exit if isinstance(raw_exit, int) else None
    if exit_code == 0:
        return exit_code, "passed"
    if exit_code is not None:
        return exit_code, "failed"
    return None, "unknown"


def relative_change_paths(item: dict[str, Any], workspace: Path) -> list[str]:
    raw_paths: list[str] = []
    changes = item.get("changes")
    if isinstance(changes, list):
        for change in changes:
            if isinstance(change, dict) and isinstance(change.get("path"), str):
                raw_paths.append(change["path"])
    if isinstance(item.get("path"), str):
        raw_paths.append(item["path"])

    paths: list[str] = []
    for raw in raw_paths:
        candidate = Path(raw)
        if not candidate.is_absolute():
            candidate = workspace / candidate
        try:
            paths.append(str(candidate.resolve().relative_to(workspace)))
        except ValueError:
            paths.append("<outside-workspace>")
    return sorted(set(paths))


class TraceObserver:
    def __init__(
        self,
        *,
        workspace: Path,
        ledger: Path,
        common_event: dict[str, object],
    ) -> None:
        self.workspace = workspace
        self.ledger = ledger
        self.common_event = common_event
        self.verifier_attempts = 0
        self.verifier_by_item: dict[str, int] = {}
        self.last_verifier_result = "unknown"
        self.last_verifier_attempt: int | None = None
        self.first_green_observed = False
        self.file_change_count = 0
        self.trace_parse_errors = 0
        self.codex_terminal_event_observed = False

    def emit(self, event: str, **values: object) -> None:
        append_event(
            self.ledger,
            {**self.common_event, "event": event, "timestamp": utc_now(), **values},
        )

    def observe_line(self, raw_line: bytes) -> None:
        try:
            payload = json.loads(raw_line.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self.trace_parse_errors += 1
            self.emit("trace_parse_error", reason="Codex JSONL contained a malformed line")
            return
        if not isinstance(payload, dict):
            self.trace_parse_errors += 1
            self.emit("trace_parse_error", reason="Codex JSONL line was not an object")
            return
        event_type = payload.get("type")
        if event_type == "turn.completed":
            self.codex_terminal_event_observed = True
        item = payload.get("item")
        if event_type not in {"item.started", "item.completed"} or not isinstance(item, dict):
            return

        item_type = item.get("type")
        item_id = str(item.get("id", "unknown"))
        if item_type == "command_execution":
            command = command_text(item)
            lifecycle = "command_start" if event_type == "item.started" else "command_end"
            values: dict[str, object] = {
                "source_event_type": str(event_type),
                "source_item_id": item_id,
                "command": command,
            }
            if lifecycle == "command_end":
                exit_code, result = command_result(item)
                values["result"] = result
                if exit_code is not None:
                    values["exit_code"] = exit_code
            self.emit(lifecycle, **values)
            if is_verifier(str(self.common_event["task_id"]), command):
                self.observe_verifier(event_type, item_id, command, item)
        elif event_type == "item.completed" and item_type == "file_change":
            self.file_change_count += 1
            self.emit(
                "file_change",
                source_event_type=str(event_type),
                source_item_id=item_id,
                file_paths=relative_change_paths(item, self.workspace),
                change_count=self.file_change_count,
            )

    def observe_verifier(
        self,
        event_type: object,
        item_id: str,
        command: str,
        item: dict[str, Any],
    ) -> None:
        if event_type == "item.started":
            self.verifier_attempts += 1
            attempt = self.verifier_attempts
            self.verifier_by_item[item_id] = attempt
            self.emit(
                "verifier_start",
                source_event_type=str(event_type),
                source_item_id=item_id,
                command=command,
                verifier_attempt=attempt,
            )
            return

        attempt = self.verifier_by_item.get(item_id)
        if attempt is None:
            self.verifier_attempts += 1
            attempt = self.verifier_attempts
        exit_code, result = command_result(item)
        values: dict[str, object] = {
            "source_event_type": str(event_type),
            "source_item_id": item_id,
            "command": command,
            "verifier_attempt": attempt,
            "result": result,
        }
        if exit_code is not None:
            values["exit_code"] = exit_code
        self.emit("verifier_end", **values)
        self.last_verifier_attempt = attempt
        self.last_verifier_result = result

        if result == "passed" and not self.first_green_observed:
            self.first_green_observed = True
            self.emit(
                "first_green",
                source_item_id=item_id,
                verifier_attempt=attempt,
                result=result,
            )
        elif result == "failed" and self.file_change_count > 0:
            self.emit(
                "repair_candidate",
                source_item_id=item_id,
                verifier_attempt=attempt,
                result=result,
                reason="verifier failed after an observed file change",
            )

    def finish(self) -> None:
        values: dict[str, object] = {"result": self.last_verifier_result}
        if self.last_verifier_attempt is not None:
            values["verifier_attempt"] = self.last_verifier_attempt
        else:
            values["reason"] = "no declared verifier command observed in Codex JSONL"
        self.emit("final_model_gate", **values)


class TraceCaptureState:
    def __init__(self) -> None:
        self.eof_confirmed = False
        self.error: str | None = None


def capture_stdout(
    stream: BinaryIO,
    trace: BinaryIO,
    observer: TraceObserver,
    state: TraceCaptureState,
) -> None:
    try:
        for line in iter(stream.readline, b""):
            trace.write(line)
            trace.flush()
            observer.observe_line(line)
        state.eof_confirmed = True
    except BaseException as exc:
        state.error = f"{type(exc).__name__}: {exc}"


def trace_capture_failure(
    *, drain_deadline_missed: bool, state: TraceCaptureState
) -> str | None:
    if drain_deadline_missed:
        return "Codex JSONL reader did not reach EOF before the drain deadline"
    if state.error is not None:
        return f"Codex JSONL capture failed: {state.error}"
    if not state.eof_confirmed:
        return "Codex JSONL reader exited without confirming EOF"
    return None


def set_parent_death_signal() -> None:
    """Ensure the brokered Codex process dies if the adapter is killed."""
    if sys.platform != "linux":
        return
    import ctypes

    libc = ctypes.CDLL(None, use_errno=True)
    if libc.prctl(1, signal.SIGKILL) != 0:
        raise OSError(ctypes.get_errno(), "prctl(PR_SET_PDEATHSIG) failed")
    if os.getppid() == 1:
        os.kill(os.getpid(), signal.SIGKILL)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if os.environ.get("CODEX_THREAD_ID"):
        print(
            "refusing nested pilot execution from an active Codex session; use an external shell or CI",
            file=sys.stderr,
        )
        return 2
    if not re.fullmatch(r"[0-9a-f]{64}", args.manifest_digest):
        print("--manifest-digest must be a lowercase SHA-256 value", file=sys.stderr)
        return 2
    if not IDENTIFIER.fullmatch(args.pilot_id) or not IDENTIFIER.fullmatch(args.attempt_id):
        print("pilot and attempt IDs must be 1-128 path-safe characters", file=sys.stderr)
        return 2
    if args.trial < 0 or args.timeout <= 0:
        print("trial must be nonnegative and timeout must be positive", file=sys.stderr)
        return 2

    workspace = Path(args.workspace).resolve()
    prompt = Path(args.prompt).resolve()
    output = Path(args.output).resolve()
    if not workspace.is_dir() or not (workspace / ".git").exists():
        print("workspace must be an initialized isolated Git fixture", file=sys.stderr)
        return 2
    if not prompt.is_file():
        print("prompt file is missing", file=sys.stderr)
        return 2
    output.mkdir(parents=True, exist_ok=True)
    evidence_names = (TRACE_FILE, STDERR_FILE, FINAL_MESSAGE_FILE, LEDGER_FILE, SUMMARY_FILE)
    if any((output / name).exists() for name in evidence_names):
        print("adapter output already contains pilot evidence; refusing overwrite", file=sys.stderr)
        return 2

    codex_bin = shutil.which(args.codex_bin)
    if codex_bin is None:
        print(f"Codex executable not found: {args.codex_bin}", file=sys.stderr)
        return 127
    python_executable = Path(os.path.abspath(sys.executable))
    child_environment = safe_environment(dict(os.environ), python_executable)
    version = subprocess.run(
        [codex_bin, "--version"],
        env=child_environment,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if version.returncode != 0 or version.stdout.strip() != CODEX_CLI_VERSION:
        print(
            f"Codex CLI drift: expected {CODEX_CLI_VERSION}, got {version.stdout.strip() or 'unavailable'}",
            file=sys.stderr,
        )
        return 2

    common_event = {
        "schema_version": "test_first_pilot.event.v1",
        "pilot_manifest_sha256": args.manifest_digest,
        "approval_id": args.approval_id,
        "pilot_id": args.pilot_id,
        "attempt_id": args.attempt_id,
        "task_id": args.task,
        "condition": args.condition,
        "trial": args.trial,
        "model": MODEL,
        "reasoning_effort": REASONING_EFFORT,
        "service_tier": SERVICE_TIER,
    }
    ledger = output / LEDGER_FILE
    append_event(ledger, {**common_event, "event": "adapter_start", "timestamp": utc_now()})
    append_event(
        ledger,
        {
            **common_event,
            "event": "human_intervention",
            "timestamp": utc_now(),
            "occurred": False,
            "reason": "non-interactive adapter with approval policy never",
        },
    )

    venv_root = python_executable.parent.parent
    codex_runtime = codex_runtime_root(codex_bin)
    command = build_command(codex_bin, workspace, output, venv_root, codex_runtime)
    prompt_bytes = prompt.read_bytes()
    prompt_sha256 = hashlib.sha256(prompt_bytes).hexdigest()
    timed_out = False
    observer = TraceObserver(workspace=workspace, ledger=ledger, common_event=common_event)
    capture_state = TraceCaptureState()
    with (output / TRACE_FILE).open("wb") as trace_handle, (output / STDERR_FILE).open("wb") as stderr_handle:
        process = subprocess.Popen(
            command,
            cwd=workspace,
            env=child_environment,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=stderr_handle,
            start_new_session=True,
            preexec_fn=set_parent_death_signal if sys.platform == "linux" else None,
        )
        assert process.stdin is not None
        assert process.stdout is not None
        reader = threading.Thread(
            target=capture_stdout,
            args=(process.stdout, trace_handle, observer, capture_state),
            name="pilot-codex-jsonl-reader",
            daemon=True,
        )
        reader.start()
        try:
            process.stdin.write(prompt_bytes)
            process.stdin.close()
        except BrokenPipeError:
            pass
        try:
            process.wait(timeout=args.timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
        reader.join(timeout=5)
        drain_deadline_missed = reader.is_alive()
        if not drain_deadline_missed:
            process.stdout.close()

    codex_exit_code = 124 if timed_out else int(process.returncode)
    capture_failure = trace_capture_failure(
        drain_deadline_missed=drain_deadline_missed,
        state=capture_state,
    )
    trace_eof_confirmed = capture_failure is None and capture_state.eof_confirmed
    missing_terminal_event = (
        not timed_out
        and codex_exit_code == 0
        and not observer.codex_terminal_event_observed
    )
    if observer.trace_parse_errors or capture_failure is not None or missing_terminal_event:
        terminal_class = "infrastructure_failure"
        wrapper_exit_code = 65
    elif timed_out:
        terminal_class = "task_timeout"
        wrapper_exit_code = 0
    elif codex_exit_code == 0:
        terminal_class = "completed"
        wrapper_exit_code = 0
    else:
        terminal_class = "infrastructure_failure"
        wrapper_exit_code = codex_exit_code

    observer.finish()
    append_event(
        ledger,
        {
            **common_event,
            "event": "adapter_end",
            "timestamp": utc_now(),
            "codex_exit_code": codex_exit_code,
            "wrapper_exit_code": wrapper_exit_code,
            "terminal_class": terminal_class,
            "timed_out": timed_out,
        },
    )
    summary = {
        **common_event,
        "schema_version": "test_first_pilot.adapter_summary.v1",
        "codex_cli": CODEX_CLI_VERSION,
        "codex_exit_code": codex_exit_code,
        "wrapper_exit_code": wrapper_exit_code,
        "terminal_class": terminal_class,
        "timed_out": timed_out,
        "network_access": False,
        "web_search": "disabled",
        "permission_profile": PERMISSION_PROFILE,
        "prompt_sha256": prompt_sha256,
        "prompt_size_bytes": len(prompt_bytes),
        "python_executable": str(python_executable),
        "venv_root": str(venv_root),
        "codex_runtime_read_root": str(codex_runtime),
        "disabled_features": list(DISABLED_FEATURES),
        "trace_parse_errors": observer.trace_parse_errors,
        "trace_eof_confirmed": trace_eof_confirmed,
        "trace_capture_error": capture_failure,
        "codex_terminal_event_observed": observer.codex_terminal_event_observed,
        "trace_path": TRACE_FILE,
        "stderr_path": STDERR_FILE,
        "final_message_path": FINAL_MESSAGE_FILE,
        "ledger_path": LEDGER_FILE,
    }
    (output / SUMMARY_FILE).write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "codex_exit_code": codex_exit_code,
                "wrapper_exit_code": wrapper_exit_code,
                "terminal_class": terminal_class,
                "timed_out": timed_out,
            },
            sort_keys=True,
        )
    )
    return wrapper_exit_code


if __name__ == "__main__":
    raise SystemExit(main())
