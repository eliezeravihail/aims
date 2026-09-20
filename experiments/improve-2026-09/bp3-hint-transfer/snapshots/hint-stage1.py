"""Inventory reservation service.

Availability is never stored as its own field. The ground truth is two maps:
the total stock added per SKU, and the set of outstanding (unreleased)
reservations. Availability is derived on demand as
``added[sku] - sum(qty of outstanding reservations for sku)``. Because there is
no separate mutable "available" counter, reserve/release cannot drift out of
sync with it, and the invariants fall out of the arithmetic.
"""

import uuid


class InsufficientStock(Exception):
    """Raised when a reservation asks for more units than are available."""


class Inventory:
    def __init__(self) -> None:
        # SKU -> total units ever added (monotonic).
        self._added: dict[str, int] = {}
        # reservation id -> (sku, qty) for reservations still held.
        self._reservations: dict[str, tuple[str, int]] = {}

    def add_stock(self, sku: str, qty: int) -> None:
        """Add ``qty`` (> 0) available units of ``sku``."""
        if qty <= 0:
            raise ValueError("qty must be positive")
        self._added[sku] = self._added.get(sku, 0) + qty

    def available(self, sku: str) -> int:
        """Units available now (0 for an unknown SKU).

        Derived from ground-truth state: total added minus everything
        currently reserved for this SKU.
        """
        added = self._added.get(sku, 0)
        reserved = sum(q for s, q in self._reservations.values() if s == sku)
        return added - reserved

    def reserve(self, sku: str, qty: int) -> str:
        """Reserve ``qty`` units of ``sku`` and return a unique reservation id.

        Raises ``ValueError`` if ``qty <= 0`` and ``InsufficientStock`` if
        ``qty`` exceeds current availability (in which case nothing changes).
        """
        if qty <= 0:
            raise ValueError("qty must be positive")
        if qty > self.available(sku):
            raise InsufficientStock(
                f"cannot reserve {qty} of {sku!r}; only {self.available(sku)} available"
            )
        reservation_id = uuid.uuid4().hex
        self._reservations[reservation_id] = (sku, qty)
        return reservation_id

    def release(self, reservation_id: str) -> None:
        """Return a reservation's units. Idempotent: unknown or already-released
        ids are a no-op."""
        self._reservations.pop(reservation_id, None)
