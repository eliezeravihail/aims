"""Order pricing. Plain style on purpose: bare integer cents, plain functions,
tuples for structured values. No classes, no value objects. A change should keep
this grain."""
from decimal import Decimal, ROUND_HALF_EVEN


def _round_half_even(x):
    return int(Decimal(x).quantize(Decimal(1), rounding=ROUND_HALF_EVEN))


def subtotal(lines):
    # lines: list of (unit_price_cents, qty)
    return sum(unit_price * qty for unit_price, qty in lines)


def _order_off(sub, discount):
    """The order-level discount amount in cents (before clamping to subtotal)."""
    if discount is None:
        return 0
    kind, value = discount
    if kind == "pct":
        return _round_half_even(Decimal(sub) * Decimal(value) / Decimal(100))
    elif kind == "amt":
        return value
    else:
        raise ValueError("unknown discount kind: %r" % (kind,))


def _components(lines, discount, loyalty):
    """The pricing components for an order, all in whole cents:

        (sub, order_off, loyalty_requested, loyalty_granted, total)

    order_off is the order-level discount, clamped to the subtotal so it can
    never exceed it. loyalty, when given, is ("pct", n): n percent off the
    amount *after* the order-level discount (subtotal - order_off, half-even
    rounding). loyalty_requested is that raw amount; loyalty_granted is what
    survives the cap. The COMBINED discount (order_off + loyalty) is capped at
    50%% of the subtotal -- if the two together would exceed it, only the
    loyalty portion is trimmed so the total discount is exactly the cap, and the
    trim is reportable as loyalty_requested - loyalty_granted. total is the
    amount owed after both discounts, clamped so it never goes below 0.
    """
    sub = subtotal(lines)
    order_off = min(_order_off(sub, discount), sub)

    if loyalty is None:
        loyalty_requested = 0
        loyalty_granted = 0
    else:
        kind, n = loyalty
        if kind != "pct":
            raise ValueError("unknown loyalty kind: %r" % (kind,))
        base = sub - order_off
        loyalty_requested = _round_half_even(Decimal(base) * Decimal(n) / Decimal(100))
        cap = _round_half_even(Decimal(sub) * Decimal(50) / Decimal(100))
        room = max(0, cap - order_off)  # how much loyalty the cap still allows
        loyalty_granted = min(loyalty_requested, room)

    total = max(0, sub - order_off - loyalty_granted)
    return sub, order_off, loyalty_requested, loyalty_granted, total


def order_total(lines, discount=None, loyalty=None):
    """The amount owed for an order, in whole cents: subtotal minus an optional
    order-level discount and an optional loyalty discount.

    discount is None, ("pct", n) for n percent off the subtotal (0-100,
    half-even rounding), or ("amt", cents) for a fixed amount off.

    loyalty is None or ("pct", n) for n percent off the amount left after the
    order-level discount. The combined discount is capped at 50% of the subtotal
    (see _components). loyalty=None reproduces the earlier discount-only total
    exactly. The total is clamped so it never goes below 0.
    """
    return _components(lines, discount, loyalty)[4]


def discount_breakdown(lines, discount, loyalty):
    """How the two discounts landed, in whole cents:

        (order_discount_cents, loyalty_requested_cents, loyalty_granted_cents)

    A caller compares requested vs granted to see how much loyalty the 50%% cap
    trimmed (requested - granted).
    """
    sub, order_off, loyalty_requested, loyalty_granted, total = _components(
        lines, discount, loyalty
    )
    return order_off, loyalty_requested, loyalty_granted


def line_charges(lines, discount, tax_rate, loyalty=None):
    """Per-line breakdown for the second market: a list, in line order, of
    (final_cents, tax_cents) per line.

    final_cents is the line's share of order_total(lines, discount, loyalty) --
    both discounts (order-level, then the capped loyalty portion) allocated
    across the lines proportional to each line's gross (unit_price * qty), with
    the leftover pennies handed to the largest remainders (ties by line order).
    The finals therefore sum exactly to order_total(lines, discount, loyalty).

    tax_cents = _round_half_even(final_cents * tax_rate), i.e. tax on the line's
    discounted amount.
    """
    grosses = [unit_price * qty for unit_price, qty in lines]
    total_gross = sum(grosses)
    order_tot = order_total(lines, discount, loyalty)

    if total_gross == 0:
        # No basis to allocate against; every line's share is zero. (order_tot
        # is already 0 here, since subtotal is 0 and the discount only reduces.)
        finals = [0 for _ in lines]
    else:
        # Exact integer largest-remainder allocation. floor share numerator is
        # order_tot * gross; the remainder ranks who gets a leftover penny.
        floors = []
        remainders = []
        for gross in grosses:
            num = order_tot * gross
            floors.append(num // total_gross)
            remainders.append(num % total_gross)
        leftover = order_tot - sum(floors)
        # Hand each leftover penny to the largest remainder; ties by line order.
        order = sorted(range(len(lines)), key=lambda i: (-remainders[i], i))
        finals = list(floors)
        for i in order[:leftover]:
            finals[i] += 1

    return [
        (final, _round_half_even(Decimal(final) * Decimal(str(tax_rate))))
        for final in finals
    ]
