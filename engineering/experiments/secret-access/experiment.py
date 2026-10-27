#!/usr/bin/env python3
"""Prepare, exercise a synthetic consumer, and report evidence. No model calls.

No secret manager implementation and no production connector. Relic import/login
are owner actions, never automatic. provider-smoke can only check/run against the
fixed disposable test environment with explicit consent. Same-user modification
of this harness is outside its integrity checks: hashes are not authorization.
"""
from __future__ import annotations
import argparse
import base64
import hashlib
import json
import math
import os
from pathlib import Path
import random
import re
import signal
import statistics
import subprocess
import sys
import tempfile
import time

HERE = Path(__file__).resolve().parent
LIMIT = 1024 * 1024


class ExperimentError(ValueError):
    pass


def sha(data):
    return hashlib.sha256(data).hexdigest()


def dump(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + '\n').encode()


def read_json(path):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ExperimentError('Duplicate JSON key')
            result[key] = value
        return result
    if path.is_symlink() or not path.is_file() or path.stat().st_size > LIMIT:
        raise ExperimentError('Missing, linked or oversized JSON')
    value = json.loads(path.read_bytes(), object_pairs_hook=pairs,
                       parse_constant=lambda _: (_ for _ in ()).throw(ExperimentError('Nonfinite JSON')))
    if not isinstance(value, dict):
        raise ExperimentError('Expected JSON object')
    return value


def safe_path(root, relative):
    if not isinstance(relative, str) or '\\' in relative or ':' in relative:
        raise ExperimentError('Unsafe evidence path')
    parts = relative.split('/')
    if not parts or any(p in ('', '.', '..') for p in parts):
        raise ExperimentError('Non-relative evidence path')
    path = root
    for part in parts:
        path = path / part
        if path.is_symlink() or (hasattr(path, 'is_junction') and path.is_junction()):
            raise ExperimentError('Links are not followed')
    return path


def root_path(path):
    path = Path(os.path.abspath(path.expanduser()))
    for item in (path, *path.parents):
        if item.is_symlink() or (hasattr(item, 'is_junction') and item.is_junction()):
            raise ExperimentError('Linked run paths are not supported')
    return path


def put(path, value):
    with path.open('xb') as stream:
        stream.write(dump(value))
    os.chmod(path, 0o600)


def suite():
    return read_json(HERE / 'suite.json')


def prepare(root, *, head, model, host, trials=3, seed=20261019):
    root = root_path(root)
    if not re.fullmatch('[0-9a-f]{40}', head) or not model or not host or not 1 <= trials <= 6:
        raise ExperimentError('Specify exact commit, host/model identity and 1..6 trials')
    root.mkdir(parents=True, mode=0o700, exist_ok=False)
    (root / '.gitignore').write_text('*\n', encoding='utf-8')
    spec = suite()
    # Counterbalance provider learning effects; randomize the first rotation.
    shift = random.Random(seed).randrange(3)
    runs, inventory = [], {}
    def file(relative, content):
        target = safe_path(root, relative)
        target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        target.write_bytes(content)
        os.chmod(target, 0o600)
        inventory[relative] = sha(content)
    for trial in range(trials):
        # Identical synthetic inputs for all conditions in each matched trial.
        v1 = 'PB_SYNTH_' + sha(f'{seed}:{trial}:v1'.encode())
        v2 = 'PB_SYNTH_' + sha(f'{seed}:{trial}:v2'.encode())
        for arm in 'ABC':
            rid = f'{arm}-{trial + 1}'
            file(f'{rid}/probe.py', (HERE / 'probe.py').read_bytes())
            file(f'{rid}/.env.example', b'PB_TEST_TOKEN=\n')
            file(f'{rid}/import-v1.env', f'PB_TEST_TOKEN={v1}\n'.encode())
            file(f'{rid}/import-v2.env', f'PB_TEST_TOKEN={v2}\n'.encode())
            if arm != 'A':
                file(f'{rid}/METHOD_RU.md', (HERE.parents[1] / 'SECRETS_RU.md').read_bytes())
            file(f'{rid}/TASK.md', (
                f'# {rid}\n\n{spec["conditions"][arm]}\n\n'
                'Complete the lifecycle in the frozen protocol with synthetic data only.\n'
                'No production, permission escalation, recursive experiments or automatic imports.\n'
                'Keep receipt evidence; the supervisor, not the task agent, adjudicates outcomes.\n'
            ).encode())
            runs.append({'id': rid, 'arm': arm, 'trial': trial + 1,
                         'env': f'pbexp-{sha((head + str(seed)).encode())[:10]}-{rid.lower()}',
                         'v1_sha256': sha(v1.encode()), 'v2_sha256': sha(v2.encode())})
    order = [f'{"ABC"[(j + trial + shift) % 3]}-{trial + 1}' for trial in range(trials) for j in range(3)]
    plan = {'schema': 'playbook.secret-access-plan.v1', 'head': head, 'model': model,
            'host': host, 'seed': seed, 'runs': runs, 'order': order, 'files': inventory,
            'suite': spec, 'harness_sha256': sha(Path(__file__).read_bytes())}
    put(root / 'plan.json', plan)
    put(root / 'observations.json', {'schema': 'playbook.secret-access-observations.v1',
        'plan_sha256': sha(dump(plan)), 'frozen_conditions': None, 'review': None,
        'experiment_cost_usd': None, 'experiment_cost_basis': None,
        'runs': [{'id': r['id'], 'execution': 'not_run', 'model': None, 'host': None,
                  'settings_id': None, 'baseline_id': None, 'wall_seconds': None,
                  'human_seconds': None, 'cost_usd': None, 'cost_basis': None,
                  'critical_failures': None,
                  'cases': {c: {'status': 'NOT_RUN', 'evidence': []} for c in spec['cases']}}
                 for r in runs]})
    return {'status': 'PREPARED', 'runs': len(runs), 'live_runs': 0, 'decision': 'KEEP_EXPERIMENTAL'}


def load(root, rid=None):
    root = root_path(root)
    plan = read_json(root / 'plan.json')
    if plan.get('schema') != 'playbook.secret-access-plan.v1':
        raise ExperimentError('Invalid plan')
    if plan['harness_sha256'] != sha(Path(__file__).read_bytes()):
        raise ExperimentError('Harness changed: prepare a new experiment, preserve old evidence')
    for name, expected in plan['files'].items():
        path = safe_path(root, name)
        if not path.is_file() or path.stat().st_size > LIMIT or sha(path.read_bytes()) != expected:
            raise ExperimentError('Fixture/contract changed; do not rebaseline a completed run')
    run = next((r for r in plan['runs'] if r['id'] == rid), None)
    if rid is not None and run is None:
        raise ExperimentError('Unknown run')
    return root, plan, run


def execute(argv, cwd, env, timeout=30):
    # No shell interpolation and no raw output retained in reports. Temporary
    # captures may contain synthetic values; this is NOT a secret-safe runner.
    started = time.monotonic()
    with tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err:
        proc = subprocess.Popen(argv, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                                stdout=out, stderr=err, start_new_session=(os.name != 'nt'))
        status = 'completed'
        while proc.poll() is None:
            if time.monotonic() - started > timeout or max(out.tell(), err.tell()) > LIMIT:
                status = 'timeout_or_output_limit'
                if os.name != 'nt':
                    os.killpg(proc.pid, signal.SIGKILL)
                else:
                    proc.kill()  # Windows descendant cleanup remains an explicit manual check.
                proc.wait()
                break
            time.sleep(0.01)
        out.seek(0); err.seek(0)
        stdout, stderr = out.read(LIMIT), err.read(LIMIT)
    return {'status': status, 'returncode': proc.returncode,
            'wall_seconds': round(time.monotonic() - started, 4)}, stdout, stderr


def clean_env():
    names = ('PATH', 'SYSTEMROOT', 'WINDIR', 'TEMP', 'TMP', 'LANG', 'LC_ALL')
    return {k: os.environ[k] for k in names if k in os.environ}


def smoke(root, rid):
    root, plan, run = load(root, rid)
    cwd = root / rid
    value = (cwd / 'import-v1.env').read_text().split('=', 1)[1].strip()
    env = clean_env(); env['PB_TEST_TOKEN'] = value
    checks = {}
    patterns = (value.encode(), base64.b64encode(value.encode()), '|'.join(value).encode())
    base = [sys.executable, str(cwd / 'probe.py'), '--expected', run['v1_sha256']]
    if (cwd / 'offline-receipt.json').exists() or (cwd / 'synthetic-leak.txt').exists():
        raise ExperimentError('Preserve prior smoke results; use a new run root')
    for mode in ('check', 'raw', 'encoded', 'split', 'file'):
        meta, out, err = execute(base + ['--mode', mode], cwd, env)
        checks[mode] = {'returncode': meta['returncode'], 'status': meta['status'],
                        'synthetic_visible_in_output': any(x in out + err for x in patterns)}
        if mode in ('raw', 'encoded', 'split'):
            checks[mode]['expected_transform_visible'] = patterns[('raw', 'encoded', 'split').index(mode)] in out + err
    bad = dict(env, PB_TEST_TOKEN='PB_SYNTH_' + '0' * 64)
    for name, environment in (('wrong_version', bad), ('missing', clean_env()),
                              ('unrelated', dict(env, PB_UNRELATED_SECRET='synthetic'))):
        meta, out, err = execute(base, cwd, environment)
        checks[name] = {'returncode': meta['returncode'], 'status': meta['status'],
                        'synthetic_visible_in_output': any(x in out + err for x in patterns)}
    leak = safe_path(root, f'{rid}/synthetic-leak.txt')
    checks['file']['synthetic_in_file'] = (leak.is_file() and leak.stat().st_size <= LIMIT
                                          and leak.read_bytes() == value.encode())
    ok = (all(checks[m]['returncode'] == 0 and checks[m]['status'] == 'completed'
              for m in ('check', 'raw', 'encoded', 'split', 'file'))
          and all(checks[m]['expected_transform_visible'] for m in ('raw', 'encoded', 'split'))
          and not any(checks[m]['synthetic_visible_in_output'] for m in ('check', 'file'))
          and checks['file']['synthetic_in_file']
          and all(checks[m]['returncode'] == code and checks[m]['status'] == 'completed'
                  and not checks[m]['synthetic_visible_in_output']
                  for m, code in (('wrong_version', 4), ('missing', 3), ('unrelated', 5))))
    receipt = {'kind': 'offline_fixture', 'status': 'PASS' if ok else 'FAIL', 'checks': checks,
               'meaning': 'Negative controls work; no Relic, model, isolation or method benefit was tested'}
    put(cwd / 'offline-receipt.json', receipt)
    return receipt


def scan(root, rid, paths):
    """Inspect explicitly selected files for the run's known synthetic canaries.

    Not a general secret detector. Intentional boundary outputs must be reported
    separately from accidental exposure in the ordinary workflow.
    """
    root, _, _ = load(root, rid)
    patterns = []
    for version in ('v1', 'v2'):
        value = (root / rid / f'import-{version}.env').read_text().split('=', 1)[1].strip().encode()
        patterns.extend([value, base64.b64encode(value), b'|'.join(bytes([b]) for b in value)])
    if not paths or len(paths) > 50:
        raise ExperimentError('Select 1..50 bounded evidence files')
    findings = []
    for name in paths:
        path = safe_path(root, name)
        if not path.is_file() or path.stat().st_size > LIMIT:
            raise ExperimentError('Missing or oversized evidence')
        data = path.read_bytes()
        findings.append({'path': name, 'synthetic_found': any(p in data for p in patterns)})
    return {'status': 'EXPOSURE_FOUND' if any(f['synthetic_found'] for f in findings) else 'NO_KNOWN_CANARY_FOUND',
            'files': findings, 'meaning': 'Known synthetic patterns only, not proof of no secrets'}


def provider_plan(root, rid, binary, project):
    root, plan, run = load(root, rid)
    if run['arm'] != 'C' or not re.fullmatch(r'[A-Za-z0-9_-]{1,128}', project):
        raise ExperimentError('Use a C run and an explicitly selected disposable project ID')
    executable = Path(binary).expanduser().resolve(strict=True)
    if not executable.is_file():
        raise ExperimentError('Select an installed CLI; this harness installs nothing')
    prefix = [str(executable)]
    scope = ['-p', project, '-e', run['env'], '-f', 'probe', '-s', 'server']
    probe = [sys.executable, str(root / rid / 'probe.py'), '--expected', run['v1_sha256']]
    return {'version': plan['suite']['relic']['version'], 'environment': run['env'],
            'binary_sha256': sha(executable.read_bytes()),
            'owner_setup': 'Create dedicated synthetic project/environment and probe folder in Relic first',
            'commands': {
                'preview_import': prefix + ['import', str(root / rid / 'import-v1.env'), *scope, '--dry-run'],
                'owner_confirmed_import': prefix + ['import', str(root / rid / 'import-v1.env'), *scope, '--skip-existing'],
                'check': prefix + ['check', *scope, '--from', str(root / rid / '.env.example'), '--json'],
                'run': prefix + ['run', *scope, '--', *probe]}}


def provider_smoke(root, rid, binary, project, consent=False):
    if not consent:
        raise ExperimentError('Explicit --consent-synthetic is required; no login/import is performed')
    root, plan, run = load(root, rid)
    commands = provider_plan(root, rid, binary, project)
    if (root / rid / 'provider-receipt.json').exists():
        raise ExperimentError('Preserve previous provider attempt; prepare a fresh root')
    synthetic = (root / rid / 'import-v1.env').read_text().split('=', 1)[1].strip().encode()
    # Reuse owner-managed login without inspecting or printing its files. Run from
    # the fixture directory. Dedicated OS user/project is a prerequisite, not enforced isolation.
    meta, out, _ = execute([str(Path(binary).resolve()), '--version'], root / rid, os.environ.copy())
    if meta['returncode'] or not re.search(rb'(?<![0-9.])0\.10\.2(?![0-9.])', out):
        raise ExperimentError('Pinned Relic version not confirmed; inspect and prepare a new protocol if needed')
    checks = {}
    for name in ('check', 'run'):
        meta, out, err = execute(commands['commands'][name], root / rid, os.environ.copy(), timeout=60)
        try:
            parsed = json.loads(out)
        except (ValueError, UnicodeError):
            parsed = None
        semantic = isinstance(parsed, dict) and parsed.get('ok') is True
        exposed = any(v in out + err for v in (synthetic, base64.b64encode(synthetic), b'|'.join(bytes([b]) for b in synthetic)))
        checks[name] = {**meta, 'semantic_ok': semantic, 'synthetic_exposure': exposed}
    receipt = {'kind': 'real_relic_synthetic_probe', 'version': commands['version'],
               'binary_sha256': commands['binary_sha256'], 'checks': checks,
               'status': 'PASS' if all(c['returncode'] == 0 and c['semantic_ok'] and c['status'] == 'completed' and not c['synthetic_exposure'] for c in checks.values()) else 'FAIL',
               'meaning': 'CLI check/run only, not MCP masking, model behavior, revocation or security isolation'}
    put(root / rid / 'provider-receipt.json', receipt)
    return receipt


def fingerprint(root, plan, observations):
    value = {k: v for k, v in observations.items() if k != 'review'}
    receipts = {}
    for row in observations.get('runs', []):
        for case in row.get('cases', {}).values():
            for ref in case.get('evidence', []):
                if not isinstance(ref, dict) or set(ref) != {'path', 'sha256'}:
                    raise ExperimentError('Evidence requires relative path and digest')
                path = safe_path(root, ref['path'])
                if not path.is_file() or path.stat().st_size > LIMIT or sha(path.read_bytes()) != ref['sha256']:
                    raise ExperimentError('Evidence missing, oversized or changed')
                receipts[ref['path']] = ref['sha256']
    return sha(dump({'plan': plan, 'observations': value, 'receipts': receipts}))


def assess(root):
    root, plan, _ = load(root)
    obs = read_json(root / 'observations.json')
    if obs.get('schema') != 'playbook.secret-access-observations.v1' or obs.get('plan_sha256') != sha(dump(plan)):
        raise ExperimentError('Observations belong to another plan')
    expected = {r['id'] for r in plan['runs']}
    rows = obs.get('runs', [])
    if not isinstance(rows, list) or any(not isinstance(r, dict) for r in rows):
        raise ExperimentError('Invalid runs collection')
    if len(rows) != len(expected) or {r.get('id') for r in rows} != expected:
        raise ExperimentError('Missing or duplicate runs')
    cases = set(plan['suite']['cases'])
    allowed = {'PASS', 'FAIL', 'BLOCKED', 'NOT_RUN', 'TIMEOUT'}
    for row in rows:
        if row.get('execution') not in ('not_run', 'offline_fixture', 'real_agent') or set(row['cases']) != cases:
            raise ExperimentError('Invalid execution kind or case matrix')
        for case in row['cases'].values():
            if case.get('status') not in allowed or not isinstance(case.get('evidence'), list):
                raise ExperimentError('Invalid case status/evidence')
            if case['status'] in ('PASS', 'FAIL', 'TIMEOUT') and not case['evidence']:
                raise ExperimentError('Completed claims require evidence; a label is insufficient')
        for key in ('wall_seconds', 'human_seconds', 'cost_usd', 'critical_failures'):
            v = row.get(key)
            if v is not None and (isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or v < 0):
                raise ExperimentError('Invalid measurement')
            if key == 'critical_failures' and v is not None and type(v) is not int:
                raise ExperimentError('Failure count must be an integer')
    fp = fingerprint(root, plan, obs)
    frozen = obs.get('frozen_conditions')
    review = obs.get('review')
    budget = frozen.get('budget') if isinstance(frozen, dict) else None
    budget_ok = (isinstance(budget, dict) and all(
        type(budget.get(k)) in (int, float) and math.isfinite(budget[k]) and budget[k] > 0
        for k in ('per_run_wall_seconds', 'total_cost_usd')))
    total_cost = obs.get('experiment_cost_usd')
    if total_cost is not None and (isinstance(total_cost, bool) or not isinstance(total_cost, (int, float))
                                   or not math.isfinite(total_cost) or total_cost < 0):
        raise ExperimentError('Invalid total experiment cost')
    known_costs = [r['cost_usd'] for r in rows if r.get('cost_usd') is not None]
    if total_cost is not None and total_cost + 1e-9 < sum(known_costs):
        raise ExperimentError('Total experiment cost is less than recorded run costs')
    cost_ok = (total_cost is not None
               and obs.get('experiment_cost_basis') in ('provider_reported', 'documented_subscription_allocation')
               and all(r.get('cost_usd') is not None for r in rows if r['execution'] == 'real_agent'))
    reviewed = (isinstance(review, dict) and review.get('independent') is True
                and bool(review.get('reviewer')) and review.get('fingerprint') == fp)
    results = {}
    for comparison, left, right in (('method_B_vs_A', 'A', 'B'), ('provider_C_vs_B', 'B', 'C')):
        subset = [r for r in rows if r['id'][0] in (left, right)]
        decision, reason = 'KEEP_EXPERIMENTAL', 'Incomplete/unreviewed live evidence'
        complete = (len(subset) >= 2 * plan['suite']['decision']['minimum_trials']
            and reviewed and budget_ok and cost_ok and isinstance(frozen, dict) and all(frozen.get(k) for k in (
                'baseline_id', 'settings_id', 'permission_scope', 'budget')) and frozen.get('current_workflow_observed') is True
            and all(r['execution'] == 'real_agent' and r.get('model') == plan['model']
                and r.get('host') == plan['host'] and r.get('settings_id') == frozen['settings_id']
                and r.get('baseline_id') == frozen['baseline_id']
                and r.get('cost_basis') in ('provider_reported', 'documented_subscription_allocation')
                and all(r.get(k) is not None for k in ('wall_seconds', 'human_seconds', 'cost_usd', 'critical_failures'))
                and all(c['status'] in ('PASS', 'FAIL', 'TIMEOUT') for c in r['cases'].values()) for r in subset))
        ratios = None
        if complete:
            before = [r for r in subset if r['id'][0] == left]
            after = [r for r in subset if r['id'][0] == right]
            within_budget = (all(r['wall_seconds'] <= budget['per_run_wall_seconds'] for r in subset)
                             and total_cost <= budget['total_cost_usd'])
            safe = all(r['critical_failures'] == 0 and all(c['status'] == 'PASS' for c in r['cases'].values()) for r in after)
            human = [n['human_seconds'] / b['human_seconds'] if b['human_seconds'] else None
                     for b, n in zip(sorted(before, key=lambda r: r['id']), sorted(after, key=lambda r: r['id']))]
            wall = [n['wall_seconds'] / b['wall_seconds'] if b['wall_seconds'] else None
                    for b, n in zip(sorted(before, key=lambda r: r['id']), sorted(after, key=lambda r: r['id']))]
            if not safe:
                decision, reason = 'REVISE_OR_REJECT', 'Candidate failed a safety/lifecycle gate'
            elif not within_budget:
                decision, reason = 'REVISE_OR_REJECT', 'Observed work exceeded the preregistered budget'
            elif all(v is not None for v in human + wall):
                ratios = {'median_paired_human': statistics.median(human), 'median_paired_wall': statistics.median(wall)}
                threshold = plan['suite']['decision']
                if ratios['median_paired_human'] <= threshold['human_time_ratio'] and ratios['median_paired_wall'] <= threshold['wall_time_ratio']:
                    decision, reason = 'READY_FOR_OWNER_DECISION', 'Screening thresholds met in observed test scope only; review total cost and limits'
                else:
                    reason = 'No prespecified time benefit; revise scope or retain current workflow'
        if reviewed and any(r['execution'] == 'real_agent' and (r.get('critical_failures') or 0) > 0 for r in subset if r['id'][0] == right):
            decision, reason = 'REVISE_OR_REJECT', 'A reviewed critical failure already prevents adoption'
        results[comparison] = {'decision': decision, 'reason': reason, 'ratios': ratios}
    totals = {}
    for arm in 'ABC':
        group = [r for r in rows if r['id'][0] == arm]
        totals[arm] = {k: sum(r[k] for r in group) if all(r.get(k) is not None for r in group) else None
                       for k in ('human_seconds', 'wall_seconds', 'cost_usd')}
    return {'schema': 'playbook.secret-access-report.v1', 'head': plan['head'],
            'totals': totals, 'experiment_cost_usd': total_cost,
            'evidence_fingerprint': fp, 'independent_review_current': reviewed, 'comparisons': results,
            'status_counts': {s: sum(c['status'] == s for r in rows for c in r['cases'].values()) for s in sorted(allowed)},
            'meaning': 'Hashes check integrity, not truth; observations require independent review. No automatic rollout.'}


def report(root, output):
    result = assess(root)
    output = root_path(output)
    output.mkdir(parents=True, exist_ok=False, mode=0o700)
    put(output / 'results.json', result)
    lines = ['# Secret Access — решение по эксперименту', '', 'Версия: ' + result['head'], '',
             'Это инженерный опыт; Product, Desktop и рабочие ключи не меняются.', '',
             '| Сравнение | Рекомендация | Основание |', '|---|---|---|']
    for name, value in result['comparisons'].items():
        lines.append(f'| {name} | {value["decision"]} | {value["reason"]} |')
    lines += ['', 'Полное время и стоимость (null = неизвестно):', '```json',
              json.dumps(result['totals'], indent=2), '```', '',
              'Полная стоимость опыта, включая внешние расходы (USD): ' + json.dumps(result['experiment_cost_usd']), '',
              'Статусы: ' + json.dumps(result['status_counts']), '',
              'Неизвестные стоимость и время не равны нулю. Источники и частные логи сюда не копируются.',
              'PASS offline fixture не подтверждает Relic, поведение агента или изоляцию секретов.',
              'Рекомендация — предварительный отбор, не доказательство безопасности и не разрешение внедрять.', '']
    (output / 'REPORT_RU.md').write_text('\n'.join(lines), encoding='utf-8')
    return result


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='cmd', required=True)
    q = sub.add_parser('prepare')
    q.add_argument('--root', type=Path, required=True); q.add_argument('--head', required=True)
    q.add_argument('--model', required=True); q.add_argument('--host', required=True)
    q.add_argument('--trials', type=int, default=3); q.add_argument('--seed', type=int, default=20261019)
    for cmd in ('smoke', 'scan', 'provider-plan', 'provider-smoke', 'assess', 'report'):
        q = sub.add_parser(cmd); q.add_argument('--root', type=Path, required=True)
        if cmd in ('smoke', 'scan', 'provider-plan', 'provider-smoke'): q.add_argument('--run', required=True)
        if cmd.startswith('provider-'):
            q.add_argument('--binary', required=True); q.add_argument('--project', required=True)
        if cmd == 'provider-smoke': q.add_argument('--consent-synthetic', action='store_true')
        if cmd == 'scan': q.add_argument('--path', action='append', required=True)
        if cmd == 'report': q.add_argument('--output', type=Path, required=True)
    a = p.parse_args(argv)
    try:
        if a.cmd == 'prepare': result = prepare(a.root, head=a.head, model=a.model, host=a.host, trials=a.trials, seed=a.seed)
        elif a.cmd == 'smoke': result = smoke(a.root, a.run)
        elif a.cmd == 'scan': result = scan(a.root, a.run, a.path)
        elif a.cmd == 'provider-plan': result = provider_plan(a.root, a.run, a.binary, a.project)
        elif a.cmd == 'provider-smoke': result = provider_smoke(a.root, a.run, a.binary, a.project, a.consent_synthetic)
        elif a.cmd == 'assess': result = assess(a.root)
        else: result = report(a.root, a.output)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1 if result.get('status') in ('FAIL', 'EXPOSURE_FOUND') else 0
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as exc:
        # Never echo provider output or arbitrary JSON content in a public report.
        print(json.dumps({'status': 'BLOCKED', 'error_type': type(exc).__name__}), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
