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
        self.root = Path(self.temp.name) / 'run'
        e.prepare(self.root, head='a' * 40, model='test-model', host='test-host')

    def observations(self):
        return e.read_json(self.root / 'observations.json')

    def save(self, value):
        (self.root / 'observations.json').write_bytes(e.dump(value))

    def complete_simulated_records(self):
        # Schema-only simulation; never publish this as observed effectiveness.
        obs = self.observations()
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
        other = Path(self.temp.name) / 'other.json'; other.write_text('{}')
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

    def test_scan_checks_declared_files_without_exposing_values(self):
        e.smoke(self.root, 'C-1')
        result = e.scan(self.root, 'C-1', ['C-1/synthetic-leak.txt', 'C-1/offline-receipt.json'])
        self.assertEqual(result['status'], 'EXPOSURE_FOUND')
        self.assertNotIn('PB_SYNTH_', json.dumps(result))
        with self.assertRaises(e.ExperimentError): e.scan(self.root, 'C-1', ['../secrets'])

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
        out = Path(self.temp.name) / 'report'
        result = e.report(self.root, out)
        self.assertTrue(all(v['decision'] == 'KEEP_EXPERIMENTAL' for v in result['comparisons'].values()))
        published = (out / 'results.json').read_text() + (out / 'REPORT_RU.md').read_text()
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
