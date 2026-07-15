from __future__ import annotations

import io
import hashlib
import json
import os
import runpy
import subprocess
import sys
import threading
from pathlib import Path

import jsonschema


ROOT = Path(__file__).resolve().parents[2]
ADAPTER = ROOT / "tools/test_first_pilot_codex_adapter.py"
EVENT_SCHEMA = json.loads(
    (ROOT / "schemas/test_first_pilot_event.schema.json").read_text(encoding="utf-8")
)
MANIFEST = "a" * 64
VERIFIER = 'python -m pytest -q pilot_tests/test_ci_pins.py'


def init_workspace(path: Path) -> None:
    path.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)


def fake_codex(
    path: Path,
    *,
    sleep: bool = False,
    exit_code: int = 0,
    emit_trace: bool = True,
    emit_malformed: bool = False,
    emit_terminal: bool = True,
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    events = [
        {
            "type": "item.completed",
            "item": {
                "id": "cmd-false-green",
                "type": "command_execution",
                "command": f"bash -lc {VERIFIER!r} || true",
                "exit_code": 0,
                "status": "completed",
            },
        },
        {
            "type": "item.started",
            "item": {"id": "cmd-red", "type": "command_execution", "command": VERIFIER},
        },
        {
            "type": "item.completed",
            "item": {
                "id": "cmd-red",
                "type": "command_execution",
                "command": VERIFIER,
                "exit_code": 1,
                "status": "failed",
            },
        },
        {
            "type": "item.completed",
            "item": {
                "id": "change-1",
                "type": "file_change",
                "changes": [{"path": ".github/workflows/ci.yml", "kind": "update"}],
                "status": "completed",
            },
        },
        {
            "type": "item.started",
            "item": {"id": "cmd-repair", "type": "command_execution", "command": VERIFIER},
        },
        {
            "type": "item.completed",
            "item": {
                "id": "cmd-repair",
                "type": "command_execution",
                "command": VERIFIER,
                "exit_code": 1,
                "status": "failed",
            },
        },
        {
            "type": "item.completed",
            "item": {
                "id": "change-2",
                "type": "file_change",
                "changes": [{"path": ".github/workflows/ci.yml", "kind": "update"}],
                "status": "completed",
            },
        },
        {
            "type": "item.started",
            "item": {"id": "cmd-green", "type": "command_execution", "command": VERIFIER},
        },
        {
            "type": "item.completed",
            "item": {
                "id": "cmd-green",
                "type": "command_execution",
                "command": VERIFIER,
                "exit_code": 0,
                "status": "completed",
            },
        },
        {
            "type": "item.started",
            "item": {
                "id": "cmd-final",
                "type": "command_execution",
                "command": f"bash -lc {VERIFIER!r}",
            },
        },
        {
            "type": "item.completed",
            "item": {
                "id": "cmd-final",
                "type": "command_execution",
                "command": f"bash -lc {VERIFIER!r}",
                "exit_code": 0,
                "status": "completed",
            },
        },
    ]
    if emit_terminal:
        events.append({"type": "turn.completed", "usage": {}})
    body = [
        "#!/usr/bin/env python3",
        "import json, os, pathlib, shutil, sys, time",
        "assert 'OPENAI_API_KEY' not in os.environ",
        "assert 'PYTHONPATH' not in os.environ",
        "assert os.environ['PYTHONDONTWRITEBYTECODE'] == '1'",
        "assert os.environ['PYTHONPYCACHEPREFIX'].startswith('/dev/null/')",
        "assert os.environ['PYTEST_DISABLE_PLUGIN_AUTOLOAD'] == '1'",
        "assert os.environ['PYTEST_ADDOPTS'] == '-p no:cacheprovider'",
        "if sys.argv[1:] == ['--version']:",
        "    print('codex-cli 0.144.4')",
        "    raise SystemExit(0)",
        "args = sys.argv[1:]",
        "assert '--sandbox' not in args",
        "assert 'default_permissions=\"test_first_pilot\"' in args",
        "assert any(value.startswith('permissions.test_first_pilot.filesystem=') for value in args)",
        "assert 'permissions.test_first_pilot.network.enabled=false' in args",
        "assert 'include_apps_instructions=false' in args",
        "assert args.count('--disable') >= 10",
        "assert pathlib.Path(shutil.which('python')).resolve() == pathlib.Path(sys.executable).resolve()",
        "final = pathlib.Path(args[args.index('--output-last-message') + 1])",
        "sys.stdin.buffer.read()",
    ]
    if sleep:
        body.append("time.sleep(10)")
    if emit_trace:
        body.extend(
            [
                f"events = {events!r}",
                "for event in events:",
                "    print(json.dumps(event), flush=True)",
            ]
        )
    if emit_malformed:
        body.append("print('{malformed-json', flush=True)")
    body.extend(
        [
            "final.write_text('fake final\\n', encoding='utf-8')",
            f"raise SystemExit({exit_code})",
        ]
    )
    path.write_text("\n".join(body) + "\n", encoding="utf-8")
    path.chmod(0o755)
    return path


def adapter_command(tmp_path: Path, codex_bin: Path, *, timeout: str = "2") -> list[str]:
    workspace = tmp_path / "workspace"
    init_workspace(workspace)
    prompt = tmp_path / "prompt.md"
    prompt.write_text("Do the bounded task.\n", encoding="utf-8")
    return [
        sys.executable,
        str(ADAPTER),
        "--workspace",
        str(workspace),
        "--prompt",
        str(prompt),
        "--output",
        str(tmp_path / "output"),
        "--pilot-id",
        "pilot-test",
        "--attempt-id",
        "pilot-test.pin-ci.baseline.0",
        "--task",
        "pin_ci_actions",
        "--condition",
        "baseline",
        "--trial",
        "0",
        "--manifest-digest",
        MANIFEST,
        "--approval-id",
        "approval-test",
        "--timeout",
        timeout,
        "--codex-bin",
        str(codex_bin),
    ]


def clean_environment() -> dict[str, str]:
    excluded = {"CODEX_MANAGED_BY_NPM", "CODEX_MANAGED_PACKAGE_ROOT", "CODEX_THREAD_ID"}
    return {key: value for key, value in os.environ.items() if key not in excluded}


def read_events(output: Path) -> list[dict[str, object]]:
    events = [json.loads(line) for line in (output / "event_ledger.jsonl").read_text().splitlines()]
    for event in events:
        jsonschema.validate(event, EVENT_SCHEMA)
    return events


def test_adapter_refuses_nested_codex_session(tmp_path: Path) -> None:
    marker = tmp_path / "fake-codex"
    command = adapter_command(tmp_path, fake_codex(marker))
    env = {**os.environ, "CODEX_THREAD_ID": "active-thread"}

    result = subprocess.run(command, env=env, text=True, capture_output=True, check=False)

    assert result.returncode == 2
    assert "refusing nested pilot execution" in result.stderr
    assert not (tmp_path / "output").exists()


def test_adapter_records_isolated_toolchain_and_trace_ledger(tmp_path: Path) -> None:
    package_root = tmp_path / "node_modules" / "@openai" / "codex"
    command = adapter_command(tmp_path, fake_codex(package_root / "bin" / "codex.js"))
    env = clean_environment()
    env["OPENAI_API_KEY"] = "must-not-propagate"

    result = subprocess.run(command, env=env, text=True, capture_output=True, check=False)

    assert result.returncode == 0, result.stderr
    output = tmp_path / "output"
    assert (output / "final_message.txt").read_text(encoding="utf-8") == "fake final\n"
    summary = json.loads((output / "adapter_summary.json").read_text())
    assert summary["web_search"] == "disabled"
    assert summary["permission_profile"] == "test_first_pilot"
    assert summary["prompt_sha256"] == hashlib.sha256(
        b"Do the bounded task.\n"
    ).hexdigest()
    assert summary["prompt_size_bytes"] == len(b"Do the bounded task.\n")
    assert summary["codex_exit_code"] == summary["wrapper_exit_code"] == 0
    assert summary["terminal_class"] == "completed"
    assert summary["trace_parse_errors"] == 0
    assert summary["trace_eof_confirmed"] is True
    assert summary["trace_capture_error"] is None
    assert summary["codex_terminal_event_observed"] is True
    assert Path(summary["python_executable"]).resolve() == Path(sys.executable).resolve()
    assert Path(summary["codex_runtime_read_root"]) == package_root

    events = read_events(output)
    event_names = [event["event"] for event in events]
    assert event_names[:2] == ["adapter_start", "human_intervention"]
    assert event_names[-2:] == ["final_model_gate", "adapter_end"]
    assert event_names.count("verifier_start") == 4
    assert event_names.count("verifier_end") == 4
    assert event_names.count("first_green") == 1
    assert event_names.count("repair_candidate") == 1
    assert next(event for event in events if event["event"] == "first_green")["verifier_attempt"] == 3
    assert next(event for event in events if event["event"] == "repair_candidate")["verifier_attempt"] == 2
    assert events[-2]["result"] == "passed"
    assert events[-2]["verifier_attempt"] == 4
    assert events[1]["occurred"] is False
    assert all(event["pilot_id"] == "pilot-test" for event in events)
    assert all(event["attempt_id"] == "pilot-test.pin-ci.baseline.0" for event in events)
    monotonic_values = [event["monotonic_ns"] for event in events]
    assert all(isinstance(value, int) and value >= 0 for value in monotonic_values)
    assert monotonic_values == sorted(monotonic_values)


def test_adapter_maps_inner_timeout_to_valid_scored_task_outcome(tmp_path: Path) -> None:
    command = adapter_command(
        tmp_path,
        fake_codex(tmp_path / "slow-codex", sleep=True, emit_trace=False),
        timeout="0.02",
    )

    result = subprocess.run(
        command,
        env=clean_environment(),
        text=True,
        capture_output=True,
        check=False,
        timeout=5,
    )

    assert result.returncode == 0, result.stderr
    output = tmp_path / "output"
    summary = json.loads((output / "adapter_summary.json").read_text())
    assert summary["timed_out"] is True
    assert summary["codex_exit_code"] == 124
    assert summary["wrapper_exit_code"] == 0
    assert summary["terminal_class"] == "task_timeout"
    events = read_events(output)
    assert events[-2]["event"] == "final_model_gate"
    assert events[-2]["result"] == "unknown"
    assert events[-1]["codex_exit_code"] == 124
    assert events[-1]["wrapper_exit_code"] == 0


def test_adapter_preserves_nonzero_infrastructure_exit(tmp_path: Path) -> None:
    command = adapter_command(
        tmp_path,
        fake_codex(tmp_path / "failing-codex", exit_code=7, emit_trace=False),
    )

    result = subprocess.run(
        command,
        env=clean_environment(),
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 7
    output = tmp_path / "output"
    summary = json.loads((output / "adapter_summary.json").read_text())
    assert summary["codex_exit_code"] == summary["wrapper_exit_code"] == 7
    assert summary["terminal_class"] == "infrastructure_failure"
    events = read_events(output)
    assert events[-1]["terminal_class"] == "infrastructure_failure"


def test_adapter_rejects_malformed_codex_jsonl_as_infrastructure_failure(
    tmp_path: Path,
) -> None:
    command = adapter_command(
        tmp_path,
        fake_codex(tmp_path / "malformed-codex", emit_malformed=True),
    )

    result = subprocess.run(
        command,
        env=clean_environment(),
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 65
    output = tmp_path / "output"
    summary = json.loads((output / "adapter_summary.json").read_text())
    assert summary["trace_parse_errors"] == 1
    assert summary["terminal_class"] == "infrastructure_failure"
    events = read_events(output)
    assert [event["event"] for event in events].count("trace_parse_error") == 1
    assert events[-1]["wrapper_exit_code"] == 65


def test_adapter_rejects_successful_trace_without_codex_terminal_event(
    tmp_path: Path,
) -> None:
    command = adapter_command(
        tmp_path,
        fake_codex(tmp_path / "truncated-codex", emit_terminal=False),
    )

    result = subprocess.run(
        command,
        env=clean_environment(),
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 65
    summary = json.loads((tmp_path / "output/adapter_summary.json").read_text())
    assert summary["codex_exit_code"] == 0
    assert summary["terminal_class"] == "infrastructure_failure"
    assert summary["trace_eof_confirmed"] is True
    assert summary["trace_capture_error"] is None
    assert summary["codex_terminal_event_observed"] is False


def test_capture_thread_fails_closed_on_reader_exception() -> None:
    adapter = runpy.run_path(str(ADAPTER), run_name="test_first_pilot_codex_adapter")

    class BrokenStream:
        def readline(self) -> bytes:
            raise OSError("synthetic read failure")

    class Observer:
        def observe_line(self, _line: bytes) -> None:
            raise AssertionError("no line should be observed")

    state = adapter["TraceCaptureState"]()
    reader = threading.Thread(
        target=adapter["capture_stdout"],
        args=(BrokenStream(), io.BytesIO(), Observer(), state),
    )
    reader.start()
    reader.join(timeout=1)

    assert reader.is_alive() is False
    assert state.eof_confirmed is False
    assert state.error == "OSError: synthetic read failure"
    assert adapter["trace_capture_failure"](
        drain_deadline_missed=False,
        state=state,
    ) == (
        "Codex JSONL capture failed: OSError: synthetic read failure"
    )


def test_trace_capture_fails_closed_without_confirmed_eof() -> None:
    adapter = runpy.run_path(str(ADAPTER), run_name="test_first_pilot_codex_adapter")
    state = adapter["TraceCaptureState"]()
    assert adapter["trace_capture_failure"](
        drain_deadline_missed=True,
        state=state,
    ) == (
        "Codex JSONL reader did not reach EOF before the drain deadline"
    )
