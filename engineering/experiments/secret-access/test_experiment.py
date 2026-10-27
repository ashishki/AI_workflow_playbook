"""Mechanism regressions. They do not test a live provider or model."""
from __future__ import annotations
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('secret_access_experiment', HERE / 'experiment.py')
e = importlib.util.module_from_spec(spec)
spec.loader.exec_module(e)


class ExperimentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve() / 'run'
        e.prepare(self.root, head='a' * 40, model='test-model', host='test-host')

    def observations(self):
        return e.read_json(self.root / 'observations.json')

    def save(self, value):
        (self.root / 'observations.json').write_bytes(e.dump(value))

    def complete_simulated_records(self):
        # Schema-only simulation; never publish this as observed effectiveness.
        obs = self.observations()
        obs.update(experiment_cost_usd=9, experiment_cost_basis='provider_reported')
        obs['frozen_conditions'] = {'baseline_id': 'baseline', 'settings_id': 'settings',
            'permission_scope': 'synthetic-only', 'budget': {'per_run_wall_seconds': 300, 'total_cost_usd': 100},
            'current_workflow_observed': True}
        for row in obs['runs']:
            rid = row['id']
            receipt = self.root / rid / 'simulated-adjudication.txt'
            receipt.write_text('SIMULATED TEST DATA; not real evidence', encoding='utf-8')
            row.update(execution='real_agent', model='test-model', host='test-host',
                       settings_id='settings', baseline_id='baseline', wall_seconds=100,
                       human_seconds={'A': 100, 'B': 50, 'C': 25}[rid[0]], cost_usd=1,
                       cost_basis='provider_reported', critical_failures=0)
            for case in row['cases'].values():
                case.update(status='PASS', evidence=[{'path': f'{rid}/{receipt.name}',
                                                      'sha256': e.sha(receipt.read_bytes())}])
        return obs

    def sign_simulated_review(self, obs):
        self.save(obs)
        fp = e.assess(self.root)['evidence_fingerprint']
        obs['review'] = {'reviewer': 'TEST ONLY', 'independent': True, 'fingerprint': fp}
        self.save(obs)

    def test_prepare_has_nine_runs_counterbalanced_and_no_live_claims(self):
        plan = e.read_json(self.root / 'plan.json')
        self.assertEqual(len(plan['runs']), 9)
        for slot in range(3):
            self.assertEqual({plan['order'][slot + 3 * t][0] for t in range(3)}, set('ABC'))
        self.assertFalse((self.root / 'A-1/METHOD_RU.md').exists())
        self.assertEqual((self.root / 'B-1/METHOD_RU.md').read_bytes(), (self.root / 'C-1/METHOD_RU.md').read_bytes())
        self.assertEqual((self.root / 'A-1/import-v1.env').read_bytes(), (self.root / 'C-1/import-v1.env').read_bytes())
        self.assertEqual(e.assess(self.root)['status_counts']['NOT_RUN'], 72)

    def test_existing_output_is_never_overwritten(self):
        with self.assertRaises(FileExistsError):
            e.prepare(self.root, head='a' * 40, model='m', host='h')

    def test_changed_fixture_blocks_checks(self):
        (self.root / 'B-1/probe.py').write_text('print("fake pass")')
        with self.assertRaises(e.ExperimentError): e.load(self.root)

    def test_symlink_escape_blocked(self):
        other = Path(self.temp.name).resolve() / 'other.json'; other.write_text('{}')
        link = self.root / 'escape.json'
        try: link.symlink_to(other)
        except OSError: self.skipTest('Symlinks unavailable for this OS user')
        with self.assertRaises(e.ExperimentError): e.safe_path(self.root, 'escape.json')

    def test_path_traversal_blocked(self):
        for path in ('../other.json', '/absolute', 'C:/other', 'a//b', 'a\\b'):
            with self.assertRaises(e.ExperimentError): e.safe_path(self.root, path)

    def test_duplicate_and_nan_json_rejected(self):
        p = self.root / 'bad.json'
        for text in ('{"x":1,"x":2}', '{"x":NaN}'):
            p.write_text(text)
            with self.assertRaises(e.ExperimentError): e.read_json(p)

    def test_pass_without_evidence_rejected(self):
        obs = self.observations(); obs['runs'][0]['cases']['setup']['status'] = 'PASS'; self.save(obs)
        with self.assertRaises(e.ExperimentError): e.assess(self.root)

    def test_real_negative_control_and_missing_key(self):
        receipt = e.smoke(self.root, 'B-1')
        self.assertEqual(receipt['status'], 'PASS')
        self.assertTrue(receipt['checks']['encoded']['synthetic_visible_in_output'])
        self.assertEqual(receipt['checks']['unrelated']['returncode'], 5)
        self.assertTrue((self.root / 'B-1/synthetic-leak.txt').is_file())
        self.assertEqual(e.assess(self.root)['status_counts']['NOT_RUN'], 72)
        with self.assertRaises(e.ExperimentError): e.smoke(self.root, 'B-1')

    def test_synthetic_application_loads_dotenv_without_overriding_injected_value(self):
        cwd = self.root / 'A-1'
        plan = e.read_json(self.root / 'plan.json')
        run = next(row for row in plan['runs'] if row['id'] == 'A-1')
        (cwd / '.env').write_bytes((cwd / 'import-v1.env').read_bytes())
        command = [sys.executable, str(cwd / 'synthetic_app.py'), '--expected', run['v1_sha256']]
        good = subprocess.run(command, cwd=cwd, env=e.clean_env(), capture_output=True)
        self.assertEqual(good.returncode, 0)
        self.assertTrue(json.loads(good.stdout)['ok'])
        bad_env = dict(e.clean_env(), PB_TEST_TOKEN='PB_SYNTH_' + '0' * 64)
        wrong = subprocess.run(command, cwd=cwd, env=bad_env, capture_output=True)
        self.assertEqual(wrong.returncode, 4)
        self.assertNotIn(bad_env['PB_TEST_TOKEN'].encode(), wrong.stdout + wrong.stderr)
        (cwd / '.env').write_text('PB_TEST_TOKEN=not-synthetic\n', encoding='utf-8')
        refused = subprocess.run(command, cwd=cwd, env=e.clean_env(), capture_output=True)
        self.assertEqual(refused.returncode, 3)
        self.assertNotIn(b'not-synthetic', refused.stdout + refused.stderr)

    def test_synthetic_application_injection_mode_has_no_dotenv_fallback(self):
        cwd = self.root / 'C-1'
        run = next(row for row in e.read_json(self.root / 'plan.json')['runs'] if row['id'] == 'C-1')
        token = (cwd / 'import-v1.env').read_text(encoding='utf-8').split('=', 1)[1].strip()
        (cwd / '.env').write_bytes((cwd / 'import-v1.env').read_bytes())
        command = [sys.executable, str(cwd / 'synthetic_app.py'), '--require-injected', '--expected', run['v1_sha256']]
        missing = subprocess.run(command, cwd=cwd, env=e.clean_env(), capture_output=True)
        self.assertEqual(missing.returncode, 3)
        invalid = subprocess.run(command, cwd=cwd, env=dict(e.clean_env(), PB_TEST_TOKEN='PB_SYNTH_' + '0' * 64), capture_output=True)
        self.assertEqual(invalid.returncode, 4)
        (cwd / '.env').write_text('PB_TEST_TOKEN=not-synthetic\n', encoding='utf-8')
        valid = subprocess.run(command, cwd=cwd, env=dict(e.clean_env(), PB_TEST_TOKEN=token), capture_output=True)
        self.assertEqual(valid.returncode, 0)
        self.assertTrue(json.loads(valid.stdout)['ok'])
        self.assertNotIn(token.encode(), valid.stdout + valid.stderr)

    def test_scan_checks_declared_files_without_exposing_values(self):
        e.smoke(self.root, 'C-1')
        result = e.scan(self.root, 'C-1', ['C-1/synthetic-leak.txt', 'C-1/offline-receipt.json'])
        self.assertEqual(result['status'], 'EXPOSURE_FOUND')
        self.assertNotIn('PB_SYNTH_', json.dumps(result))
        with self.assertRaises(e.ExperimentError): e.scan(self.root, 'C-1', ['../secrets'])

    def test_smoke_rejects_missing_negative_control_output(self):
        actual_execute = e.execute
        def suppress_raw(argv, *args, **kwargs):
            meta, out, err = actual_execute(argv, *args, **kwargs)
            return (meta, b'', b'') if argv[-2:] == ['--mode', 'raw'] else (meta, out, err)
        with patch.object(e, 'execute', side_effect=suppress_raw):
            self.assertEqual(e.smoke(self.root, 'B-1')['status'], 'FAIL')

    def test_smoke_rejects_missing_file_control(self):
        actual_execute = e.execute
        def remove_file(argv, cwd, *args, **kwargs):
            result = actual_execute(argv, cwd, *args, **kwargs)
            if argv[-2:] == ['--mode', 'file']:
                (cwd / 'synthetic-leak.txt').unlink()
            return result
        with patch.object(e, 'execute', side_effect=remove_file):
            self.assertEqual(e.smoke(self.root, 'B-1')['status'], 'FAIL')

    def test_smoke_rejects_exposure_in_normal_check(self):
        actual_execute = e.execute
        value = (self.root / 'B-1/import-v1.env').read_bytes().split(b'=', 1)[1].strip()
        def leak_on_check(argv, *args, **kwargs):
            meta, out, err = actual_execute(argv, *args, **kwargs)
            return (meta, out + value, err) if argv[-2:] == ['--mode', 'check'] else (meta, out, err)
        with patch.object(e, 'execute', side_effect=leak_on_check):
            self.assertEqual(e.smoke(self.root, 'B-1')['status'], 'FAIL')

    def test_smoke_rejects_incomplete_negative_control(self):
        actual_execute = e.execute
        def timeout_missing(argv, cwd, env, *args, **kwargs):
            meta, out, err = actual_execute(argv, cwd, env, *args, **kwargs)
            if 'PB_TEST_TOKEN' not in env:
                meta['status'] = 'timeout_or_output_limit'
            return meta, out, err
        with patch.object(e, 'execute', side_effect=timeout_missing):
            self.assertEqual(e.smoke(self.root, 'B-1')['status'], 'FAIL')

    def test_non_synthetic_token_is_not_printed(self):
        env = e.clean_env(); env['PB_TEST_TOKEN'] = 'not-a-synthetic-credential'
        meta, out, err = e.execute([sys.executable, str(HERE / 'probe.py'), '--expected', '0' * 64], self.root, env)
        self.assertNotEqual(meta['returncode'], 0)
        self.assertNotIn(b'not-a-synthetic-credential', out + err)

    def test_provider_plan_is_offline_scoped_and_non_destructive(self):
        with patch.object(e.subprocess, 'Popen', side_effect=AssertionError('no execution')):
            plan = e.provider_plan(self.root, 'C-1', sys.executable, 'disposable')
        self.assertTrue(plan['environment'].startswith('pbexp-'))
        serialized = json.dumps(plan)
        for forbidden in ('--overwrite', '--delete-source', '--prune', 'PB_SYNTH_'):
            self.assertNotIn(forbidden, serialized)
        self.assertIn('--dry-run', plan['commands']['preview_import'])
        self.assertIn('--skip-existing', plan['commands']['owner_confirmed_import'])
        with self.assertRaises(e.ExperimentError): e.provider_plan(self.root, 'A-1', sys.executable, 'p')

    def test_harness_suite_preparation_preserves_schedule_and_fixtures(self):
        output = Path(self.temp.name).resolve() / 'lab-suite'
        cmd = [sys.executable, str(HERE / 'lab_suite.py'), '--root', str(self.root), '--output', str(output)]
        prepared = subprocess.run(cmd, capture_output=True, text=True, check=False)
        self.assertEqual(prepared.returncode, 0)
        self.assertEqual(json.loads(prepared.stdout)['live_runs'], 0)
        schedule = e.read_json(output / 'schedule.json')
        plan = e.read_json(self.root / 'plan.json')
        self.assertEqual(schedule['order'], plan['order'])
        self.assertEqual(schedule['conditions']['A-1'], 'baseline')
        self.assertEqual(schedule['conditions']['C-1'], 'playbook')
        self.assertFalse((output / 'fixtures/A-1/METHOD_RU.md').exists())
        self.assertEqual((output / 'fixtures/B-1/METHOD_RU.md').read_bytes(),
                         (output / 'fixtures/C-1/METHOD_RU.md').read_bytes())
        self.assertEqual((output / 'fixtures/A-1/import-v1.env').read_bytes(),
                         (self.root / 'A-1/import-v1.env').read_bytes())
        self.assertNotEqual(subprocess.run(cmd, capture_output=True).returncode, 0)
        env = e.clean_env()
        env['PYTHONPATH'] = str(HERE.parents[2] / 'companion/ai_workflow_harness_lab/src')
        validated = subprocess.run([sys.executable, '-m', 'ai_workflow_harness_lab.cli',
                                    'validate-suite', str(output)], env=env, capture_output=True, text=True)
        self.assertEqual(validated.returncode, 0, validated.stderr)
        self.assertEqual(json.loads(validated.stdout)['tasks'], 9)
        self.assertEqual(subprocess.run(cmd + ['--check'], capture_output=True).returncode, 0)
        prompt = output / 'prompts/B-1.md'
        original = prompt.read_bytes()
        prompt.write_bytes(original + b'changed')
        self.assertNotEqual(subprocess.run(cmd + ['--check'], capture_output=True).returncode, 0)
        prompt.write_bytes(original)
        fixture = output / 'fixtures/C-1/METHOD_RU.md'
        fixture_original = fixture.read_bytes()
        fixture.write_bytes(b'changed')
        self.assertNotEqual(subprocess.run(cmd + ['--check'], capture_output=True).returncode, 0)
        fixture.write_bytes(fixture_original)
        (output / 'extra').mkdir()
        self.assertNotEqual(subprocess.run(cmd + ['--check'], capture_output=True).returncode, 0)
        (output / 'extra').rmdir()
        if hasattr(os, 'mkfifo'):
            os.mkfifo(output / 'fixtures/C-1/extra-pipe')
            self.assertNotEqual(subprocess.run(cmd + ['--check'], capture_output=True).returncode, 0)
            (output / 'fixtures/C-1/extra-pipe').unlink()
        self.assertEqual(subprocess.run(cmd + ['--check'], capture_output=True).returncode, 0)
        self.assertEqual(e.assess(self.root)['status_counts']['NOT_RUN'], 72)

    def test_provider_requires_consent_before_subprocess(self):
        with patch.object(e.subprocess, 'Popen', side_effect=AssertionError('no execution')):
            with self.assertRaises(e.ExperimentError):
                e.provider_smoke(self.root, 'C-1', sys.executable, 'disposable')

    def test_provider_version_mismatch_blocks(self):
        with patch.object(e, 'execute', return_value=({'returncode': 0}, b'0.10.20', b'')):
            with self.assertRaises(e.ExperimentError):
                e.provider_smoke(self.root, 'C-1', sys.executable, 'disposable', True)

    def test_fake_provider_success_not_empirical_evidence(self):
        meta = {'returncode': 0, 'status': 'completed', 'wall_seconds': 0.1}
        with patch.object(e, 'execute', side_effect=[(meta, b'relic 0.10.2', b''),
                                                   (meta, b'{"ok":true}', b''),
                                                   (meta, b'{"ok":true}', b'')]):
            result = e.provider_smoke(self.root, 'C-1', sys.executable, 'disposable', True)
        self.assertEqual(result['status'], 'PASS')
        self.assertTrue(all(v['decision'] == 'KEEP_EXPERIMENTAL' for v in e.assess(self.root)['comparisons'].values()))

    def test_exit_zero_with_error_json_is_failure(self):
        meta = {'returncode': 0, 'status': 'completed', 'wall_seconds': 0.1}
        with patch.object(e, 'execute', side_effect=[(meta, b'0.10.2', b''),
                (meta, b'{"ok":false}', b''), (meta, b'not valid JSON', b'')]):
            result = e.provider_smoke(self.root, 'C-1', sys.executable, 'disposable', True)
        self.assertEqual(result['status'], 'FAIL')

    def test_report_does_not_publish_inputs_or_promote_offline(self):
        out = Path(self.temp.name).resolve() / 'report'
        result = e.report(self.root, out)
        self.assertTrue(all(v['decision'] == 'KEEP_EXPERIMENTAL' for v in result['comparisons'].values()))
        published = (out / 'results.json').read_text(encoding='utf-8') + (out / 'REPORT_RU.md').read_text(encoding='utf-8')
        self.assertNotIn('PB_SYNTH_', published); self.assertNotIn(str(self.root), published)
        with self.assertRaises(FileExistsError): e.report(self.root, out)

    def test_unknown_cost_and_no_review_block_decision(self):
        obs = self.complete_simulated_records(); self.save(obs)
        self.assertFalse(e.assess(self.root)['independent_review_current'])
        obs['runs'][-1]['cost_usd'] = None; self.sign_simulated_review(obs)
        self.assertEqual(e.assess(self.root)['comparisons']['provider_C_vs_B']['decision'], 'KEEP_EXPERIMENTAL')

    def test_review_currentness_and_separate_decisions(self):
        obs = self.complete_simulated_records(); self.sign_simulated_review(obs)
        result = e.assess(self.root)
        self.assertTrue(all(v['decision'] == 'READY_FOR_OWNER_DECISION' for v in result['comparisons'].values()))
        obs['runs'][-1]['critical_failures'] = 1; self.save(obs)
        self.assertFalse(e.assess(self.root)['independent_review_current'])
        self.sign_simulated_review(obs)
        result = e.assess(self.root)
        self.assertEqual(result['comparisons']['method_B_vs_A']['decision'], 'READY_FOR_OWNER_DECISION')
        self.assertEqual(result['comparisons']['provider_C_vs_B']['decision'], 'REVISE_OR_REJECT')

    def test_offline_execution_cannot_be_admitted(self):
        obs = self.complete_simulated_records()
        for row in obs['runs']: row['execution'] = 'offline_fixture'
        self.sign_simulated_review(obs)
        self.assertTrue(all(v['decision'] == 'KEEP_EXPERIMENTAL' for v in e.assess(self.root)['comparisons'].values()))

    def test_budget_overrun_and_unknown_budget_block_adoption(self):
        obs = self.complete_simulated_records()
        obs['frozen_conditions']['budget'] = {}
        self.sign_simulated_review(obs)
        self.assertTrue(all(v['decision'] == 'KEEP_EXPERIMENTAL' for v in e.assess(self.root)['comparisons'].values()))
        obs['frozen_conditions']['budget'] = {'per_run_wall_seconds': 1, 'total_cost_usd': 2}
        self.sign_simulated_review(obs)
        self.assertTrue(all(v['decision'] == 'REVISE_OR_REJECT' for v in e.assess(self.root)['comparisons'].values()))

    def test_total_budget_includes_all_arms_and_external_costs(self):
        obs = self.complete_simulated_records()
        obs['frozen_conditions']['budget']['total_cost_usd'] = 8
        self.sign_simulated_review(obs)
        self.assertTrue(all(v['decision'] == 'REVISE_OR_REJECT' for v in e.assess(self.root)['comparisons'].values()))
        obs['experiment_cost_usd'] = 8
        self.save(obs)
        with self.assertRaises(e.ExperimentError): e.assess(self.root)
        obs['experiment_cost_usd'] = None
        self.sign_simulated_review(obs)
        self.assertTrue(all(v['decision'] == 'KEEP_EXPERIMENTAL' for v in e.assess(self.root)['comparisons'].values()))

    def test_method_can_be_assessed_when_provider_is_not_run(self):
        obs = self.complete_simulated_records()
        for row in obs['runs']:
            if row['id'].startswith('C'):
                row.update(execution='not_run', cost_usd=None)
        obs['experiment_cost_usd'] = 6
        self.sign_simulated_review(obs)
        result = e.assess(self.root)['comparisons']
        self.assertEqual(result['method_B_vs_A']['decision'], 'READY_FOR_OWNER_DECISION')
        self.assertEqual(result['provider_C_vs_B']['decision'], 'KEEP_EXPERIMENTAL')

    def test_changed_evidence_is_rejected(self):
        obs = self.complete_simulated_records(); self.sign_simulated_review(obs)
        (self.root / 'C-1/simulated-adjudication.txt').write_text('modified')
        with self.assertRaises(e.ExperimentError): e.assess(self.root)

    def test_duplicate_run_is_rejected(self):
        obs = self.observations(); obs['runs'][1] = obs['runs'][0]; self.save(obs)
        with self.assertRaises(e.ExperimentError): e.assess(self.root)

    def test_timeout_terminates_process(self):
        meta, _, _ = e.execute([sys.executable, '-c', 'import time; time.sleep(20)'], self.root, e.clean_env(), timeout=0.1)
        self.assertEqual(meta['status'], 'timeout_or_output_limit')
        self.assertLess(meta['wall_seconds'], 5)


if __name__ == '__main__':
    unittest.main()
