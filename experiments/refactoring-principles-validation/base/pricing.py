"""Order pricing — market 1: a single final total.

Stage-1 implementation. Deliberately lean: the order-level discount is computed
once at the order total; there is no per-line allocation, because stage 1 does
not need one (correct YAGNI at this point).
"""
from decimal import Decimal, ROUND_HALF_EVEN


class Line:
    def __init__(self, unit_price_cents: int, qty: int):
        if unit_price_cents < 0 or qty < 0:
            raise ValueError("line values must be non-negative")
        self.unit_price_cents = unit_price_cents
        self.qty = qty

    @property
    def total_cents(self) -> int:
        return self.unit_price_cents * self.qty


class Order:
    # discount is one of: ("pct", percent_int_0_to_100) | ("amt", cents_int) | None
    def __init__(self, lines, discount=None):
        self.lines = list(lines)
        self.discount = discount

    @property
    def subtotal_cents(self) -> int:
        return sum(line.total_cents for line in self.lines)


def _round_half_even(x: Decimal) -> int:
    return int(x.quantize(Decimal(1), rounding=ROUND_HALF_EVEN))


def order_total(order: Order) -> int:
    """Market 1: subtotal minus the order-level discount, in whole cents."""
    subtotal = order.subtotal_cents
    discount = order.discount
    if discount is None:
        return subtotal
    kind, value = discount
    if kind == "pct":
        reduction = _round_half_even(Decimal(subtotal) * Decimal(value) / Decimal(100))
    elif kind == "amt":
        reduction = min(value, subtotal)
    else:
        raise ValueError(f"unknown discount kind: {kind!r}")
    return subtotal - reduction
