# Stage 1 — inventory reservation service

Build a small in-memory **inventory reservation service** as a single Python module `inventory.py`.

## Public API (exact — the test suite imports these names)
```python
class InsufficientStock(Exception): ...

class Inventory:
    def __init__(self) -> None: ...
    def add_stock(self, sku: str, qty: int) -> None:
        """Add `qty` (>0) available units of `sku`."""
    def available(self, sku: str) -> int:
        """Units currently available to reserve for `sku` (0 for an unknown sku)."""
    def reserve(self, sku: str, qty: int) -> str:
        """Reserve `qty` units of `sku`; return a unique reservation id (a str).
        Raise InsufficientStock if qty > available(sku). Raise ValueError if qty <= 0."""
    def release(self, reservation_id: str) -> None:
        """Release a reservation, returning its units to availability.
        Releasing an unknown or already-released id is a no-op (idempotent)."""
```

## Rules (invariants)
- **R1** `available(sku)` is never negative and never exceeds total added stock minus outstanding reserved.
- **R2** A reservation holds exactly its `qty` units until released; releasing returns exactly those units.
- **R3** Reservation ids are unique and opaque.
- **R4** Reserving more than available raises `InsufficientStock` and changes nothing.

Deliver `inventory.py` (working Python, standard library only). Build it well.
