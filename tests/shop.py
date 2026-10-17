"""
Shop arithmetic, in one place.

The checks that verify money compute what the order should cost from the
prices the run itself read, so a wrong total cannot pass by sitting
inside a tolerance.
"""

import re
from decimal import ROUND_HALF_UP, Decimal

TAX_RATE = Decimal("0.08")
CENTS = Decimal("0.01")
_AMOUNT = re.compile(r"-?\d+(?:[.,]\d+)?")


def amount(text: str) -> Decimal:
    """The amount in a price or a label, such as Item total: $29.99."""
    found = _AMOUNT.search((text or "").replace(",", "."))
    if not found:
        raise ValueError(f"no amount in {text!r}")
    return Decimal(found.group())


def money(value: Decimal) -> str:
    return f"${value.quantize(CENTS, rounding=ROUND_HALF_UP)}"


def tax_on(subtotal: Decimal) -> Decimal:
    return (subtotal * TAX_RATE).quantize(CENTS, rounding=ROUND_HALF_UP)


def totals(prices) -> dict:
    """What the order should cost, from the prices the run read."""
    subtotal = sum((amount(p) if isinstance(p, str) else p for p in prices),
                   Decimal("0"))
    tax = tax_on(subtotal)
    return {"subtotal": subtotal, "tax": tax, "total": subtotal + tax}
