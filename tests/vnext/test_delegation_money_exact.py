"""Numerical repair regressions, not simulated model observations."""
import importlib.util
from pathlib import Path
import random
import sys
import unittest

PATH = Path(__file__).resolve().parents[2] / 'engineering/experiments/controlled-delegation/money_exact.py'
SPEC = importlib.util.spec_from_file_location('money_exact', PATH)
money = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(money)


class ExactMoneyTests(unittest.TestCase):
    def test_original_intent_in_explicit_minor_units(self):
        self.assertEqual(money.split_budget(money.to_minor_units('10.00'), [1, 1, 1]), [334, 333, 333])
        self.assertEqual(money.split_budget(1200, [1, 2, 3]), [200, 400, 600])
        self.assertEqual([money.format_minor_units(x) for x in (334, 333, 333)], ['3.34', '3.33', '3.33'])

    def test_review_findings_and_failed_repair_counts(self):
        for amount in ('1e15', '1e16', str(sys.float_info.max)):
            total = money.to_minor_units(amount)
            for count in (2, 3, 9, 11, 12, 17, 18, 20, 101):
                with self.subTest(amount=amount, count=count):
                    result = money.split_budget(total, [1] * count)
                    self.assertEqual(sum(result), total)
                    self.assertEqual(sum(money.to_minor_units(money.format_minor_units(x)) for x in result), total)
                    self.assertLessEqual(max(result) - min(result), 1)

    def test_quota_error_order_and_conservation(self):
        rng = random.Random(20261008)
        for _ in range(500):
            total = rng.randrange(10 ** 80)
            weights = [rng.randrange(1, 10 ** 30) for _ in range(rng.randrange(1, 30))]
            result = money.split_budget(total, weights)
            self.assertEqual(sum(result), total)
            self.assertEqual(len(result), len(weights))
            for part, weight in zip(result, weights):
                self.assertGreaterEqual(part, 0)
                self.assertLess(abs(part * sum(weights) - total * weight), sum(weights))

    def test_invalid_inputs_are_explicit(self):
        for amount in ('NaN', 'Infinity', '-1.00', '0.001', 'bad', 10.0):
            with self.subTest(amount=amount), self.assertRaises(ValueError): money.to_minor_units(amount)
        for weights in ([], [0], [1, -1], [True], [1.5], None):
            with self.subTest(weights=weights), self.assertRaises(ValueError): money.split_budget(100, weights)
        for total in (-1, 1.0, True):
            with self.subTest(total=total), self.assertRaises(ValueError): money.split_budget(total, [1])


    def test_format_all_accepted_digits_without_global_limit_change(self):
        before = sys.get_int_max_str_digits() if hasattr(sys, 'get_int_max_str_digits') else None
        for value in ('0', '0.01', '123456789012345678901234567890.99', '1e4300', '1e5000'):
            with self.subTest(amount=value):
                amount = money.to_minor_units(value)
                formatted = money.format_minor_units(amount)
                self.assertEqual(money.to_minor_units(formatted), amount)
                self.assertTrue(formatted.endswith('.00') if value.startswith('1e') else True)
        self.assertEqual(money.format_minor_units(money.to_minor_units('1e5000')), '1' + '0' * 5000 + '.00')
        after = sys.get_int_max_str_digits() if hasattr(sys, 'get_int_max_str_digits') else None
        self.assertEqual(after, before)
