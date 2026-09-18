# Change request — order cancellation

You are handed an existing, working order lifecycle (`orders.py` + `test_orders.py`).

Add a `"cancel"` event:

- An order may be cancelled only while it is **PENDING** or **PAID**. Cancelling moves it to a new
  `"CANCELLED"` status.
- Cancelling an order that had already been **paid** must record a refund: set `order.refunded = True`.
  Cancelling a **PENDING** order records no refund (`order.refunded` stays `False`).
- An order that is **SHIPPED** or **DELIVERED** cannot be cancelled — `"cancel"` from those states raises
  `IllegalTransition`, exactly as any illegal event does today.

Everything the lifecycle does today must keep working **exactly** — the existing `test_orders.py` must pass
**unchanged**. Deliver the adapted `orders.py`. Do not edit `test_orders.py`.
