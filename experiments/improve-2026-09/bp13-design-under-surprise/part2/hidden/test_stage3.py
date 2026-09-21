"""BP13 part-2 hidden tests: a NEW rule kind PercentOffOrder(percent) = percent% off the whole subtotal.
Also re-checks stage-1/stage-2 behavior is intact (floor). Imports the same names each build defines."""
import importlib, os
promo = importlib.import_module(os.environ.get("PROMO_MOD", "promo"))
Cart, Engine = promo.Cart, promo.Engine
PercentOffOrder = promo.PercentOffOrder
PercentOff = promo.PercentOff


def cart(*items):
    c = Cart()
    for it in items:
        c.add_item(*it)
    return c


def test_percent_off_order_basic():
    c = cart(("a", "food", 100, 4), ("b", "toy", 200, 1))  # subtotal 600
    assert Engine([PercentOffOrder(10)]).total(c) == 600 - 60


def test_percent_off_order_floor():
    c = cart(("a", "food", 101, 1))  # subtotal 101
    assert Engine([PercentOffOrder(33)]).total(c) == 101 - 33  # 33.33 -> 33


def test_percent_off_order_composes_with_existing():
    c = cart(("a", "food", 100, 4))  # subtotal 400
    # additive with a category PercentOff: 10% order (40) + 25% food (100)
    assert Engine([PercentOffOrder(10), PercentOff("food", 25)]).total(c) == 400 - 40 - 100
