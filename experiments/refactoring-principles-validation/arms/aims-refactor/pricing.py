"""Order pricing — market 1: a single final total.

Stage-1 implementation. Deliberately lean: the order-level discount is computed
once at the order total; there is no per-line allocation, because stage 1 does
not need one (correct YAGNI at this point).
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


# --- Market 2: per-line reporting with tax ---------------------------------
#
# Market 2 adds per-line reporting on top of the *same* discounted order total
# market 1 produces. Two invariants must hold by construction, so neither is
# left to a caller to re-derive:
#   * order_final == order_total(order)  -- the discount rule keeps its single
#     owner (order_total); market 2 consumes it, it does not recompute it.
#   * sum(line_finals) == order_final    -- the order total is *decomposed* into
#     per-line shares. This is an allocation (shares of a total), not a discount
#     applied again per line, so it lives in one place: _allocate_by_largest_remainder.


def _allocate_by_largest_remainder(total: int, weights) -> list:
    """Split ``total`` cents into integer shares proportional to ``weights``.

    The shares sum to exactly ``total`` (largest-remainder method): each share is
    the floored proportional amount, then the leftover cents are handed one each
    to the lines with the largest fractional remainders (ties broken by line
    order). ``total`` and every weight are non-negative integer cents.
    """
    n = len(weights)
    if n == 0:
        return []
    weight_sum = sum(weights)
    if weight_sum == 0:
        # No line carries any gross to be proportional to. In market 2 this only
        # arises when the subtotal is 0, in which case total is 0 as well, so the
        # only allocation summing to total is all-zeros.
        return [0] * n
    floors = []
    remainders = []
    for w in weights:
        share, remainder = divmod(total * w, weight_sum)
        floors.append(share)
        remainders.append(remainder)
    leftover = total - sum(floors)  # in [0, n): the pennies the floors dropped
    # Largest remainder first; ties keep line order (lower index wins).
    order = sorted(range(n), key=lambda i: (-remainders[i], i))
    for i in order[:leftover]:
        floors[i] += 1
    return floors


@dataclass
class Market2Result:
    order_final: int          # discounted order total in whole cents (== market 1)
    line_finals: list         # per-line final after discount allocation; sums to order_final
    line_taxes: list          # per-line tax on that line's discounted final amount


def price_market2(order: Order, tax_rate: Decimal) -> Market2Result:
    """Market 2: the order's discounted total, allocated to lines, plus per-line tax.

    ``order_final`` is exactly what market 1 computes for the same order. It is
    then decomposed across the lines proportional to each line's *gross*
    ``total_cents`` (largest-remainder, so the shares sum to ``order_final``), and
    each line's tax is ``round_half_even(line_final * tax_rate)`` on the
    discounted share.
    """
    order_final = order_total(order)
    gross_weights = [line.total_cents for line in order.lines]
    line_finals = _allocate_by_largest_remainder(order_final, gross_weights)
    line_taxes = [_round_half_even(Decimal(final) * tax_rate) for final in line_finals]
    return Market2Result(
        order_final=order_final,
        line_finals=line_finals,
        line_taxes=line_taxes,
    )
