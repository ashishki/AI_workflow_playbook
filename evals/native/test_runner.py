"""Harness failure handling only. Fake CLI output is NEVER a model evaluation."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / 'evals/native/run.py'


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='native-runner-test-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.bin = self.root / 'bin'
        self.bin.mkdir()
        cli = self.bin / 'codex'
        cli.write_text('''#!/usr/bin/env python3
import json, os, sys, time
from pathlib import Path
if '--version' in sys.argv:
 print('FAKE CLI FOR HARNESS UNIT TESTS'); raise SystemExit
sys.stdin.read()
mode=os.environ['NATIVE_HARNESS_TEST_MODE']
if mode=='timeout':
 print(json.dumps({'type':'thread.started','thread_id':'fake-test'}),flush=True)
 time.sleep(30)
elif mode=='missing-completion':
 print(json.dumps({'type':'turn.failed','error':{'message':'synthetic failure'}}))
elif mode=='bad-json':
 print('broken-event')
 print(json.dumps({'type':'turn.completed','usage':{}}))
else:
 Path(sys.argv[sys.argv.index('-o')+1]).write_text('Harness test, not an agent result.')
 print(json.dumps({'type':'turn.completed','usage':{}}))
''')
        cli.chmod(0o755)

    def run_trial(self, mode, out=None):
        out = out or self.root / 'trial'
        env = dict(os.environ, PATH=str(self.bin) + os.pathsep + os.environ['PATH'],
                   NATIVE_HARNESS_TEST_MODE=mode)
        result = subprocess.run([sys.executable, str(RUNNER), '--case', 'plan',
                                 '--condition', 'native', '--output', str(out),
                                 '--timeout', '1'], env=env, capture_output=True,
                                text=True, timeout=12)
        return result, out

    def test_existing_evidence_cannot_be_overwritten(self):
        out = self.root / 'existing'
        out.mkdir()
        sentinel = out / 'events.jsonl'
        sentinel.write_bytes(b'original evidence\n')
        result, _ = self.run_trial('success', out)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(sentinel.read_bytes(), b'original evidence\n')
        self.assertFalse((out / 'workspace').exists())

    def test_process_exit_zero_is_not_task_completion(self):
        result, out = self.run_trial('missing-completion')
        self.assertNotEqual(result.returncode, 0)
        summary = json.loads((out / 'summary.json').read_text())
        self.assertEqual(summary['exit_code'], 0)
        self.assertFalse(summary['turn_completed'])
        self.assertTrue((out / 'events.jsonl').read_text())

    def test_timeout_preserves_partial_evidence(self):
        result, out = self.run_trial('timeout')
        self.assertNotEqual(result.returncode, 0)
        summary = json.loads((out / 'summary.json').read_text())
        self.assertTrue(summary['timed_out'])
        self.assertFalse(summary['turn_completed'])
        self.assertTrue((out / 'events.jsonl').read_text())

    def test_success_captures_unchanged_fixture_and_package(self):
        result, out = self.run_trial('success')
        self.assertEqual(result.returncode, 0, result.stderr)
        meta = json.loads((out / 'metadata.json').read_text())
        summary = json.loads((out / 'summary.json').read_text())
        self.assertEqual(meta['fixture_before'], summary['fixture_after'])
        self.assertTrue(meta['source_hashes'])
        self.assertIn('FAKE CLI', meta['codex_version'])

    def test_corrupt_event_stream_cannot_pass(self):
        result, out = self.run_trial('bad-json')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(json.loads((out / 'summary.json').read_text())['event_parse_errors'], 1)


if __name__ == '__main__':
    unittest.main()
