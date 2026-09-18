"""Stage-1 tests — the existing evaluator behavior. Ship with the code."""
import calc


def test_add():
    assert calc.evaluate("2 + 3") == 5


def test_precedence_mul_over_add():
    assert calc.evaluate("2 + 3 * 4") == 14


def test_parens():
    assert calc.evaluate("(2 + 3) * 4") == 20


def test_left_assoc_sub():
    assert calc.evaluate("10 - 3 - 2") == 5


def test_div_floor():
    assert calc.evaluate("7 / 2") == 3


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
    print("all stage-1 calc tests passed")
