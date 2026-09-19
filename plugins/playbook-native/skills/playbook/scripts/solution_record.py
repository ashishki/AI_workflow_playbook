#!/usr/bin/env python3
"""Inspect a solution record and explicit file snapshots; never execute its commands.

Optional shared helper, not an orchestrator, database, release gate or authorization
service. Markdown/task state may remain canonical; do not create a competing record.
Snapshot integrity is not independent attestation or proof of application quality.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import re
import sys
from typing import Any

MAX_JSON_BYTES = 1_048_576
MAX_FILE_BYTES = 16_777_216
MAX_FILES = 100
SCHEMA = 'playbook.solution.v1'
SNAPSHOT_SCHEMA = 'playbook.snapshot.v1'
KINDS = {'undecided', 'no_change', 'process_change', 'configure', 'template', 'automation', 'code', 'ai'}
STAGES = ('discover', 'decide', 'design', 'build', 'verify', 'introduce', 'observe',
          'change', 'diagnose', 'recover', 'transfer', 'grow', 'retire')
HASH = re.compile(r'^[a-f0-9]{64}$')


class RecordError(ValueError):
    pass


def safe_path(root: Path, name: str, *, exists: bool = True) -> Path:
    """No absolute/parent/ambiguous paths, symlinks or known secret locations.

    Protection assumes no hostile process races path checks. Use the host sandbox
    for isolation. Path checks and file hashes are not a content secret scanner.
    """
    if not isinstance(name, str) or not name or '\\' in name or ':' in name or '\x00' in name:
        raise RecordError(f'Invalid relative path: {name!r}')
    rel = PurePosixPath(name)
    if rel.is_absolute() or '..' in rel.parts or name != rel.as_posix():
        raise RecordError(f'Non-canonical project path: {name!r}')
    blocked = {'.git', '.ssh', '.aws', '.azure', 'secrets', 'credentials', 'auth.json', 'credentials.json'}
    for part in rel.parts:
        lower = part.lower()
        if lower in blocked or lower.startswith('.env') or lower.endswith(('.pem', '.key', '.p12', '.pfx')):
            raise RecordError(f'Sensitive path is not evidence: {name}')
    current = root
    for part in rel.parts:
        current = current / part
        if current.is_symlink():
            raise RecordError(f'Symlink is not an evidence path: {name}')
    if exists and not current.is_file():
        raise RecordError(f'Missing regular file: {name}')
    if not current.parent.is_dir():
        raise RecordError(f'Output parent must already exist: {name}')
    return current


def load_json(path: Path) -> Any:
    if path.stat().st_size > MAX_JSON_BYTES:
        raise RecordError('JSON exceeds the bounded record size')
    def reject_duplicate(pairs):
        out = {}
        for key, value in pairs:
            if key in out:
                raise RecordError(f'Duplicate JSON field: {key}')
            out[key] = value
        return out
    def reject_constant(value):
        raise RecordError(f'Non-finite JSON number: {value}')
    return json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=reject_duplicate,
                      parse_constant=reject_constant)


def validate(data: Any) -> list[str]:
    errors = []
    if not isinstance(data, dict):
        return ['Record must be a JSON object']
    if data.get('schema_version') != SCHEMA:
        errors.append('Unsupported schema_version')
    for key in ('problem', 'owner', 'next_step'):
        if not isinstance(data.get(key), str) or not data[key].strip():
            errors.append(f'{key} must be non-empty text')
    decision = data.get('decision')
    if not isinstance(decision, dict) or decision.get('kind') not in KINDS or not isinstance(decision.get('reason'), str) or not decision['reason'].strip():
        errors.append('decision needs a supported kind and reason')
    state = data.get('state')
    allowed = {'technical': {'not_applicable', 'not_checked', 'partial', 'checked', 'failed'},
               'in_use': {'not_observed', 'trial', 'in_use', 'stopped'},
               'effect': {'unknown', 'no_change', 'improved', 'worse'}}
    if not isinstance(state, dict):
        errors.append('state is required')
    else:
        for key, choices in allowed.items():
            if state.get(key) not in choices:
                errors.append(f'Invalid state.{key}')
    for key in ('rules', 'open_issues'):
        value = data.get(key)
        if not isinstance(value, list) or any(not isinstance(x, str) for x in value):
            errors.append(f'{key} must be an array of text')
    operations = data.get('operations')
    if not isinstance(operations, dict) or any(not isinstance(operations.get(k), str) or not operations[k].strip()
            for k in ('open', 'fallback', 'diagnose', 'recover', 'transfer', 'retire')):
        errors.append('operations requires open/fallback/diagnose/recover/transfer/retire text')
    locations = data.get('data')
    if not isinstance(locations, dict) or not isinstance(locations.get('sensitive'), bool) or any(
            not isinstance(locations.get(k), list) or any(not isinstance(x, str) for x in locations[k])
            for k in ('locations', 'access')):
        errors.append('data needs locations, access and sensitive')
    for key in ('checks', 'observations', 'interventions', 'costs'):
        if not isinstance(data.get(key), list) or any(not isinstance(x, dict) for x in data[key]):
            errors.append(f'{key} must be an array of objects')
    for check in data.get('checks', []) if isinstance(data.get('checks'), list) else []:
        if not isinstance(check, dict): continue
        evidence = check.get('evidence')
        if check.get('status') not in {'not_run', 'passed', 'failed', 'blocked', 'not_applicable'} or not isinstance(check.get('claim'), str) or not check['claim'].strip():
            errors.append('Invalid check claim/status')
        if not isinstance(evidence, list) or any(not isinstance(x, str) or not x.strip() for x in evidence):
            errors.append('check.evidence must be text references')
        elif check.get('status') in {'passed', 'failed'} and not evidence:
            errors.append('A reported check result needs evidence references')
    for cost in data.get('costs', []) if isinstance(data.get('costs'), list) else []:
        if not isinstance(cost, dict): continue
        amount = cost.get('amount')
        if not isinstance(cost.get('label'), str) or not isinstance(cost.get('unit'), str) or (
                amount is not None and (isinstance(amount, bool) or not isinstance(amount, (int, float)) or not math.isfinite(amount) or amount < 0)):
            errors.append('Invalid cost; use null for unknown, not a fabricated zero')
    for obs in data.get('observations', []) if isinstance(data.get('observations'), list) else []:
        if not isinstance(obs, dict): continue
        if not isinstance(obs.get('metric'), str) or not isinstance(obs.get('evidence'), list):
            errors.append('Observation needs metric and evidence references')
        for k in ('before', 'after'):
            val = obs.get(k)
            if val is not None and (isinstance(val, bool) or not isinstance(val, (int, float)) or not math.isfinite(val)):
                errors.append(f'Observation {k} must be finite or null')
    for item in data.get('interventions', []) if isinstance(data.get('interventions'), list) else []:
        if not isinstance(item, dict): continue
        if item.get('stage') not in STAGES or not isinstance(item.get('reason'), str) or item.get('actor') not in {'owner', 'author', 'specialist', 'colleague', 'assistant'}:
            errors.append('Invalid intervention stage/reason/actor')
        val = item.get('minutes')
        if val is not None and (isinstance(val, bool) or not isinstance(val, (int, float)) or not math.isfinite(val) or val < 0):
            errors.append('Intervention minutes must be nonnegative or null')
    if isinstance(state, dict) and state.get('technical') == 'checked':
        checks = data.get('checks', [])
        if not isinstance(checks, list) or not any(isinstance(c, dict) and c.get('status') == 'passed' for c in checks) or any(isinstance(c, dict) and c.get('status') in {'failed', 'blocked'} for c in checks):
            errors.append('A checked technical state needs reported passing evidence and no failed/blocked check')
    if isinstance(state, dict) and state.get('effect') in {'improved', 'worse', 'no_change'}:
        observations = data.get('observations', [])
        if not isinstance(observations, list) or not any(isinstance(o, dict) and o.get('before') is not None and o.get('after') is not None and o.get('evidence') for o in observations):
            errors.append('A reported effect needs before/after observation and evidence')
    return errors


def read_record(root: Path, name: str) -> dict:
    data = load_json(safe_path(root, name))
    errors = validate(data)
    if errors:
        raise RecordError('; '.join(errors))
    return data


def digest(path: Path) -> str:
    if path.stat().st_size > MAX_FILE_BYTES:
        raise RecordError(f'File too large for bounded snapshot: {path.name}')
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(65536), b''):
            value.update(chunk)
    return value.hexdigest()


def snapshot(root: Path, record_name: str, files: list[str]) -> dict:
    read_record(root, record_name)
    names = sorted(set([record_name] + files))
    if not files or len(names) > MAX_FILES:
        raise RecordError(f'Choose explicit evidence files (at most {MAX_FILES} including record)')
    return {'schema_version': SNAPSHOT_SCHEMA, 'record': record_name,
            'meaning': 'Explicit file identities only; not runtime, correctness, approval or business-effect evidence.',
            'files': {name: digest(safe_path(root, name)) for name in names}}


def verify_snapshot(root: Path, payload: Any) -> list[str]:
    if not isinstance(payload, dict) or payload.get('schema_version') != SNAPSHOT_SCHEMA:
        raise RecordError('Unsupported snapshot schema')
    files = payload.get('files')
    if not isinstance(files, dict) or not files or len(files) > MAX_FILES or payload.get('record') not in files:
        raise RecordError('Invalid or incomplete snapshot files/record')
    changed = []
    for name, expected in files.items():
        if not isinstance(expected, str) or not HASH.fullmatch(expected):
            raise RecordError(f'Invalid digest for {name}')
        try:
            if digest(safe_path(root, name)) != expected:
                changed.append(name)
        except (RecordError, OSError):
            changed.append(name)
    return changed


def render(data: dict) -> str:
    lines = ['# Состояние рабочего решения', '',
        '> Записанное состояние — не независимое подтверждение качества и не разрешение на действия.', '',
        f'**Проблема:** {data["problem"]}', f'**Владелец:** {data["owner"]}',
        f'**Решение:** {data["decision"]["kind"]} — {data["decision"]["reason"]}',
        f'**Техника / использование / эффект:** {data["state"]["technical"]} / {data["state"]["in_use"]} / {data["state"]["effect"]}', '',
        '## Правила', *[f'- {v}' for v in data['rules']], '', '## Как пользоваться и продолжать']
    labels = {'open':'Открыть', 'fallback':'Ручной способ', 'diagnose':'Диагностика', 'recover':'Восстановление', 'transfer':'Передача', 'retire':'Отключение'}
    lines.extend(f'**{label}:** {data["operations"][k]}' for k,label in labels.items())
    lines += ['', '## Данные', 'Места: ' + '; '.join(data['data']['locations']),
              'Доступ: ' + '; '.join(data['data']['access']), '', '## Заявленные проверки']
    lines.extend(f'- {c["claim"]}: {c["status"]}; ' + (', '.join(c['evidence']) or 'свидетельств пока нет') for c in data['checks'])
    lines += ['', '## Наблюдения и участие']
    fmt = lambda v: 'неизвестно' if v is None else str(v)
    lines.extend(f'- {o["metric"]}: {fmt(o.get("before"))} → {fmt(o.get("after"))}' for o in data['observations'])
    lines.extend(f'- {i["stage"]}: {i["actor"]}; {i["reason"]}; {fmt(i.get("minutes"))} мин.' for i in data['interventions'])
    lines += ['', '## Расходы']
    lines.extend(f'- {c["label"]}: {fmt(c.get("amount"))} {c["unit"]}' for c in data['costs'])
    if not data['costs']: lines.append('Не измерены; отсутствие записи не означает нулевую стоимость.')
    lines += ['', '## Открыто', *[f'- {x}' for x in data['open_issues']], '', f'**Следующий шаг:** {data["next_step"]}', '',
              'Секреты передавайте отдельно через разрешённые средства. Перед передачей проверьте содержание этой записки.',
              'Откат файлов не отменяет внешние операции и не доказывает восстановление данных.', '']
    return '\n'.join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path('.'))
    commands = parser.add_subparsers(dest='command', required=True)
    for action in ('check', 'summary', 'snapshot', 'handoff'):
        p = commands.add_parser(action); p.add_argument('--record', required=True)
        if action == 'snapshot':
            p.add_argument('--files', nargs='+', required=True)
            p.add_argument('--output', required=True)
        if action == 'handoff': p.add_argument('--snapshot', required=True)
    p = commands.add_parser('verify'); p.add_argument('--snapshot', required=True)
    args = parser.parse_args(argv)
    try:
        root = args.root.expanduser().resolve(strict=True)
        if not root.is_dir(): raise RecordError('Root is not a directory')
        if args.command in {'verify', 'handoff'}:
            proof = load_json(safe_path(root, args.snapshot))
            changed = verify_snapshot(root, proof)
            if changed:
                print(json.dumps({'status':'stale', 'changed':changed}, ensure_ascii=False)); return 1
            if args.command == 'verify':
                print(json.dumps({'status':'snapshot_matches', 'quality':'not_assessed'})); return 0
            if proof['record'] != args.record:
                raise RecordError('Snapshot belongs to a different record')
        data = read_record(root, args.record)
        if args.command == 'check':
            print(json.dumps({'status':'schema_valid', 'quality':'not_assessed'}))
        elif args.command in {'summary', 'handoff'}:
            print(render(data), end='')
            if args.command == 'handoff':
                print('\nИдентичность перечисленных файлов сверена. Полнота выбранного списка и работа приложения этим не подтверждаются.')
        elif args.command == 'snapshot':
            proof = snapshot(root, args.record, args.files)
            if args.output in proof['files']: raise RecordError('Snapshot cannot overwrite an input')
            dest = safe_path(root, args.output, exists=False)
            with dest.open('x', encoding='utf-8') as stream:
                json.dump(proof, stream, ensure_ascii=False, indent=2); stream.write('\n')
            print(json.dumps({'status':'snapshot_written', 'quality':'not_assessed', 'path':args.output}))
        return 0
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(f'solution_record: {exc}', file=sys.stderr); return 2


if __name__ == '__main__':
    raise SystemExit(main())
