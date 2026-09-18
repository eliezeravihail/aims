"""Order pricing.

Market 1 (``order_total``): a single final total — subtotal minus the
order-level discount.

Market 2 (``price_market2``): a per-line breakdown for the customer — per line,
the charge for that line and the tax on that charge. The per-line charges sum
*exactly* to the order's total charge (the same total market 1 reports), because
the order-level discount is **allocated down to the lines** as shares of the
discounted total, not re-applied per line.
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


def _discount_reduction(subtotal: int, discount) -> int:
    """The order-level discount reduction in whole cents.

    Single owner of the discount rule: both markets derive the order's total
    charge as ``subtotal - _discount_reduction(...)``, so the two markets can
    never disagree about what the order costs.
    """
    if discount is None:
        return 0
    kind, value = discount
    if kind == "pct":
        return _round_half_even(Decimal(subtotal) * Decimal(value) / Decimal(100))
    elif kind == "amt":
        return min(value, subtotal)
    else:
        raise ValueError(f"unknown discount kind: {kind!r}")


def order_total(order: Order) -> int:
    """Market 1: subtotal minus the order-level discount, in whole cents."""
    subtotal = order.subtotal_cents
    return subtotal - _discount_reduction(subtotal, order.discount)


def _allocate(total: int, weights) -> list:
    """Partition ``total`` cents into shares proportional to ``weights``.

    A *decomposition* of a whole into parts (not a per-part delta): remainder
    pennies are handed to the largest fractional remainders (ties by earliest
    line) so the returned shares sum to ``total`` **exactly**. A zero-weight line
    (fractional remainder 0) is never handed a penny, so a line the customer
    bought nothing on is never charged.
    """
    weight_sum = sum(weights)
    if weight_sum == 0:
        return [0] * len(weights)
    floors = []
    remainders = []  # (fractional_remainder, line_index)
    for i, w in enumerate(weights):
        exact = total * w
        floor = exact // weight_sum
        floors.append(floor)
        remainders.append((exact - floor * weight_sum, i))
    leftover = total - sum(floors)
    remainders.sort(key=lambda r: (-r[0], r[1]))
    for k in range(leftover):
        floors[remainders[k][1]] += 1
    return floors


@dataclass
class Market2Result:
    order_final: int          # the order's total charge (== order_total)
    line_finals: list         # per-line charge, in line order; sums to order_final
    line_taxes: list          # per-line tax on that line's charge, in line order


def price_market2(order: Order, tax_rate) -> Market2Result:
    """Market 2: per-line charges (that sum to the order's total charge) and the
    tax on each line's charge at ``tax_rate`` (half-even).

    ``order_final`` is the same total market 1 reports. It is decomposed across
    the lines by each line's pre-discount weight, so ``sum(line_finals) ==
    order_final`` holds for every discount and every set of lines. Tax is the
    market rate applied to each line's *own* charge, rounded half-even
    independently per line.
    """
    subtotal = order.subtotal_cents
    order_final = subtotal - _discount_reduction(subtotal, order.discount)
    weights = [line.total_cents for line in order.lines]
    line_finals = _allocate(order_final, weights)
    rate = tax_rate if isinstance(tax_rate, Decimal) else Decimal(str(tax_rate))
    line_taxes = [_round_half_even(Decimal(final) * rate) for final in line_finals]
    return Market2Result(
        order_final=order_final,
        line_finals=line_finals,
        line_taxes=line_taxes,
    )
