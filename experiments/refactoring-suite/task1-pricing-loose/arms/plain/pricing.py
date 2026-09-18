"""Order pricing.

Market 1: a single final total (subtotal minus the order-level discount).
Market 2: a per-line breakdown whose line charges sum exactly to the order's
total charge, plus per-line tax at the market rate.
"""
from dataclasses import dataclass
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


# Public alias — the market-2 caller rounds line tax with the same rule as market 1.
round_half_even = _round_half_even


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


@dataclass
class Market2Result:
    order_final: int            # order's total charge = order_total(order)
    line_finals: list           # per-line charge, line order; sums to order_final
    line_taxes: list            # per-line tax on that line's charge


def _allocate(total: int, weights) -> list:
    """Split ``total`` cents across buckets proportional to integer ``weights``,
    with the parts summing to exactly ``total`` (largest-remainder method).

    Purely integer arithmetic, so there is no rounding ambiguity: every leftover
    cent is handed to the bucket with the largest fractional claim on it.
    """
    n = len(weights)
    s = sum(weights)
    if s == 0:
        return [0] * n
    base = []
    remainders = []
    for w in weights:
        q, r = divmod(total * w, s)
        base.append(q)
        remainders.append(r)
    leftover = total - sum(base)
    for i in sorted(range(n), key=lambda i: remainders[i], reverse=True)[:leftover]:
        base[i] += 1
    return base


def price_market2(order: Order, tax_rate) -> Market2Result:
    """Market 2: per-line charges that add up to the order's total charge, each
    taxed at the market rate.

    The order-level discount is allocated across lines in proportion to each
    line's own total, so ``sum(line_finals) == order_final == order_total(order)``
    exactly — the customer can add up their line charges and reach what they pay.
    Tax on each line is ``round_half_even(line_charge * tax_rate)``.
    """
    order_final = order_total(order)
    weights = [line.total_cents for line in order.lines]
    line_finals = _allocate(order_final, weights)
    rate = Decimal(str(tax_rate))
    line_taxes = [_round_half_even(Decimal(charge) * rate) for charge in line_finals]
    return Market2Result(
        order_final=order_final,
        line_finals=line_finals,
        line_taxes=line_taxes,
    )
