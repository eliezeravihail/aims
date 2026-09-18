"""Stage-2 tests — the cancel event and its refund side effect."""
import orders


def test_cancel_from_pending_no_refund():
    o = orders.Order()
    orders.transition(o, "cancel")
    assert o.status == "CANCELLED"
    assert o.refunded is False


def test_cancel_from_paid_records_refund():
    o = orders.Order()
    orders.transition(o, "pay")
    orders.transition(o, "cancel")
    assert o.status == "CANCELLED"
    assert o.refunded is True


def _expect_illegal_cancel(o):
    try:
        orders.transition(o, "cancel")
    except orders.IllegalTransition:
        return
    assert False, "expected IllegalTransition"


def test_cannot_cancel_from_shipped():
    o = orders.Order()
    orders.transition(o, "pay")
    orders.transition(o, "ship")
    _expect_illegal_cancel(o)
    assert o.status == "SHIPPED"
    assert o.refunded is False


def test_cannot_cancel_from_delivered():
    o = orders.Order()
    orders.transition(o, "pay")
    orders.transition(o, "ship")
    orders.transition(o, "deliver")
    _expect_illegal_cancel(o)
    assert o.status == "DELIVERED"
    assert o.refunded is False


def test_cannot_cancel_twice():
    o = orders.Order()
    orders.transition(o, "cancel")
    _expect_illegal_cancel(o)


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
    print("all stage-2 cancel tests passed")
