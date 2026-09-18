"""Existing behavior. Ships with the code."""
import checkout as c


def test_subtotal():
    assert c.subtotal([(1000, 1), (500, 2)]) == 2000


def test_order_total_is_subtotal():
    assert c.order_total([(1000, 1), (500, 2)]) == 2000


def test_empty():
    assert c.order_total([]) == 0


if __name__ == "__main__":
    for n, f in sorted(globals().items()):
        if n.startswith("test_") and callable(f):
            f(); print("ok", n)
    print("all base tests passed")
