"""Order pricing. Plain style on purpose: bare integer cents, plain functions,
tuples for structured values. No classes, no value objects. A change should keep
this grain."""
from decimal import Decimal, ROUND_HALF_EVEN


def _round_half_even(x):
    return int(Decimal(x).quantize(Decimal(1), rounding=ROUND_HALF_EVEN))


def subtotal(lines):
    # lines: list of (unit_price_cents, qty)
    return sum(unit_price * qty for unit_price, qty in lines)


def order_total(lines, discount=None, loyalty=None):
    """The amount owed for an order, in whole cents: the subtotal, less an
    optional order-level discount, less an optional loyalty discount applied
    after it. discount is ("pct", n) for n percent off the subtotal (0-100,
    half-even), ("amt", cents) for a fixed amount off, or None. loyalty is
    ("pct", n) off the subtotal, applied after the order-level discount, or None;
    the COMBINED order+loyalty discount is capped at 50% of the subtotal (the cap
    rule is owned by discount_breakdown, read here). loyalty=None behaves exactly
    as the two-argument form. The total never goes below 0."""
    amount = subtotal(lines)
    if discount is not None:
        kind, value = discount
        if kind == "pct":
            amount -= _round_half_even(Decimal(amount * value) / 100)
        elif kind == "amt":
            amount -= value
    if loyalty is not None:
        _order, _requested, granted = discount_breakdown(lines, discount, loyalty)
        amount -= granted
    return max(0, amount)


def discount_breakdown(lines, discount, loyalty):
    """The single owner of the cap/precedence rule. Returns
    (order_discount_cents, loyalty_requested_cents, loyalty_granted_cents).
    Precedence: the order-level discount comes first — read as the cents removed
    by order_total (its owner), never re-derived. The loyalty discount ("pct", n)
    is then requested off the subtotal. The COMBINED order+loyalty discount is
    capped at 50% of the subtotal (half-even, the module's pct convention): the
    granted loyalty is reduced so the total discount is exactly the cap when the
    two together would exceed it, and never below 0 (a lone order discount already
    at or above the cap grants no loyalty). The requested/granted pair makes the
    reduction reportable (reduction = requested - granted)."""
    sub = subtotal(lines)
    order_discount = sub - order_total(lines, discount)
    if loyalty is None:
        return (order_discount, 0, 0)
    kind, value = loyalty
    requested = _round_half_even(Decimal(sub * value) / 100) if kind == "pct" else 0
    cap = _round_half_even(Decimal(sub * 50) / 100)
    granted = min(requested, max(0, cap - order_discount))
    return (order_discount, requested, granted)


def _allocate(total, weights):
    """Split a whole (bare cents) across buckets in proportion to weights so the
    parts SUM EXACTLY to total. Floor each proportional share, then hand the
    leftover pennies to the largest fractional remainders (largest-remainder
    method), ties broken by bucket order. A zero total or all-zero weights gives
    all zeros. Returns one int per weight, in order. This is the single owner of
    the Σ parts == whole conservation invariant."""
    n = len(weights)
    g = sum(weights)
    if g == 0:
        return [0] * n
    shares = [total * w // g for w in weights]
    remainders = [total * w % g for w in weights]
    leftover = total - sum(shares)
    for i in sorted(range(n), key=lambda i: (-remainders[i], i))[:leftover]:
        shares[i] += 1
    return shares


def line_charges(lines, discount, tax_rate, loyalty=None):
    """A per-line breakdown of a discounted order, in line order. Returns a list of
    (final_cents, tax_cents) per line, where final_cents is the line's share of
    order_total(lines, discount, loyalty) — the combined (capped) discount allocated
    across lines in proportion to each line's gross (unit_price*qty), remainder
    pennies by largest remainder — so the line finals SUM EXACTLY to
    order_total(lines, discount, loyalty). tax_cents is the tax on that discounted
    share, half-even: round_half_even(final_cents * tax_rate). tax_rate is a Decimal
    fraction. loyalty=None behaves exactly as the four-argument form omitted."""
    total = order_total(lines, discount, loyalty)
    grosses = [unit_price * qty for unit_price, qty in lines]
    finals = _allocate(total, grosses)
    return [(final, _round_half_even(final * tax_rate)) for final in finals]


def refund(lines, discount, tax_rate, loyalty, line_index):
    """The money and tax to give back when the single item on line_index is
    returned: exactly what the customer PAID for that line and the tax charged on
    it. Reads the per-line breakdown from its owner (line_charges) and returns that
    line's (amount_cents, tax_cents) — it does NOT re-derive the discounted share
    or tax. Because line_charges' finals SUM EXACTLY to order_total(lines, discount,
    loyalty) and tax is per line, refunding every line in turn returns the whole
    order total and all its tax."""
    return line_charges(lines, discount, tax_rate, loyalty)[line_index]
