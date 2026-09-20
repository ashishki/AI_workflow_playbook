"""Portable Native profile of the actual Role Runner, with an explicit fake CLI."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / 'plugins/playbook-native/skills/playbook/scripts/run_codex_role.py'


class NativeReviewTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix='playbook-review-test-')
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.project = self.root / 'Проект с пробелами'
        self.project.mkdir()
        (self.project / 'app.py').write_text('answer = 42\n')
        (self.project / 'данные.txt').write_text('Пользовательский файл\n', encoding='utf-8')
        (self.project / '.playbook-artifacts').mkdir()
        self.request = self.project / '.playbook-artifacts/request.md'
        self.request.write_text('Check that answer remains 42. Do not edit files.')
        fake = self.root / 'fake_codex.py'
        fake.write_text('''import json, os, sys, time
from pathlib import Path
if sys.argv[1:] == ['--version']:
 print('FAKE codex for portable runner tests'); raise SystemExit
assert 'CODEX_THREAD_ID' not in os.environ
assert os.environ['PLAYBOOK_REVIEW_WORKER'] == '1'
assert sys.argv[sys.argv.index('--sandbox')+1] == 'read-only'
assert '--model' not in sys.argv
assert not any('model_reasoning_effort=' in arg for arg in sys.argv)
prompt = sys.stdin.read()
assert 'Check that answer remains 42' in prompt
mode = os.environ.get('PLAYBOOK_FAKE_REVIEW', 'pass')
if mode == 'timeout':
 print(json.dumps({'type':'thread.started'}),flush=True); time.sleep(30)
if mode == 'mutate': Path('app.py').write_text('answer = 0\\n')
marker = next(m for m in ['PRODUCT_DESIGN_REVIEW','PROGRAM_DESIGN_REVIEW','SLICE_REVIEW','MAINTAINABILITY_REVIEW'] if m in prompt)
report = 'No marker' if mode == 'marker' else marker + ': PASS\\nFAKE review, not a model evaluation.'
Path(sys.argv[sys.argv.index('--output-last-message')+1]).write_text(report)
if mode == 'corrupt': print('not-json')
print(json.dumps({'type':'thread.started' if mode == 'incomplete' else 'turn.completed','usage':{'input_tokens':20,'output_tokens':10}}))
''')
        if os.name == 'nt':
            self.cli = self.root / 'fake-codex.cmd'
            self.cli.write_text(f'@"{sys.executable}" "{fake}" %*\n')
        else:
            self.cli = self.root / 'fake-codex'
            self.cli.write_text(f'#!{sys.executable}\n' + fake.read_text())
            self.cli.chmod(0o755)

    def run_review(self, mode='pass', role='slice_review'):
        return subprocess.run([
            sys.executable, '-B', str(RUNNER), 'run', '--profile', 'native',
            '--root', str(self.project), '--task', 'example', '--role', role,
            '--request', str(self.request), '--codex-bin', str(self.cli),
            '--run-id', role + '-' + mode, '--timeout-seconds', '1' if mode == 'timeout' else '10',
        ], env={**os.environ, 'PLAYBOOK_FAKE_REVIEW': mode, 'CODEX_THREAD_ID': 'parent-test'},
            capture_output=True, text=True, timeout=18)

    def verify(self, path):
        return subprocess.run([sys.executable, '-B', str(RUNNER), 'verify', '--root',
                               str(self.project), '--result', str(path)],
                              capture_output=True, text=True, timeout=10)

    def test_all_roles_work_without_git_or_governance_files(self):
        for role in ('slice_review', 'maintainability_review', 'program_design_review', 'product_design_review'):
            with self.subTest(role=role):
                result = self.run_review(role=role)
                self.assertEqual(result.returncode, 0, result.stderr)
                payload = json.loads(result.stdout)
                self.assertEqual(payload['status'], 'validated')
                self.assertEqual(self.verify(payload['result']).returncode, 0)
                record = json.loads(Path(payload['result']).read_text())
                self.assertIsNone(record['base_commit'])
                self.assertEqual(record['codex']['reasoning_effort'], 'inherit')
        self.assertFalse((self.project / '.git').exists())
        self.assertEqual((self.project / 'app.py').read_text(), 'answer = 42\n')

    def test_source_change_invalidates_saved_review_without_a_commit(self):
        result = self.run_review()
        self.assertEqual(result.returncode, 0, result.stderr)
        (self.project / 'app.py').write_text('answer = 41\n')
        checked = self.verify(json.loads(result.stdout)['result'])
        self.assertNotEqual(checked.returncode, 0)
        self.assertIn('stale', checked.stderr)

    def test_missing_completion_corruption_marker_and_timeout_cannot_pass(self):
        for mode in ('incomplete', 'corrupt', 'marker', 'timeout'):
            with self.subTest(mode=mode):
                result = self.run_review(mode)
                self.assertNotEqual(result.returncode, 0)
                self.assertNotEqual(json.loads(result.stdout)['status'], 'validated')

    def test_reviewer_write_drift_is_reported(self):
        result = self.run_review('mutate')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('changed repository files', result.stdout)

    def test_evidence_cannot_be_overwritten(self):
        first = self.run_review()
        self.assertEqual(first.returncode, 0, first.stderr)
        path = Path(json.loads(first.stdout)['result'])
        before = path.read_bytes()
        self.assertNotEqual(self.run_review().returncode, 0)
        self.assertEqual(path.read_bytes(), before)

    def test_packaged_engine_matches_canonical_runner(self):
        for name in ('run_codex_role.py', 'codex_role_run_lib.py'):
            self.assertEqual((RUNNER.parent / name).read_bytes(), (ROOT / 'tools' / name).read_bytes())


if __name__ == '__main__':
    unittest.main()
