"""Mechanism tests use temporary fixtures, not a fake complete repo audit."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('vnext_check',ROOT/'tools/vnext_check.py')
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)

class ContractTests(unittest.TestCase):
    def test_longest_prefix_preserves_zone(self):
        rules=v.validate_rules(json.loads((ROOT/'shared/ownership.json').read_text(encoding='utf-8')))
        for path,expected in [('tools/run_codex_role.py','shared'),('product/pilots/README.md','author_eval'),
          ('engineering/USAGE_RU.md','engineering'),('engineering/experiments/new.md','engineering_experiments'),
          ('docs/governed/README.md','engineering'),('docs/vnext/history/old.md','archive'),
          ('plugins/playbook-native/skills/playbook/scripts/solution_record.py','shared')]:
            self.assertEqual(v.classify(path,rules),expected)
        with self.assertRaises(ValueError):v.classify('surprise/new.txt',rules)

    def test_invalid_rules_do_not_silently_classify(self):
        for bad in ([],[{'path':'../','zone':'product'}],[{'path':'*','zone':'shared'}],
                    [{'path':'docs/','zone':'invalid'}],[{'path':'docs/','zone':'product'}]*2):
            with self.subTest(bad=bad),self.assertRaises(ValueError):
                v.validate_rules({'schema_version':'playbook.ownership.v1','rules':bad})

    def test_catalogue_missing_stage_and_empty_reference_detected(self):
        original=json.loads((ROOT/v.SKILL/'assets/lifecycle.json').read_text(encoding='utf-8'))
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            for c in original['capabilities']:
                f=root/v.SKILL/c['reference'];f.parent.mkdir(parents=True,exist_ok=True);f.write_text('example procedure '*30)
                for path in c['engineering_sources']:
                    f=root/path;f.parent.mkdir(parents=True,exist_ok=True);f.write_text('fixture')
            self.assertEqual(v.check_catalogue(root,original),[])
            bad=copy.deepcopy(original);bad['capabilities'].pop()
            self.assertTrue(v.check_catalogue(root,bad))
            (root/v.SKILL/original['capabilities'][0]['reference']).write_text('')
            self.assertTrue(v.check_catalogue(root,original))

    def test_missing_source_and_fake_empirical_claim_rejected(self):
        original=json.loads((ROOT/v.SKILL/'assets/lifecycle.json').read_text(encoding='utf-8'))
        bad=copy.deepcopy(original);bad['capabilities'][0]['maturity']['user_benefit']='proven'
        self.assertTrue(any('empirical' in x for x in v.check_catalogue(ROOT,bad)))
        bad=copy.deepcopy(original);bad['capabilities'][0]['engineering_sources']=['missing.py']
        self.assertTrue(any('missing source' in x for x in v.check_catalogue(ROOT,bad)))

    def test_component_inventory_is_complete_and_explicit(self):
        data=json.loads((ROOT/'shared/component_map.json').read_text(encoding='utf-8'))
        self.assertEqual([c['id'] for c in data['components']],[f'PB-{n:02}' for n in range(1,51)])
        for c in data['components']:
            self.assertTrue(c['inspection']);self.assertTrue(c['source_paths'])
            self.assertEqual(c['disposition'],'reuse_or_adapt_no_deletion')
            self.assertTrue(set(c['lifecycle']).issubset(v.STAGES))

    def test_each_stage_has_substantial_packaged_procedure(self):
        data=json.loads((ROOT/v.SKILL/'assets/lifecycle.json').read_text(encoding='utf-8'))
        self.assertEqual([c['id'] for c in data['capabilities']],list(v.STAGES))
        for c in data['capabilities']:
            self.assertGreater(len((ROOT/v.SKILL/c['reference']).read_text(encoding='utf-8')),200)
        text=(ROOT/v.SKILL/'references/lifecycle.md').read_text(encoding='utf-8')
        for stage in v.STAGES:self.assertIn(f'lifecycle/{stage}.md',text)

if __name__=='__main__':unittest.main()
