from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class SuiteTask:
    task_id: str
    version: str
    title: str
    fixture: Path
    baseline_prompt: Path
    playbook_prompt: Path
    scorers: list[dict[str, Any]]
    correction_budget: int
    expected_failure_taxonomy: list[str]
    required_verification: dict[str, Any] | None = None


@dataclass(frozen=True)
class Suite:
    path: Path
    suite_id: str
    version: str
    tasks: list[SuiteTask]


@dataclass
class AdapterResult:
    exit_code: int
    output_path: Path
    receipt_paths: list[Path]
    trace_paths: list[Path]
    metadata: dict[str, Any]


@dataclass
class ExecutionResult:
    receipt_path: Path
    exit_code: int
    start_timestamp: str
    end_timestamp: str
    timed_out: bool
    command_argv: list[str]


@dataclass
class ScorerResult:
    scorer_id: str
    scorer_version: str
    verdict: str
    score: float
    output_path: Path
    failure_records: list[dict[str, Any]]
    metrics: dict[str, Any]


@dataclass
class TrialResult:
    task: SuiteTask
    condition: str
    trial_index: int
    workspace: Path
    output_dir: Path
    bundle_path: Path
    valid: bool
    score: float
    failure_records: list[dict[str, Any]]
