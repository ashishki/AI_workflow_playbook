#!/usr/bin/env python3
"""External acceptance checks, outside the agent-editable fixture."""
import argparse
import json
import os
import subprocess
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'companion/ai_workflow_harness_lab/src'))
from ai_workflow_harness_lab.environment import tree_manifest, safe_workspace_path


def check(workspace: Path, task: str) -> list[str]:
    summary = json.loads((workspace.parent / 'adapter/adapter_summary.json').read_text())
    before = summary['workspace_before_agent']
    after = tree_manifest(workspace)
    changed = {p for p in before.keys() | after.keys() if before.get(p) != after.get(p)}
    if task == 'plan':
        return ['Plan-only task changed files: ' + ', '.join(sorted(changed))] if changed else []
    if task == 'review':
        changed = {p for p in changed if not p.startswith('.playbook-artifacts/')}
        return ['Check-only task changed source: ' + ', '.join(sorted(changed))] if changed else []
    if task == 'frontend':
        module = os.environ.get('PLAYBOOK_EVAL_PLAYWRIGHT_MODULE')
        if not module or not Path(module).exists():
            print('Browser verifier unavailable: supply an installed Playwright module', file=sys.stderr)
            raise SystemExit(2)
        try:
            result = subprocess.run(['node', str(ROOT / 'evals/native/check-ui.cjs'), str(workspace),
                                     str(workspace.parent / 'external-browser')], timeout=40)
        except (OSError, subprocess.TimeoutExpired) as exc:
            print(f'Browser verifier unavailable: {exc}', file=sys.stderr)
            raise SystemExit(2) from exc
        if result.returncode == 2:
            raise SystemExit(2)
        return [] if result.returncode == 0 else ['External browser acceptance failed']
    # Tests may be added or extended; project instructions and unrelated files stay intact.
    unexpected = {p for p in changed if p not in ('slugs.py', 'test_slugs.py')
                  and not p.startswith(('__pycache__/', '.playbook-artifacts/'))}
    errors = ['Unexpected change: ' + p for p in sorted(unexpected)]
    namespace = {'__name__': 'slugs_acceptance'}
    source = safe_workspace_path(workspace, 'slugs.py')
    exec(compile(source.read_text(), str(source), 'exec'), namespace)
    examples = [('Two Words', 'two-words'), ('  Hello, world!  ', 'hello-world'),
                ('   ', ''), ('', ''), ('__A---B__', 'a-b'), ('123', '123'),
                ('UPPER_case', 'upper-case')]
    for value, expected in examples:
        actual = namespace['slugify'](value)
        if actual != expected:
            errors.append(f'{value!r}: expected {expected!r}, got {actual!r}')
    return errors


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--workspace', type=Path, required=True)
    ap.add_argument('--task', choices=('backend', 'plan', 'review', 'frontend'), required=True)
    args = ap.parse_args()
    try:
        errors = check(args.workspace, args.task)
    except Exception as exc:
        errors = [f'Acceptance failed: {type(exc).__name__}: {exc}']
    print(json.dumps({'passed': not errors, 'errors': errors}, ensure_ascii=False))
    raise SystemExit(bool(errors))
