"""Negative cases for a record's own internal consistency, not truth attestation."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('state_claim_record', ROOT/'tools/solution_record.py')
record = importlib.util.module_from_spec(spec); spec.loader.exec_module(record)

class StateClaimTests(unittest.TestCase):
    def test_checked_cannot_hide_an_unrun_check(self):
        data = json.loads((ROOT/'plugins/playbook-native/skills/playbook/assets/solution-record.example.json').read_text(encoding='utf-8'))
        data['state']['technical'] = 'checked'
        data['checks'] = [{'claim':'main', 'status':'passed', 'evidence':['observed.txt']}]
        self.assertEqual(record.validate(data), [])
        for status in ('not_run', 'blocked', 'failed'):
            changed = copy.deepcopy(data)
            changed['checks'].append({'claim':'remaining', 'status':status,
                                     'evidence':['observed.txt'] if status == 'failed' else []})
            self.assertTrue(record.validate(changed), status)
        data['state']['technical'] = 'partial'
        data['checks'].append({'claim':'remaining', 'status':'not_run', 'evidence':[]})
        self.assertEqual(record.validate(data), [])

if __name__ == '__main__': unittest.main()
