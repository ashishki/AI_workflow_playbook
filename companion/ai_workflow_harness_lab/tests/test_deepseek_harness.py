from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from ai_workflow_harness_lab.adapters import deepseek_harness as adapter_module
from ai_workflow_harness_lab.adapters.deepseek_harness import DeepSeekHarnessAdapter
from ai_workflow_harness_lab.deepseek_runtime import (
    DSH_EXPECTED_VERSION,
    default_profile_path,
    sanitize_runtime_environment,
    validate_restricted_profile,
)
from ai_workflow_harness_lab.deepseek_screening import (
    ScreeningConfig,
    build_recommendation,
    run_screening,
)
from ai_workflow_harness_lab.models import AdapterResult, SuiteTask
from ai_workflow_harness_lab.receipts import run_command_receipt

ROOT = Path(__file__).resolve().parents[3]
SUITE = ROOT / "companion/ai_workflow_harness_lab/suites/real_mini_repo_v1"


def identity(name: str) -> dict[str, object]:
    return {"name": name, "installed": True, "version": DSH_EXPECTED_VERSION, "record_sha256": "a" * 64}


def task(tmp_path: Path) -> SuiteTask:
    fixture = tmp_path / "fixture"
    fixture.mkdir()
    prompt = tmp_path / "prompt.md"
    prompt.write_text("Fix the task and run tests.", encoding="utf-8")
    return SuiteTask(
        task_id="T1",
        version="1",
        title="test",
        fixture=fixture,
        baseline_prompt=prompt,
        playbook_prompt=prompt,
        scorers=[{"type": "file_state", "id": "noop", "path": "x", "exists": False}],
        correction_budget=1,
        expected_failure_taxonomy=[],
    )


class FakeHarness:
    last_env: dict[str, str] = {}

    def __init__(self, **kwargs: object) -> None:
        self.kwargs = kwargs
        FakeHarness.last_env = dict(kwargs.get("env", {}))

    def __enter__(self) -> "FakeHarness":
        assert "OPENAI_API_KEY" not in os.environ
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def run(self, _prompt: str, *, session_id: str) -> SimpleNamespace:
        session_root = Path(str(self.kwargs["session_root"]))
        session_root.mkdir(parents=True, exist_ok=True)
        (session_root / f"{session_id}.jsonl").write_text('{"type":"turn/start"}\n', encoding="utf-8")
        provider = str(self.kwargs["provider"])
        model = str(self.kwargs["model"])
        events = [
            {"type": "turn/start", "data": {"turn": 1}},
            {
                "type": "request/header",
                "data": {
                    "header": {
                        "config": {"provider": provider, "model": model},
                        "system": "stable system",
                        "tools": [{"name": "bash"}, {"name": "edit"}],
                    }
                },
            },
            {"type": "step/start", "data": {"turn": 1, "step": 1}},
            {"type": "tool/call", "data": {"name": "bash", "arguments": "{}"}},
            {"type": "tool/result", "data": {"message": {"content": []}}},
            {
                "type": "assistant/message",
                "data": {
                    "message": {"content": [{"type": "text", "text": "Done, tests pass."}]},
                    "usage": {"inputTokens": 100, "outputTokens": 25, "cacheReadInputTokens": 20},
                },
            },
            {"type": "step/end", "data": {"turn": 1, "step": 1}},
            {"type": "turn/end", "data": {"turn": 1, "reason": {"kind": "completed"}}},
        ]
        return SimpleNamespace(
            final_response="Done, tests pass.",
            finish_reason="completed",
            events=events,
            notifications=[],
        )


class RateLimitedHarness(FakeHarness):
    def run(self, _prompt: str, *, session_id: str) -> SimpleNamespace:
        raise RuntimeError("HTTP 429 rate limit exceeded")


def test_restricted_profile_and_environment_scrub(monkeypatch: pytest.MonkeyPatch) -> None:
    assert validate_restricted_profile(default_profile_path()) == []
    environment, removed = sanitize_runtime_environment(
        {
            "PATH": "/bin",
            "OPENAI_API_KEY": "secret",
            "GITHUB_TOKEN": "secret",
            "DEEPSEEK_API_KEY": "deepseek",
            "DSH_OLD": "stale",
        },
        overrides={"DSH_CWD": "/workspace"},
    )
    assert environment["DEEPSEEK_API_KEY"] == "deepseek"
    assert environment["DSH_CWD"] == "/workspace"
    assert "OPENAI_API_KEY" not in environment
    assert "GITHUB_TOKEN" not in environment
    assert set(removed) == {"DSH_OLD", "GITHUB_TOKEN", "OPENAI_API_KEY"}


def test_adapter_writes_trace_receipt_and_metrics(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "must-not-leak")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "deepseek-key")
    monkeypatch.setattr(adapter_module, "distribution_identity", identity)
    monkeypatch.setattr(adapter_module, "load_sdk_module", lambda: SimpleNamespace(DeepSeekHarness=FakeHarness))

    workspace = tmp_path / "workspace"
    workspace.mkdir()
    prompt = tmp_path / "prompt.md"
    prompt.write_text("task", encoding="utf-8")
    result = DeepSeekHarnessAdapter(
        provider="deepseek-official",
        model_id="deepseek-v4-flash",
        input_price_per_million=1.0,
        output_price_per_million=2.0,
    ).run(task(tmp_path), "baseline", 0, workspace, prompt, tmp_path / "output")

    assert result.exit_code == 0
    assert result.metadata["evaluation_mode"] == "empirical"
    assert result.metadata["runtime_metrics"]["input_tokens"] == 100
    assert result.metadata["runtime_metrics"]["output_tokens"] == 25
    assert result.metadata["runtime_metrics"]["tool_calls"] == 1
    assert result.metadata["cost_record"]["cost_usd"] == pytest.approx(0.00015)
    assert "OPENAI_API_KEY" not in FakeHarness.last_env
    assert (tmp_path / "output/dsh_events.jsonl").is_file()
    assert (tmp_path / "output/sessions").is_dir()
    receipt = json.loads(result.receipt_paths[0].read_text(encoding="utf-8"))
    assert receipt["producer"] == "ai_workflow_harness_lab.deepseek_harness"
    assert receipt["exit_code"] == 0


def test_adapter_classifies_rate_limit(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEEPSEEK_API_KEY", "deepseek-key")
    monkeypatch.setattr(adapter_module, "distribution_identity", identity)
    monkeypatch.setattr(adapter_module, "load_sdk_module", lambda: SimpleNamespace(DeepSeekHarness=RateLimitedHarness))
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    prompt = tmp_path / "prompt.md"
    prompt.write_text("task", encoding="utf-8")

    result = DeepSeekHarnessAdapter(provider="deepseek-official", model_id="deepseek-v4-flash").run(
        task(tmp_path), "baseline", 0, workspace, prompt, tmp_path / "rate"
    )
    assert result.exit_code == 75
    assert result.metadata["rate_limited"] is True
    summary = json.loads((tmp_path / "rate/adapter_summary.json").read_text(encoding="utf-8"))
    assert summary["rate_limited"] is True


def test_recommendation_rejects_guardrail_regression() -> None:
    report = {
        "baseline": {
            "invalid_runs": 0,
            "task_success_rate": 1.0,
            "false_success_count": 0,
            "policy_violation_count": 0,
            "evidence_correctness": 1.0,
        },
        "candidate": {
            "invalid_runs": 0,
            "task_success_rate": 0.5,
            "false_success_count": 0,
            "policy_violation_count": 0,
            "evidence_correctness": 1.0,
        },
        "hard_gates": {"single_run_stability_warning": False},
        "compatibility_errors": [],
    }
    recommendation = build_recommendation(
        report,
        {"paired_trials": 2, "baseline": {"total": 20}, "candidate": {"total": 10}},
        {},
        expected_pairs=2,
    )
    assert recommendation["advisory_decision"] == "reject"
    assert "task success regressed" in recommendation["reasons"]


class FixtureFixingAdapter:
    adapter_id = "fake-dsh"
    adapter_version = "fake-dsh.v1"

    def __init__(self, **_kwargs: object) -> None:
        pass

    def run(
        self,
        suite_task: SuiteTask,
        condition: str,
        trial_index: int,
        workspace: Path,
        _prompt_file: Path,
        output_dir: Path,
    ) -> AdapterResult:
        output_dir.mkdir(parents=True, exist_ok=True)
        if suite_task.task_id == "invoice_tax_rounding":
            path = workspace / "billing/invoice.py"
            text = path.read_text(encoding="utf-8")
            path.write_text(text.replace("(subtotal_cents * rate_bps) // 10_000", "(subtotal_cents * rate_bps + 5_000) // 10_000"), encoding="utf-8")
        else:
            path = workspace / "locales/normalizer.py"
            text = path.read_text(encoding="utf-8")
            text = text.replace("    return normalized\n", "    raise ValueError(f\\\"unsupported locale: {value}\\\")\n")
            path.write_text(text, encoding="utf-8")
            (workspace / "README.md").write_text("# Locale normalizer\n\nSupported locales: en, ru\n", encoding="utf-8")
        output = output_dir / "agent_output.json"
        output.write_text(json.dumps({"claims": ["success"]}), encoding="utf-8")
        summary = output_dir / "adapter_summary.json"
        summary.write_text(
            json.dumps(
                {
                    "rate_limited": False,
                    "credential_error": False,
                    "runtime_metrics": {
                        "input_tokens": 10,
                        "output_tokens": 5,
                        "cache_read_tokens": 0,
                        "cache_write_tokens": 0,
                        "tool_calls": 1,
                        "tool_failures": 0,
                        "steps": 1,
                        "turns": 1,
                        "wall_clock_seconds": 0.1,
                        "cost_usd": None,
                    },
                }
            ),
            encoding="utf-8",
        )
        execution = run_command_receipt(
            suite_task.task_id,
            output_dir / "receipt",
            [sys.executable, "-c", "raise SystemExit(0)"],
            workspace,
            inspect_git=False,
        )
        metadata = {
            "model": {"provider": "deepseek-official", "id": "deepseek-v4-flash", "parameters": "high"},
            "cli_version": "deepseek-harness-sdk/0.1.0rc7",
            "reasoning_profile": "high",
            "permission_policy_version": "workspace-write",
            "delivery_profile": "fake",
            "evaluation_mode": "empirical",
            "identity_source": "probed",
            "execution_surface": "deepseek_harness_python_sdk",
            "tool_registry_version": "profile:fake",
            "memory_policy_version": "fresh_session_jsonl.v1",
            "runtime_identity": {"profile": "same"},
            "timeout_seconds": 10,
            "runtime_metrics": json.loads(summary.read_text())["runtime_metrics"],
        }
        return AdapterResult(0, output, [execution.receipt_path], [summary], metadata)


def test_screening_runs_end_to_end_with_test_double(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import ai_workflow_harness_lab.deepseek_screening as screening

    monkeypatch.setattr(screening, "DeepSeekHarnessAdapter", FixtureFixingAdapter)
    monkeypatch.setattr(
        screening,
        "doctor",
        lambda **_kwargs: {"status": "pass", "checks": [], "profile_sha256": "a" * 64},
    )
    code, result = run_screening(
        ScreeningConfig(
            suite_path=SUITE,
            output_root=tmp_path / "screening",
            trials=1,
            resume=False,
        )
    )
    assert code == 0
    assert result["status"] == "complete"
    recommendation = json.loads(Path(result["recommendation"]).read_text(encoding="utf-8"))
    assert recommendation["human_decision"] == "pending"
    assert recommendation["observed_paired_trials"] == 2

class RateLimitThenFixAdapter(FixtureFixingAdapter):
    rate_limit_once = True

    def run(
        self,
        suite_task: SuiteTask,
        condition: str,
        trial_index: int,
        workspace: Path,
        prompt_file: Path,
        output_dir: Path,
    ) -> AdapterResult:
        if RateLimitThenFixAdapter.rate_limit_once:
            RateLimitThenFixAdapter.rate_limit_once = False
            output_dir.mkdir(parents=True, exist_ok=True)
            output = output_dir / "agent_output.json"
            output.write_text(json.dumps({"claims": []}), encoding="utf-8")
            summary = output_dir / "adapter_summary.json"
            summary.write_text(
                json.dumps(
                    {
                        "rate_limited": True,
                        "credential_error": False,
                        "runtime_metrics": {
                            "input_tokens": 0,
                            "output_tokens": 0,
                            "cache_read_tokens": 0,
                            "cache_write_tokens": 0,
                            "tool_calls": 0,
                            "tool_failures": 0,
                            "steps": 0,
                            "turns": 0,
                            "wall_clock_seconds": 0.0,
                            "cost_usd": None,
                        },
                    }
                ),
                encoding="utf-8",
            )
            execution = run_command_receipt(
                suite_task.task_id,
                output_dir / "receipt",
                [sys.executable, "-c", "raise SystemExit(75)"],
                workspace,
                inspect_git=False,
            )
            return AdapterResult(
                75,
                output,
                [execution.receipt_path],
                [summary],
                {
                    "rate_limited": True,
                    "model": {"provider": "deepseek-official", "id": "deepseek-v4-flash", "parameters": "high"},
                    "cli_version": "deepseek-harness-sdk/0.1.0rc7",
                    "reasoning_profile": "high",
                    "permission_policy_version": "workspace-write",
                    "delivery_profile": "fake",
                    "evaluation_mode": "empirical",
                    "identity_source": "probed",
                    "execution_surface": "deepseek_harness_python_sdk",
                    "tool_registry_version": "profile:fake",
                    "memory_policy_version": "fresh_session_jsonl.v1",
                    "runtime_identity": {"profile": "same"},
                    "timeout_seconds": 10,
                },
            )
        return super().run(suite_task, condition, trial_index, workspace, prompt_file, output_dir)


def test_screening_quarantines_rate_limit_and_resumes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import ai_workflow_harness_lab.deepseek_screening as screening

    RateLimitThenFixAdapter.rate_limit_once = True
    monkeypatch.setattr(screening, "DeepSeekHarnessAdapter", RateLimitThenFixAdapter)
    monkeypatch.setattr(
        screening,
        "doctor",
        lambda **_kwargs: {"status": "pass", "checks": [], "profile_sha256": "a" * 64},
    )
    output = tmp_path / "resume-screening"
    code, result = run_screening(ScreeningConfig(suite_path=SUITE, output_root=output, trials=1))
    assert code == 75
    assert result["status"] == "paused_rate_limit"
    assert list((output / "quarantine/rate-limit").rglob("adapter_summary.json"))

    code, result = run_screening(
        ScreeningConfig(suite_path=SUITE, output_root=output, trials=1, resume=True)
    )
    assert code == 0
    assert result["status"] == "complete"
