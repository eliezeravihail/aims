"""In-memory inventory reservation service.

A single-module service that tracks available stock per SKU and lets callers
reserve and release units. Reservations are opaque, unique handles that hold a
fixed quantity until released; releasing is idempotent.
"""

from __future__ import annotations

import uuid


class InsufficientStock(Exception):
    """Raised when a reservation asks for more units than are available."""


class Inventory:
    """Tracks available stock and outstanding reservations, in memory."""

    def __init__(self) -> None:
        # SKU -> units currently available for reservation.
        self._available: dict[str, int] = {}
        # reservation id -> (sku, qty) for units held out of availability.
        self._reservations: dict[str, tuple[str, int]] = {}

    def add_stock(self, sku: str, qty: int) -> None:
        """Add ``qty`` (>0) available units of ``sku``."""
        if qty <= 0:
            raise ValueError("qty must be > 0")
        self._available[sku] = self._available.get(sku, 0) + qty

    def available(self, sku: str) -> int:
        """Return units available for ``sku`` (0 for an unknown SKU)."""
        return self._available.get(sku, 0)

    def reserve(self, sku: str, qty: int) -> str:
        """Reserve ``qty`` units of ``sku`` and return a unique reservation id.

        Raises ``ValueError`` if ``qty <= 0`` and ``InsufficientStock`` if
        ``qty`` exceeds current availability. On failure nothing changes.
        """
        if qty <= 0:
            raise ValueError("qty must be > 0")
        if qty > self.available(sku):
            raise InsufficientStock(
                f"cannot reserve {qty} of {sku!r}; only {self.available(sku)} available"
            )
        self._available[sku] -= qty
        reservation_id = uuid.uuid4().hex
        self._reservations[reservation_id] = (sku, qty)
        return reservation_id

    def release(self, reservation_id: str) -> None:
        """Return a reservation's units to availability. Idempotent no-op for an
        unknown or already-released id."""
        entry = self._reservations.pop(reservation_id, None)
        if entry is None:
            return
        sku, qty = entry
        self._available[sku] = self._available.get(sku, 0) + qty
