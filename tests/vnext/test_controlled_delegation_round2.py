"""Source and rubric checks; no model calls or invented experiment successes."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
HERE=ROOT/'engineering/experiments/controlled-delegation'
sys.path.insert(0,str(HERE))
from round2 import prepare
from round2_checks import score,sha,write
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
