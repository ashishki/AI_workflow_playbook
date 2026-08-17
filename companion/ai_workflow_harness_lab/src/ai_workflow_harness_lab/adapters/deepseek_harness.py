from __future__ import annotations

import json
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..deepseek_runtime import (
    DSH_EXPECTED_VERSION,
    DSH_RELEASE_TAG,
    DSH_RUNTIME_DISTRIBUTION,
    DSH_SDK_DISTRIBUTION,
    DSH_UPSTREAM_COMMIT,
    DeepSeekCredentialError,
    DeepSeekRateLimitError,
    DeepSeekRuntimeError,
    default_profile_path,
    distribution_identity,
    extract_runtime_metrics,
    find_session_logs,
    is_credential_failure,
    is_rate_limit,
    isolated_process_environment,
    jsonable,
    load_sdk_module,
    sanitize_runtime_environment,
    validate_restricted_profile,
    write_jsonl,
)
from ..environment import git as run_git
from ..models import AdapterResult, SuiteTask
from ..receipts import dirty, sha256_file, utc_now
from .base import Adapter


class DeepSeekHarnessAdapter(Adapter):
    adapter_id = "deepseek-harness"
    adapter_version = "deepseek-harness-sdk.v1"

    def __init__(
        self,
        *,
        provider: str,
        model_id: str,
        profile_path: Path | None = None,
        max_tokens: int | None = None,
        request_timeout_seconds: float | None = 900.0,
        reasoning_profile: str = "provider_default",
        permission_policy: str = "workspace-write",
        delivery_profile: str = "harness_lab_deepseek_single_agent",
        expected_version: str = DSH_EXPECTED_VERSION,
        input_price_per_million: float | None = None,
        output_price_per_million: float | None = None,
        require_durable_log: bool = True,
        environment: dict[str, str] | None = None,
    ) -> None:
        self.provider = provider
        self.model_id = model_id
        self.profile_path = (profile_path or default_profile_path()).resolve()
        self.max_tokens = max_tokens
        self.request_timeout_seconds = request_timeout_seconds
        self.reasoning_profile = reasoning_profile
        self.permission_policy = permission_policy
        self.delivery_profile = delivery_profile
        self.expected_version = expected_version
        self.input_price_per_million = input_price_per_million
        self.output_price_per_million = output_price_per_million
        self.require_durable_log = require_durable_log
        self.environment = environment

    def run(
        self,
        task: SuiteTask,
        condition: str,
        trial_index: int,
        workspace: Path,
        prompt_file: Path,
        output_dir: Path,
    ) -> AdapterResult:
        output_dir.mkdir(parents=True, exist_ok=True)
        profile_errors = validate_restricted_profile(self.profile_path)
        if profile_errors:
            raise DeepSeekRuntimeError("unsafe DeepSeek Harness profile: " + "; ".join(profile_errors))

        sdk_identity = distribution_identity(DSH_SDK_DISTRIBUTION)
        runtime_identity = distribution_identity(DSH_RUNTIME_DISTRIBUTION)
        for identity in (sdk_identity, runtime_identity):
            if not identity["installed"]:
                raise DeepSeekRuntimeError(f"{identity['name']} is not installed")
            if identity["version"] != self.expected_version:
                raise DeepSeekRuntimeError(
                    f"{identity['name']} version mismatch: expected {self.expected_version}, got {identity['version']}"
                )

        sdk = load_sdk_module()
        session_id = f"{task.task_id}-{condition}-{trial_index}-{uuid.uuid4().hex[:12]}"
        session_root = output_dir / "sessions"
        dsh_home = output_dir / "dsh-home"
        session_root.mkdir(parents=True, exist_ok=True)
        dsh_home.mkdir(parents=True, exist_ok=True)
        prompt = prompt_file.read_text(encoding="utf-8")

        overrides = {
            "DSH_HOME": str(dsh_home),
            "DSH_SESSION_ROOT": str(session_root),
            "DSH_CWD": str(workspace.resolve()),
            "DSH_MODEL": self.model_id,
            "DSH_PERMISSION_MODE": self.permission_policy,
            "DSH_TELEMETRY_DISABLED": "1",
        }
        runtime_env, removed_environment = sanitize_runtime_environment(
            self.environment,
            overrides=overrides,
        )

        start_timestamp = utc_now()
        start_monotonic = time.monotonic()
        final_response = ""
        finish_reason: str | None = None
        events: list[dict[str, Any]] = []
        notifications: list[Any] = []
        exception_text = ""
        exit_code = 0
        rate_limited = False
        credential_error = False
        timed_out = False

        try:
            with isolated_process_environment(runtime_env):
                with sdk.DeepSeekHarness(
                    provider=self.provider,
                    model=self.model_id,
                    max_tokens=self.max_tokens,
                    cwd=str(workspace.resolve()),
                    session_root=str(session_root.resolve()),
                    cordis=str(self.profile_path),
                    env=runtime_env,
                    request_timeout_seconds=self.request_timeout_seconds,
                ) as harness:
                    result = harness.run(prompt, session_id=session_id)
            final_response = str(getattr(result, "final_response", "") or "")
            finish_reason = getattr(result, "finish_reason", None)
            events = [jsonable(item) for item in list(getattr(result, "events", []) or [])]
            notifications = list(getattr(result, "notifications", []) or [])
            if is_rate_limit({"response": final_response, "events": events, "notifications": notifications}):
                rate_limited = True
                exit_code = 75
            elif is_credential_failure({"response": final_response, "events": events, "notifications": notifications}):
                credential_error = True
                exit_code = 76
            elif finish_reason != "completed":
                exit_code = 78
        except Exception as exc:  # SDK-specific exception classes are not a stable public contract yet.
            exception_text = f"{type(exc).__name__}: {exc}"
            if is_rate_limit(exception_text):
                rate_limited = True
                exit_code = 75
            elif is_credential_failure(exception_text):
                credential_error = True
                exit_code = 76
            elif isinstance(exc, TimeoutError) or "timeout" in exception_text.lower():
                timed_out = True
                exit_code = 124
            else:
                exit_code = 70

        end_timestamp = utc_now()
        wall_clock_seconds = max(0.0, time.monotonic() - start_monotonic)
        events_path = write_jsonl(output_dir / "dsh_events.jsonl", events)
        notifications_path = write_jsonl(output_dir / "dsh_notifications.jsonl", notifications)
        final_path = output_dir / "final_message.txt"
        final_path.write_text(final_response, encoding="utf-8")
        stderr_path = output_dir / "dsh_stderr.txt"
        stderr_path.write_text(exception_text + ("\n" if exception_text else ""), encoding="utf-8")

        session_logs = find_session_logs(session_root, session_id)
        metrics = extract_runtime_metrics(
            events,
            notifications,
            input_price_per_million=self.input_price_per_million,
            output_price_per_million=self.output_price_per_million,
        )
        metrics["wall_clock_seconds"] = wall_clock_seconds
        metrics["finish_reason"] = finish_reason
        metrics["durable_session_logs"] = len(session_logs)
        if exit_code == 0 and not metrics["request_header_observed"]:
            exit_code = 77
        if exit_code == 0 and self.require_durable_log and not session_logs:
            exit_code = 77

        summary = {
            "schema_version": "harness_lab.deepseek_adapter_summary.v1",
            "task_id": task.task_id,
            "condition": condition,
            "trial_index": trial_index,
            "session_id": session_id,
            "provider": self.provider,
            "model_id": self.model_id,
            "finish_reason": finish_reason,
            "exit_code": exit_code,
            "rate_limited": rate_limited,
            "credential_error": credential_error,
            "timed_out": timed_out,
            "profile_path": str(self.profile_path),
            "profile_sha256": sha256_file(self.profile_path),
            "release_tag": DSH_RELEASE_TAG,
            "upstream_commit": DSH_UPSTREAM_COMMIT,
            "sdk_identity": sdk_identity,
            "runtime_identity": runtime_identity,
            "removed_environment_variables": removed_environment,
            "runtime_metrics": metrics,
            "start_timestamp": start_timestamp,
            "end_timestamp": end_timestamp,
        }
        summary_path = output_dir / "adapter_summary.json"
        summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

        claims: list[str] = []
        lower_response = final_response.lower()
        if any(token in lower_response for token in ("tests pass", "test passed", "completed", "done", "success")):
            claims.append("success")
        output_path = output_dir / "agent_output.json"
        output_path.write_text(
            json.dumps(
                {
                    "task_id": task.task_id,
                    "condition": condition,
                    "trial": trial_index,
                    "claims": claims,
                    "final_response": final_response,
                    "finish_reason": finish_reason,
                    "session_id": session_id,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

        receipt_path = self._write_receipt(
            task=task,
            workspace=workspace,
            output_dir=output_dir / "receipt",
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
            exit_code=exit_code,
            final_path=final_path,
            stderr_path=stderr_path,
            metrics=metrics,
        )
        trace_paths = [events_path, notifications_path, final_path, stderr_path, summary_path, *session_logs]
        cost_record = {
            "cost_usd": metrics["cost_usd"] if metrics["cost_usd"] is not None else "unknown",
            "tokens": {
                "input": metrics["input_tokens"],
                "output": metrics["output_tokens"],
                "cache_read": metrics["cache_read_tokens"],
                "cache_write": metrics["cache_write_tokens"],
            },
        }
        metadata = {
            "adapter": self.adapter_id,
            "adapter_version": self.adapter_version,
            "timed_out": timed_out,
            "rate_limited": rate_limited,
            "credential_error": credential_error,
            "invalid_trace": exit_code == 77,
            "finish_reason": finish_reason,
            "timeout_seconds": self.request_timeout_seconds,
            "model": {
                "provider": self.provider,
                "id": self.model_id,
                "parameters": self.reasoning_profile,
            },
            "cli_version": f"deepseek-harness-sdk/{sdk_identity['version']}",
            "reasoning_profile": self.reasoning_profile,
            "permission_policy_version": self.permission_policy,
            "delivery_profile": self.delivery_profile,
            "evaluation_mode": "empirical",
            "identity_source": "probed",
            "execution_surface": "deepseek_harness_python_sdk",
            "tool_registry_version": f"dsh-profile:{summary['profile_sha256']}",
            "memory_policy_version": "fresh_session_jsonl.v1",
            "runtime_identity": {
                "release_tag": DSH_RELEASE_TAG,
                "upstream_commit": DSH_UPSTREAM_COMMIT,
                "sdk": sdk_identity,
                "runtime": runtime_identity,
                "profile_sha256": summary["profile_sha256"],
                "system_prompt_sha256": metrics["system_prompt_sha256"],
                "tool_schema_sha256": metrics["tool_schema_sha256"],
            },
            "runtime_metrics": metrics,
            "cost_record": cost_record,
        }
        return AdapterResult(
            exit_code=exit_code,
            output_path=output_path,
            receipt_paths=[receipt_path],
            trace_paths=trace_paths,
            metadata=metadata,
        )

    def _write_receipt(
        self,
        *,
        task: SuiteTask,
        workspace: Path,
        output_dir: Path,
        start_timestamp: str,
        end_timestamp: str,
        exit_code: int,
        final_path: Path,
        stderr_path: Path,
        metrics: dict[str, Any],
    ) -> Path:
        output_dir.mkdir(parents=True, exist_ok=True)
        stdout_copy = output_dir / "stdout.txt"
        stderr_copy = output_dir / "stderr.txt"
        diff_path = output_dir / "diff_stat.txt"
        stdout_copy.write_bytes(final_path.read_bytes())
        stderr_copy.write_bytes(stderr_path.read_bytes())
        diff = run_git(["diff", "--stat"], workspace)
        diff_path.write_text(diff.stdout if diff.returncode == 0 else "", encoding="utf-8")
        commit = run_git(["rev-parse", "HEAD"], workspace)
        commit_value = commit.stdout.strip() if commit.returncode == 0 else "git-unavailable"
        receipt = {
            "schema_version": "playbook.command_receipt.v1",
            "receipt_id": f"{task.task_id}-dsh-{uuid.uuid4().hex[:12]}",
            "task_id": task.task_id,
            "producer": "ai_workflow_harness_lab.deepseek_harness",
            "command_argv": [
                "deepseek-harness-sdk",
                "run",
                "--provider",
                self.provider,
                "--model",
                self.model_id,
            ],
            "working_directory": str(workspace),
            "start_timestamp": start_timestamp,
            "end_timestamp": end_timestamp,
            "exit_code": int(exit_code),
            "stdout_artifact_path": "stdout.txt",
            "stdout_sha256": sha256_file(stdout_copy),
            "stderr_artifact_path": "stderr.txt",
            "stderr_sha256": sha256_file(stderr_copy),
            "repo_commit_before": commit_value,
            "repo_commit_after": commit_value,
            "dirty_state_before": ["fixture_initialized"],
            "dirty_state_after": dirty(workspace),
            "diff_stat_artifact_path": "diff_stat.txt",
            "diff_stat_sha256": sha256_file(diff_path),
            "environment_summary": {
                "execution_surface": "deepseek_harness_python_sdk",
                "profile_sha256": sha256_file(self.profile_path),
                "permission_policy": self.permission_policy,
                "wall_clock_seconds": metrics["wall_clock_seconds"],
                "timed_out": bool(exit_code == 124),
            },
            "parent_receipt_id": None,
            "redaction_status": "not_requested",
        }
        receipt_path = output_dir / "receipt.json"
        receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return receipt_path
