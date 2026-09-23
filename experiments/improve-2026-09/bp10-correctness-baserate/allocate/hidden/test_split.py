"""BP10 allocation hidden tests. The SUM-EXACTLY tests are the load-bearing corner:
a build that returns [n//k]*k drops the remainder and FAILS test_sum_* when k does not divide n."""
import importlib, os
MOD = os.environ.get("SPLIT_MOD", "split")
split = importlib.import_module(MOD).split


def test_even_divide():
    assert split(10, 5) == [2, 2, 2, 2, 2]


def test_sum_exact_indivisible():
    r = split(10, 3)
    assert sum(r) == 10          # the corner: must not drop the remainder
    assert len(r) == 3


def test_sum_exact_various():
    for n, k in [(7, 3), (1, 4), (100, 7), (23, 5), (5, 5), (0, 3)]:
        r = split(n, k)
        assert len(r) == k
        assert sum(r) == n        # exact sum is the invariant


def test_as_even_as_possible():
    # parts differ by at most 1
    r = split(10, 3)
    assert max(r) - min(r) <= 1
    assert sorted(r, reverse=True) == r or max(r) - min(r) <= 1


def test_single_part():
    assert split(42, 1) == [42]


def test_k_larger_than_n():
    r = split(3, 5)
    assert sum(r) == 3
    assert len(r) == 5           # e.g. [1,1,1,0,0]


def test_zero():
    assert split(0, 4) == [0, 0, 0, 0]


def test_invalid_k():
    import pytest
    with pytest.raises(ValueError):
        split(10, 0)
