import json
from pathlib import Path
import unittest
from src.pipeline import replay

ROOT = Path(__file__).resolve().parents[1]

def run_case(name):
    return replay(json.loads((ROOT / 'data/current' / (name + '.json')).read_text()))

class ReplayChecks(unittest.TestCase):
    def test_warehouse_replay(self):
        view = run_case('inventory')
        self.assertEqual(view['metrics']['reserved_units'], 4)
        self.assertEqual(view['inventory']['accepted'], 2)
        self.assertEqual(view['inventory']['replayed'], 1)
        self.assertTrue(view['orders'][0]['ready'])

    def test_order_replay(self):
        view = run_case('checkout')
        self.assertEqual(view['orders'][0]['revision'], 10)
        self.assertEqual(view['orders'][0]['status'], 'paid')
        self.assertTrue(view['orders'][0]['ready'])

    def test_provider_replay(self):
        view = run_case('refunds')
        self.assertEqual(view['metrics']['refunded_minor'], 900)
        self.assertEqual(view['refunds']['replayed'], 1)
        self.assertEqual(view['refunds']['rejected'], [])
        self.assertEqual(len(view['refunds']['accepted']), 2)

    def test_joined_replay(self):
        view = run_case('combined')
        self.assertEqual(view['metrics'], {'ready_orders':1, 'reserved_units':4,
                         'refunded_minor':900, 'rejected_refunds':0})
        self.assertEqual(view['orders'][0]['net_minor'], 100)

    def test_normal_path(self):
        view = run_case('baseline')
        self.assertEqual(view['metrics'], {'ready_orders':1, 'reserved_units':2,
                         'refunded_minor':400, 'rejected_refunds':0})
        self.assertEqual(view['orders'][0]['net_minor'], 600)

class TransportChecks(unittest.TestCase):
    def test_checkpoint_and_canonical_equivalence(self):
        import copy
        from src.adapters import decode
        from src.checkpoints import seal
        baseline = json.loads((ROOT/'data/current/baseline.json').read_text())
        wrapper = dict(build='r31',format='checkpoint-v1',
                       checkpoint=seal(baseline,'test-checkpoint'),batches=[])
        original = copy.deepcopy(wrapper)
        self.assertEqual(decode(wrapper), baseline)
        self.assertEqual(replay(wrapper), replay(baseline))
        self.assertEqual(wrapper, original)
        wrapper['checkpoint']['events']['inventory_events'][0]['qty'] += 1
        with self.assertRaises(ValueError):
            replay(wrapper)

    def test_batch_order_and_identity(self):
        from src.adapters import decode
        wrapper = json.loads((ROOT/'data/current/inventory.json').read_text())
        normal = decode(wrapper)
        wrapper['batches'].reverse()
        self.assertEqual(decode(wrapper), normal)
        wrapper['batches'].append(dict(wrapper['batches'][0]))
        self.assertEqual(decode(wrapper), normal)
        wrapper['batches'][0]['ordinal'] = 9
        with self.assertRaises(ValueError):
            decode(wrapper)

    def test_source_index_survives_checkpoint(self):
        from src.diagnostics import order_sources
        wrapper = json.loads((ROOT/'data/current/combined.json').read_text())
        records = order_sources(wrapper,'shop','O-17')
        self.assertEqual(len(records),8)
        self.assertEqual({r['channel'] for r in records},
                         {'inventory_events','checkout_events','refund_events'})


if __name__ == '__main__':
    unittest.main()
