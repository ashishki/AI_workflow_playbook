import unittest

from budget import split_budget


class BudgetTests(unittest.TestCase):
    def test_rounding_preserves_exact_total(self):
        result = split_budget(10.00, [1, 1, 1])
        self.assertEqual(result, [3.34, 3.33, 3.33])
        self.assertAlmostEqual(sum(result), 10.00, places=2)

    def test_order_and_proportion_are_preserved(self):
        result = split_budget(12.00, [1, 2, 3])
        self.assertEqual(result, [2.00, 4.00, 6.00])

    def test_invalid_weights_are_rejected(self):
        for weights in ([], [1, 0], [1, -1]):
            with self.subTest(weights=weights), self.assertRaises(ValueError):
                split_budget(10.0, weights)


if __name__ == "__main__":
    unittest.main()
