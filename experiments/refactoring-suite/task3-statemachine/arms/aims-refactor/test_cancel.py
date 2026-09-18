"""Stage-2 tests — the cancel adaptation, plus a re-trace of cancel x every state.

Kept separate from test_orders.py (which must pass UNCHANGED). These exercise the
new behavior and confirm out-of-scope behavior is preserved bit-for-bit.
"""
import orders


def _expect_illegal(o, event):
    try:
        orders.transition(o, event)
    except orders.IllegalTransition:
        return
    assert False, f"expected IllegalTransition for {event!r} from {o.status}"


# --- new behavior: cancel ---

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


def test_transition_returns_order():
    o = orders.Order()
    assert orders.transition(o, "cancel") is o


# --- guard: cancel illegal once shipped/delivered/cancelled (fall-through) ---

def test_cancel_from_shipped_illegal():
    o = orders.Order()
    orders.transition(o, "pay")
    orders.transition(o, "ship")
    _expect_illegal(o, "cancel")
    assert o.status == "SHIPPED" and o.refunded is False


def test_cancel_from_delivered_illegal():
    o = orders.Order()
    for e in ("pay", "ship", "deliver"):
        orders.transition(o, e)
    _expect_illegal(o, "cancel")
    assert o.status == "DELIVERED" and o.refunded is False


def test_cancel_is_terminal():
    # CANCELLED is terminal: no event, including a second cancel, is legal from it.
    o = orders.Order()
    orders.transition(o, "cancel")
    for e in ("cancel", "pay", "ship", "deliver"):
        _expect_illegal(o, e)
    assert o.status == "CANCELLED"


# --- preserved out-of-scope behavior: refunded stays False on the forward path ---

def test_forward_path_never_refunds():
    o = orders.Order()
    for e in ("pay", "ship", "deliver"):
        orders.transition(o, e)
    assert o.status == "DELIVERED"
    assert o.refunded is False


def test_illegal_message_unchanged():
    o = orders.Order()
    try:
        orders.transition(o, "cancel")  # legal
        orders.transition(o, "cancel")  # now illegal from CANCELLED
    except orders.IllegalTransition as e:
        assert str(e) == "cannot 'cancel' from CANCELLED"
        return
    assert False, "expected IllegalTransition"


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
    print("all stage-2 cancel tests passed")
