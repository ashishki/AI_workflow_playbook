#!/usr/bin/env python3
"""Round 3: six real, sequential debugging runs; no repair/model-review phase."""
from __future__ import annotations
import argparse
import datetime
import os
import json
from pathlib import Path
import random
import shutil
import subprocess
import time
import uuid
import round2
from round2_host import execute, setup_bin, events
from round3_checks import guard, inventory, read, score, sha, task_status, write
from round3_fixtures import cases

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
EXPERIMENT = 'controlled-delegation-round3-2026-10-08'
MAIN_SECONDS = 600
WORKER_SECONDS = 180
COMMON = '''Read AGENTS.md and TASK.md and diagnose/fix all three defects. Work only in this isolated workspace. No parent/sibling/session reads, evaluator access, network, accounts, dependencies, commit/push. Use local python with -B. Modify only existing src/**/*.py, diagnosis.json and STATE.md. All tests, input data, TASK/AGENTS, skills and other files are frozen; do not add source/helper/cache files. First attempt only: no operator feedback, repair phase or reviewers. Main has 600 seconds including its own checks. Operator executes the same frozen behavioral+diagnosis rubric after each run. No model reviewer occurs inside or after an individual run. After all six runs a separate operator independent source/output/report review is recorded outside task outcomes. Write diagnosis.json exactly as TASK specifies and short STATE.md headings Rules, Verification, Limits, Next step; record actual checks and limits. Main is sole writer. If native workers are allowed, start 2-3 distinct native analysis workers for inventory, checkout and refunds (two may combine scopes). Each spawn message MUST contain [R3_READ_ONLY], its named subsystem(s), '180 seconds', and prohibit writes, nested delegation, network and reviewer work; use fork_turns="none" with inherited model/reasoning (no overrides). Workers read sources/tests/data and return concise root cause, concrete patch recommendation and tests, without writing files. Each has 180 seconds within main budget, depth=1,max parallel=3. Monitor deadline, interrupt overdue/missing workers and finish from sources; do not reuse completed workers or send followups. Native child sandbox is inherited workspace-write; read-only is an instruction whose observable compliance is checked, not OS-enforced isolation. Finish once requested outputs/checks are complete.'''
CONDITIONS = {
    'A': 'Ordinary Codex baseline. No Playbook skills. Choose ordinary host behavior; native workers are optional under the common scope/budget constraints.',
    'B': 'Read .agents/skills/playbook/SKILL.md and relevant Playbook task/delegation references. Use Playbook; one implementation agent, no native workers or reviewers.',
    'C': 'Read .agents/skills/playbook/SKILL.md and relevant Playbook delegation reference. Use Playbook and 2-3 real native read-only workers for independent inventory/checkout/refund diagnosis. Main alone integrates and writes. No reviewers.'}


def source_manifest():
    paths = [*HERE.glob('round3*.py'), HERE / 'ROUND3_PROTOCOL_RU.md',
             *HERE.glob('round2*.py'),
             *(REPO / 'plugins/playbook-native/skills').rglob('*'),
             *(REPO / 'tests/vnext').glob('test_controlled_delegation_round3*.py')]
    paths = [p for p in paths if p.is_file()]
    return {p.relative_to(REPO).as_posix(): sha(p) for p in sorted(paths)}


def prepare(root, head, model='gpt-6.1-sol', reasoning='high', repeats=2, seed=20261008, root_exception_authorized=False):
    if (model, reasoning, repeats) != ('gpt-6.1-sol', 'high', 2):
        raise ValueError('preregistered experiment fixes model/reasoning/repeats')
    root = Path(root).resolve()
    if root.exists() and any(root.iterdir()):
        raise ValueError('refuse to overwrite experiment')
    root.mkdir(parents=True, exist_ok=True)
    plan = {'schema': 'playbook.delegation.round3.plan.v1', 'experiment_id': EXPERIMENT,
            'head': head, 'model': model, 'reasoning': reasoning, 'repeats': repeats, 'seed': seed,
            'execution_context': {'uid': os.getuid(), 'user': os.environ.get('USER'), 'hostname': os.uname().nodename, 'authorization': 'EXPLICIT_ROOT_EXCEPTION' if os.getuid() == 0 and root_exception_authorized else 'PENDING_ROOT_EXCEPTION' if os.getuid() == 0 else 'AUTHORIZED_TASK_NONROOT'},
            'main_seconds': MAIN_SECONDS, 'worker_seconds': WORKER_SECONDS, 'repair_policy': 'NONE',
            'review_policy': 'one independent common source/output/report review AFTER six runs; outside task outcomes',
            'cost_policy': 'actual counters only; USD/human minutes null without actual receipts',
            'worker_read_only_policy': 'scoped instruction and observable postcheck; inherited sandbox, no OS read-only proof',
            'rubric': {name: spec['groups'] for name, spec in cases().items()},
            'task_metadata': {name: spec.get('metadata', {}) for name, spec in cases().items()}, 'order': []}
    if len(cases()) != 1:
        raise ValueError('round3 requires exactly one larger task')
    name, spec = next(iter(cases().items()))
    rng = random.Random(seed)
    for repeat in (1, 2):
        order = list('ABC'); rng.shuffle(order)
        for condition in order:
            run_id = uuid.uuid4().hex[:12]
            workspace = root / 'workspaces' / run_id; workspace.mkdir(parents=True)
            for filename, content in spec['files'].items():
                p = workspace / filename; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(content)
            if condition in 'BC':
                shutil.copytree(REPO / 'plugins/playbook-native/skills', workspace / '.agents/skills')
            (workspace / 'AGENTS.md').write_text('# Isolated round-3 workspace\n\n' + CONDITIONS[condition] + '\n\n' + COMMON + '\n')
            (workspace / 'TASK.md').write_text(spec['task'])
            subprocess.run(['git', 'init', '-q', '-b', 'benchmark-round3', str(workspace)], check=True)
            write(root / 'initial' / f'{run_id}.json', inventory(workspace))
            plan['order'].append({'id': run_id, 'case': name, 'repeat': repeat,
                                  'condition': condition, 'workspace': workspace.relative_to(root).as_posix()})
    write(root / 'run-plan.json', plan)
    write(root / 'source-sha256.json', source_manifest())
    write(root / 'preregistration.json', {'plan_sha256': sha(root / 'run-plan.json'),
           'source_manifest_sha256': sha(root / 'source-sha256.json'),
           'initial_sha256': {p.name: sha(p) for p in sorted((root / 'initial').glob('*.json'))}})
    return {'status': 'PREPARED', 'runs': 6, 'root': str(root)}


def verify_preregistration(root):
    frozen = read(root / 'preregistration.json')
    if sha(root / 'run-plan.json') != frozen['plan_sha256'] or sha(root / 'source-sha256.json') != frozen['source_manifest_sha256']:
        raise ValueError('preregistration changed')
    for name, digest in read(root / 'source-sha256.json').items():
        if sha(REPO / name) != digest:
            raise ValueError('source changed after preregistration: ' + name)
    for name, digest in frozen['initial_sha256'].items():
        if sha(root / 'initial' / name) != digest:
            raise ValueError('initial manifest changed: ' + name)


def function_calls(path):
    if not Path(path).is_file():
        return []
    return [e.get('payload', {}) for e in events(path)
            if e.get('type') == 'response_item' and e.get('payload', {}).get('type') in ('function_call', 'custom_tool_call')]


def observed_telemetry(root, workspace, phase, wrapper):
    # Persistent provider thread counters, including actual native children.
    data = round2.telemetry(root, workspace, [phase], [], wrapper)
    sessions = data['host_sessions']; ids = phase.get('thread_ids', [])
    complete = data['usage_complete'] and bool(ids) and len(set(ids)) == len(ids)
    for entry in sessions:
        usage = entry.get('usage') or {}
        if (not usage or any(type(usage.get(k)) is not int or usage[k] < 0
                            for k in ('input_tokens', 'cached_input_tokens', 'output_tokens'))
                or usage.get('cached_input_tokens', 0) > usage.get('input_tokens', 0)):
            complete = False
    data['usage_complete'] = complete
    data['uncached_input_tokens'] = data['input_tokens'] - data['cached_input_tokens'] if complete else None
    worker_calls = []; spawn_calls = []
    for entry in sessions:
        calls = function_calls(entry['raw_file'])
        if isinstance(entry.get('source'), dict):
            worker_calls.append({'thread_id': entry['id'], 'tools': [c.get('name') for c in calls],
                'known_write_tool_observed': any(c.get('name', '').split('.')[-1] in
                    ('apply_patch', 'write_file', 'create_file', 'edit_file') for c in calls),
                'sandbox_policy': (entry.get('context') or {}).get('sandbox_policy')})
        else:
            for call in calls:
                if call.get('name', '').split('.')[-1] != 'spawn_agent': continue
                try: args = json.loads(call.get('arguments', '{}'))
                except ValueError: args = {}
                message = args.get('message', '')
                spawn_calls.append({'call_id': call.get('call_id'), 'task_name': args.get('task_name'),
                    'scope_instruction_present': '[R3_READ_ONLY]' in message and '180 seconds' in message
                        and any(s in message.lower() for s in ('inventory', 'checkout', 'refund')),
                    'model_override_present': bool(args.get('model') or args.get('reasoning_effort')),
                    'fork_turns': args.get('fork_turns'), 'message': message})
    data['native_spawn_receipts'] = spawn_calls; data['worker_tool_observations'] = worker_calls
    data['read_only_os_enforced'] = False
    for child in data['worker_observed_durations']:
        child['over_180_seconds'] = any(v is not None and v > WORKER_SECONDS for v in child['interval_seconds'])
        child.pop('over_60_seconds', None)
        if not child['interval_seconds'] or any(v is None for v in child['interval_seconds']):
            data['usage_complete'] = False
    if not data['usage_complete']: data['uncached_input_tokens'] = None
    return data


def protocol_check(condition, phase, data):
    failures = []; blockers = []
    if not data.get('settings_verified'): blockers.append('model/reasoning settings unverified')
    if not data.get('usage_complete'): blockers.append('provider counters/receipt incomplete')
    if phase.get('timeout') or not phase.get('completed'): blockers.append('main host incomplete or timed out')
    if data.get('max_parallel', 0) > 3 or data.get('max_depth', 0) > 1: failures.append('worker concurrency/depth limit')
    if data.get('completed_worker_reuse'): failures.append('worker reused')
    if condition == 'B' and data.get('workers'): failures.append('B single-agent condition delegated')
    if condition == 'C':
        if not 2 <= data.get('workers', 0) <= 3: failures.append('C requires 2-3 genuine native workers')
    if data.get('workers'):
        receipts = data.get('native_spawn_receipts', [])
        if len(receipts) != data.get('workers'): blockers.append('native spawn receipt incomplete')
        for receipt in receipts:
            if not receipt['scope_instruction_present'] or receipt['model_override_present'] or receipt['fork_turns'] != 'none':
                failures.append('worker scope/budget/inheritance instruction violated')
    for child in data.get('worker_observed_durations', []):
        if child.get('over_180_seconds'): failures.append('worker exceeded observed 180-second bound: ' + child['thread_id'])
        if not child.get('interval_seconds') or any(x is None for x in child['interval_seconds']):
            blockers.append('worker observed deadline unavailable: ' + child['thread_id'])
    if any(x['known_write_tool_observed'] for x in data.get('worker_tool_observations', [])):
        failures.append('read-only worker used known write tool')
    return {'status': 'FAIL' if failures else 'BLOCKED' if blockers else 'PASS', 'failures': failures, 'blockers': blockers}


def run(root):
    root = Path(root).resolve(); verify_preregistration(root)
    plan = read(root / 'run-plan.json')
    context = plan['execution_context']
    if os.getuid() != context['uid']:
        raise ValueError('execution uid differs from preregistered environment')
    if os.getuid() == 0 and context['authorization'] != 'EXPLICIT_ROOT_EXCEPTION':
        raise ValueError('model calls blocked: explicit owner root exception is pending')
    wrapper = setup_bin(root, plan['model'], plan['reasoning'])
    for index, item in enumerate(plan['order'], 1):
        output = root / 'results' / f'{item["id"]}.json'
        if output.exists(): continue
        workspace = root / item['workspace']; logs = root / 'logs' / item['id']
        if logs.exists(): raise ValueError('recorded partial attempt needs explicit recovery; never overwrite')
        initial = read(root / 'initial' / f'{item["id"]}.json')
        if inventory(workspace) != initial: raise ValueError('workspace changed before first attempt')
        begin = time.monotonic()
        print(f'START {index}/6 {item["condition"]} repeat={item["repeat"]}', flush=True)
        phase = execute(workspace, logs, 'main', wrapper, COMMON, MAIN_SECONDS)
        checks = score(item['case'], workspace, initial); write(logs / 'first-checks.json', checks)
        data = observed_telemetry(root, workspace, phase, wrapper)
        protocol = protocol_check(item['condition'], phase, data)
        outcome = task_status(checks, phase)
        result = {**item, **data, 'schema': 'playbook.delegation.round3.run.v1',
            'task_status': outcome, 'first_attempt_status': outcome, 'protocol_status': protocol['status'],
            'protocol': protocol, 'status': 'FAIL' if 'FAIL' in (outcome, protocol['status']) else
                'PASS' if outcome == protocol['status'] == 'PASS' else 'BLOCKED',
            'score': checks.get('score'), 'mechanical': checks, 'phases': [phase], 'reviews': [],
            'execution_status': 'TIMEOUT' if phase.get('timeout') else 'COMPLETED' if phase.get('completed') else 'ERROR_OR_INCOMPLETE',
            'repair_count': 0, 'model_review_status': 'NOT_RUN_PER_PROTOCOL',
            'implementation_wall_seconds': phase['wall_seconds'],
            'wall_seconds': round(time.monotonic() - begin, 3), 'cost_usd': None,
            'human_minutes': None, 'owner_requests': None, 'qualification_status': 'BLOCKED',
            'measurement_blockers': ['USD billing not exposed', 'active human minutes not measured'],
            'final_files_sha256': inventory(workspace)}
        write(output, result)
        print(f'END task={outcome} protocol={protocol["status"]} score={checks.get("score")}', flush=True)
    return {'status': 'FINISHED', 'runs': len(plan['order'])}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); sub = parser.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('prepare'); p.add_argument('--root', type=Path, required=True); p.add_argument('--head', required=True)
    p.add_argument('--root-exception-authorized', action='store_true', help='only after explicit owner authorization for root model calls')
    p.add_argument('--model', default='gpt-6.1-sol'); p.add_argument('--reasoning', default='high')
    p = sub.add_parser('run'); p.add_argument('--root', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.root, args.head, args.model, args.reasoning, root_exception_authorized=args.root_exception_authorized) if args.cmd == 'prepare' else run(args.root), ensure_ascii=False, indent=2))
