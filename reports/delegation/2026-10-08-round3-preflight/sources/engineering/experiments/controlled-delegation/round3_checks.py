"""Frozen behavioral scoring and integrity checks; never repairs model output."""
from __future__ import annotations
import fnmatch
from pathlib import Path
from round2_checks import read, sha, write
from round3_fixtures import cases, evaluate


def inventory(workspace):
    workspace = Path(workspace)
    return {p.relative_to(workspace).as_posix(): sha(p) for p in workspace.rglob('*')
            if p.is_file() and not p.is_symlink()}


def guard(workspace, initial, case_id='fulfillment_replay'):
    workspace = Path(workspace)
    patterns = cases()[case_id]['mutable']
    def mutable(name):
        return any(fnmatch.fnmatchcase(name, pattern) or ('/**/' in pattern and
                   fnmatch.fnmatchcase(name, pattern.replace('/**/', '/'))) for pattern in patterns)
    drift = []
    symlinks = [p.relative_to(workspace).as_posix() for p in workspace.rglob('*') if p.is_symlink()]
    for name, digest in initial.items():
        p = workspace / name
        if not p.is_file() or p.is_symlink():
            drift.append(name)
        elif not mutable(name) and sha(p) != digest:
            drift.append(name)
    # New modules/helpers are unnecessary for these three fixes. No cache or
    # conftest/sitecustomize addition may execute during operator verification.
    added = sorted(set(inventory(workspace)) - set(initial) - {'STATE.md', 'diagnosis.json'})
    return {'status': 'FAIL' if drift or added or symlinks else 'PASS',
            'protected_drift': sorted(drift), 'unexpected_added_files': added,
            'symlinks': sorted(symlinks)}


def score(case_id, workspace, initial):
    protected = guard(workspace, initial, case_id)
    if protected['status'] != 'PASS':
        return {**protected, 'score': 0, 'groups': {}, 'evidence': {},
                'evaluator_executed': False, 'reason': 'integrity guard failed before importing workspace code'}
    managed_paths = tuple(name for name in initial if name not in cases()[case_id]['files'])
    observed = evaluate(Path(workspace), case_id, managed_paths=managed_paths)
    # Missing/timeout verification is BLOCKED unless an actually evaluated
    # group already proves a defect. No completion claim is supplied by model.
    groups = observed.get('groups', {})
    failed = any(value is False for value in groups.values())
    complete = (set(groups) == set(cases()[case_id]['groups'])
                and all(type(value) is bool for value in groups.values()))
    status = 'FAIL' if failed else 'PASS' if complete and observed.get('score') == 100 else 'BLOCKED'
    return {**observed, **protected, 'status': status, 'evaluator_executed': True}


def task_status(checks, phase):
    if checks.get('status') == 'FAIL':
        return 'FAIL'
    if checks.get('status') != 'PASS' or not phase.get('completed') or phase.get('timeout'):
        return 'BLOCKED'
    return 'PASS'
