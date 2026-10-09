"""Distribute a budget using stable largest-remainder allocation."""

from fractions import Fraction
from math import isfinite


def split_budget(total: float, weights: list[float]) -> list[float]:
    """Return ordered shares, assigning rounding ties to earlier entries.

    Allocation uses exact decimal amounts internally. A total with fractional
    cents retains that remainder in one share; returned floats have the usual
    binary floating-point representation limits.
    """
    if not isfinite(total) or total < 0:
        raise ValueError("total must be finite and non-negative")
    if not weights or any(not isfinite(weight) or weight <= 0 for weight in weights):
        raise ValueError("weights must be finite and positive")

    total_cents = Fraction(str(total)) * 100
    exact_weights = [Fraction(str(weight)) for weight in weights]
    weight_sum = sum(exact_weights)
    quotas = [total_cents * weight / weight_sum for weight in exact_weights]
    cents = [quota.numerator // quota.denominator for quota in quotas]
    order = sorted(range(len(weights)), key=lambda i: quotas[i] - cents[i], reverse=True)
    remaining = int(total_cents) - sum(cents)
    for index in order[:remaining]:
        cents[index] += 1

    # Retain input precision instead of rounding a fractional-cent total away.
    cents[order[remaining]] += total_cents - int(total_cents)
    result = [float(Fraction(amount) / 100) for amount in cents]
    # Conversion may erase cents at large magnitudes. Reconcile the returned
    # decimal amounts, not just the exact internal allocation. Preserve order
    # and assign the conversion remainder to the largest share (stable ties).
    index = max(range(len(result)), key=result.__getitem__)
    difference = Fraction(str(total)) - sum(Fraction(str(value)) for value in result)
    result[index] = float(Fraction(str(result[index])) + difference)
    return result
