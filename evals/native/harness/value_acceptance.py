#!/usr/bin/env python3
"""Task acceptance outside the editable project; public rules are in fixture README."""
import csv
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile


def evaluate(workspace, task):
    workspace = Path(workspace).resolve()
    filename = 'booking.py' if task == 'booking' else 'export_contacts.py'
    source = workspace / filename
    if not source.resolve().is_relative_to(workspace):
        raise ValueError('Source escapes workspace')
    spec = importlib.util.spec_from_file_location('product_under_test', source)
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(workspace))
    sys.dont_write_bytecode = True
    spec.loader.exec_module(module)
    errors, passed = [], []

    def expect(condition, message):
        if not condition:
            raise AssertionError(message)

    def rejects(callback):
        try:
            callback()
        except ValueError:
            return
        raise AssertionError('Expected ValueError')

    def run(name, callback):
        try:
            with tempfile.TemporaryDirectory(prefix='playbook-acceptance-') as directory:
                callback(Path(directory))
            passed.append(name)
        except Exception as exc:
            errors.append(f'{name}: {type(exc).__name__}: {exc}')

    if task == 'booking':
        seed = [dict(id='kept', slot='old-slot', email='kept@example.test', request_id='old-request')]

        def existing(root):
            path = root / 'bookings.json'; path.write_text(json.dumps(seed))
            store = module.BookingStore(path)
            expect(store.list_bookings() == seed, 'Existing bookings lost')
            store.reserve('new-slot', 'next@example.test', 'new-request')
            expect(seed[0] in module.BookingStore(path).list_bookings(), 'Existing record changed')

        def restart(root):
            path = root / 'bookings.json'; store = module.BookingStore(path)
            record = store.reserve('new-slot', 'reader@example.test', 'request')
            expect(bool(record.get('id')), 'Missing booking id')
            command = 'import json,sys; from booking import BookingStore; print(json.dumps(BookingStore(sys.argv[1]).list_bookings()))'
            result = subprocess.run([sys.executable, '-B', '-c', command, str(path)],
                                    cwd=workspace, text=True, capture_output=True, timeout=5, check=True)
            expect(json.loads(result.stdout) == [record], 'Data did not survive a fresh process')

        def idempotent(root):
            store = module.BookingStore(root / 'bookings.json')
            first = store.reserve('slot', 'reader@example.test', 'request')
            expect(store.reserve('slot', 'reader@example.test', 'request') == first, 'Retry changed record')
            expect(len(store.list_bookings()) == 1, 'Retry created duplicate')

        def conflict(root):
            path = root / 'bookings.json'; first = module.BookingStore(path); second = module.BookingStore(path)
            kept = first.reserve('slot', 'reader@example.test', 'request')
            rejects(lambda: second.reserve('slot', 'other@example.test', 'another-request'))
            expect(second.list_bookings() == [kept], 'Objects disagree about persisted state')

        def request_reuse(root):
            store = module.BookingStore(root / 'bookings.json')
            kept = store.reserve('slot', 'reader@example.test', 'request')
            rejects(lambda: store.reserve('different-slot', 'reader@example.test', 'request'))
            rejects(lambda: store.reserve('slot', 'other@example.test', 'request'))
            expect(store.list_bookings() == [kept], 'Rejected request changed data')

        def normalization(root):
            store = module.BookingStore(root / 'bookings.json')
            record = store.reserve('slot', ' Reader@Example.Test ', 'request')
            expect(record['email'] == 'reader@example.test', 'Email not normalized')

        def invalid_input(root):
            path = root / 'bookings.json'; path.write_text(json.dumps(seed)); before = path.read_bytes()
            store = module.BookingStore(path)
            for args in [('slot', '', 'req'), ('slot', 'wrong', 'req'), ('', 'a@b.test', 'req'), ('slot', 'a@b.test', '')]:
                rejects(lambda args=args: store.reserve(*args))
            expect(path.read_bytes() == before, 'Invalid input changed stored data')

        def corrupt(root):
            path = root / 'bookings.json'; path.write_bytes(b'{broken')
            rejects(lambda: module.BookingStore(path).reserve('slot', 'a@b.test', 'req'))
            expect(path.read_bytes() == b'{broken', 'Corrupted source overwritten')

        for callback in (existing, restart, idempotent, conflict, request_reuse, normalization, invalid_input, corrupt):
            run(callback.__name__, callback)
    else:
        def export(root, rows):
            source = root / 'in.json'; output = root / 'out.csv'
            source.write_text(json.dumps(rows, ensure_ascii=False), encoding='utf-8'); before = source.read_bytes()
            count = module.export_csv(source, output)
            expect(source.read_bytes() == before, 'Source changed')
            reader = csv.DictReader(io.StringIO(output.read_text(encoding='utf-8-sig'), newline=''))
            expect(reader.fieldnames == ['name', 'email'], 'Wrong columns / internal data leaked')
            return count, list(reader)

        def consent(root):
            rows = [dict(name=str(i), email=f'{i}@example.test', consent=c, notes='PRIVATE')
                    for i, c in enumerate([True, False, 'false', 'true', 1, None])]
            rows.append(dict(name='missing', email='missing@example.test'))
            count, data = export(root, rows)
            expect(count == 1 and data == [dict(name='0', email='0@example.test')], 'Non-consenting contact exported')

        def escaping(root):
            name = 'Анна, "ведущая"\nвторой строки'
            count, data = export(root, [dict(name=name, email='a@example.test', consent=True, notes='PRIVATE')])
            expect(count == 1 and data == [dict(name=name, email='a@example.test')], 'CSV did not round-trip')

        def deduplication(root):
            count, data = export(root, [dict(name=name, email=email, consent=True) for name, email in
                [('first', ' A@Example.Test '), ('later', 'a@example.test'), ('second', 'b@example.test'), ('bad', ''), ('bad', 'wrong')]])
            expect(count == 2 and data == [dict(name='first', email='a@example.test'), dict(name='second', email='b@example.test')], 'Wrong ordering, normalization, validation or duplicate handling')

        def empty(root):
            expect(export(root, []) == (0, []), 'Empty export must contain header only')

        def collision(root):
            source = root / 'in.json'; source.write_bytes(b'[]')
            rejects(lambda: module.export_csv(source, source))
            expect(source.read_bytes() == b'[]', 'Same-path export destroyed source')

        def linked_collision(root):
            source = root / 'in.json'; source.write_bytes(b'[]'); output = root / 'out.csv'; output.symlink_to(source)
            rejects(lambda: module.export_csv(source, output))
            expect(source.read_bytes() == b'[]', 'Symlink export destroyed source')

        def corrupt(root):
            source = root / 'in.json'; output = root / 'out.csv'
            source.write_bytes(b'{broken'); output.write_bytes(b'keep previous export')
            rejects(lambda: module.export_csv(source, output))
            expect(output.read_bytes() == b'keep previous export', 'Invalid JSON destroyed previous export')

        for callback in (consent, escaping, deduplication, empty, collision, linked_collision, corrupt):
            run(callback.__name__, callback)

    summary_path = workspace.parent / 'adapter/adapter_summary.json'
    if summary_path.exists():
        before = json.loads(summary_path.read_text())['workspace_before_agent']
        protected = {'bookings.json', 'contacts.json', 'AGENTS.md'}
        for name, digest in before.items():
            if name in protected or name.startswith('.agents/'):
                path = workspace / name
                if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
                    errors.append('Protected project data/instructions changed: ' + name)
    return dict(passed=not errors, checks_passed=passed, errors=errors)


if __name__ == '__main__':
    try:
        result = evaluate(Path(sys.argv[1]), sys.argv[2])
    except Exception as exc:
        result = dict(passed=False, errors=[f'{type(exc).__name__}: {exc}'])
    print(json.dumps(result, ensure_ascii=False))
    raise SystemExit(not result['passed'])
