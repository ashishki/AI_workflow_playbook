"""Publish immutable round-3 evidence with explicit post-batch interpretation."""
from copy import deepcopy
import datetime
import hashlib
import json
from pathlib import Path
import shutil
import sys

REPO = Path('/srv/openclaw-you/workspace/AI_workflow_playbook')
HERE = REPO / 'engineering/experiments/controlled-delegation'
sys.path.insert(0, str(HERE))
from round3 import scope_instruction_presence, protocol_check
from round3_report import sanitize, summarize, common_review
from round3_checks import read, sha, write

root = REPO / '.playbook-artifacts/delegation-round3/runs'
out = Path(sys.argv[1]).resolve()
assert not out.exists(), 'never overwrite a published/draft report'
draft = root / 'draft-report'
source = REPO / '.playbook-artifacts/delegation-round3/frozen-repo'
manifest = read(root / 'source-sha256.json')
for name, digest in manifest.items():
    assert sha(source / name) == digest, name
shutil.copytree(draft, out)
results = read(out / 'results.json')
original_collector = deepcopy(results)
assessment = []
plan = read(root / 'run-plan.json')
for item, public in zip(plan['order'], results['runs']):
    original_path = root / 'results' / (item['id'] + '.json')
    raw = read(original_path)
    assert raw['task_status'] == 'PASS' and raw['score'] == 100
    assert raw['phases'][0]['completed'] and not raw['phases'][0]['timeout']
    assert raw['usage_complete'] is True
    evidence = out / f'evidence/{item["case"]}-{item["condition"]}-{item["repeat"]}.json'
    assert read(evidence)['protocol_status'] == raw['protocol_status']
    data = deepcopy(raw)
    for worker in data['native_spawn_receipts']:
        worker['scope_instruction_present'] = scope_instruction_presence(worker.get('message'))
    corrected = protocol_check(item['condition'], raw['phases'][0], data)
    assert corrected['status'] == ('PASS' if item['condition'] == 'B' else 'BLOCKED')
    assert not corrected['failures']
    public['collector_status'] = public['status']
    public['collector_protocol_status'] = public['protocol_status']
    public['collector_protocol'] = public['protocol']
    public['protocol_status'] = corrected['status']
    public['protocol'] = corrected
    public['status'] = 'PASS' if corrected['status'] == 'PASS' else 'BLOCKED'
    public['posthoc_interpretation'] = 'same observed evidence; unreadable scope is unknown, not a proven violation'
    for worker, corrected_worker in zip(public['native_spawn_receipts'], data['native_spawn_receipts']):
        worker['collector_scope_instruction_present'] = worker['scope_instruction_present']
        worker['scope_instruction_present'] = corrected_worker['scope_instruction_present']
    assessment.append({'id': item['id'], 'condition': item['condition'], 'repeat': item['repeat'],
        'original_receipt_sha256': sha(original_path), 'original_protocol_status': raw['protocol_status'],
        'posthoc_protocol': corrected, 'task_score_unchanged': raw['score'],
        'scope_verified': corrected['status'] == 'PASS' and raw['workers'] == 0})
write(out / 'evidence/posthoc-protocol.json', {'scope': 'classification correction after actual independent STOP_SHIP',
    'no_task_or_score_or_original_receipt_changes': True, 'runs': assessment})
write(out / 'evidence/original-collector-summary.json', original_collector['comparisons'])
write(out / 'evidence/owner-authorization.json', read(root / 'owner-authorization.json'))
write(out / 'evidence/a2-child-commands.json', read(root / 'operator-observations/a2-child-commands.json'))
first = read(root / 'common-review/receipt.json')
write(out / 'review/initial-receipt.json', sanitize(first, root))
for artifact in first['artifacts']:
    if artifact['kind'] == 'report':
        text = Path(artifact['path']).read_text()
        (out / 'review/initial-report.md').write_text(sanitize(text, root))
results['collector_task_batch_status'] = results['task_batch_status']
results['task_batch_status'] = 'BLOCKED'
results['application_verification_status'] = 'PASS'
results['qualification_status'] = 'BLOCKED'
results['environment_blocker'] = None
results['comparisons'] = summarize(results['runs'])
results['comparisons']['application_results_equal'] = True
results['comparisons']['wall_ratio_interpretation'] = 'descriptive observed equal-score completed applications; worker scope unverified, not a qualified successful workflow comparison'
results['initial_independent_review'] = sanitize(first, root)
results['a2_worker_command_claim'] = {'status': 'PASS_OBSERVED', 'evidence': 'evidence/a2-child-commands.json'}
results['baseline_limit'] = 'A was permitted workers and COMMON also urged their use; A used three workers in both repeats. Do not interpret A as a solo or unprompted baseline.'
results['posthoc_assessment'] = 'evidence/posthoc-protocol.json'
results['source_execution_head'] = plan['head']
corrected_files = [HERE / 'round3.py', HERE / 'ROUND3_PROTOCOL_RU.md',
                   REPO / 'tests/vnext/test_controlled_delegation_round3.py']
for path in corrected_files:
    dest = out / 'source-corrections' / path.relative_to(REPO)
    dest.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(path, dest)
results['source_corrections_sha256'] = {p.relative_to(REPO).as_posix(): sha(p) for p in corrected_files}
script = Path(__file__).resolve()
dest = out / 'publication-code/build-final-report.py'; dest.parent.mkdir(exist_ok=True); shutil.copyfile(script, dest)
results['publication_producer_sha256'] = sha(script)
results['source_review_accounting'] = 'after-batch reviews excluded from A/B/C implementation wall and token ratios; coordinator/source-preparation tokens not measured here'
results['limits'].extend(['Opaque native scope instructions remain unverified; no PASS inferred from encrypted payload.',
                       results['baseline_limit'], 'No OS read-only guarantee under authorized root execution.'])
if len(sys.argv) > 2:
    audit_root = Path(sys.argv[2]).resolve()
    final = common_review(audit_root, results['runs'])
    assert final['status'] == 'validated', final
    results['common_independent_review'] = sanitize(final, root)
    write(out / 'review/final-receipt.json', sanitize(final, root))
    write(out / 'review/final-snapshot.json', sanitize(read(audit_root / final['snapshot_path']), root))
    for a in final['artifacts']:
        if a['kind'] == 'report': (out / 'review/final-report.md').write_text(sanitize(Path(a['path']).read_text(), root))
else:
    final = {'status': 'BLOCKED', 'verdict': None, 'reason': 'independent correction recheck pending'}
    results['common_independent_review'] = final
write(out / 'results.json', results)
comp = results['comparisons']; totals = comp['token_totals']
lines = ['# Что показал третий раунд', '',
    'Проведены **6/6 настоящих A/B/C-прогонов** на связанном синтетическом проекте: 67 файлов, '
    '44 исходника, 527 строк рабочего кода. В каждом запуске исправлены три причины сбоя '
    'в inventory, checkout и refunds. Все шесть получили **100/100 / application PASS**; '
    'первое независимое ревью подтвердило правильность кода и объяснений всех шести результатов.', '',
    'Добавочная польза делегирования **не показана**. В обоих повторах C медленнее B. '
    'Медиана C/B времени — **1.46×**; uncached input — **2.93×**, output — **1.69×**. '
    'Это наблюдаемые расходы и длительность завершённых приложений с одинаковой оценкой, '
    'не квалифицированное сравнение полностью проверенных workflows: scope инструкций workers неизвестен.', '',
    '**Application PASS; protocol A/C BLOCKED, B PASS; полная qualification BLOCKED. '
    'Решение: не включать делегирование по умолчанию.**', '',
    '| Повтор | A, с | B, с | C, с | C/B время |', '|---|---:|---:|---:|---:|']
for pair in comp['paired_outcomes']:
    lines.append(f'| {pair["repeat"]} | {pair["A"]["implementation_wall_seconds"]:.3f} | {pair["B"]["implementation_wall_seconds"]:.3f} | {pair["C"]["implementation_wall_seconds"]:.3f} | {pair["c_b_wall"]:.2f}× |')
lines += ['', '| Режим | Median, с | Input | Cached input | Uncached input | Output | Workers |',
          '|---|---:|---:|---:|---:|---:|---:|']
for c in 'ABC':
    t = totals[c]
    lines.append(f'| {c} | {comp["median_implementation_wall_seconds"][c]:.3f} | {t["input_tokens"]} | {t["cached_input_tokens"]} | {t["uncached_input_tokens"]} | {t["output_tokens"]} | {0 if c == "B" else 3} в каждом |')
lines += ['', 'Counters полные во всех шести попытках: отдельные persistent provider threads main и '
    '12 настоящих native workers. CLI main summary не прибавляется повторно. Время включает '
    'работу модели и её проверки; operator scoring и послеэкспериментальное ревью раскрыты отдельно. '
    '**USD и активные человеко-минуты неизвестны / NOT MEASURED**, не ноль и не ценовая оценка.', '',
    'Критерий был закреплён до calls: одинаково успешные B/C, median C/B ≤0.80, '
    'полные uncached-input/output ratios ≤2.0. Наблюдённые время и uncached input не достигают порогов '
    'даже без проблемы проверки scope. Два повтора одного среднего synthetic repo не дают статистического '
    'или production-вывода и не проверяют automatic routing.', '',
    '## Исправление оценщика и независимое ревью', '',
    'Первый настоящий общий read-only Native review: **validated STOP_SHIP**. Он обнаружил, '
    'что поиск literal markers в opaque `gAAAAAB…` сообщениях породил четыре необоснованных protocol FAIL. '
    'В отдельной posthoc-интерпретации они заменены на **BLOCKED**, не PASS. Оригинальные receipts, '
    'scores, источник `0c27438`, четыре FAIL и исходный STOP_SHIP сохранены. Новых model runs '
    'или task repairs после batch не было. [Коррекция](evidence/posthoc-protocol.json), '
    '[первое ревью](review/initial-report.md).', '',
    'Дополнительно найдены actual child custom-tool calls/stdout трёх CLI replay-команд из STATE A2. '
    'Это связанные исходные журналы, а не повторная имитация исполнения. '
    '[Свидетельство](evidence/a2-child-commands.json).', '',
    'Будущий collector различает unreadable/unknown и подтверждённое нарушение, не скрывая '
    'реальные deadline/inheritance defects. Будущий prompt ясно разрешает A solo work. '
    'В этом batch общий текст подталкивал A к workers: A/C действительно использовали по три. '
    'Поэтому A не считается чистым solo или unprompted baseline; основной ориентир — B.', '',
    f'Повторная независимая проверка исправлений и скорректированной интерпретации: '
    f'**{final.get("status")} / {final.get("verdict") or "NOT RUN"}**. '
    'Её scope и фактические counters указаны в results.json. Первое полное ревью и повторная '
    'проверка не входят в task ratios. Координаторские и подготовительные model tokens здесь не измерены.', '',
    'Прогоны выполнены под root после явного разрешения владельца, одной моделью '
    'gpt-6.1-sol/high, последовательно, без repair, per-run model reviewers, внешних аккаунтов '
    'и production действий. Source/parent/child evidence локально в '
    '`.playbook-artifacts/delegation-round3/runs`; raw chats не публикуются. '
    'Inherited worker sandbox не доказывает отдельную OS read-only изоляцию.', '',
    '[results.json](results.json), [evidence-index.json](evidence-index.json). Предыдущие раунды и preflight сохранены.']
(out / 'REPORT_RU.md').write_text('\n'.join(lines) + '\n')
# Raw prompt/chat fields stay local. Keep their hashes and transport assessment.
for path in [out / 'results.json', *(out / 'evidence').glob('*.json')]:
    doc = read(path)
    def redact(value):
        if isinstance(value, dict):
            result = {}
            for k, v in value.items():
                if k == 'messages': continue
                if k == 'message':
                    result['message_sha256'] = hashlib.sha256(str(v).encode()).hexdigest()
                    result['message_content_published'] = False
                else: result[k] = redact(v)
            return result
        if isinstance(value, list): return [redact(v) for v in value]
        return value
    write(path, redact(doc))
entries = []
original_index = {e['path']: e for e in read(draft / 'evidence-index.json')['receipts']}
for p in sorted(out.rglob('*')):
    if not p.is_file() or p.name == 'evidence-index.json': continue
    relative = p.relative_to(out).as_posix()
    entry = {'path': relative, 'sha256': sha(p)}
    if relative in original_index:
        entry['draft_sha256'] = original_index[relative]['sha256']
        if 'original_sha256' in original_index[relative]: entry['original_sha256'] = original_index[relative]['original_sha256']
    entries.append(entry)
write(out / 'evidence-index.json', {'schema': 'playbook.delegation.round3.evidence.v1', 'receipts': entries,
    'publication_producer_sha256': sha(script), 'source_execution_head': plan['head'],
    'raw_original_receipts_preserved': True, 'posthoc_interpretation': 'explicit classification correction; no reruns or score edits'})
for row in entries: assert sha(out / row['path']) == row['sha256']
print(json.dumps({'report': str(out / 'REPORT_RU.md'), 'application': 'PASS', 'qualification': 'BLOCKED',
    'actual_runs': 6, 'indexed_files': len(entries), 'c_b_wall': comp['c_b_wall'], 'final_review': final.get('status')}))
