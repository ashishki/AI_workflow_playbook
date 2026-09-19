#!/usr/bin/env python3
"""Native delivery for Harness Lab's command adapter; not a second runner."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'companion/ai_workflow_harness_lab/src'))
from ai_workflow_harness_lab.environment import tree_manifest
from ai_workflow_harness_lab.receipts import run_command_receipt
from ai_workflow_harness_lab.telemetry import execution_metrics


def prepare(workspace: Path, prompt: Path, output: Path, condition: str,
            package: Path | None) -> dict:
    # This adapter may only write the disposable layout created by Harness Lab.
    if (workspace.is_symlink() or output.is_symlink() or prompt.is_symlink()
            or workspace.resolve() != output.resolve().parent / 'workspace'
            or prompt.resolve() != output.resolve().parent / 'prompt.md'
            or not (workspace / '.git').is_dir()):
        raise ValueError('Expected a disposable Harness Lab trial layout')
    if (any(p.name != 'receipts' for p in output.iterdir())
            or (output / 'receipts/codex').exists()):
        raise FileExistsError('Refusing to overwrite adapter evidence')
    package_hashes = {}
    if package is not None:
        for path in package.rglob('*'):
            if path.is_symlink():
                raise ValueError('Package symlinks are not supported')
        if (workspace / '.agents').exists() or (workspace / 'AGENTS.md').exists():
            raise FileExistsError('Fixture already has agent instructions')
        package_hashes = tree_manifest(package)
        shutil.copytree(package / 'skills', workspace / '.agents/skills')
        shutil.copyfile(package / 'skills/playbook/assets/project-block.md',
                        workspace / 'AGENTS.md')
    summary = {
        'adapter': 'native-command.v1', 'condition': condition,
        'package_hashes': package_hashes,
        'workspace_before_agent': tree_manifest(workspace),
        'turn_completed': False, 'evaluation': 'execution_only_not_task_verdict',
    }
    (output / 'adapter_summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    return summary


def run(args) -> int:
    workspace, prompt, output = args.workspace, args.prompt_file, args.output_dir
    package = args.package if args.condition == 'playbook' else args.baseline_package
    summary = prepare(workspace, prompt, output, args.condition, package)
    # Reuse the lab's process timeout, descendant cleanup and receipt handling.
    execution = run_command_receipt(
        args.task_id, output / 'receipts/codex',
        ['codex', 'exec', '--ephemeral', '--sandbox', 'workspace-write',
         '-c', 'approval_policy="never"', '--json', '-C', str(workspace),
         '-o', str(output / 'final_message.txt'), prompt.read_text()],
        workspace, timeout=args.timeout, inspect_git=False,
    )
    receipt_dir = execution.receipt_path.parent
    shutil.copyfile(receipt_dir / 'stdout.txt', output / 'codex_events.jsonl')
    shutil.copyfile(receipt_dir / 'stderr.txt', output / 'codex_stderr.txt')
    events, parse_errors = [], 0
    for line in (output / 'codex_events.jsonl').read_text(errors='replace').splitlines():
        if not line.strip():
            continue
        try:
            event = json.loads(line)
            if not isinstance(event, dict) or not isinstance(event.get('type'), str):
                raise ValueError('Malformed event')
            events.append(event)
        except (ValueError, TypeError):
            parse_errors += 1
    terminal = [e for e in events if e['type'] in ('turn.completed', 'turn.failed', 'error')]
    completed = bool(terminal) and terminal[-1]['type'] == 'turn.completed'
    failed = any(e['type'] in ('turn.failed', 'error') for e in events)
    final = output / 'final_message.txt'
    valid = (execution.exit_code == 0 and not execution.timed_out and completed
             and not failed and not parse_errors and final.is_file()
             and bool(final.read_text().strip()))
    summary.update(exit_code=execution.exit_code, timed_out=execution.timed_out,
                   turn_completed=completed, event_parse_errors=parse_errors,
                   execution_valid=bool(valid),
                   usage=terminal[-1].get('usage', 'unknown') if completed else 'unknown')
    reviews = sorted((workspace / '.playbook-artifacts/runs').glob('*/codex_events.jsonl'))
    # Preserve nested review traces with the parent bundle. Do not hide their cost.
    captured_reviews = []
    for path in reviews:
        if path.is_symlink() or not path.resolve().is_relative_to(workspace.resolve()):
            raise ValueError('Review trace escapes the fixture')
        captured_reviews.append({'path': str(path.relative_to(workspace)), 'events': path.read_text()})
    (output / 'review_runs.json').write_text(json.dumps(captured_reviews, indent=2) + '\n')
    try:
        summary['execution_telemetry'] = execution_metrics(
            output / 'codex_events.jsonl', execution.receipt_path, reviews)
    except (ValueError, OSError, KeyError, TypeError) as exc:
        summary['telemetry_error'] = str(exc)  # Corruption must never become a zero bill.
    (output / 'adapter_summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    return 0 if valid else 1


def positive_seconds(raw: str) -> float:
    value = float(raw)
    if not 0 < value < float('inf'):
        raise argparse.ArgumentTypeError('Timeout must be finite and positive')
    return value


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    for name in ('workspace', 'prompt-file', 'output-dir'):
        ap.add_argument('--' + name, type=Path, required=True)
    ap.add_argument('--task-id', required=True)
    ap.add_argument('--condition', choices=('baseline', 'playbook'), required=True)
    ap.add_argument('--package', type=Path, default=ROOT / 'plugins/playbook-native')
    ap.add_argument('--baseline-package', type=Path,
                    help='Previous Native package; omit for plain Codex baseline')
    ap.add_argument('--timeout', type=positive_seconds, default=300)
    try:
        raise SystemExit(run(ap.parse_args()))
    except (OSError, ValueError) as exc:
        print(f'native adapter: {exc}', file=sys.stderr)
        raise SystemExit(1)
