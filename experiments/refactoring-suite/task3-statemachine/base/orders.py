"""Order lifecycle state machine.

States: PENDING -> PAID -> SHIPPED -> DELIVERED, driven by events.
An event that is not a legal transition from the current status raises IllegalTransition.
"""


class IllegalTransition(Exception):
    pass


# (current_status, event) -> next_status
TRANSITIONS = {
    ("PENDING", "pay"): "PAID",
    ("PAID", "ship"): "SHIPPED",
    ("SHIPPED", "deliver"): "DELIVERED",
}


class Order:
    def __init__(self):
        self.status = "PENDING"
        self.refunded = False


def transition(order: Order, event: str) -> Order:
    key = (order.status, event)
    if key not in TRANSITIONS:
        raise IllegalTransition(f"cannot {event!r} from {order.status}")
    order.status = TRANSITIONS[key]
    return order
