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


class Market2Result:
    """Per-line report for market 2.

    order_final: the order's discounted total (identical to what market 1 returns).
    line_finals: each line's share of order_final after the order-level discount is
        allocated across lines, proportional to gross total_cents, remainder cents
        assigned by largest fractional remainder. Sums exactly to order_final.
    line_taxes: tax on each line's discounted final amount, rounded half-even.
    """

    def __init__(self, order_final: int, line_finals, line_taxes):
        self.order_final = order_final
        self.line_finals = line_finals
        self.line_taxes = line_taxes


def _allocate(total: int, weights) -> list:
    """Split `total` cents across positions in proportion to `weights` (ints).

    Largest-remainder apportionment: floor each ideal share, then hand the leftover
    cents one at a time to the positions with the largest fractional remainder,
    breaking ties by position order. The result sums exactly to `total`.
    """
    n = len(weights)
    total_weight = sum(weights)
    if n == 0:
        return []
    if total_weight == 0:
        # No basis to weight by (e.g. all-zero lines); nothing to distribute.
        return [0] * n
    floors = []
    remainders = []  # (remainder, index) for tie-broken selection
    for i, w in enumerate(weights):
        scaled = total * w
        floors.append(scaled // total_weight)
        remainders.append((scaled % total_weight, i))
    leftover = total - sum(floors)
    # Largest remainder first; ties resolved by earlier position (smaller index).
    remainders.sort(key=lambda r: (-r[0], r[1]))
    for k in range(leftover):
        floors[remainders[k][1]] += 1
    return floors


def price_market2(order: Order, tax_rate: Decimal) -> Market2Result:
    """Market 2: per-line report with tax, without touching market 1's total."""
    order_final = order_total(order)
    weights = [line.total_cents for line in order.lines]
    line_finals = _allocate(order_final, weights)
    line_taxes = [_round_half_even(final * tax_rate) for final in line_finals]
    return Market2Result(order_final, line_finals, line_taxes)
