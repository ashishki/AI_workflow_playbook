from __future__ import annotations

import json
from pathlib import Path

from ..models import AdapterResult, SuiteTask
from ..receipts import run_command_receipt
from .base import Adapter


class CommandAdapter(Adapter):
    adapter_id = "command"
    adapter_version = "command.v1"

    def __init__(self, command_template: str, timeout: float | None = None):
        self.command_template = command_template
        self.timeout = timeout

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
        command = self.command_template.format(
            workspace=str(workspace),
            prompt_file=str(prompt_file),
            task_id=task.task_id,
            condition=condition,
            trial=trial_index,
            output_dir=str(output_dir),
        )
        argv = ["/bin/sh", "-c", command]
        execution = run_command_receipt(
            task.task_id,
            output_dir / "receipts/command",
            argv,
            workspace,
            timeout=self.timeout,
            inspect_git=False,
        )
        output_path = output_dir / "agent_output.json"
        output_path.write_text(
            json.dumps(
                {
                    "task_id": task.task_id,
                    "condition": condition,
                    "trial": trial_index,
                    "claims": [],
                    "command_template": self.command_template,
                    "command_argv": argv,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        trace_paths = [
            output_dir / name
            for name in (
                "codex_events.jsonl",
                "codex_stderr.txt",
                "final_message.txt",
                "event_ledger.jsonl",
                "adapter_summary.json",
            )
            if (output_dir / name).is_file()
        ]
        return AdapterResult(
            exit_code=execution.exit_code,
            output_path=output_path,
            receipt_paths=[execution.receipt_path],
            trace_paths=trace_paths,
            metadata={
                "adapter": self.adapter_id,
                "adapter_version": self.adapter_version,
                "timed_out": execution.timed_out,
                "command_receipt": str(execution.receipt_path),
                "command_template": self.command_template,
                "timeout_seconds": self.timeout,
            },
        )
