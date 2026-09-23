"""BP7 stage-1 hidden tests — correctness of the three rule types + composition.
Import path is patched by the runner to the arm's promo.py."""
import importlib, os, sys
import pytest

MOD = os.environ.get("PROMO_MOD", "promo")
promo = importlib.import_module(MOD)
Cart, Engine = promo.Cart, promo.Engine
PercentOff, AmountOffOver, BuyXGetY = promo.PercentOff, promo.AmountOffOver, promo.BuyXGetY


def cart(*items):
    c = Cart()
    for it in items:
        c.add_item(*it)
    return c


def test_subtotal():
    c = cart(("a", "food", 100, 3), ("b", "toy", 250, 2))
    assert c.subtotal() == 100 * 3 + 250 * 2  # 800


def test_percent_off_only_matching_category():
    c = cart(("a", "food", 100, 4), ("b", "toy", 200, 1))  # food base 400, toy 200
    e = Engine([PercentOff("food", 25)])  # 25% of 400 = 100
    assert e.total(c) == 600 - 100


def test_percent_off_integer_floor():
    c = cart(("a", "food", 101, 1))  # base 101
    e = Engine([PercentOff("food", 33)])  # 33% of 101 = 33.33 -> floor 33
    assert e.total(c) == 101 - 33


def test_amount_off_over_threshold_met():
    c = cart(("a", "food", 500, 1))  # subtotal 500
    e = Engine([AmountOffOver(500, 100)])
    assert e.total(c) == 400


def test_amount_off_over_threshold_not_met():
    c = cart(("a", "food", 499, 1))
    e = Engine([AmountOffOver(500, 100)])
    assert e.total(c) == 499  # no discount


def test_buy_x_get_y_basic():
    # buy 2 get 1: group of 3. qty 7 -> 2 groups -> 2 free units.
    c = cart(("a", "food", 100, 7))
    e = Engine([BuyXGetY("a", 2, 1)])
    assert e.total(c) == 700 - 2 * 100


def test_buy_x_get_y_no_full_group():
    c = cart(("a", "food", 100, 2))  # group of 3, qty 2 -> 0 free
    e = Engine([BuyXGetY("a", 2, 1)])
    assert e.total(c) == 200


def test_buy_x_get_y_only_matching_sku():
    c = cart(("a", "food", 100, 3), ("b", "food", 100, 3))
    e = Engine([BuyXGetY("a", 2, 1)])  # only sku a
    assert e.total(c) == 600 - 100


def test_multiple_rules_compose_additively():
    c = cart(("a", "food", 100, 4), ("b", "toy", 200, 1))  # subtotal 600
    e = Engine([PercentOff("food", 25), AmountOffOver(500, 50)])  # 100 + 50
    assert e.total(c) == 600 - 150


def test_total_floored_at_zero():
    c = cart(("a", "food", 100, 1))  # subtotal 100
    e = Engine([AmountOffOver(50, 999)])  # discount exceeds subtotal
    assert e.total(c) == 0


def test_empty_cart():
    e = Engine([PercentOff("food", 25)])
    assert e.total(Cart()) == 0


def test_no_rules():
    c = cart(("a", "food", 100, 2))
    assert Engine([]).total(c) == 200
