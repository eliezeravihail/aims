"""Stage-1 tests — the existing lifecycle. Ship with the code."""
import orders


def test_happy_path():
    o = orders.Order()
    orders.transition(o, "pay")
    assert o.status == "PAID"
    orders.transition(o, "ship")
    assert o.status == "SHIPPED"
    orders.transition(o, "deliver")
    assert o.status == "DELIVERED"


def test_illegal_ship_from_pending():
    o = orders.Order()
    try:
        orders.transition(o, "ship")
    except orders.IllegalTransition:
        return
    assert False, "expected IllegalTransition"


def test_illegal_deliver_from_paid():
    o = orders.Order()
    orders.transition(o, "pay")
    try:
        orders.transition(o, "deliver")
    except orders.IllegalTransition:
        return
    assert False, "expected IllegalTransition"


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
    print("all stage-1 orders tests passed")
