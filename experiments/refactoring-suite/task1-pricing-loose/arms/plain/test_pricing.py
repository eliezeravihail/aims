"""Stage-1 tests — market 1 behavior. These ship with the existing code."""
from decimal import Decimal
import pricing as m


def test_subtotal_no_discount():
    o = m.Order([m.Line(1000, 1), m.Line(500, 2)])
    assert o.subtotal_cents == 2000
    assert m.order_total(o) == 2000


def test_pct_discount():
    o = m.Order([m.Line(1000, 1), m.Line(500, 1)], ("pct", 10))
    assert m.order_total(o) == 1350  # 1500 - 150


def test_amt_discount():
    o = m.Order([m.Line(1000, 1)], ("amt", 250))
    assert m.order_total(o) == 750


def test_amt_discount_clamped():
    o = m.Order([m.Line(100, 1)], ("amt", 250))
    assert m.order_total(o) == 0


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
    print("all stage-1 tests passed")
