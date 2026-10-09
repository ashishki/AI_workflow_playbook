"""Real rename/fsync and CLI regressions; selectable frozen app for RED evidence."""
import importlib.util
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from unittest import mock

APP_PATH = Path(os.environ.get('BOOKING_APP_PATH', Path(__file__).with_name('app.py'))).resolve()
spec = importlib.util.spec_from_file_location('correction_target', APP_PATH)
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)


class PersistenceCorrectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / 'bookings.json'
        self.server = app.BookingServer(('127.0.0.1', 0), app.Handler)
        self.server.store = app.Store(self.path)
        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.start()
        self.url = f'http://127.0.0.1:{self.server.server_port}/api/bookings'

    def tearDown(self):
        self.server.shutdown()
        self.thread.join()
        self.server.server_close()
        self.temp.cleanup()

    def request(self, request_id=None, slot='09:00', booking_id=None):
        body = None if request_id is None else json.dumps(dict(student='Fault synthetic', date='2026-11-20', slot=slot, request_id=request_id)).encode()
        request = urllib.request.Request(self.url + ('/' + booking_id if booking_id else ''), body,
                                         {'X-Teacher': 'anna'}, method='GET' if body is None else 'POST')
        try:
            response = urllib.request.urlopen(request, timeout=5)
        except urllib.error.HTTPError as error:
            response = error
        with response:
            return response.status, json.loads(response.read())

    def one_directory_fsync_failure(self):
        real_fsync, fired = app.os.fsync, [False]
        def fail_once(fd):
            if stat.S_ISDIR(os.fstat(fd).st_mode) and not fired[0]:
                fired[0] = True
                raise OSError('one-shot directory fsync after real rename')
            return real_fsync(fd)
        return mock.patch.object(app.os, 'fsync', side_effect=fail_once)

    def test_post_rename_fault_replay_and_other_request_preserve_both(self):
        with self.one_directory_fsync_failure():
            status, error = self.request('first')
        self.assertEqual(503, status)
        disk_first = json.loads(self.path.read_text())['bookings'][0]
        self.assertEqual('first', disk_first['request_id'])  # The real rename happened.
        self.assertIn('неопредел', error['error'].lower())
        status, replay = self.request('first')
        self.assertEqual(200, status)
        self.assertTrue(replay['replayed'])
        self.assertEqual(disk_first, replay['booking'])
        self.assertEqual(201, self.request('second', '09:30')[0])
        self.assertEqual({'first', 'second'}, {b['request_id'] for b in json.loads(self.path.read_text())['bookings']})

    def test_post_rename_fault_next_other_request_does_not_erase_commit(self):
        with self.one_directory_fsync_failure():
            self.assertEqual(503, self.request('first')[0])
        first = json.loads(self.path.read_text())['bookings'][0]
        self.assertEqual(201, self.request('second', '09:30')[0])
        saved = json.loads(self.path.read_text())['bookings']
        self.assertIn(first, saved)
        self.assertEqual(2, len(saved))

    def test_precommit_failure_reloads_old_disk_then_allows_retry(self):
        self.assertEqual(201, self.request('existing')[0])
        before = self.path.read_bytes()
        with mock.patch.object(app.os, 'replace', side_effect=OSError('precommit rename failure')):
            self.assertEqual(503, self.request('new', '09:30')[0])
        self.assertEqual(before, self.path.read_bytes())
        self.assertEqual(1, len(self.request()[1]['bookings']))
        self.assertEqual(201, self.request('new', '09:30')[0])
        self.assertEqual(2, len(json.loads(self.path.read_text())['bookings']))

    def test_reload_failure_blocks_all_reads_and_writes_until_reopen(self):
        with self.one_directory_fsync_failure(), mock.patch.object(app.Path, 'read_text', side_effect=OSError('disk reload unavailable')):
            self.assertEqual(503, self.request('committed')[0])
        committed = self.path.read_bytes()
        booking = json.loads(committed)['bookings'][0]
        self.assertEqual(503, self.request()[0])
        self.assertEqual(503, self.request(booking_id=booking['id'])[0])
        self.assertEqual(503, self.request('later', '09:30')[0])
        self.assertEqual(committed, self.path.read_bytes())
        self.server.store = app.Store(self.path)  # Explicit reopen after recovery.
        self.assertEqual(200, self.request('committed')[0])
        self.assertEqual(201, self.request('later', '09:30')[0])

    def test_invalid_reload_document_also_fails_closed(self):
        actual_atomic = app.atomic_json
        def corrupt_after_replace(path, document):
            actual_atomic(path, document)
            Path(path).write_text('{"version":1,"bookings":"corrupted"}')
            raise OSError('write failed and actual disk invalid')
        with mock.patch.object(app, 'atomic_json', side_effect=corrupt_after_replace):
            self.assertEqual(503, self.request('first')[0])
        before = self.path.read_bytes()
        self.assertEqual(503, self.request()[0])
        self.assertEqual(503, self.request('second', '09:30')[0])
        self.assertEqual(before, self.path.read_bytes())


class LifecyclePathCorrectionTests(unittest.TestCase):
    def test_real_cli_reserved_symlink_target_rejected_without_changes(self):
        for suffix in ('.retired', '.lock'):
            with self.subTest(suffix=suffix), tempfile.TemporaryDirectory() as folder:
                data = Path(folder) / 'data.json'
                app.Store(data)
                metadata = Path(str(data) + suffix)
                target = Path(folder) / 'dangling-target.json'
                metadata.symlink_to(target)
                before_data, before_paths = data.read_bytes(), set(Path(folder).iterdir())
                result = subprocess.run([sys.executable, str(APP_PATH), 'retire', '--data', str(data), '--output', str(metadata)],
                                        text=True, capture_output=True, timeout=10)
                self.assertNotEqual(0, result.returncode)
                self.assertIn('reserved', result.stderr.lower())
                self.assertEqual(before_paths, set(Path(folder).iterdir()))
                self.assertEqual(before_data, data.read_bytes())
                self.assertEqual(target, metadata.readlink())
                self.assertFalse(target.exists())

    def test_real_cli_rejects_all_reserved_paths_before_mutation(self):
        for command in ('export', 'backup', 'retire'):
            for suffix in ('.retired', '.lock', '.before-restore-future.json'):
                with self.subTest(command=command, suffix=suffix), tempfile.TemporaryDirectory() as folder:
                    data = Path(folder) / 'data.json'
                    app.Store(data)
                    output = Path(str(data) + suffix)
                    before = {str(p): p.read_bytes() for p in Path(folder).iterdir() if p.is_file()}
                    result = subprocess.run([sys.executable, str(APP_PATH), command, '--data', str(data), '--output', str(output)],
                                            text=True, capture_output=True, timeout=10)
                    self.assertNotEqual(0, result.returncode, result.stdout)
                    self.assertIn('reserved', result.stderr.lower())
                    after = {str(p): p.read_bytes() for p in Path(folder).iterdir() if p.is_file()}
                    self.assertEqual(before, after)  # No new lock/marker/export or changed bytes.

    def test_real_cli_reserved_existing_marker_bytes_preserved(self):
        with tempfile.TemporaryDirectory() as folder:
            data = Path(folder) / 'data.json'
            app.Store(data)
            marker = Path(str(data) + '.retired')
            marker.write_bytes(b'keep this existing retirement marker\n')
            before = {p.name: p.read_bytes() for p in Path(folder).iterdir()}
            result = subprocess.run([sys.executable, str(APP_PATH), 'retire', '--data', str(data), '--output', str(marker)],
                                    text=True, capture_output=True, timeout=10)
            self.assertNotEqual(0, result.returncode)
            self.assertIn('reserved', result.stderr.lower())
            self.assertEqual(before, {p.name: p.read_bytes() for p in Path(folder).iterdir()})


if __name__ == '__main__':
    unittest.main(verbosity=2)
