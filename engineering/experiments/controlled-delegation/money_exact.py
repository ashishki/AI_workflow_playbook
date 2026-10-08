"""Exact monetary reference for round 2. Amounts and results are integer cents.

This is an explicit new contract, not a rewrite of frozen float-based runs.
No Decimal context or binary float arithmetic participates in allocation.
"""
from decimal import Decimal, InvalidOperation
from fractions import Fraction


def to_minor_units(amount: str) -> int:
    if not isinstance(amount, str):
        raise ValueError('amount must be a decimal string')
    try:
        value = Decimal(amount)
    except InvalidOperation as exc:
        raise ValueError('invalid amount') from exc
    if not value.is_finite() or value < 0:
        raise ValueError('amount must be finite and non-negative')
    cents = Fraction(value) * 100
    if cents.denominator != 1:
        raise ValueError('amount must contain whole cents')
    return cents.numerator


def format_minor_units(amount: int) -> str:
    if type(amount) is not int or amount < 0:
        raise ValueError('amount must be non-negative integer cents')
    major, minor = divmod(amount, 100)
    # Python limits decimal str(int) conversions even though the integer is exact.
    # Small chunks preserve the accepted unbounded amount contract without
    # changing the interpreter's process-wide digit limit.
    chunks = []
    while major >= 10 ** 9:
        major, part = divmod(major, 10 ** 9)
        chunks.append(f'{part:09d}')
    digits = str(major) + ''.join(reversed(chunks))
    return f'{digits}.{minor:02d}'


def split_budget(total_minor: int, weights: list[int]) -> list[int]:
    if type(total_minor) is not int or total_minor < 0:
        raise ValueError('total must be non-negative integer cents')
    if not isinstance(weights, (list, tuple)) or not weights or any(type(w) is not int or w <= 0 for w in weights):
        raise ValueError('weights must be positive integers in input order')
    denominator = sum(weights)
    quotients = [divmod(total_minor * w, denominator) for w in weights]
    result = [q for q, _ in quotients]
    remainder = total_minor - sum(result)
    priority = sorted(range(len(weights)), key=lambda i: (-quotients[i][1], i))
    for index in priority[:remainder]:
        result[index] += 1
    return result
