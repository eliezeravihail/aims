"""Market 2 tests — per-line breakdown that reconciles to the order total."""
from decimal import Decimal
import pricing as m


def _check_reconciles(res):
    assert sum(res.line_finals) == res.order_final


def test_no_discount_split_and_tax():
    o = m.Order([m.Line(1000, 1), m.Line(500, 2)])  # subtotal 2000
    res = m.price_market2(o, Decimal("0.10"))
    assert res.order_final == 2000
    assert res.line_finals == [1000, 1000]
    assert res.line_taxes == [100, 100]
    _check_reconciles(res)


def test_pct_discount_allocated():
    o = m.Order([m.Line(1000, 1), m.Line(500, 1)], ("pct", 10))  # total 1350
    res = m.price_market2(o, Decimal("0.07"))
    assert res.order_final == 1350
    _check_reconciles(res)
    # proportional: 1350 * 1000/1500 = 900, 1350 * 500/1500 = 450
    assert res.line_finals == [900, 450]


def test_penny_reconciles_with_odd_split():
    # subtotal 1000, 10% off -> 900 spread over three equal lines: 300/300/300
    o = m.Order([m.Line(100, 1), m.Line(100, 1), m.Line(100, 1)])
    # force an uneven split via weights that don't divide evenly
    o2 = m.Order([m.Line(333, 1), m.Line(333, 1), m.Line(334, 1)], ("pct", 3))
    res = m.price_market2(o2, Decimal("0.05"))
    _check_reconciles(res)
    assert res.order_final == m.order_total(o2)


def test_amt_discount_clamped_to_zero():
    o = m.Order([m.Line(100, 1)], ("amt", 250))  # order_final 0
    res = m.price_market2(o, Decimal("0.20"))
    assert res.order_final == 0
    assert res.line_finals == [0]
    assert res.line_taxes == [0]
    _check_reconciles(res)


def test_half_even_rounding_on_tax():
    # charge 5, rate 0.10 -> 0.5 -> rounds to 0 (banker's), charge 15 -> 1.5 -> 2
    o = m.Order([m.Line(5, 1), m.Line(15, 1)])
    res = m.price_market2(o, Decimal("0.10"))
    assert res.line_finals == [5, 15]
    assert res.line_taxes == [0, 2]


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
    print("all market-2 tests passed")
