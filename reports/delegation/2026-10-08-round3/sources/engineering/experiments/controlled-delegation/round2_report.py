"""Publish observed round-2 results, preserving first attempts and unknown costs."""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import json
from pathlib import Path
import statistics

from round2_checks import read, sha, write, task_verification
from round2_host import worker_durations


def first_attempt(run, checks, review_engine_matches=None):
    """The collector's old first_attempt_status only described mechanical checks."""
    review = next(iter(run.get('reviews', [])), None)
    phases = run.get('phases', [])[:1]
    return {
        'task_status': task_verification(run['case'], checks, phases, review, review_engine_matches),
        'implementation_completed': bool(phases and phases[0].get('completed')),
        'mechanical_status': checks.get('status', 'NOT_RUN'),
        'mechanical_score': checks.get('score'),
        'review_status': review.get('status') if review else 'NOT_REQUIRED' if run['case'] != 'sales_import' else 'NOT_RUN',
        'review_verdict': review.get('verdict') if review else None,
        'repair_count': max(0, len(run.get('phases', [])) - 1),
    }


def summarize(runs):
    comparisons = []
    for name in ('sales_import', 'release_gate'):
        buckets = {c: [r for r in runs if r['case'] == name and r['condition'] == c
                       and r.get('wall_seconds') is not None] for c in 'ABC'}
        medians = {c: statistics.median(r['wall_seconds'] for r in values) if values else None
                   for c, values in buckets.items()}
        totals = {c: {key: sum(r.get(key, 0) for r in values)
                      for key in ('input_tokens', 'cached_input_tokens', 'output_tokens', 'uncached_input_tokens')}
                  for c, values in buckets.items()}
        def ratio(key):
            denominator = totals['B'][key]
            return totals['C'][key] / denominator if denominator else None
        pairs = []
        for repeat in (1, 2):
            pair = {'repeat': repeat}
            for c in 'ABC':
                found = next((r for r in buckets[c] if r['repeat'] == repeat), None)
                pair[c] = {key: found.get(key) for key in ('score', 'task_status', 'preregistered_task_verification', 'collector_task_status', 'protocol_status', 'wall_seconds')} if found else None
            pairs.append(pair)
        comparisons.append({'case': name, 'median_wall': medians, 'token_totals': totals,
                            'usage_complete': {c: len(values) == 2 and all(r.get('usage_complete') is True for r in values)
                                               for c, values in buckets.items()},
                            'c_b_wall': medians['C'] / medians['B'] if medians['C'] is not None and medians['B'] else None,
                            'token_ratio_status': 'COMPLETE' if len(buckets['B']) == len(buckets['C']) == 2 and all(r.get('usage_complete') is True for r in buckets['B'] + buckets['C']) else 'PARTIAL',
                            'c_b_input': ratio('input_tokens'), 'c_b_cached_input': ratio('cached_input_tokens'),
                            'c_b_uncached_input': ratio('uncached_input_tokens'), 'c_b_output': ratio('output_tokens'),
                            'paired_outcomes': pairs})
    return comparisons


def publish(root, output):
    root = Path(root).resolve()
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    plan = read(root / 'run-plan.json')
    runs, receipts = [], []
    audit_path = root / 'posthoc' / 'large_decimal' / 'result.json'
    audit = read(audit_path) if audit_path.is_file() else None
    audited = {entry['id']: entry for entry in audit.get('runs', [])} if audit else {}
    for item in plan['order']:
        path = root / 'results' / f'{item["id"]}.json'
        if not path.is_file():
            runs.append({**item, 'status': 'NOT_RUN', 'task_status': 'NOT_RUN',
                         'protocol_status': 'NOT_RUN', 'score': None, 'cost_usd': None, 'human_minutes': None})
            continue
        run = deepcopy(read(path))
        for thread in run.get('host_sessions', []):
            thread.pop('messages', None)
        name = f'evidence/{item["case"]}-{item["condition"]}-{item["repeat"]}.json'
        write(output / name, run)
        receipts.append({'path': name, 'sha256': sha(output / name), 'original_sha256': sha(path)})
        first_checks = root / 'logs' / item['id'] / 'first-checks.json'
        checks = read(first_checks) if first_checks.is_file() else {}
        first_name = f'evidence/{item["case"]}-{item["condition"]}-{item["repeat"]}-first-checks.json'
        write(output / first_name, checks)
        receipts.append({'path': first_name, 'sha256': sha(output / first_name)})
        first_review = run.get('reviews', [None])[0] if run.get('reviews') else None
        first_bound = None
        if first_review and first_review.get('workspace'):
            snapshot = Path(first_review['workspace']).resolve()
            first_engine = snapshot / 'engine.py'
            if (root / 'review-workspaces') in snapshot.parents and first_engine.is_file() and not first_engine.is_symlink():
                first_bound = sha(first_engine) == first_review.get('reviewed_engine_sha256')
        run['first_attempt'] = first_attempt(run, checks, first_bound)
        run['collector_task_status'] = run['task_status']
        latest_review = run.get('reviews', [])[-1] if run.get('reviews') else None
        engine = root / item['workspace'] / 'engine.py'
        if run['case'] == 'sales_import':
            run['review_engine_matches'] = bool(latest_review and engine.is_file()
                and latest_review.get('reviewed_engine_sha256') == sha(engine))
        run['task_status'] = task_verification(run['case'], run.get('mechanical', {}), run.get('phases', []), latest_review, run.get('review_engine_matches'))
        run['preregistered_task_verification'] = run['task_status']
        run['posthoc_contract_check'] = audited.get(item['id'])
        if run['posthoc_contract_check'] and run['posthoc_contract_check']['status'] == 'FAIL':
            run['task_status'] = 'FAIL'
        run['synthetic_outputs'] = []
        for filename in ('engine.py', 'decision.json', 'STATE.md', 'BRIEF.md'):
            source = root / item['workspace'] / filename
            if source.is_file() and not source.is_symlink():
                target = output / 'outputs' / f'{item["case"]}-{item["condition"]}-{item["repeat"]}' / filename
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(source.read_bytes())
                saved = {'path': target.relative_to(output).as_posix(), 'sha256': sha(target)}
                run['synthetic_outputs'].append(saved)
                receipts.append(saved)
        first_review = run.get('reviews', [None])[0] if run.get('reviews') else None
        if first_review and first_review.get('workspace'):
            snapshot = Path(first_review['workspace']).resolve()
            if (root / 'review-workspaces') in snapshot.parents:
                for filename in ('engine.py', 'STATE.md'):
                    source = snapshot / filename
                    if source.is_file() and not source.is_symlink():
                        if filename == 'engine.py' and sha(source) != first_review.get('reviewed_engine_sha256'):
                            raise ValueError('first reviewed engine snapshot changed')
                        target = output / 'outputs' / f'{item["case"]}-{item["condition"]}-{item["repeat"]}' / 'first-attempt' / filename
                        target.parent.mkdir(parents=True, exist_ok=True)
                        target.write_bytes(source.read_bytes())
                        saved = {'path': target.relative_to(output).as_posix(), 'sha256': sha(target)}
                        run['synthetic_outputs'].append(saved)
                        receipts.append(saved)
        run['worker_observed_durations'] = worker_durations(run)
        run['posthoc_protocol_findings'] = ['worker exceeded 60-second bound: ' + v['thread_id'] + ' (' + str(max(t for t in v['interval_seconds'] if t is not None)) + ' seconds)'
                                           for v in run['worker_observed_durations'] if v['over_60_seconds']]
        run['collector_protocol_status'] = run['protocol_status']
        if run['posthoc_protocol_findings']:
            run['protocol_status'] = 'FAIL'
        run['uncached_input_tokens'] = run['input_tokens'] - run['cached_input_tokens']
        runs.append(run)
    diagnostics = []
    for path in sorted((root / 'diagnostics').glob('*/result.json')):
        diagnostic = deepcopy(read(path))
        for thread in diagnostic.get('threads', []):
            thread.pop('messages', None)
        diagnostics.append(diagnostic)
        name = f'evidence/diagnostic-{diagnostic["kind"]}.json'
        write(output / name, diagnostic)
        receipts.append({'path': name, 'sha256': sha(output / name), 'original_sha256': sha(path)})
    if audit:
        write(output / 'evidence' / 'posthoc-large-decimal.json', audit)
        receipts.append({'path': 'evidence/posthoc-large-decimal.json',
                         'sha256': sha(output / 'evidence' / 'posthoc-large-decimal.json'),
                         'original_sha256': sha(audit_path)})
    decision = 'REVISE_OR_REJECT' if any(r['condition'] == 'C' and (
        r['task_status'] in ('FAIL', 'BLOCKED') or r['protocol_status'] == 'FAIL' or r.get('posthoc_protocol_findings'))
        for r in runs) else 'KEEP_EXPERIMENTAL'
    comparisons = summarize(runs)
    results = {
        'schema': 'playbook.delegation.round2.results.v1', 'experiment_id': plan['experiment_id'],
        'environment': {k: plan[k] for k in ('head', 'model', 'reasoning', 'seed', 'repeats')},
        'runs': runs, 'diagnostics': diagnostics, 'posthoc_contract_audit': audit, 'comparisons': comparisons, 'decision': decision,
        'qualification_status': 'BLOCKED',
        'measurement_status': {'cost_usd': 'NOT_RUN', 'active_human_minutes': 'NOT_RUN'},
        'qualification_note': 'Unknown USD and active human minutes remain blockers; task PASS cannot enable the capability.',
        'interpretation_note': 'Original receipts are preserved. task_status separates confirmed FAIL from missing-verification BLOCKED; collector_task_status and collector_protocol_status retain original labels. first_attempt includes first external review; Legacy collector first_attempt_status described mechanical checks only; its scope is retained in original receipts. Worker duration findings are disclosed post hoc, without changing original receipts.',
    }
    write(output / 'results.json', results)
    write(output / 'run-plan.json', plan)
    prepared_hashes = root / 'source-sha256.json'
    if prepared_hashes.is_file():
        write(output / 'prepared-source-sha256.json', read(prepared_hashes))
    write(output / 'evidence-index.json', {'raw_root': str(root), 'receipts': receipts,
                                         'publishing_source_sha256': sha(Path(__file__))})
    lines = ['# Что получилось во втором раунде', '',
             'Два одинаковых повтора A/B/C на двух задачах: импорт продаж в SQLite и решение о выпуске релиза. '
             'A — обычный Codex, B — Playbook в одной implementation session, C — Playbook с 2–3 настоящими помощниками. '
             'Модель `gpt-6.1-sol`, reasoning `high`; порядок, исходные файлы и шкала закреплены до запусков.', '',

             f'**Решение: {decision}. Полная квалификация: BLOCKED.** Фактические USD и активные человеко-минуты '
             'не измерены и остаются `null / NOT RUN`. Делегирование не становится режимом по умолчанию.', '',
             '## Результаты задач', '', '| Задача | A | B | C |', '|---|---|---|---|']
    for name in ('sales_import', 'release_gate'):
        cells = []
        for condition in 'ABC':
            values = [r for r in runs if r['case'] == name and r['condition'] == condition]
            counts = Counter(r['task_status'] for r in values)
            protocol_failures = sum(r['protocol_status'] == 'FAIL' or bool(r.get('posthoc_protocol_findings')) for r in values)
            cell = ', '.join(f'{n} {status}' for status, n in sorted(counts.items()))
            if protocol_failures:
                cell += f'; protocol FAIL: {protocol_failures}'
            cells.append(cell)
        lines.append(f'| {name} | ' + ' | '.join(cells) + ' |')
    complete_comparisons = all(all(c['median_wall'][mode] is not None for mode in 'ABC') for c in comparisons)
    if complete_comparisons:
        sales, release = comparisons
        comparable_outcomes = all(
            sum(r['task_status'] == 'PASS' for r in runs if r['case'] == case and r['condition'] == 'C')
            <= sum(r['task_status'] == 'PASS' for r in runs if r['case'] == case and r['condition'] == 'B')
            and max(r.get('score') or 0 for r in runs if r['case'] == case and r['condition'] == 'C')
            <= max(r.get('score') or 0 for r in runs if r['case'] == case and r['condition'] == 'B')
            for case in ('sales_import', 'release_gate'))
        if comparable_outcomes and sales['c_b_wall'] > 1 and release['c_b_wall'] > 1:
            lines.insert(4, 'На этих задачах добавочная польза делегирования не показана: медиана полного времени C выше B '
                + f'в {sales["c_b_wall"]:.2f} раза на импорте и в {release["c_b_wall"]:.2f} раза на решении о релизе. '
                + 'Эти времена включают разные результаты приёмки, поэтому они не доказывают ускорение успешной работы.')
            lines.insert(5, '')
    lines += ['', 'Task PASS требует score=100, STATE, завершённого host и пригодного независимого review изменённого приложения. '
              'BLOCKED означает недостающую проверку, включая отсутствующий/timeout QA, и не доказывает неправильность кода. Для текстового решения о релизе дополнительный review не требуется. Исходный collector label сохранён отдельно.', '',
              '## Время и токены', '',
              '| Задача | Median A, с | Median B, с | Median C, с | C/B wall | C/B uncached input | C/B output |',
              '|---|---:|---:|---:|---:|---:|---:|']
    for comparison in comparisons:
        fmt = lambda value: f'{value:.2f}' if value is not None else 'NOT RUN'
        ratios = [f'{comparison[key]:.2f}×' if comparison[key] is not None else '—'
                  for key in ('c_b_wall', 'c_b_uncached_input', 'c_b_output')]
        if comparison['token_ratio_status'] == 'PARTIAL':
            ratios[1:] = [value + ' partial' for value in ratios[1:]]
        lines.append('| ' + comparison['case'] + ' | ' + ' | '.join(
            [fmt(comparison['median_wall'][c]) for c in 'ABC'] + ratios) + ' |')
    lines += ['', 'Wall включает implementation, реальные проверки, review и repair. Меньше 1× — меньше времени/токенов C. '
              'Input включает cached; uncached=input−cached. Суммы ниже включают доступные counters main, отдельных native children, reviews и repairs. Неизвестные counters не считаются нулём. '
              'Partial counters — нижняя наблюдаемая граница, а не полный расход. Partial ratio не доказывает меньшего полного расхода C. Время неуспешного/непроверенного решения не доказывает ускорение успешной работы.', '',
              '| Задача / режим | Input | Cached input | Output | Counters |', '|---|---:|---:|---:|---|']
    for comparison in comparisons:
        for condition in 'ABC':
            totals = comparison['token_totals'][condition]
            state = 'complete' if comparison['usage_complete'][condition] else 'partial / incomplete'
            lines.append(f'| {comparison["case"]} / {condition} | {totals["input_tokens"]} | '
                         f'{totals["cached_input_tokens"]} | {totals["output_tokens"]} | {state} |')
    lines += ['', 'Токены не названы денежной стоимостью; API price estimate не заменяет billing receipt. '
              'Отсутствие обращений к владельцу не означает ноль активных человеко-минут. При двух повторах вывод ограничен этими задачами.', '',
              '## Первые попытки и исправления', '',
              '| Задача / режим / повтор | Первая приёмка | Первый score | Первый review | Исправления | Итог задачи |',
              '|---|---|---:|---|---:|---|']
    for run in runs:
        first = run.get('first_attempt', {})
        lines.append(f'| {run["case"]} / {run["condition"]} / {run["repeat"]} | '
                     f'{first.get("task_status", "NOT_RUN")} | {first.get("mechanical_score", "—")} | '
                     f'{first.get("review_verdict") or first.get("review_status", "NOT_RUN")} | '
                     f'{first.get("repair_count", 0)} | {run["task_status"]} |')
    if audit:
        lines += ['', '## Одинаковая дополнительная проверка', '',
                  'После основных прогонов всем шести замороженных приложений импорта дана одна и та же допустимая сумма `1e5000`: '
                  'импорт, повтор и точный вывод. Проверка выполнялась в копиях. Она раскрывает наблюдённый независимым QA '
                  'дефект лимита цифр и его пропуски; это дополнительная проверка после основных запусков, исходные score/rubric/receipts не изменены.', '',
                  '| Режим / повтор | Приёмка по исходной процедуре | Доп. проверка контракта | Итог задачи |',
                  '|---|---|---|---|']
        for run in runs:
            check = run.get('posthoc_contract_check')
            if check:
                lines.append(f'| {run["condition"]} / {run["repeat"]} | {run["preregistered_task_verification"]} | '
                             f'{check["status"]} | {run["task_status"]} |')
        lines += ['', 'Итог задачи учитывает подтверждённое нарушение контракта из этой дополнительной проверки. '
                  'PASS независимого модельного проверяющего не доказывает отсутствия такого дефекта. '
                  '[Полный receipt](evidence/posthoc-large-decimal.json).']
    lines += ['', 'Первый STOP_SHIP/timeout не скрыт последующим repair. First-checks и исходные receipts сохранены отдельно; '
              'у старого поля `first_attempt_status` в raw receipt более узкий смысл — implementation+mechanical check.', '',
              '## Проверки помощников', '']
    for item in diagnostics:
        lines.append(f'- {item["kind"]}: **{item["status"]}**. [Receipt](evidence/diagnostic-{item["kind"]}.json).')
    for kind in ('stale_advice', 'worker_timeout'):
        if not any(d['kind'] == kind for d in diagnostics):
            lines.append(f'- {kind}: **NOT RUN**.')
    violations = [(r, f) for r in runs for f in r.get('posthoc_protocol_findings', [])]
    for run, finding in violations:
        lines.append(f'- {run["case"]}/{run["condition"]}/{run["repeat"]}: **protocol FAIL**, {finding}.')
    lines += ['', 'Stale probe даёт настоящему worker старый GO-снимок и проверяет реальный конфликт с текущим HOLD. '
              'Это controlled stale-input fault, а не доказательство обнаружения любой галлюцинации. Timeout probe '
              'проверяет реальный interrupt настоящего native worker. Workers получили read-only инструкции; '
              'их sandbox наследуется от main, отдельная OS-изоляция от записи этим раундом не доказана.', '',
              '## Что исправлено и что остаётся', '',
              'Деньги переведены на явный новый контракт: целые копейки и decimal strings, без float. '
              'Regression tests проверяют старые precision/overflow cases и числа долей из failed repair. '
              'Дополнительно исправлено форматирование принятых сумм больше 4300 цифр без изменения глобального лимита Python. '
              'Это source fix после batch: замороженный helper и generated code прогонов не подменены. '
              'Collector теперь учитывает первый QA, отделяет missing QA от дефекта и отклоняет наблюдённый worker interval больше 60 с. '
              'Первые failed outputs и отчёт первого раунда заморожены. Бюджеты: implementation 300 с, worker 60 с, '
              'весь run 540 с, максимум одна repair; независимый общий review привязан к SHA проверенной версии приложения.', '',
              'Результаты описывают эти синтетические задачи и конкретную среду. Успешные задачи и диагностические пробы '
              'не разрешают production rollout и не заполняют неизвестные USD/человеко-минуты. '
              'Для решения о включении нужны эти измерения и более широкий опыт.', '',
              'Подробные paired scores, отдельные actual input/cached/output counters, thread/settings/usage, '
              'first attempts и review verdicts: [results.json](results.json). '
              'Индекс sanitized receipts: [evidence-index.json](evidence-index.json). Raw chats остаются локально: `'
              + str(root) + '`.']
    (output / 'REPORT_RU.md').write_text('\n'.join(lines) + '\n')
    return {'decision': decision, 'qualification_status': 'BLOCKED',
            'report': str(output / 'REPORT_RU.md'), 'runs': len(runs)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(publish(args.root, args.output), ensure_ascii=False, indent=2))
