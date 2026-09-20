"""BP7 stage-2 hidden tests — priority ordering + exclusivity short-circuit.
Rules now take priority=<int> (lower applies first) and exclusive=<bool>.
When an exclusive rule produces a nonzero discount, no lower-priority
(higher-number) rule is applied. Backward compat: default rules behave as stage 1."""
import importlib, os
MOD = os.environ.get("PROMO_MOD", "promo")
promo = importlib.import_module(MOD)
Cart, Engine = promo.Cart, promo.Engine
PercentOff, AmountOffOver, BuyXGetY = promo.PercentOff, promo.AmountOffOver, promo.BuyXGetY


def cart(*items):
    c = Cart()
    for it in items:
        c.add_item(*it)
    return c


def test_backward_compat_all_default():
    c = cart(("a", "food", 100, 4), ("b", "toy", 200, 1))  # subtotal 600
    e = Engine([PercentOff("food", 25), AmountOffOver(500, 50)])  # 100 + 50 additive
    assert e.total(c) == 600 - 150


def test_exclusive_blocks_lower_priority():
    c = cart(("a", "food", 100, 10))  # subtotal 1000
    # priority 1 exclusive fires (100 off) -> priority 2 (would be 250 off) is skipped
    excl = PercentOff("food", 10, priority=1, exclusive=True)   # 100 off
    lower = PercentOff("food", 25, priority=2, exclusive=False)  # 250 off, skipped
    assert Engine([lower, excl]).total(c) == 1000 - 100


def test_exclusive_with_zero_discount_does_not_block():
    c = cart(("a", "food", 100, 4))  # subtotal 400
    # exclusive rule at priority 1 yields 0 (threshold not met) -> does NOT block
    excl_zero = AmountOffOver(1000, 500, priority=1, exclusive=True)  # 0 (subtotal<1000)
    lower = PercentOff("food", 25, priority=2)  # 100 off, should still apply
    assert Engine([excl_zero, lower]).total(c) == 400 - 100


def test_priority_order_determines_which_exclusive_wins():
    c = cart(("a", "food", 100, 10))  # subtotal 1000
    # two exclusives; the higher-priority (lower number) one wins and blocks the other
    first = AmountOffOver(0, 100, priority=1, exclusive=True)   # 100 off, fires first
    second = PercentOff("food", 50, priority=2, exclusive=True)  # 500 off, blocked
    assert Engine([second, first]).total(c) == 1000 - 100


def test_non_exclusive_before_exclusive_accumulates_then_stops():
    c = cart(("a", "food", 100, 10))  # subtotal 1000
    a = AmountOffOver(0, 50, priority=1, exclusive=False)       # 50 off, applies
    b = PercentOff("food", 10, priority=2, exclusive=True)      # 100 off, applies then stops
    d = AmountOffOver(0, 300, priority=3, exclusive=False)      # 300 off, skipped
    assert Engine([a, b, d]).total(c) == 1000 - 50 - 100


def test_all_non_exclusive_still_additive_in_priority_order():
    c = cart(("a", "food", 100, 10))  # subtotal 1000
    r1 = AmountOffOver(0, 100, priority=5)
    r2 = PercentOff("food", 10, priority=1)  # 100
    assert Engine([r1, r2]).total(c) == 1000 - 200


def test_floor_still_applies_with_stacking():
    c = cart(("a", "food", 100, 1))  # subtotal 100
    r = AmountOffOver(0, 999, priority=1)
    assert Engine([r]).total(c) == 0
