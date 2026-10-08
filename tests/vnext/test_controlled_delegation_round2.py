"""Source and rubric checks; no model calls or invented experiment successes."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import subprocess
import contextlib
import io

ROOT=Path(__file__).resolve().parents[2]
HERE=ROOT/'engineering/experiments/controlled-delegation'
sys.path.insert(0,str(HERE))
from round2 import prepare,review,telemetry,run as run_round2
from round2_checks import score,sha,write,task_verification
from round2_host import worker_durations
from round2_report import first_attempt,publish
from round2_fixtures import cases


class Round2Tests(unittest.TestCase):
    def test_preregistered_rubric_has_real_groups(self):
        for name,case in cases().items():
            self.assertEqual(sum(case['groups'].values()),100)
            self.assertEqual(case['min_workers_c'],2)
            if name=='sales_import':
                for method in case['groups']:self.assertIn('def '+method+'(',case['files']['test_engine.py'])

    def test_prepare_isolated_inputs_and_skill_equality(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'experiment';prepare(root,'a'*40,'test-model','high')
            plan=json.loads((root/'run-plan.json').read_text())
            self.assertEqual(len(plan['order']),12)
            by={(x['case'],x['repeat'],x['condition']):root/x['workspace'] for x in plan['order']}
            for name,case in cases().items():
                for repeat in (1,2):
                    a,b,c=(by[(name,repeat,k)] for k in 'ABC')
                    self.assertFalse((a/'.agents').exists())
                    for filename in case['files']:self.assertEqual((a/filename).read_bytes(),(c/filename).read_bytes())
                    for path in (b/'.agents').rglob('*'):
                        if path.is_file():self.assertEqual(path.read_bytes(),(c/path.relative_to(b)).read_bytes())
            with self.assertRaises(ValueError):prepare(root,'b'*40,'test-model','high')

    def test_unimplemented_sales_cannot_score(self):
        with tempfile.TemporaryDirectory() as tmp:
            w=Path(tmp);case=cases()['sales_import']
            for name,content in case['files'].items():(w/name).write_text(content)
            (w/'money_exact.py').write_bytes((HERE/'money_exact.py').read_bytes())
            initial={p.name:sha(p) for p in w.iterdir()}
            result=score('sales_import',w,initial)
            self.assertEqual(result['status'],'FAIL');self.assertEqual(result['score'],0)

    def test_release_fields_are_typed_and_protected(self):
        with tempfile.TemporaryDirectory() as tmp:
            w=Path(tmp);case=cases()['release_gate']
            for name,content in case['files'].items():
                p=w/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(content)
            initial={p.relative_to(w).as_posix():sha(p) for p in w.rglob('*') if p.is_file()}
            state='## Rules\nCurrent sources apply.\n## Verification\nRead three sources.\n## Limits\nSynthetic data; no deployment.\n## Next step\nFix blockers before release.\n'
            (w/'STATE.md').write_text(state);(w/'BRIEF.md').write_text(state*3)
            write(w/'decision.json',case['expected'])
            self.assertEqual(score('release_gate',w,initial)['status'],'PASS')
            wrong=dict(case['expected'],cost_delta_minor=str(case['expected']['cost_delta_minor']))
            write(w/'decision.json',wrong)
            self.assertLess(score('release_gate',w,initial)['score'],100)
            (w/'data/incidents.csv').write_text('removed evidence')
            result=score('release_gate',w,initial)
            self.assertEqual(result['score'],0);self.assertEqual(result['status'],'FAIL')


    def test_missing_review_is_blocked_but_confirmed_defect_is_fail(self):
        completed = [{'completed': True}]
        checks = {'status': 'PASS', 'score': 100}
        review = {'status': 'validated', 'verdict': 'PASS'}
        self.assertEqual(task_verification('sales_import', checks, completed, None), 'BLOCKED')
        self.assertEqual(task_verification('sales_import', checks, completed, {'status': 'timeout', 'verdict': None}), 'BLOCKED')
        self.assertEqual(task_verification('sales_import', checks, completed, {'status': 'validated', 'verdict': 'STOP_SHIP'}, True), 'FAIL')
        self.assertEqual(task_verification('sales_import', checks, completed, review, False), 'BLOCKED')
        self.assertEqual(task_verification('sales_import', {'status': 'FAIL'}, completed, review), 'FAIL')
        self.assertEqual(task_verification('release_gate', checks, completed, None), 'PASS')
        run = {'case': 'sales_import', 'phases': completed + completed,
               'reviews': [{'status': 'validated', 'verdict': 'STOP_SHIP'}, review]}
        first = first_attempt(run, checks, True)
        self.assertEqual(first['task_status'], 'FAIL')
        self.assertEqual(first['mechanical_score'], 100)
        self.assertEqual(first['repair_count'], 1)

    def test_worker_deadline_uses_observed_interval(self):
        run = {'host_sessions': [{'id': 'real-receipt-shape', 'source': {'subagent': {}},
                'task_completed': True,
                'intervals': [['2026-10-08T12:00:00.000Z', '2026-10-08T12:01:04.085Z']]},
               {'id': 'unfinished', 'source': {'subagent': {}}, 'task_completed': False,
                'intervals': [['2026-10-08T12:00:00.000Z', None]]}]}
        measured = worker_durations(run)
        self.assertEqual(measured[0]['interval_seconds'], [64.085])
        self.assertTrue(measured[0]['over_60_seconds'])
        self.assertEqual(measured[1]['interval_seconds'], [None])
        self.assertFalse(measured[1]['task_completed'])

    def test_publisher_preserves_original_receipt_and_unknown_measurements(self):
        # Synthetic unit fixture only: never counted as a live model result.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)/'input'; output = Path(tmp)/'output'; root.mkdir()
            item = {'id': 'unit-only', 'case': 'release_gate', 'condition': 'C',
                    'repeat': 1, 'workspace': 'workspaces/unit-only'}
            plan = {'experiment_id': 'unit-only', 'head': 'a'*40, 'model': 'unit-only',
                    'reasoning': 'high', 'seed': 1, 'repeats': 2, 'order': [item]}
            write(root/'run-plan.json', plan)
            (root/item['workspace']).mkdir(parents=True)
            (root/item['workspace']/'STATE.md').write_text('unit-only synthetic output')
            run = {**item, 'task_status': 'PASS', 'protocol_status': 'PASS', 'score': 100,
                   'status': 'BLOCKED', 'wall_seconds': 1.0, 'input_tokens': 10,
                   'cached_input_tokens': 3, 'output_tokens': 2, 'usage_complete': True,
                   'phases': [{'completed': True}], 'reviews': [],
                   'host_sessions': [{'source': 'exec', 'messages': ['private-unit-marker']}],
                   'mechanical': {'status': 'PASS', 'score': 100}}
            original = root/'results/unit-only.json'; write(original, run); before = original.read_bytes()
            write(root/'logs/unit-only/first-checks.json', run['mechanical'])
            publish(root, output)
            self.assertEqual(original.read_bytes(), before)
            results = json.loads((output/'results.json').read_text())
            self.assertEqual(results['qualification_status'], 'BLOCKED')
            self.assertEqual(results['measurement_status']['cost_usd'], 'NOT_RUN')
            self.assertNotIn('private-unit-marker', (output/'results.json').read_text())
            self.assertNotIn('private-unit-marker', (output/'evidence/release_gate-C-1.json').read_text())
            self.assertEqual(results['runs'][0]['collector_task_status'], 'PASS')
            self.assertEqual(results['comparisons'][1]['token_ratio_status'], 'PARTIAL')
            for receipt in json.loads((output/'evidence-index.json').read_text())['receipts']:
                self.assertEqual(sha(output/receipt['path']), receipt['sha256'])


    def test_matching_stop_ship_outranks_missing_phase_but_stale_does_not(self):
        checks = {'status': 'PASS', 'score': 100}
        stop = {'status': 'validated', 'verdict': 'STOP_SHIP'}
        self.assertEqual(task_verification('sales_import', checks, [{'completed': False}], stop, True), 'FAIL')
        self.assertEqual(task_verification('sales_import', checks, [{'completed': True}], stop, False), 'BLOCKED')
        self.assertEqual(task_verification('sales_import', checks, [{'completed': False}], stop, False), 'BLOCKED')
        self.assertEqual(task_verification('sales_import', checks, [{'completed': True}], stop, None), 'BLOCKED')

    def test_outer_review_timeout_preserves_partial_capture_and_blocked_receipt(self):
        # Process-boundary unit fixture, not a simulated live reviewer result.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); workspace = root/'workspace'; workspace.mkdir()
            (root/'logs').mkdir(); (workspace/'engine.py').write_text('pass\n')
            write(root/'run-plan.json', {'model': 'unit-only', 'reasoning': 'high'})
            write(root/'initial/unit-only.json', {'engine.py': sha(workspace/'engine.py')})
            before = sha(workspace/'engine.py')
            timeout = subprocess.TimeoutExpired(['role'], 21, output=b'partial stdout fixture', stderr=b'partial stderr fixture')
            with patch('round2.subprocess.run', side_effect=timeout):
                result = review(root, {'id': 'unit-only'}, workspace, {'status': 'PASS'}, root/'bin/codex', 'review', 1)
            self.assertEqual(result['status'], 'BLOCKED')
            self.assertIsNone(result['verdict']); self.assertTrue(result['outer_timeout'])
            self.assertEqual((root/'logs/unit-only/review.stdout.txt').read_text(), 'partial stdout fixture')
            self.assertEqual((root/'logs/unit-only/review.stderr.txt').read_text(), 'partial stderr fixture')
            self.assertEqual(json.loads((root/'logs/unit-only/review.receipt.json').read_text())['status'], 'BLOCKED')
            self.assertEqual(sha(workspace/'engine.py'), before)

    def test_timed_out_review_retains_counters_but_totals_remain_partial(self):
        # Provider-shaped unit receipt; no model is called by this regression.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); write(root/'run-plan.json', {'model': 'unit-only', 'reasoning': 'high'})
            host = {'id': 'main', 'source': 'exec', 'task_completed': True,
                    'context': {'model': 'unit-only', 'effort': 'high'}, 'intervals': [],
                    'usage': {'input_tokens': 10, 'cached_input_tokens': 3, 'output_tokens': 2}}
            phases = [{'thread_ids': ['main'], 'completed': True}]
            qa = {'status': 'timeout', 'exit_code': None,
                  'usage': [{'input_tokens': 40, 'cached_input_tokens': 20, 'output_tokens': 3}]}
            with patch('round2.capture_threads', return_value=[host]):
                measured = telemetry(root, root/'workspace', phases, [qa], root/'bin/codex')
            self.assertFalse(measured['usage_complete'])
            self.assertEqual((measured['input_tokens'], measured['cached_input_tokens'], measured['output_tokens']), (50, 23, 5))
            qa.update(status='validated', exit_code=0)
            with patch('round2.capture_threads', return_value=[host]):
                self.assertTrue(telemetry(root, root/'workspace', phases, [qa], root/'bin/codex')['usage_complete'])
            del qa['usage'][0]['output_tokens']
            with patch('round2.capture_threads', return_value=[host]):
                missing = telemetry(root, root/'workspace', phases, [qa], root/'bin/codex')
            self.assertFalse(missing['usage_complete'])
            self.assertEqual(missing['output_tokens'], 2)


    def test_omitted_hash_binding_cannot_assert_pass_or_confirmed_stop_ship(self):
        checks = {'status': 'PASS', 'score': 100}
        complete = [{'completed': True}]; incomplete = [{'completed': False}]
        stop = {'status': 'validated', 'verdict': 'STOP_SHIP'}
        passed = {'status': 'validated', 'verdict': 'PASS'}
        for phases in (complete, incomplete):
            self.assertEqual(task_verification('sales_import', checks, phases, stop), 'BLOCKED')
            self.assertEqual(task_verification('sales_import', checks, phases, passed), 'BLOCKED')
        self.assertEqual(task_verification('sales_import', checks, complete, passed, True), 'PASS')
        run = {'case': 'sales_import', 'phases': complete, 'reviews': [stop]}
        self.assertEqual(first_attempt(run, checks)['task_status'], 'BLOCKED')
        self.assertEqual(first_attempt(run, checks, True)['task_status'], 'FAIL')


    def test_actual_final_run_caller_binds_stop_ship_independent_of_verdict(self):
        # Bounded source integration fixtures: model/process boundaries mocked.
        # Exercise the actual run() caller, not only the helper in isolation.
        variants = [
            ('matching_stop_incomplete_repair', True, False, 'STOP_SHIP', True, 'FAIL'),
            ('matching_stop_complete', True, True, 'STOP_SHIP', True, 'FAIL'),
            ('stale_stop', True, False, 'STOP_SHIP', False, 'BLOCKED'),
            ('incomplete_main_no_qa', False, False, None, False, 'BLOCKED'),
            ('missing_qa', True, False, None, False, 'BLOCKED'),
            ('matching_pass', True, False, 'PASS', True, 'PASS'),
            ('stale_pass', True, False, 'PASS', False, 'BLOCKED'),
        ]
        for name, main_complete, repair_complete, verdict, matching, expected in variants:
            with self.subTest(case=name), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp); workspace = root/'workspace'; workspace.mkdir()
                (workspace/'engine.py').write_text('pass\n')
                item = {'id': 'unit-caller-only', 'case': 'sales_import', 'condition': 'A', 'repeat': 1, 'workspace': 'workspace'}
                write(root/'run-plan.json', {'model': 'unit-only', 'reasoning': 'high', 'order': [item]})
                write(root/'source-sha256.json', {})
                write(root/'initial/unit-caller-only.json', {})
                receipt = {'status': 'validated' if verdict else 'BLOCKED', 'verdict': verdict,
                           'report': 'unit-only fixture',
                           'reviewed_engine_sha256': sha(workspace/'engine.py') if matching else 'b'*64,
                           'submitted_engine_sha256': sha(workspace/'engine.py')}
                measured = {'settings_verified': True, 'workers': 0, 'max_parallel': 0, 'max_depth': 0,
                            'completed_worker_reuse': 0, 'worker_observed_durations': []}
                with patch('round2.setup_bin', return_value=root/'bin/codex'), \
                     patch('round2.execute', side_effect=[{'completed': main_complete}, {'completed': repair_complete}]), \
                     patch('round2.score', return_value={'status': 'PASS', 'score': 100}), \
                     patch('round2.review', return_value=receipt), \
                     patch('round2.telemetry', return_value=measured), \
                     contextlib.redirect_stdout(io.StringIO()):
                    run_round2(root)
                result = json.loads((root/'results/unit-caller-only.json').read_text())
                self.assertEqual(result['task_status'], expected)
                if verdict == 'STOP_SHIP' and matching:
                    self.assertEqual(result['first_attempt_status'], 'FAIL')
                    self.assertEqual(result['status'], 'FAIL')
