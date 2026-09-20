"""Real archive integration; not a real Codex session or human transfer trial."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[2]
STAGES = ('discover', 'decide', 'design', 'build', 'verify', 'introduce', 'observe',
          'change', 'diagnose', 'recover', 'transfer', 'grow', 'retire')

class DeliveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # No mocks: CI uses the actual existing builder and canonical helper sources.
        sys.path.insert(0, str(ROOT/'distribution/native'))
        spec = importlib.util.spec_from_file_location('vnext_native_build', ROOT/'distribution/native/build.py')
        cls.builder = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.builder)
        cls.tmp = tempfile.TemporaryDirectory(prefix='playbook-vnext-delivery-')
        cls.addClassCleanup(cls.tmp.cleanup)
        cls.base = Path(cls.tmp.name)
        result = cls.builder.build(cls.base/'archive')
        cls.zip_path = Path(result['archive'])
        with zipfile.ZipFile(cls.zip_path) as z:
            cls.names = z.namelist()
            z.extractall(cls.base/'Проверка передачи с пробелами')
        cls.kit = cls.base/'Проверка передачи с пробелами/Playbook'
        cls.project = cls.kit/'Мой проект'
        cls.skill = cls.project/'.agents/skills/playbook'

    def test_full_lifecycle_and_exact_shared_helpers_are_delivered(self):
        catalog = json.loads((self.skill/'assets/lifecycle.json').read_text(encoding='utf-8'))
        self.assertEqual(catalog['order'], list(STAGES))
        for stage in STAGES:
            ref = self.skill/'references/lifecycle'/f'{stage}.md'
            self.assertTrue(ref.is_file())
            self.assertEqual(ref.read_bytes(), (ROOT/'plugins/playbook-native/skills/playbook/references/lifecycle'/f'{stage}.md').read_bytes())
        for name in ('solution_record.py', 'run_codex_role.py', 'codex_role_run_lib.py'):
            self.assertEqual((self.skill/'scripts'/name).read_bytes(), (ROOT/'tools'/name).read_bytes())
        self.assertFalse(any('/engineering/' in x or '/companion/' in x or '/reports/' in x for x in self.names))

    def test_packaged_helper_supports_new_session_then_detects_changed_record(self):
        with tempfile.TemporaryDirectory(prefix='playbook-handoff-') as tmp:
            project = Path(tmp)/'Рабочий процесс'
            project.mkdir()
            record = json.loads((self.skill/'assets/solution-record.example.json').read_text(encoding='utf-8'))
            record['decision'] = {'kind':'process_change', 'reason':'Synthetic mechanism test, not live benefit'}
            path = project/'solution.json'
            path.write_text(json.dumps(record, ensure_ascii=False), encoding='utf-8')
            (project/'rules.txt').write_text('Every open request has a next action.', encoding='utf-8')
            helper = self.skill/'scripts/solution_record.py'
            def run(*args):
                return subprocess.run([sys.executable, str(helper), '--root', str(project), *args],
                    cwd=self.base, capture_output=True, text=True, encoding='utf-8',
                    env={**os.environ, 'PYTHONIOENCODING':'utf-8'}, timeout=30)
            result = run('snapshot', '--record', 'solution.json', '--files', 'rules.txt', '--output', 'snapshot.json')
            self.assertEqual(result.returncode, 0, result.stderr)
            before = path.read_bytes()
            result = run('handoff', '--record', 'solution.json', '--snapshot', 'snapshot.json')
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('Состояние рабочего решения', result.stdout)
            self.assertEqual(path.read_bytes(), before)
            record['next_step'] = 'A new real rule must be checked.'
            path.write_text(json.dumps(record, ensure_ascii=False), encoding='utf-8')
            result = run('handoff', '--record', 'solution.json', '--snapshot', 'snapshot.json')
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertEqual(json.loads(result.stdout)['status'], 'stale')
            self.assertNotIn('Состояние рабочего решения', result.stdout)

if __name__ == '__main__':
    unittest.main()
