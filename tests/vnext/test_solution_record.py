"""Actual helper tests; fixtures are not model/user evidence."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / 'tools' / 'solution_record.py'
spec = importlib.util.spec_from_file_location('solution_record', SCRIPT)
record = importlib.util.module_from_spec(spec)
spec.loader.exec_module(record)


def fixture():
    return {
        'schema_version': 'playbook.solution.v1',
        'problem': 'Теряются следующие действия по заявкам',
        'owner': 'Владелец тестового процесса',
        'decision': {'kind': 'process_change', 'reason': 'Достаточно согласовать правило'},
        'rules': ['У каждой открытой заявки есть следующее действие'],
        'state': {'technical': 'not_checked', 'in_use': 'not_observed', 'effect': 'unknown'},
        'data': {'locations': ['Тестовые данные'], 'access': ['Владелец'], 'sensitive': True},
        'operations': {'open': 'Открыть тестовую таблицу', 'fallback': 'Ручная проверка',
                       'diagnose': 'Проверить сохранение', 'recover': 'Восстановить проверенную копию',
                       'transfer': 'Передать владельцу права отдельно', 'retire': 'Экспорт и отзыв доступа'},
        'checks': [{'claim': 'Следующее действие сохраняется', 'status': 'not_run', 'evidence': []}],
        'observations': [], 'interventions': [], 'costs': [], 'open_issues': [],
        'next_step': 'Проверить на разрешённых примерах',
    }


class RecordTests(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory(); self.addCleanup(self.t.cleanup)
        self.root = Path(self.t.name)
        self.file = self.root / 'solution.json'
        self.write_record()
        (self.root / 'app.py').write_text('value = 1\n')

    def write_record(self, data=None):
        self.file.write_text(json.dumps(data or fixture(), ensure_ascii=False), encoding='utf-8')

    def cli(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), '--root', str(self.root), *args],
                              text=True, capture_output=True, encoding='utf-8',
                              env={**os.environ, 'PYTHONIOENCODING':'utf-8'}, timeout=30)

    def test_valid_does_not_mean_working(self):
        result = self.cli('check', '--record', 'solution.json')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['status'], 'schema_valid')
        self.assertNotIn('release_ready', result.stdout)

    def test_no_build_is_a_first_class_decision(self):
        for kind in ('no_change', 'process_change', 'configure', 'template', 'automation', 'code', 'ai'):
            data = fixture(); data['decision']['kind'] = kind
            self.assertEqual(record.validate(data), [])

    def test_bad_record_and_forged_check_rejected(self):
        data = fixture(); data['checks'][0]['status'] = 'passed'
        self.assertTrue(record.validate(data))
        data = fixture(); data['decision']['kind'] = 'auto_approve'
        self.assertTrue(record.validate(data))
        self.assertTrue(record.validate({'schema_version': 'made-up'}))
        self.assertTrue(record.validate([]))

    def test_passed_requires_evidence_but_evidence_is_not_attestation(self):
        data = fixture(); data['checks'][0].update(status='passed', evidence=['tests/result.txt'])
        self.assertEqual(record.validate(data), [])
        text = record.render(data)
        self.assertIn('не независимое подтверждение', text)

    def test_snapshot_is_valid_then_stale_after_source_change(self):
        result = self.cli('snapshot', '--record', 'solution.json', '--files', 'app.py', '--output', 'proof.json')
        self.assertEqual(result.returncode, 0, result.stderr)
        result = self.cli('verify', '--snapshot', 'proof.json')
        self.assertEqual(result.returncode, 0, result.stderr)
        (self.root / 'app.py').write_text('value = 2\n')
        result = self.cli('verify', '--snapshot', 'proof.json')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('stale', result.stdout)

    def test_record_change_stales_handoff(self):
        self.assertEqual(self.cli('snapshot', '--record', 'solution.json', '--files', 'app.py', '--output', 'proof.json').returncode, 0)
        d = fixture(); d['rules'].append('Новое правило'); self.write_record(d)
        self.assertNotEqual(self.cli('handoff', '--record', 'solution.json', '--snapshot', 'proof.json').returncode, 0)

    def test_missing_file_and_empty_or_malformed_snapshot_fail(self):
        for invalid in ({}, {'schema_version': 'playbook.snapshot.v1', 'files': {}},
                        {'schema_version': 'playbook.snapshot.v1', 'record': 'solution.json', 'files': {'solution.json': 'x'}}):
            (self.root/'proof.json').write_text(json.dumps(invalid))
            self.assertNotEqual(self.cli('verify', '--snapshot', 'proof.json').returncode, 0)
        self.assertNotEqual(self.cli('snapshot', '--record', 'solution.json', '--files', 'missing.py', '--output', 'proof.json').returncode, 0)

    def test_no_overwrite_including_existing_empty_output(self):
        (self.root / 'proof.json').write_text('user content')
        self.assertNotEqual(self.cli('snapshot', '--record', 'solution.json', '--files', 'app.py', '--output', 'proof.json').returncode, 0)
        self.assertEqual((self.root / 'proof.json').read_text(), 'user content')

    def test_path_escape_absolute_and_secret_paths_denied(self):
        for path in ('../outside', '/etc/passwd', '.env', '.git/config', 'auth.json', 'secrets/key.txt', 'key.pem', 'x\\..\\secret'):
            with self.subTest(path=path):
                self.assertNotEqual(self.cli('snapshot', '--record', 'solution.json', '--files', path, '--output', 'proof.json').returncode, 0)
        self.assertFalse((self.root/'proof.json').exists())

    def test_symlink_file_and_parent_denied(self):
        try:
            (self.root/'alias').symlink_to(self.root/'app.py')
            (self.root/'dirlink').symlink_to(self.root, target_is_directory=True)
        except OSError:
            self.skipTest('OS does not permit symlinks')
        for p in ('alias', 'dirlink/app.py'):
            self.assertNotEqual(self.cli('snapshot', '--record', 'solution.json', '--files', p, '--output', 'proof.json').returncode, 0)
        self.assertNotEqual(self.cli('snapshot', '--record', 'solution.json', '--files', 'app.py', '--output', 'dirlink/new.json').returncode, 0)

    def test_handoff_for_new_session_has_no_source_bytes(self):
        (self.root/'app.py').write_text('private_value_not_for_export = 1\n')
        self.assertEqual(self.cli('snapshot', '--record', 'solution.json', '--files', 'app.py', '--output', 'proof.json').returncode, 0)
        result = self.cli('handoff', '--record', 'solution.json', '--snapshot', 'proof.json')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('Теряются', result.stdout)
        self.assertIn('not_checked', result.stdout)
        self.assertNotIn('private_value_not_for_export', result.stdout)
        self.assertIn('не разрешение', result.stdout)

    def test_unknown_cost_not_zero(self):
        data = fixture(); data['costs'] = [{'label':'AI', 'amount': None, 'unit':'USD'}]
        self.assertEqual(record.validate(data), [])
        self.assertIn('неизвестно', record.render(data))

    def test_interventions_and_observations_are_not_fake_success(self):
        data = fixture()
        data['observations'] = [{'metric':'minutes', 'before': 20, 'after': None, 'evidence': []}]
        data['interventions'] = [{'stage':'decide', 'reason':'Неясное правило', 'actor':'owner', 'minutes':10}]
        self.assertEqual(record.validate(data), [])
        text = record.render(data)
        self.assertIn('Неясное правило', text)
        self.assertIn('неизвестно', text)

    def test_oversized_json_denied_without_writing(self):
        self.file.write_bytes(b' ' * (record.MAX_JSON_BYTES + 1))
        self.assertNotEqual(self.cli('check', '--record', 'solution.json').returncode, 0)

    def test_handoff_requires_record_in_snapshot(self):
        self.assertEqual(self.cli('snapshot', '--record', 'solution.json', '--files', 'app.py', '--output', 'proof.json').returncode, 0)
        proof = json.loads((self.root/'proof.json').read_text()); proof['files'].pop('solution.json')
        (self.root/'proof.json').write_text(json.dumps(proof))
        self.assertNotEqual(self.cli('handoff', '--record', 'solution.json', '--snapshot', 'proof.json').returncode, 0)

    def test_cli_is_read_only_except_named_snapshot(self):
        before = {p.name:p.read_bytes() for p in self.root.iterdir()}
        self.cli('check', '--record', 'solution.json'); self.cli('summary', '--record', 'solution.json')
        after = {p.name:p.read_bytes() for p in self.root.iterdir()}
        self.assertEqual(before, after)

    def test_positive_state_cannot_hide_unrun_or_blocked_checks(self):
        d = fixture(); d['state']['technical'] = 'checked'
        self.assertTrue(record.validate(d))
        d['checks'][0].update(status='passed', evidence=['result.txt'])
        self.assertEqual(record.validate(d), [])
        d['checks'].append({'claim':'external', 'status':'blocked', 'evidence':[]})
        self.assertTrue(record.validate(d))

    def test_effect_requires_observation_not_author_optimism(self):
        d = fixture(); d['state']['effect'] = 'improved'
        self.assertTrue(record.validate(d))
        d['observations'] = [{'metric':'minutes', 'before':20, 'after':15, 'evidence':['observation.txt']}]
        self.assertEqual(record.validate(d), [])

    def test_duplicate_json_and_nonfinite_values_are_rejected(self):
        for text in ('{"schema_version":"x","schema_version":"y"}', '{"cost":NaN}'):
            self.file.write_text(text)
            self.assertNotEqual(self.cli('check', '--record', 'solution.json').returncode, 0)

    def test_selected_file_limit(self):
        with self.assertRaises(record.RecordError):
            record.snapshot(self.root, 'solution.json', [f'f{i}.txt' for i in range(record.MAX_FILES+1)])

if __name__ == '__main__': unittest.main()
