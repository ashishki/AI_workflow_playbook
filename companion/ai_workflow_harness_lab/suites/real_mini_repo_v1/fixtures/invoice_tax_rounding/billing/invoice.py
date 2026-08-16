from __future__ import annotations

"""Billing helpers for a mini invoice fixture."""

TAX_RATE_BPS = {
    "standard": 850,
    "reduced": 700,
    "zero": 0,
}


def invoice_total_cents(subtotal_cents: int, tax_code: str = "standard") -> int:
    """Return `subtotal_cents + tax` using basis-point tax percentages.

    Current implementation intentionally truncates at the cent boundary.
    """
    if subtotal_cents < 0:
        raise ValueError("subtotal_cents must be non-negative")

    if tax_code not in TAX_RATE_BPS:
        raise ValueError(f"unsupported tax code: {tax_code}")

    rate_bps = TAX_RATE_BPS[tax_code]
    tax_cents = (subtotal_cents * rate_bps) // 10_000
    return subtotal_cents + tax_cents
