from __future__ import annotations

from billing.invoice import invoice_total_cents


def test_rounding_prefers_half_up_for_fractional_tax_cents() -> None:
    assert invoice_total_cents(100, "standard") == 109
    assert invoice_total_cents(199, "standard") == 216
    assert invoice_total_cents(199, "reduced") == 213


def test_zero_and_unknown_rates() -> None:
    assert invoice_total_cents(199, "zero") == 199
