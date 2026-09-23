# Stage 3 — confirmation & partial reservation

Extend `inventory.py`.

## API additions
```python
    def confirm(self, reservation_id: str) -> None:
        """Confirm a reservation: it becomes PERMANENT and never expires thereafter,
        even if it had a ttl and even past that ttl. Confirming an unknown/released id is a no-op."""
    def reserve_up_to(self, sku: str, qty: int, *, now: float = 0.0) -> tuple[str, int]:
        """Reserve as many units as are available for sku at `now`, up to qty (qty > 0).
        Return (reservation_id, reserved_qty) where 0 <= reserved_qty <= qty.
        If nothing is available, reserved_qty is 0. Raise ValueError if qty <= 0."""
```

## Rules (added)
- **R8** A confirmed reservation holds its units permanently — expiry no longer applies to it.
- **R9** `reserve_up_to` never over-reserves (R1 holds); `reserved_qty = min(qty, available(sku, now))`.
- **R10** All stage-1 and stage-2 behavior is preserved.

Build it well.
