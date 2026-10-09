"""Meaningful synthetic integration checks; no external services or fixtures."""
import concurrent.futures
import hashlib
import json
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from unittest import mock

import app


class BookingHTTPTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / 'bookings.json'
        self.server = app.BookingServer(('127.0.0.1', 0), app.Handler)
        self.server.store = app.Store(self.path)
        self.base = f'http://127.0.0.1:{self.server.server_port}'
        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.thread.join()
        self.server.server_close()
        self.temp.cleanup()

    def request(self, method='GET', path='/api/bookings', teacher='anna', payload=None, raw=None):
        headers = {'Content-Type': 'application/json'}
        if teacher is not None:
            headers['X-Teacher'] = teacher
        body = raw if raw is not None else (json.dumps(payload).encode() if payload is not None else None)
        request = urllib.request.Request(self.base + path, body, headers, method=method)
        try:
            response = urllib.request.urlopen(request, timeout=5)
        except urllib.error.HTTPError as error:
            response = error
        with response:
            return response.status, json.loads(response.read())

    def booking(self, request_id='one', slot='10:30', student='Синтетический ученик', **extra):
        return dict(student=student, date='2026-10-20', slot=slot, request_id=request_id, **extra)

    def test_create_list_id_and_header_owns_teacher(self):
        status, result = self.request('POST', payload=self.booking(teacher='boris'))
        self.assertEqual(201, status)
        booking = result['booking']
        self.assertEqual('anna', booking['teacher'])
        self.assertEqual(booking, self.request(path='/api/bookings/' + booking['id'])[1]['booking'])
        self.assertEqual([booking], self.request()[1]['bookings'])

    def test_teacher_isolation_and_nonleaking_missing_id(self):
        _, first = self.request('POST', payload=self.booking(student='PRIVATE-ANNA'))
        self.assertEqual([], self.request(teacher='boris')[1]['bookings'])
        status, forbidden = self.request(path='/api/bookings/' + first['booking']['id'], teacher='boris')
        self.assertEqual((404, {'error': 'Запись не найдена.'}), (status, forbidden))
        self.assertNotIn('PRIVATE-ANNA', json.dumps(forbidden))
        status, second = self.request('POST', teacher='boris', payload=self.booking(student='PRIVATE-BORIS'))
        self.assertEqual(201, status)  # Same date/slot and request id is allowed for another teacher.
        self.assertNotIn('PRIVATE-BORIS', json.dumps(self.request()[1]))
        self.assertNotEqual(first['booking']['id'], second['booking']['id'])

    def test_missing_unknown_identity_forbidden(self):
        for identity in (None, '', 'admin', 'Anna'):
            self.assertEqual(403, self.request(teacher=identity)[0])
            self.assertEqual(403, self.request('POST', teacher=identity, payload=self.booking())[0])

    def test_idempotency_and_distinct_request_conflict(self):
        _, first = self.request('POST', payload=self.booking())
        status, replay = self.request('POST', payload=self.booking())
        self.assertEqual(200, status)
        self.assertTrue(replay['replayed'])
        self.assertEqual(first['booking'], replay['booking'])
        status, changed = self.request('POST', payload=self.booking(student='Changed', slot='12:00'))
        self.assertEqual(200, status)
        self.assertEqual(first['booking'], changed['booking'])
        self.assertEqual(409, self.request('POST', payload=self.booking(request_id='two'))[0])
        self.assertEqual(1, len(self.request()[1]['bookings']))

    def test_validation_dates_times_names_and_bad_json(self):
        mutations = [{'date': '2026-02-30'}, {'date': '2026-2-01'}, {'date': '0000-01-01'},
                     {'slot': '24:00'}, {'slot': '10:60'}, {'slot': '1:00'}, {'student': ' '},
                     {'student': 123}, {'request_id': ''}, {'date': None}]
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                payload = self.booking()
                payload.update(mutation)
                self.assertEqual(400, self.request('POST', payload=payload)[0])
        for raw in (b'{', b'null', b'[]', b'{"student":NaN}', b'\xff'):
            self.assertEqual(400, self.request('POST', raw=raw)[0])
        self.assertEqual([], self.request()[1]['bookings'])

    def test_concurrent_conflict_exactly_one_winner(self):
        def create(index):
            return self.request('POST', payload=self.booking(request_id=f'race-{index}'))
        with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
            responses = list(pool.map(create, range(12)))
        self.assertEqual(1, sum(status == 201 for status, _ in responses))
        self.assertEqual(11, sum(status == 409 for status, _ in responses))
        self.assertEqual(1, len(app.Store(self.path).list('anna')))

    def test_concurrent_replay_exactly_one_record(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            responses = list(pool.map(lambda _: self.request('POST', payload=self.booking()), range(8)))
        self.assertEqual(1, sum(status == 201 for status, _ in responses))
        self.assertEqual(7, sum(status == 200 for status, _ in responses))
        self.assertEqual(1, len({value['booking']['id'] for _, value in responses}))

    def test_failed_persistence_keeps_previous_data(self):
        self.request('POST', payload=self.booking())
        before = self.path.read_bytes()
        with mock.patch('app.atomic_json', side_effect=OSError('synthetic disk failure')):
            status, _ = self.request('POST', payload=self.booking(request_id='second', slot='12:00'))
        self.assertEqual(503, status)
        self.assertEqual(before, self.path.read_bytes())
        self.assertEqual(1, len(self.request()[1]['bookings']))
        self.assertEqual(201, self.request('POST', payload=self.booking(request_id='second', slot='12:00'))[0])

    def test_static_page_local_demo_and_xss_safe_rendering(self):
        with urllib.request.urlopen(self.base) as response:
            html = response.read().decode()
            self.assertIn('Демо-идентификация', html)
            self.assertIn('lang="ru"', html)
            self.assertIn("script-src 'self'", response.headers['Content-Security-Policy'])
        self.request('POST', payload=self.booking(student='<img src=x onerror=alert(1)>'))
        self.assertEqual('<img src=x onerror=alert(1)>', self.request()[1]['bookings'][0]['student'])
        script = (app.ROOT / 'web' / 'app.js').read_text()
        self.assertIn('name.textContent = booking.student', script)
        self.assertNotIn('innerHTML', script)


class LifecycleTests(unittest.TestCase):
    def command(self, *args):
        return subprocess.run([sys.executable, str(app.ROOT / 'app.py'), *map(str, args)],
                              text=True, capture_output=True, timeout=10)

    def start(self, data):
        process = subprocess.Popen([sys.executable, str(app.ROOT / 'app.py'), 'serve', '--port', '0', '--data', str(data)],
                                   text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        line = process.stdout.readline()
        self.assertIn('http://127.0.0.1:', line)
        return process, line.split(' ')[2]

    def stop(self, process):
        process.send_signal(signal.SIGINT)
        stdout, stderr = process.communicate(timeout=10)
        self.assertEqual(0, process.returncode, stderr)

    def test_actual_process_restart_and_maintenance_lock(self):
        with tempfile.TemporaryDirectory() as folder:
            data = Path(folder) / 'data.json'
            process, url = self.start(data)
            try:
                request = urllib.request.Request(url + '/api/bookings',
                    json.dumps(dict(student='Restart synthetic', date='2026-11-01', slot='09:00', request_id='restart')).encode(),
                    {'X-Teacher': 'anna'}, method='POST')
                with urllib.request.urlopen(request) as response:
                    first = json.loads(response.read())['booking']
                locked = self.command('backup', '--data', data, '--output', Path(folder) / 'blocked.json')
                self.assertEqual(1, locked.returncode)
                self.assertIn('Data is in use', locked.stderr)
            finally:
                self.stop(process)
            process, url = self.start(data)
            try:
                request = urllib.request.Request(url + '/api/bookings/' + first['id'], headers={'X-Teacher': 'anna'})
                with urllib.request.urlopen(request) as response:
                    self.assertEqual(first, json.loads(response.read())['booking'])
            finally:
                self.stop(process)

    def test_backup_export_restore_retire_on_disposable_copy(self):
        with tempfile.TemporaryDirectory() as folder:
            data, restored = Path(folder) / 'original.json', Path(folder) / 'restored.json'
            store = app.Store(data)
            booking, _ = store.create('boris', dict(student='Recovery synthetic', date='2026-12-01', slot='08:00', request_id='restore-me'))
            backup, exported = Path(folder) / 'backup.json', Path(folder) / 'export.json'
            self.assertEqual(0, self.command('backup', '--data', data, '--output', backup).returncode)
            self.assertEqual(0, self.command('export', '--data', data, '--output', exported).returncode)
            self.assertEqual(json.loads(backup.read_text()), json.loads(exported.read_text()))
            app.Store(restored).create('anna', dict(student='Before restore', date='2026-12-02', slot='09:00', request_id='old'))
            self.assertEqual(0, self.command('restore', '--data', restored, '--input', backup).returncode)
            self.assertEqual([booking], app.Store(restored).list('boris'))
            self.assertEqual(1, len(list(Path(folder).glob('restored.json.before-restore-*.json'))))
            replay, created = app.Store(restored).create('boris', dict(student='Recovery synthetic', date='2026-12-01', slot='08:00', request_id='restore-me'))
            self.assertFalse(created)
            self.assertEqual(booking, replay)
            retirement = Path(folder) / 'retired-export.json'
            self.assertEqual(0, self.command('retire', '--data', restored, '--output', retirement).returncode)
            denied = self.command('serve', '--port', '0', '--data', restored)
            self.assertEqual(1, denied.returncode)
            self.assertIn('retired', denied.stderr)
            self.assertTrue(restored.exists())
            self.assertEqual([booking], json.loads(retirement.read_text())['bookings'])
            self.assertEqual(0, self.command('resume', '--data', restored).returncode)
            process, _ = self.start(restored)
            self.stop(process)

    def test_corrupt_restore_rejected_without_touching_data(self):
        with tempfile.TemporaryDirectory() as folder:
            data, corrupt = Path(folder) / 'data.json', Path(folder) / 'corrupt.json'
            app.Store(data)
            before = data.read_bytes()
            corrupt.write_text('{"version":1,"bookings":[{"teacher":"admin"}]}')
            self.assertEqual(1, self.command('restore', '--data', data, '--input', corrupt).returncode)
            self.assertEqual(before, data.read_bytes())

    def test_existing_files_preserved(self):
        record = json.loads((app.ROOT / '.playbook-artifacts' / 'preserved-baseline.json').read_text())
        for filename, expected in record.items():
            with self.subTest(filename=filename):
                self.assertEqual(expected, hashlib.sha256((app.ROOT / filename).read_bytes()).hexdigest())


if __name__ == '__main__':
    unittest.main(verbosity=2)
