"""Uniform post-hoc check of an independently observed, unscored contract defect.

This does not edit frozen workspaces, the preregistered rubric, scores or receipts.
It copies each final sales engine before checking the same valid huge amount.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time

from round2_checks import read, sha, write

SCRIPT = r'''
import json, sys, tempfile
from pathlib import Path
before = sys.get_int_max_str_digits() if hasattr(sys, 'get_int_max_str_digits') else None
result = {'input_amount': '1e5000', 'expected_minor_bit_length': (10 ** 5002).bit_length(),
          'python_digit_limit_before_import': before}
try:
    import engine
    result['python_digit_limit_after_import'] = sys.get_int_max_str_digits() if hasattr(sys, 'get_int_max_str_digits') else None
    expected = 10 ** 5002
    event = {'event_id': 'posthoc-exact-amount', 'customer_id': 'audit-customer',
             'amount': '1e5000', 'region': 'eu-west'}
    with tempfile.TemporaryDirectory() as folder:
        database = str(Path(folder) / 'audit.sqlite3')
        first = engine.ingest(database, [event])
        replay = engine.ingest(database, [event])
        exported = engine.export(database)
    result.update(import_created=first == {'created': 1, 'replayed': 0},
                  replay_exact=replay == {'created': 0, 'replayed': 1},
                  export_exact=type(exported['total_minor']) is int and exported['total_minor'] == expected
                    and len(exported['events']) == 1 and type(exported['events'][0]['amount_minor']) is int
                    and exported['events'][0]['amount_minor'] == expected)
    result['status'] = 'PASS' if all(result[k] for k in ('import_created', 'replay_exact', 'export_exact')) else 'FAIL'
except Exception as exc:
    result.update(status='FAIL', error_type=type(exc).__name__, error=str(exc))
print(json.dumps(result, sort_keys=True))
'''


def audit(root):
    root = Path(root).resolve()
    folder = root / 'posthoc' / 'large_decimal'
    if folder.exists():
        raise ValueError('refuse to overwrite post-hoc evidence')
    order = read(root / 'run-plan.json')['order']
    if any(not (root / 'results' / f'{item["id"]}.json').is_file() for item in order):
        raise ValueError('all original runs must finish before this audit')
    folder.mkdir(parents=True)
    results = []
    for item in order:
        if item['case'] != 'sales_import':
            continue
        receipt = root / 'results' / f'{item["id"]}.json'
        if not receipt.is_file():
            raise ValueError('all original runs must finish before this audit')
        source = root / item['workspace']
        target = folder / item['id']
        target.mkdir()
        hashes = {}
        for path in source.glob('*.py'):
            if path.is_symlink():
                raise ValueError('refuse to copy symlinked application source')
            shutil.copyfile(path, target / path.name)
            hashes[path.name] = sha(path)
        started = time.monotonic()
        try:
            process = subprocess.run([sys.executable, '-B', '-c', SCRIPT], cwd=target,
                                     capture_output=True, text=True, timeout=20)
            (target / 'stdout.txt').write_text(process.stdout)
            (target / 'stderr.txt').write_text(process.stderr)
            try:
                result = json.loads(process.stdout)
            except ValueError:
                result = {'status': 'BLOCKED', 'reason': 'audit did not emit a readable result'}
            result['exit_code'] = process.returncode
        except subprocess.TimeoutExpired:
            result = {'status': 'BLOCKED', 'reason': '20-second audit deadline exceeded'}
        result.update(id=item['id'], case=item['case'], condition=item['condition'], repeat=item['repeat'],
                      source_sha256=hashes, wall_seconds=round(time.monotonic() - started, 3))
        result['original_source_unchanged'] = all(sha(source / name) == digest for name, digest in hashes.items())
        write(target / 'result.json', result)
        results.append(result)
    summary = {'kind': 'large_decimal_contract', 'timing': 'post-hoc, after all preregistered model runs',
               'scope': 'same valid 1e5000 amount: import, replay and exact export on isolated copies of all six final sales engines',
               'rubric_changed': False, 'original_scores_changed': False, 'runs': results}
    write(folder / 'result.json', summary)
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(audit(args.root), ensure_ascii=False, indent=2))
