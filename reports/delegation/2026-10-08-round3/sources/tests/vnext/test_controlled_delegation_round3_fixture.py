"""Offline fixture acceptance; these results say nothing about live agent usefulness."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT/'engineering/experiments/controlled-delegation/round3_fixtures.py'
SPEC = importlib.util.spec_from_file_location('round3_fixture_acceptance', SOURCE)
fixture = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(fixture)


class Round3FixtureTests(unittest.TestCase):
    def make(self, root, reference=False):
        fixture.materialize(root, reference=reference)
        return Path(root)

    def public(self, root):
        return subprocess.run([sys.executable,'-I','-B','-c',
            "import sys,unittest;sys.path.insert(0,sys.argv[1]);"
            "suite=unittest.defaultTestLoader.discover(sys.argv[1]+'/tests');"
            "result=unittest.TextTestRunner(verbosity=2).run(suite);"
            "sys.exit(not result.wasSuccessful())",str(root)],
            capture_output=True,text=True,timeout=30)

    def complete_diagnosis(self, root):
        observed = self.public(root)
        self.assertEqual(observed.returncode,0,observed.stderr)
        document = fixture.reference_diagnosis()
        document['verification'] = {'commands':['isolated unittest discovery on synthetic reference'],
                                    'observed_results':[observed.stderr.strip()]}
        (root/'diagnosis.json').write_text(json.dumps(document))
        (root/'STATE.md').write_text('# State\nObserved python -B -m unittest: pass.\n'
            'Limits: synthetic fixture only.\nNext step: independent local review.\n')

    def test_fixed_size_and_preregistered_weight_sum(self):
        case = fixture.cases()['fulfillment_replay']
        self.assertEqual(sum(case['groups'].values()),100)
        self.assertGreaterEqual(len(case['files']),40)
        self.assertLessEqual(len(case['files']),70)
        source_lines = sum(v.count('\n') for k,v in case['files'].items() if k.startswith('src/'))
        self.assertGreaterEqual(source_lines,500)
        self.assertEqual(len(fixture.reference_patches()),3)
        self.assertEqual(case['min_workers_c'],2)
        self.assertNotIn('reference_patches',case['task'])
        for body in case['files'].values():
            self.assertNotIn('reference_patches',body)
            self.assertNotIn('HIDDEN_SCRIPT',body)

    def test_genuinely_broken_and_healthy_control(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make(Path(tmp)/'task')
            result = self.public(root)
            self.assertNotEqual(result.returncode,0)
            self.assertIn('failures=4',result.stderr)
            self.assertIn('test_normal_path',result.stderr)
            self.assertIn('test_checkpoint_and_canonical_equivalence',result.stderr)
            evaluated = fixture.evaluate(root)
            self.assertFalse(evaluated['groups']['inventory'])
            self.assertFalse(evaluated['groups']['checkout'])
            self.assertFalse(evaluated['groups']['refunds'])
            self.assertFalse(evaluated['groups']['integration'])
            self.assertTrue(evaluated['groups']['unaffected'])
            self.assertEqual(evaluated['score'],10)

    def test_reference_passes_public_hidden_and_provenance(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make(Path(tmp)/'task',reference=True)
            result = self.public(root)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertIn('Ran 8 tests',result.stderr)
            self.complete_diagnosis(root)
            evaluated = fixture.evaluate(root)
            self.assertEqual(evaluated['score'],100,evaluated)
            self.assertTrue(all(evaluated['groups'].values()),evaluated)
            self.assertFalse(any(root.rglob('__pycache__')))

    def test_each_root_is_independently_replayable_and_repairable(self):
        for domain,path in [('inventory','src/inventory/registry.py'),
                            ('checkout','src/checkout/revisions.py'),
                            ('refunds','src/refunds/ledger.py')]:
            with self.subTest(domain=domain), tempfile.TemporaryDirectory() as tmp:
                root = self.make(Path(tmp)/'task')
                (root/path).write_text(fixture.reference_patches()[path])
                groups = fixture.evaluate(root)['groups']
                self.assertTrue(groups[domain])
                self.assertFalse(groups['integration'])
                for other in {'inventory','checkout','refunds'}-{domain}:
                    self.assertFalse(groups[other])
                self.assertTrue(groups['unaffected'])

    def test_protected_files_and_unknown_source_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make(Path(tmp)/'task',reference=True)
            self.complete_diagnosis(root)
            (root/'tests/test_replays.py').write_text('# doctored test')
            self.assertEqual(fixture.evaluate(root)['score'],0)
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make(Path(tmp)/'task',reference=True)
            (root/'src/sneaky.py').write_text('pass')
            self.assertEqual(fixture.evaluate(root)['score'],0)

    def test_only_explicit_manifested_harness_paths_are_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make(Path(tmp)/'task',reference=True)
            self.complete_diagnosis(root)
            (root/'AGENTS.md').write_text('harness instruction')
            self.assertEqual(fixture.evaluate(root)['score'],0)
            self.assertEqual(fixture.evaluate(root,managed_paths=('AGENTS.md',))['score'],100)
            with self.assertRaises(ValueError):
                fixture.evaluate(root,managed_paths=('../escape',))

    def test_diagnosis_requires_current_evidence_and_stale_exclusion(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make(Path(tmp)/'task',reference=True)
            self.complete_diagnosis(root)
            document = fixture.reference_diagnosis()
            document['defects'][0]['evidence_ids'] = ['ARC-CACHE-29','TRACE-INV-31']
            (root/'diagnosis.json').write_text(json.dumps(document))
            evaluated = fixture.evaluate(root)
            self.assertFalse(evaluated['groups']['diagnosis_inventory'])
            self.assertFalse(evaluated['groups']['state'])
            self.assertTrue(evaluated['groups']['diagnosis_checkout'])
            document = fixture.reference_diagnosis()
            document['defects'][1]['stale_evidence_ids'] = []
            (root/'diagnosis.json').write_text(json.dumps(document))
            self.assertFalse(fixture.evaluate(root)['groups']['diagnosis_checkout'])

    def test_context_paths_and_non_english_prose_do_not_false_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make(Path(tmp)/'task',reference=True)
            self.complete_diagnosis(root)
            document = json.loads((root/'diagnosis.json').read_text())
            document['defects'][0]['source_files'].append('src/inventory/projector.py')
            document['defects'][0]['mechanism'] = 'Ключ операции ошибочно исключает склад и арендатора.'
            document['defects'][0]['impact'] = 'Пропадает резерв второго склада; заказ не готов.'
            (root/'diagnosis.json').write_text(json.dumps(document))
            self.assertEqual(fixture.evaluate(root)['score'],100)

    def test_evaluator_infrastructure_timeout_is_unknown(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make(Path(tmp)/'task')
            with patch.object(fixture.subprocess,'run',side_effect=subprocess.TimeoutExpired('evaluator',30)):
                result = fixture.evaluate(root)
            self.assertIsNone(result['score'])
            self.assertEqual(result['groups'],{})
