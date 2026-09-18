"""Order lifecycle state machine.

Forward lifecycle: PENDING -> PAID -> SHIPPED -> DELIVERED, driven by events.
An order may also be cancelled while PENDING or PAID, moving it to the terminal
CANCELLED status; cancelling an order that had already been PAID records a refund.
An event that is not a legal transition from the current status raises IllegalTransition.

The (status, event) -> Transition table is the single owner of every transition:
its target status, its legality (a missing key is an illegal event), and any side
effect it records on the order. New transitions are added as sibling rows here; the
guard for cancel (legal only from PENDING/PAID) is expressed by which rows exist, so
cancel from SHIPPED/DELIVERED falls through to IllegalTransition like any illegal event.
"""

from typing import NamedTuple, Optional


class IllegalTransition(Exception):
    pass


class Transition(NamedTuple):
    """A legal transition: the status it moves to, plus any attribute values it
    records on the order as a side effect (empty for a pure state change)."""
    to: str
    effects: Optional[dict] = None


# (current_status, event) -> Transition
TRANSITIONS = {
    ("PENDING", "pay"): Transition("PAID"),
    ("PAID", "ship"): Transition("SHIPPED"),
    ("SHIPPED", "deliver"): Transition("DELIVERED"),
    # Cancellation: legal only from PENDING or PAID (no row from SHIPPED/DELIVERED,
    # so those fall through to IllegalTransition). Cancelling a PAID order records a
    # refund; cancelling a PENDING order records none.
    ("PENDING", "cancel"): Transition("CANCELLED"),
    ("PAID", "cancel"): Transition("CANCELLED", {"refunded": True}),
}


class Order:
    def __init__(self):
        self.status = "PENDING"
        self.refunded = False


def transition(order: Order, event: str) -> Order:
    key = (order.status, event)
    if key not in TRANSITIONS:
        raise IllegalTransition(f"cannot {event!r} from {order.status}")
    t = TRANSITIONS[key]
    order.status = t.to
    for attr, value in (t.effects or {}).items():
        setattr(order, attr, value)
    return order
