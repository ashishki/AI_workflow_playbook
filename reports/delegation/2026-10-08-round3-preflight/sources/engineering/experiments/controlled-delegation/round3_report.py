"""Publish honest first-attempt results and frozen-source/output hash receipts."""
from __future__ import annotations
import argparse
import datetime
from copy import deepcopy
import json
from pathlib import Path
import statistics
from round3 import HERE, REPO, verify_preregistration
from round3_checks import guard, inventory, read, sha, task_status, write


def summarize(runs):
    buckets = {c: [r for r in runs if r['condition'] == c] for c in 'ABC'}
    def complete(c):
        return len(buckets[c]) == 2 and all(r.get('usage_complete') is True for r in buckets[c])
    medians = {c: statistics.median(r['implementation_wall_seconds'] for r in v)
               if len(v) == 2 and all(type(r.get('implementation_wall_seconds')) in (int, float) for r in v)
               else None for c, v in buckets.items()}
    totals = {c: {k: sum(r[k] for r in v) if complete(c) and all(type(r.get(k)) is int for r in v) else None
                 for k in ('input_tokens', 'cached_input_tokens', 'uncached_input_tokens', 'output_tokens')}
              for c, v in buckets.items()}
    def ratio(a, b):
        return a / b if a is not None and b is not None and b > 0 else None
    paired = []
    for repeat in (1, 2):
        row = {'repeat': repeat}
        for condition in 'ABC':
            run = next((r for r in buckets[condition] if r['repeat'] == repeat), {})
            row[condition] = {k: run.get(k) for k in ('task_status', 'protocol_status', 'score',
                    'implementation_wall_seconds', 'wall_seconds', 'input_tokens',
                    'cached_input_tokens', 'uncached_input_tokens', 'output_tokens', 'usage_complete')}
        row['c_b_wall'] = ratio(row['C']['implementation_wall_seconds'], row['B']['implementation_wall_seconds'])
        paired.append(row)
    wall_ratio = ratio(medians['C'], medians['B'])
    token_ratios = {k: ratio(totals['C'][k], totals['B'][k]) for k in totals['B']}
    comparability = (len(buckets['B']) == len(buckets['C']) == 2
        and all(r.get('task_status') == r.get('protocol_status') == 'PASS'
                and len(r.get('phases', [])) == 1 and not r['phases'][0].get('timeout')
                for r in buckets['B'] + buckets['C']))
    quality = all(row['B']['score'] is not None and row['C']['score'] is not None
                  and row['C']['score'] >= row['B']['score'] for row in paired)
    known = wall_ratio is not None and all(token_ratios[k] is not None for k in ('uncached_input_tokens', 'output_tokens'))
    potential = comparability and quality and known and wall_ratio <= .80 and all(
        token_ratios[k] <= 2.0 for k in ('uncached_input_tokens', 'output_tokens'))
    return {'median_implementation_wall_seconds': medians, 'token_totals': totals,
        'usage_complete': {c: complete(c) for c in 'ABC'}, 'c_b_wall': wall_ratio,
        'c_b_token_ratios': token_ratios, 'paired_outcomes': paired,
        'successful_pair_comparable': comparability,
        'wall_ratio_interpretation': 'success comparison' if comparability else 'descriptive only; capped/failing runs are not speedup',
        'scenario_signal': 'POTENTIAL_BENEFIT_THIS_SCENARIO' if potential else 'NO_SHOWN_BENEFIT_OR_MIXED' if known else 'BLOCKED_INCOMPLETE_MEASUREMENTS'}


def sanitize(value, root):
    if isinstance(value, dict):
        return {k: sanitize(v, root) for k, v in value.items() if k != 'messages'}
    if isinstance(value, list): return [sanitize(v, root) for v in value]
    if isinstance(value, str):
        return value.replace(str(root), '<LOCAL_RUN_ROOT>').replace(str(REPO), '<REPO>').replace(str(Path.home()), '<HOME>')
    return value


def create_review_snapshot(root, report_directory):
    """Freeze real source + six run receipts/outputs + pre-review report hashes."""
    root = Path(root).resolve(); report_directory = Path(report_directory).resolve()
    verify_preregistration(root)
    destination = root / 'common-review/snapshot.json'
    if destination.exists(): raise ValueError('refuse to overwrite independent review snapshot')
    entries = []
    def add(path, kind, run_id=None):
        if not path.is_file() or path.is_symlink(): raise ValueError('review snapshot source missing or unsafe')
        item = {'path': str(path), 'sha256': sha(path), 'kind': kind}
        if run_id: item['run_id'] = run_id
        entries.append(item)
    for name in read(root / 'source-sha256.json'): add(REPO / name, 'source')
    for item in read(root / 'run-plan.json')['order']:
        result_path = root / 'results' / (item['id'] + '.json')
        add(result_path, 'run_receipt', item['id'])
        result = read(result_path); workspace = root / item['workspace']
        if inventory(workspace) != result.get('final_files_sha256'):
            raise ValueError('run outputs changed before independent review snapshot')
        for name in sorted(result['final_files_sha256']):
            if name.startswith(('.git/', '.agents/')): continue
            add(workspace / name, 'output', item['id'])
    for name in ('REPORT_RU.md', 'results.json', 'evidence-index.json'):
        add(report_directory / name, 'report')
    write(destination, {'schema': 'playbook.delegation.round3.review-snapshot.v1', 'entries': entries})
    return {'snapshot_path': 'common-review/snapshot.json', 'reviewed_snapshot_sha256': sha(destination),
            'entries': len(entries), 'status': 'FROZEN_FOR_REVIEW'}


def common_review(root, runs):
    """Validate separate reviewer receipt against a non-circular frozen snapshot."""
    receipt_path = root / 'common-review/receipt.json'
    if not receipt_path.is_file() or receipt_path.is_symlink():
        return {'status': 'BLOCKED', 'reason': 'independent common source/output/report review not yet observed'}
    receipt = read(receipt_path)
    reasons = []
    if (receipt.get('status') != 'validated' or receipt.get('actual_provider') is not True
            or receipt.get('scope') != 'common_source_output_report'):
        reasons.append('actual independent common review not confirmed')
    if len(runs) != 6 or any(r.get('execution_status') == 'NOT_RUN' or not r.get('phases') for r in runs):
        reasons.append('review is not after all six recorded attempts')
    snapshot_path = root / receipt.get('snapshot_path', 'common-review/snapshot.json')
    def safe(path):
        absolute = path.absolute()
        return (path.is_file() and not path.is_symlink() and path.resolve() == absolute
                and any(anchor == absolute or anchor in absolute.parents for anchor in (root, REPO)))
    if not safe(snapshot_path) or sha(snapshot_path) != receipt.get('reviewed_snapshot_sha256'):
        reasons.append('review snapshot hash missing or mismatched')
        snapshot = {}
    else:
        snapshot = read(snapshot_path)
        entries = snapshot.get('entries', [])
        if not entries: reasons.append('review snapshot has no source/output/report evidence')
        for entry in entries:
            source = Path(entry.get('path', ''))
            if not source.is_absolute(): source = root / source
            if not safe(source) or sha(source) != entry.get('sha256'):
                reasons.append('review snapshot entry missing or changed')
        expected_ids = {r['id'] for r in runs}
        for kind in ('run_receipt', 'output'):
            if {e.get('run_id') for e in entries if e.get('kind') == kind} != expected_ids:
                reasons.append('review snapshot does not cover six run ' + kind + ' sets')
        kinds = {entry.get('kind') for entry in entries}
        if not {'source', 'run_receipt', 'output', 'report'} <= kinds:
            reasons.append('review snapshot does not bind source/receipts/outputs/report')
    artifacts = receipt.get('artifacts', [])
    if not {'provider_trace', 'report'} <= {a.get('kind') for a in artifacts}:
        reasons.append('actual reviewer trace/report hashes absent')
    for artifact in artifacts:
        source = Path(artifact.get('path', ''))
        if not source.is_absolute(): source = root / source
        if not safe(source) or sha(source) != artifact.get('sha256'):
            reasons.append('reviewer artifact missing or changed')
    try:
        parse = lambda value: datetime.datetime.fromisoformat(value.replace('Z', '+00:00'))
        began = parse(receipt['review_started_utc']); finished = parse(receipt['review_finished_utc'])
        endings = [parse(r['phases'][0]['started_utc']) + datetime.timedelta(seconds=r['phases'][0]['wall_seconds']) for r in runs]
        if began < max(endings) or finished < began: reasons.append('review timestamps do not follow batch')
    except (KeyError, ValueError, TypeError):
        reasons.append('review timing evidence incomplete')
    return {**receipt, 'status': 'BLOCKED' if reasons else 'validated',
            'binding_verified': not reasons, 'binding_findings': sorted(set(reasons))}


def publish(root, output):
    root = Path(root).resolve(); output = Path(output).resolve()
    verify_preregistration(root)
    if output.exists() and any(output.iterdir()):
        raise ValueError('refuse to overwrite published evidence; use a fresh output destination')
    output.mkdir(parents=True, exist_ok=True)
    plan = read(root / 'run-plan.json'); receipts = []; runs = []
    def emit(name, source=None, document=None):
        destination = output / name; destination.parent.mkdir(parents=True, exist_ok=True)
        if source is not None:
            if not source.is_file() or source.is_symlink(): raise ValueError('unsafe evidence source: ' + str(source))
            destination.write_bytes(source.read_bytes())
        else: write(destination, sanitize(document, root))
        entry = {'path': name, 'sha256': sha(destination)}
        if source is not None: entry['original_sha256'] = sha(source)
        receipts.append(entry)
    emit('run-plan.json', document=plan)
    emit('preregistration.json', source=root / 'preregistration.json')
    emit('source-sha256.json', source=root / 'source-sha256.json')
    for name, digest in read(root / 'source-sha256.json').items():
        source = REPO / name
        if source.is_symlink() or sha(source) != digest: raise ValueError('frozen source changed')
        emit('sources/' + name, source=source)
    for item in plan['order']:
        name = f'{item["case"]}-{item["condition"]}-{item["repeat"]}'
        path = root / 'results' / f'{item["id"]}.json'
        if not path.is_file():
            runs.append({**item, 'status': 'BLOCKED', 'task_status': 'BLOCKED', 'protocol_status': 'BLOCKED',
                         'execution_status': 'NOT_RUN', 'reason': 'run not observed', 'score': None, 'cost_usd': None, 'human_minutes': None})
            continue
        run = deepcopy(read(path)); workspace = root / item['workspace']
        initial_path = root / 'initial' / f'{item["id"]}.json'
        integrity = guard(workspace, read(initial_path), item['case'])
        final_match = run.get('final_files_sha256') == inventory(workspace)
        if integrity['status'] != 'PASS' or not final_match:
            run['publication_integrity'] = integrity
            run['task_status'] = run['status'] = 'FAIL'
        else: run['publication_integrity'] = integrity
        # Preserve source receipt; never silently trust an absent completion.
        phases = run.get('phases', [])
        host_path = root / 'logs' / item['id'] / 'main.receipt.json'
        checks_path = root / 'logs' / item['id'] / 'first-checks.json'
        host = read(host_path) if host_path.is_file() and not host_path.is_symlink() else {}
        checked = read(checks_path) if checks_path.is_file() and not checks_path.is_symlink() else {}
        receipts_match = len(phases) == 1 and host == phases[0] and checked == run.get('mechanical')
        run['collector_task_status'] = run.get('task_status')
        run['receipts_verified'] = receipts_match
        run['task_status'] = 'FAIL' if integrity['status'] == 'FAIL' or not final_match else task_status(checked, host if receipts_match else {})
        if not receipts_match:
            run['protocol_status'] = 'BLOCKED' if run.get('protocol_status') != 'FAIL' else 'FAIL'
            run['usage_complete'] = False
            run['uncached_input_tokens'] = None
        emit(f'evidence/{name}.json', document=run)
        receipts[-1]['original_sha256'] = sha(path)
        emit(f'evidence/{name}-initial.json', source=initial_path)
        for filename in ('main.receipt.json', 'first-checks.json'):
            src = root / 'logs' / item['id'] / filename
            if src.is_file(): emit(f'evidence/{name}-{filename}', document=read(src))
        run['synthetic_outputs'] = []
        # Every initial source/test/input plus explicit mutable outputs is copied.
        # Refuse unsafe links before copying source, independently of scoring.
        for filename in sorted(set(read(initial_path)) | {'STATE.md', 'diagnosis.json'}):
            if filename.startswith(('.git/', '.agents/')): continue
            source = workspace / filename
            if source.is_symlink() or any(p.is_symlink() for p in source.parents if p != workspace and workspace in p.parents):
                raise ValueError('symlink output source: ' + filename)
            if source.is_file():
                emit(f'outputs/{name}/{filename}', source=source)
                run['synthetic_outputs'].append(receipts[-1].copy())
        runs.append(sanitize(run, root))
    comparisons = summarize(runs)
    # A separate actual after-batch reviewer may append its own artifact. Its
    # verdict is neither a per-run code review nor a timed performance phase.
    common = root / 'common-review' / 'receipt.json'
    review = common_review(root, runs)
    if common.is_file():
        emit('common-review/receipt.json', document=review)
        receipts[-1]['original_sha256'] = sha(common)
        snapshot_path = root / review.get('snapshot_path', 'common-review/snapshot.json')
        if snapshot_path.is_file() and not snapshot_path.is_symlink():
            emit('common-review/snapshot.json', document=read(snapshot_path))
            receipts[-1]['original_sha256'] = sha(snapshot_path)
        for index, artifact in enumerate(review.get('artifacts', [])):
            source = Path(artifact.get('path', ''))
            if not source.is_absolute(): source = root / source
            if artifact.get('kind') == 'report' and source.is_file() and not source.is_symlink():
                emit(f'common-review/reviewer-{index}.json', document={'text': source.read_text(), 'original_sha256': sha(source)})
    task_batch = 'FAIL' if any(r['task_status'] == 'FAIL' or r['protocol_status'] == 'FAIL' for r in runs) else 'PASS' if len(runs) == 6 and all(r['task_status'] == r['protocol_status'] == 'PASS' for r in runs) else 'BLOCKED'
    results = {'schema': 'playbook.delegation.round3.report.v1', 'experiment': sanitize(plan, root),
        'runs': runs, 'comparisons': comparisons, 'task_batch_status': task_batch,
        'qualification_status': 'BLOCKED', 'production_enable': False,
        'execution_context': plan.get('execution_context'),
        'environment_blocker': 'explicit owner root exception pending' if plan.get('execution_context', {}).get('authorization') == 'PENDING_ROOT_EXCEPTION' else None,
        'measurement_status': {'cost_usd': 'NOT_MEASURED', 'human_minutes': 'NOT_MEASURED'},
        'common_independent_review': sanitize(review, root),
        'limits': ['n=2 repeats of one synthetic debugging repository; not statistical evidence',
            'C forces delegation on selected independently diagnosable subsystems; automatic routing policy not tested',
            'worker read-only scope is instructed/observed with inherited sandbox; no OS read-only proof',
            'no repair and no per-run model review; incomplete/timeouts preserved',
            'USD/human minutes null; no production enable']}
    emit('results.json', document=results)
    lines = ['# Controlled Delegation — третий раунд', '',
        f'Наблюдённый batch: **{task_batch}**. Полная qualification: **BLOCKED**. '
        f'Сигнал сценария: **{comparisons["scenario_signal"]}**. Production enable: нет.', '',
        'Одна средняя синтетическая debugging-задача, три независимо исследуемые подсистемы; '
        'A/B/C × 2, шесть последовательных первых попыток. Repair отсутствует. '
        'Модель gpt-6.1-sol/high, одинаковые runtime flags, main 600 секунд с host deadline. '
        'Worker 180 секунд — scoped instruction и фактическая postcheck длительность, без OS read-only гарантий. '
        'A выбирает обычный host behavior с возможными native workers, B — Playbook/один агент, '
        'C — Playbook/обязательные 2–3 native workers и main sole writer.', '',
        '| Повтор | A task/protocol | B task/protocol | C task/protocol | C/B wall |',
        '|---|---|---|---|---|']
    metadata = next(iter(plan.get('task_metadata', {}).values()), {})
    lines.insert(5, 'Фактический размер fixture: ' + str(metadata.get('file_count', 'null')) +
        ' файлов, ' + str(metadata.get('source_file_count', 'null')) + ' source files, ' +
        str(metadata.get('source_line_count', 'null')) + ' source lines. Это connected synthetic repo, не production complexity.')
    lines.insert(6, '')
    def number(value): return 'null' if value is None else f'{value:.3f}'
    for row in comparisons['paired_outcomes']:
        states = [f'{row[c]["task_status"]}/{row[c]["protocol_status"]}' for c in 'ABC']
        lines.append(f'| {row["repeat"]} | ' + ' | '.join(states) + f' | {number(row["c_b_wall"])} |')
    lines += ['', f'Медиана wall C/B: {number(comparisons["c_b_wall"])}. '
        f'Uncached-input C/B: {number(comparisons["c_b_token_ratios"]["uncached_input_tokens"])}; '
        f'output C/B: {number(comparisons["c_b_token_ratios"]["output_tokens"])}. '
        f'Интерпретация: {comparisons["wall_ratio_interpretation"]}.', '',
        'Заранее заданный сигнал потенциальной пользы требует обе C task/protocol PASS, '
        'качество не хуже B в каждом повторе, median C/B wall ≤0.80 и полные uncached-input/output '
        'ratios каждый ≤2.0. Capped/failed runs не считаются ускорением. '
        'Два повтора одного synthetic case не дают статистического вывода.', '',
        'USD и активные человеко-минуты остаются null: actual billing/participation receipts отсутствуют. '
        'Наблюдаемые provider counters main/реальных children раскрыты отдельно; неполные totals не дают полного token ratio.', '',
        f'Отдельный общий source/output/report review после batch: {review.get("status", "BLOCKED")}. '
        'Это не per-run model review и не часть timed task outcome. Предыдущие два раунда сохранены.', '',
        'Sources, outputs и sanitized receipts: [results.json](results.json), '
        '[evidence-index.json](evidence-index.json). Raw provider chats остаются локально.']
    (output / 'REPORT_RU.md').write_text('\n'.join(lines) + '\n')
    receipts.append({'path': 'REPORT_RU.md', 'sha256': sha(output / 'REPORT_RU.md')})
    write(output / 'evidence-index.json', {'schema': 'playbook.delegation.round3.evidence.v1', 'receipts': receipts})
    return {'status': task_batch, 'qualification_status': 'BLOCKED', 'report': str(output / 'REPORT_RU.md'), 'runs': len(runs)}


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--root', type=Path, required=True); p.add_argument('--output', type=Path, required=True)
    p.add_argument('--snapshot-for-review', action='store_true')
    args = p.parse_args(); print(json.dumps(create_review_snapshot(args.root, args.output) if args.snapshot_for_review else publish(args.root, args.output), ensure_ascii=False, indent=2))
