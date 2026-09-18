"""Market-2 tests, plus market-1 preservation checks.

Covers the interactions the new requirement implies (refactoring-principles.md
Section 6): discount x per-line allocation x tax over the full input space --
no discount, pct with a rounding remainder, amt (clamped and not), the empty
order, zero-priced lines, all-zero lines -- and the two by-construction
invariants: order_final == order_total(order), and sum(line_finals) == order_final.
"""
from decimal import Decimal
import pricing as m


# --- Market 1 stays bit-for-bit (Section 4: preserve out of scope) ----------
# The shipped test_pricing.py already guards these; re-pin them here so this
# file fails loudly if market 1 ever drifts.

def test_market1_unchanged():
    assert m.order_total(m.Order([m.Line(1000, 1), m.Line(500, 2)])) == 2000
    assert m.order_total(m.Order([m.Line(1000, 1), m.Line(500, 1)], ("pct", 10))) == 1350
    assert m.order_total(m.Order([m.Line(1000, 1)], ("amt", 250))) == 750
    assert m.order_total(m.Order([m.Line(100, 1)], ("amt", 250))) == 0


# --- The two invariants, asserted on every case -----------------------------

def _check_invariants(order, tax_rate):
    r = m.price_market2(order, tax_rate)
    # order_final is exactly what market 1 computes.
    assert r.order_final == m.order_total(order), (r.order_final, m.order_total(order))
    # line_finals sum exactly to order_final.
    assert sum(r.line_finals) == r.order_final, (r.line_finals, r.order_final)
    # one final and one tax per line, in line order.
    assert len(r.line_finals) == len(order.lines)
    assert len(r.line_taxes) == len(order.lines)
    # each tax is round_half_even(final * rate) on the discounted share.
    for final, tax in zip(r.line_finals, r.line_taxes):
        assert tax == m._round_half_even(Decimal(final) * tax_rate)
    return r


def test_no_discount_multi_line():
    o = m.Order([m.Line(1000, 1), m.Line(500, 2)])  # gross 1000, 1000
    r = _check_invariants(o, Decimal("0.10"))
    assert r.order_final == 2000
    assert r.line_finals == [1000, 1000]
    assert r.line_taxes == [100, 100]


def test_pct_discount_allocates_and_distributes_remainder():
    # gross 333/333/334, subtotal 1000, 10% -> order_final 900.
    o = m.Order([m.Line(333, 1), m.Line(333, 1), m.Line(334, 1)], ("pct", 10))
    r = _check_invariants(o, Decimal("0.00"))
    assert r.order_final == 900
    # floors 299/299/300 (=898); 2 leftover pennies to the two largest
    # remainders (indices 0 and 1, tie broken by line order).
    assert r.line_finals == [300, 300, 300]


def test_tax_is_on_discounted_amount_half_even():
    # order_final 900 split 300/300/300; tax at 2.5% -> 7.5 each -> half-even 8.
    o = m.Order([m.Line(333, 1), m.Line(333, 1), m.Line(334, 1)], ("pct", 10))
    r = _check_invariants(o, Decimal("0.025"))
    assert r.line_finals == [300, 300, 300]
    assert r.line_taxes == [8, 8, 8]  # round_half_even(7.5) == 8


def test_amt_discount_not_clamped():
    o = m.Order([m.Line(1000, 1)], ("amt", 250))
    r = _check_invariants(o, Decimal("0.20"))
    assert r.order_final == 750
    assert r.line_finals == [750]
    assert r.line_taxes == [150]


def test_amt_discount_clamped_to_zero():
    o = m.Order([m.Line(100, 1)], ("amt", 250))
    r = _check_invariants(o, Decimal("0.20"))
    assert r.order_final == 0
    assert r.line_finals == [0]
    assert r.line_taxes == [0]


def test_empty_order():
    o = m.Order([])
    r = _check_invariants(o, Decimal("0.10"))
    assert r.order_final == 0
    assert r.line_finals == []
    assert r.line_taxes == []


def test_zero_priced_line_gets_zero_share():
    o = m.Order([m.Line(0, 1), m.Line(1000, 1)], ("pct", 10))  # subtotal 1000 -> 900
    r = _check_invariants(o, Decimal("0.10"))
    assert r.order_final == 900
    assert r.line_finals == [0, 900]
    assert r.line_taxes == [0, 90]


def test_all_zero_lines():
    o = m.Order([m.Line(0, 1), m.Line(0, 3)])
    r = _check_invariants(o, Decimal("0.10"))
    assert r.order_final == 0
    assert r.line_finals == [0, 0]
    assert r.line_taxes == [0, 0]


def test_remainder_penny_lands_by_largest_remainder():
    # gross 100/100/100, subtotal 300, order_final via amt 1 -> 299.
    # floors: 299*100/300 = 99 r 200 each -> 99/99/99 = 297; leftover 2 pennies.
    # all remainders equal (200) -> ties by line order -> indices 0,1.
    o = m.Order([m.Line(100, 1), m.Line(100, 1), m.Line(100, 1)], ("amt", 1))
    r = _check_invariants(o, Decimal("0"))
    assert r.order_final == 299
    assert r.line_finals == [100, 100, 99]


if __name__ == "__main__":
    passed = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
            passed += 1
    print(f"all {passed} market-2 tests passed")
