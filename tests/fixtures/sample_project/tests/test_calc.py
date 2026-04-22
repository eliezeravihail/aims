"""Existing tests — note the gap: no string/numeric coercion cases."""

from src.calc import add, multiply


def test_add_positive_ints():
    assert add(2, 3) == 5


def test_add_negative_ints():
    assert add(-1, -2) == -3


def test_multiply():
    assert multiply(3, 4) == 12
