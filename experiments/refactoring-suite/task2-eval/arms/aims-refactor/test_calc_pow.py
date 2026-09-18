"""Stage-2 tests — the '^' exponentiation adaptation.

Separate from test_calc.py (which must pass UNCHANGED). These exercise the
interactions the new operator implies (refactoring-principles.md §6): its
precedence against every existing operator, its right-associativity, and the
parenthesis override in both directions.
"""
import calc


def test_pow_basic():
    assert calc.evaluate("2 ^ 3") == 8


# Precedence: '^' binds TIGHTER than '*' and '/'.
def test_pow_tighter_than_mul():
    assert calc.evaluate("2 * 3 ^ 2") == 18   # 2 * (3 ^ 2)


def test_pow_tighter_than_mul_left():
    assert calc.evaluate("3 ^ 2 * 2") == 18   # (3 ^ 2) * 2


def test_pow_tighter_than_div():
    assert calc.evaluate("16 / 2 ^ 3") == 2   # 16 / (2 ^ 3) = 16 / 8


# Precedence: '^' also binds tighter than '+' and '-'.
def test_pow_tighter_than_add():
    assert calc.evaluate("1 + 2 ^ 3") == 9    # 1 + (2 ^ 3)


def test_pow_tighter_than_sub():
    assert calc.evaluate("10 - 2 ^ 3") == 2   # 10 - (2 ^ 3)


# Associativity: '^' is RIGHT-associative.
def test_pow_right_assoc():
    assert calc.evaluate("2 ^ 2 ^ 3") == 256  # 2 ^ (2 ^ 3) = 2 ^ 8


def test_pow_right_assoc_chain():
    assert calc.evaluate("2 ^ 1 ^ 4") == 2    # 2 ^ (1 ^ 4) = 2 ^ 1


# Parentheses override the precedence and the associativity.
def test_parens_override_assoc():
    assert calc.evaluate("(2 ^ 2) ^ 3") == 64  # left-grouped by parens


def test_parens_override_precedence():
    assert calc.evaluate("(1 + 2) ^ 3") == 27  # (1 + 2) ^ 3
    assert calc.evaluate("2 ^ (2 ^ 3)") == 256


# Degenerate / edge cases; results stay non-negative integers.
def test_pow_identities():
    assert calc.evaluate("5 ^ 0") == 1
    assert calc.evaluate("5 ^ 1") == 5
    assert calc.evaluate("0 ^ 5") == 0
    assert calc.evaluate("1 ^ 100") == 1


def test_pow_deeply_nested_parens():
    assert calc.evaluate("((2)) ^ ((3))") == 8


def test_pow_result_is_int():
    assert isinstance(calc.evaluate("2 ^ 10"), int)
    assert calc.evaluate("2 ^ 10") == 1024


def test_bad_char_still_rejected():
    # '^' is now valid, but unknown characters must still raise.
    try:
        calc.evaluate("2 % 3")
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError for '%'")


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
    print("all stage-2 pow tests passed")
