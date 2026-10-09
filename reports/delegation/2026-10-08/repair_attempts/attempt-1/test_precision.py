"""Post-experiment repair checks; never substituted for original A/B/C runs."""
from decimal import Decimal, localcontext
import math
import random
import sys
import unittest
from budget import split_budget


class PrecisionTests(unittest.TestCase):
    def assert_conservation(self,total,weights):
        result=split_budget(total,weights)
        self.assertEqual(len(result),len(weights))
        self.assertTrue(all(math.isfinite(x) and x>=0 for x in result))
        self.assertTrue(math.isfinite(sum(result)))
        with localcontext() as context:
            context.prec=400
            self.assertEqual(sum((Decimal(str(x)) for x in result),Decimal(0)),Decimal(str(total)))

    def test_actual_independent_review_findings(self):
        for total in (1e15,1e16,sys.float_info.max):
            with self.subTest(total=total): self.assert_conservation(total,[1,1,1])

    def test_seeded_currency_allocations(self):
        rng=random.Random(20261008)
        for _ in range(1000):
            total=rng.randrange(0,10000000)/100
            weights=[rng.randrange(1,1000) for _ in range(rng.randrange(1,21))]
            self.assert_conservation(total,weights)

    def test_large_magnitudes_and_varied_counts(self):
        for total in (1e15,1e16,sys.float_info.max):
            for count in (2,3,9,11,12,17,18,20):
                with self.subTest(total=total,count=count): self.assert_conservation(total,[1]*count)
