"""Market 2 tests + market-1-preservation and the cross-market invariant.

Run: python3 test_market2.py
"""
import random
from decimal import Decimal, ROUND_HALF_EVEN

import pricing as m


def _rhe(x):
    return int(Decimal(x).quantize(Decimal(1), rounding=ROUND_HALF_EVEN))


# --- Market 1 preserved bit-for-bit (the refactor must not drift it) ---

def test_market1_unchanged_after_refactor():
    assert m.order_total(m.Order([m.Line(1000, 1), m.Line(500, 2)])) == 2000
    assert m.order_total(m.Order([m.Line(1000, 1), m.Line(500, 1)], ("pct", 10))) == 1350
    assert m.order_total(m.Order([m.Line(1000, 1)], ("amt", 250))) == 750
    assert m.order_total(m.Order([m.Line(100, 1)], ("amt", 250))) == 0
    try:
        m.order_total(m.Order([m.Line(100, 1)], ("bogus", 1)))
        assert False, "unknown kind must still raise"
    except ValueError:
        pass


# --- The core invariant: per-line charges sum to the order's total charge ---

def test_line_finals_sum_to_order_final_and_order_total():
    o = m.Order([m.Line(1000, 1), m.Line(500, 1)], ("pct", 10))
    r = m.price_market2(o, Decimal("0.07"))
    assert r.order_final == m.order_total(o) == 1350
    assert sum(r.line_finals) == r.order_final
    assert r.line_finals == [900, 450]  # proportional decomposition of 1350


def test_no_discount_gives_each_line_its_own_total():
    o = m.Order([m.Line(1000, 1), m.Line(500, 2)])
    r = m.price_market2(o, Decimal("0.10"))
    assert r.order_final == 2000
    assert r.line_finals == [1000, 1000]  # 500*2 = 1000
    assert sum(r.line_finals) == r.order_final


def test_amt_discount_allocated_with_remainder_penny():
    # subtotal 1000, amt 1 -> final 999 across equal lines 500/500 -> 500/499
    o = m.Order([m.Line(500, 1), m.Line(500, 1)], ("amt", 1))
    r = m.price_market2(o, Decimal("0"))
    assert r.order_final == 999
    assert sum(r.line_finals) == 999
    assert r.line_finals == [500, 499]  # odd penny to earliest line, sum exact


def test_amt_fully_clamped_zeroes_everything():
    o = m.Order([m.Line(100, 1), m.Line(200, 1)], ("amt", 9999))
    r = m.price_market2(o, Decimal("0.2"))
    assert r.order_final == 0
    assert r.line_finals == [0, 0]
    assert r.line_taxes == [0, 0]


def test_empty_order():
    r = m.price_market2(m.Order([]), Decimal("0.07"))
    assert r.order_final == 0 and r.line_finals == [] and r.line_taxes == []
    assert sum(r.line_finals) == r.order_final


def test_single_line_gets_whole_final():
    o = m.Order([m.Line(1000, 1)], ("pct", 10))
    r = m.price_market2(o, Decimal("0.07"))
    assert r.line_finals == [900] and sum(r.line_finals) == r.order_final


def test_zero_weight_line_never_charged():
    # a free line (qty 0) among a paid one: all charge lands on the paid line
    o = m.Order([m.Line(0, 5), m.Line(300, 1)], ("pct", 10))
    r = m.price_market2(o, Decimal("0.05"))
    assert r.line_finals[0] == 0
    assert sum(r.line_finals) == r.order_final == 270


# --- Tax: market rate on each line's OWN charge, half-even, independent ---

def test_line_tax_is_rate_on_that_lines_charge_half_even():
    o = m.Order([m.Line(1000, 1), m.Line(500, 1)])  # finals 1000, 500
    r = m.price_market2(o, Decimal("0.075"))
    assert r.line_taxes == [_rhe(Decimal(1000) * Decimal("0.075")),   # 75
                            _rhe(Decimal(500) * Decimal("0.075"))]    # 38 (37.5 half-even -> 38)
    assert r.line_taxes == [75, 38]


def test_tax_rounds_half_even_not_half_up():
    # charge 50 at 5% = 2.5 -> half-even -> 2 ; charge 150 at 5% = 7.5 -> 8
    o = m.Order([m.Line(50, 1), m.Line(150, 1)])
    r = m.price_market2(o, Decimal("0.05"))
    assert r.line_taxes == [2, 8]


# --- Property sweep: invariant holds over the whole input space ---

def test_invariant_property_sweep():
    random.seed(7)
    kinds = [None, ("pct", 0), ("pct", 10), ("pct", 33), ("pct", 100),
             ("amt", 0), ("amt", 1), ("amt", 777), ("amt", 10 ** 9)]
    for _ in range(20000):
        n = random.randint(0, 6)
        lines = [m.Line(random.randint(0, 5000), random.randint(0, 4)) for _ in range(n)]
        disc = random.choice(kinds)
        o = m.Order(lines, disc)
        r = m.price_market2(o, Decimal(str(random.choice([0, 0.05, 0.07, 0.2]))))
        # 1) charges reconstruct the order's total charge, exactly
        assert sum(r.line_finals) == r.order_final
        # 2) order_final agrees with market 1
        assert r.order_final == m.order_total(o)
        # 3) shape + non-negativity
        assert len(r.line_finals) == n == len(r.line_taxes)
        assert all(f >= 0 for f in r.line_finals)
        assert all(t >= 0 for t in r.line_taxes)
        # 4) a line the customer bought nothing on is never charged
        for line, f in zip(o.lines, r.line_finals):
            if line.total_cents == 0:
                assert f == 0


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
    print("all market-2 tests passed")
