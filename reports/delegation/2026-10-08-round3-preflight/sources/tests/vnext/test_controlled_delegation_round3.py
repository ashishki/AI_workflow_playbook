"""Offline harness regressions; synthetic receipts are not live run evidence."""
from pathlib import Path
import contextlib
import io
import json
import sys
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / 'engineering/experiments/controlled-delegation'
sys.path.insert(0, str(HERE))
from round3 import (function_calls, observed_telemetry, prepare, protocol_check,
                    run, verify_preregistration)
from round3_checks import guard, inventory, read, score, sha, task_status, write
from round3_fixtures import cases, materialize, reference_diagnosis
from round3_report import common_review, publish, summarize
from round2_host import execute


class Round3HarnessTests(unittest.TestCase):
    def workspace(self, root):
        case = cases()['fulfillment_replay']
        for filename, content in case['files'].items():
            p = root / filename; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(content)
        return inventory(root)

    def test_prepare_six_paired_runs_and_frozen_plan(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / 'runs'; prepare(root, 'unit-only-source')
            plan = read(root / 'run-plan.json'); verify_preregistration(root)
            self.assertEqual(len(plan['order']), 6)
            self.assertEqual(plan['main_seconds'], 600)
            self.assertEqual(plan['worker_seconds'], 180)
            self.assertEqual(plan['repair_policy'], 'NONE')
            for repeat in (1, 2):
                items = {r['condition']: root / r['workspace'] for r in plan['order'] if r['repeat'] == repeat}
                self.assertEqual(set(items), set('ABC'))
                self.assertFalse((items['A'] / '.agents').exists())
                for filename in cases()['fulfillment_replay']['files']:
                    self.assertEqual((items['A'] / filename).read_bytes(), (items['C'] / filename).read_bytes())
                for p in (items['B'] / '.agents').rglob('*'):
                    if p.is_file(): self.assertEqual(p.read_bytes(), (items['C'] / p.relative_to(items['B'])).read_bytes())
            write(root / 'run-plan.json', dict(plan, main_seconds=601))
            with self.assertRaises(ValueError): verify_preregistration(root)
            with self.assertRaises(ValueError): prepare(root, 'unit-only')

    def test_root_pending_gate_precedes_any_provider_setup(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / 'runs'
            with patch('round3.os.getuid', return_value=0):
                prepare(root, 'unit-root-pending')
                self.assertEqual(read(root / 'run-plan.json')['execution_context']['authorization'], 'PENDING_ROOT_EXCEPTION')
                with patch('round3.setup_bin') as provider:
                    with self.assertRaisesRegex(ValueError, 'root exception is pending'): run(root)
                    provider.assert_not_called()

    def test_reference_scoring_accepts_only_guarded_harness_context(self):
        # Host-side reference fixture acceptance; forbidden for model workspaces.
        with tempfile.TemporaryDirectory() as tmp:
            w = Path(tmp); materialize(w, reference=True)
            observed = subprocess.run([sys.executable, '-I', '-B', '-c',
                'import sys,unittest;sys.path.insert(0,sys.argv[1]);suite=unittest.defaultTestLoader.discover(sys.argv[1]+"/tests");result=unittest.TextTestRunner().run(suite);sys.exit(not result.wasSuccessful())',
                str(w)], capture_output=True, text=True, timeout=30)
            self.assertEqual(observed.returncode, 0, observed.stderr)
            diagnosis = reference_diagnosis()
            diagnosis['verification'] = {'commands': ['isolated unittest discovery on synthetic reference'],
                                        'observed_results': [observed.stderr.strip()]}
            write(w / 'diagnosis.json', diagnosis)
            (w / 'STATE.md').write_text('# Rules\nSynthetic reference.\n# Verification\nObserved unittest: pass.\n# Limits\nSynthetic only.\n# Next step\nIndependent review.\n')
            (w / 'AGENTS.md').write_text('unit harness context')
            initial = inventory(w)
            checked = score('fulfillment_replay', w, initial)
            self.assertEqual(checked['status'], 'PASS'); self.assertEqual(checked['score'], 100)
            (w / 'AGENTS.md').write_text('modified frozen context')
            self.assertEqual(score('fulfillment_replay', w, initial)['status'], 'FAIL')

    def test_common_review_requires_actual_artifacts_and_all_six_output_sets(self):
        # Synthetic receipt fixture only; never reported as an actual reviewer.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); entries = []; runs = []
            def entry(name, kind, run_id=None):
                p = root / name; p.write_text('unit-only evidence')
                e = {'path': str(p), 'sha256': sha(p), 'kind': kind}
                if run_id: e['run_id'] = run_id
                entries.append(e)
            entry('source.py', 'source'); entry('report.md', 'report')
            for i in range(6):
                identity = f'unit-{i}'
                entry(identity + '-receipt.json', 'run_receipt', identity)
                entry(identity + '-output.py', 'output', identity)
                runs.append({'id': identity, 'execution_status': 'COMPLETED',
                    'phases': [{'started_utc': '2026-10-08T12:00:00+00:00', 'wall_seconds': 1}]})
            snapshot = root / 'common-review/snapshot.json'
            write(snapshot, {'entries': entries})
            artifact = root / 'provider-unit-trace.jsonl'; artifact.write_text('unit receipt shape, not provider evidence')
            reviewer_report = root / 'review-unit.md'; reviewer_report.write_text('unit reviewer shape')
            receipt = {'status': 'validated', 'actual_provider': True, 'scope': 'common_source_output_report',
                'snapshot_path': 'common-review/snapshot.json', 'reviewed_snapshot_sha256': sha(snapshot),
                'review_started_utc': '2026-10-08T12:00:02+00:00', 'review_finished_utc': '2026-10-08T12:00:03+00:00',
                'artifacts': [{'path': str(artifact), 'sha256': sha(artifact), 'kind': 'provider_trace'},
                              {'path': str(reviewer_report), 'sha256': sha(reviewer_report), 'kind': 'report'}]}
            write(root / 'common-review/receipt.json', receipt)
            self.assertEqual(common_review(root, runs)['status'], 'validated')
            artifact.unlink()
            self.assertEqual(common_review(root, runs)['status'], 'BLOCKED')
            artifact.write_text('unit receipt shape, not provider evidence')
            entries = [e for e in entries if e.get('run_id') != 'unit-5']
            write(snapshot, {'entries': entries}); receipt['reviewed_snapshot_sha256'] = sha(snapshot)
            write(root / 'common-review/receipt.json', receipt)
            self.assertEqual(common_review(root, runs)['status'], 'BLOCKED')
            receipt['reviewed_snapshot_sha256'] = '0' * 64
            write(root / 'common-review/receipt.json', receipt)
            self.assertEqual(common_review(root, runs)['status'], 'BLOCKED')

    def test_integrity_guard_stops_before_workspace_evaluation(self):
        for variant in ('frozen_edit', 'added_helper', 'added_cache', 'symlink', 'removed_source'):
            with self.subTest(variant=variant), tempfile.TemporaryDirectory() as tmp:
                w = Path(tmp); initial = self.workspace(w)
                source = next(p for p in w.rglob('*.py') if 'src' in p.parts)
                if variant == 'frozen_edit': (w / 'TASK.md').write_text('added frozen control file')
                if variant == 'added_helper': (w / 'sitecustomize.py').write_text('raise RuntimeError()')
                if variant == 'added_cache': (w / 'cache.txt').write_text('cache')
                if variant == 'symlink': source.unlink(); source.symlink_to('/etc/passwd')
                if variant == 'removed_source': source.unlink()
                with patch('round3_checks.evaluate') as evaluator:
                    checked = score('fulfillment_replay', w, initial)
                self.assertEqual(checked['status'], 'FAIL'); self.assertEqual(checked['score'], 0)
                evaluator.assert_not_called()

    def test_mutable_existing_source_and_explicit_outputs_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            w = Path(tmp); initial = self.workspace(w)
            source = next(p for p in w.rglob('*.py') if 'src' in p.parts)
            source.write_text(source.read_text() + '\n# unit mutation\n')
            (w / 'diagnosis.json').write_text('{}'); (w / 'STATE.md').write_text('unit fixture')
            self.assertEqual(guard(w, initial)['status'], 'PASS')
            (source.parent / 'new_helper.py').write_text('pass')
            self.assertEqual(guard(w, initial)['status'], 'FAIL')

    def test_incomplete_verification_and_host_are_blocked_confirmed_failure_wins(self):
        with tempfile.TemporaryDirectory() as tmp:
            w = Path(tmp); initial = self.workspace(w)
            with patch('round3_checks.evaluate', return_value={'groups': {}, 'score': None, 'details': {'timeout': True}}):
                self.assertEqual(score('fulfillment_replay', w, initial)['status'], 'BLOCKED')
        self.assertEqual(task_status({'status': 'PASS'}, {'completed': False, 'timeout': True}), 'BLOCKED')
        self.assertEqual(task_status({'status': 'FAIL'}, {'completed': False}), 'FAIL')
        self.assertEqual(task_status({'status': 'PASS'}, {'completed': True}), 'PASS')

    def test_empty_and_partial_provider_counters_never_complete(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); w = root / 'workspace'; w.mkdir()
            write(root / 'run-plan.json', {'model': 'gpt-6.1-sol', 'reasoning': 'high'})
            phase = {'completed': True, 'thread_ids': ['main']}
            host = {'id': 'main', 'source': 'exec', 'task_completed': True, 'intervals': [],
                    'raw_file': str(root / 'missing-rollout.jsonl'),
                    'context': {'model': 'gpt-6.1-sol', 'effort': 'high'},
                    'usage': {'input_tokens': 10, 'cached_input_tokens': 3, 'output_tokens': 2}}
            for records, ids, complete in (([], [], False), ([host], ['main'], True),
                    ([dict(host, usage={'input_tokens': 10, 'cached_input_tokens': 3})], ['main'], False)):
                with patch('round2.capture_threads', return_value=records):
                    measured = observed_telemetry(root, w, dict(phase, thread_ids=ids), root / 'bin/codex')
                self.assertEqual(measured['usage_complete'], complete)
                if not complete: self.assertIsNone(measured['uncached_input_tokens'])

    def test_worker_timeout_and_incomplete_scope_receipts(self):
        data = {'settings_verified': True, 'usage_complete': True, 'workers': 2,
            'max_parallel': 2, 'max_depth': 1, 'completed_worker_reuse': 0,
            'native_spawn_receipts': [], 'worker_tool_observations': [],
            'worker_observed_durations': [{'thread_id': 'unit-child', 'interval_seconds': [181], 'over_180_seconds': True}]}
        result = protocol_check('C', {'completed': True}, data)
        self.assertEqual(result['status'], 'FAIL')
        self.assertIn('native spawn receipt incomplete', result['blockers'])
        data['worker_observed_durations'] = [{'thread_id': 'unit-child', 'interval_seconds': [None]}]
        self.assertEqual(protocol_check('C', {'completed': True}, data)['status'], 'BLOCKED')
        data.update(workers=0, native_spawn_receipts=[], worker_observed_durations=[])
        self.assertEqual(protocol_check('A', {'completed': False, 'timeout': True}, data)['status'], 'BLOCKED')

    def test_custom_write_tool_is_visible_in_actual_rollout_parser(self):
        with tempfile.TemporaryDirectory() as tmp:
            trace = Path(tmp) / 'trace.jsonl'
            trace.write_text(json.dumps({'type': 'response_item', 'payload': {'type': 'custom_tool_call', 'name': 'apply_patch', 'input': 'unit-only'}}) + '\n')
            self.assertEqual(function_calls(trace)[0]['name'], 'apply_patch')

    def test_host_real_process_timeout_keeps_partial_receipt(self):
        # A tiny local executable checks process boundary only; never a model.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); wrapper = root / 'unit-host'
            wrapper.write_text('#!/usr/bin/python3\nimport json,time\nprint(json.dumps({"type":"thread.started","thread_id":"unit-process"}),flush=True)\ntime.sleep(3)\n')
            wrapper.chmod(0o755)
            receipt = execute(root, root / 'logs', 'main', wrapper, 'unit deadline', 1)
            self.assertTrue(receipt['timeout']); self.assertFalse(receipt['completed'])
            self.assertEqual(receipt['thread_ids'], ['unit-process'])
            self.assertTrue((root / 'logs/main.events.jsonl').read_text())
            with self.assertRaises(RuntimeError): execute(root, root / 'logs', 'main', wrapper, 'unit', 1)

    def test_ratios_partial_failed_capped_not_speedup(self):
        runs = []
        for repeat in (1, 2):
            for c in 'ABC':
                runs.append({'condition': c, 'repeat': repeat, 'task_status': 'PASS', 'protocol_status': 'PASS',
                    'score': 100, 'usage_complete': True, 'input_tokens': 10, 'cached_input_tokens': 3,
                    'uncached_input_tokens': 7, 'output_tokens': 2, 'implementation_wall_seconds': 100 if c != 'C' else 70,
                    'phases': [{'completed': True, 'timeout': False}]})
        self.assertEqual(summarize(runs)['scenario_signal'], 'POTENTIAL_BENEFIT_THIS_SCENARIO')
        runs[-1]['phases'][0]['timeout'] = True; runs[-1]['task_status'] = 'BLOCKED'
        result = summarize(runs); self.assertFalse(result['successful_pair_comparable'])
        self.assertNotEqual(result['scenario_signal'], 'POTENTIAL_BENEFIT_THIS_SCENARIO')
        runs[-1]['usage_complete'] = False
        self.assertIsNone(summarize(runs)['c_b_token_ratios']['output_tokens'])

    def test_publisher_missing_receipts_blocked_hash_index_cost_null(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / 'runs'; output = Path(tmp) / 'public'; prepare(root, 'unit-source')
            item = read(root / 'run-plan.json')['order'][0]
            w = root / item['workspace']
            run_doc = {**item, 'task_status': 'PASS', 'protocol_status': 'PASS', 'status': 'PASS',
                'mechanical': {'status': 'PASS', 'score': 100}, 'score': 100,
                'phases': [{'completed': True}], 'host_sessions': [{'messages': ['private-unit-marker']}],
                'final_files_sha256': inventory(w), 'cost_usd': None, 'human_minutes': None}
            result_path = root / 'results' / (item['id'] + '.json'); write(result_path, run_doc)
            before = result_path.read_bytes(); publish(root, output)
            public = read(output / 'results.json')
            self.assertEqual(public['runs'][0]['task_status'], 'BLOCKED')
            self.assertIsNone(public['runs'][0]['cost_usd']); self.assertIsNone(public['runs'][0]['human_minutes'])
            self.assertEqual(public['qualification_status'], 'BLOCKED'); self.assertFalse(public['production_enable'])
            self.assertEqual(before, result_path.read_bytes())
            self.assertNotIn('private-unit-marker', (output / 'results.json').read_text())
            for entry in read(output / 'evidence-index.json')['receipts']:
                self.assertEqual(sha(output / entry['path']), entry['sha256'])
            with self.assertRaises(ValueError): publish(root, output)
