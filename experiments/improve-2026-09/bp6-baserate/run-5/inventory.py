"""A simple inventory management system with stock reservations."""

import uuid
from typing import Dict, Tuple


class InsufficientStock(Exception):
    """Raised when attempting to reserve more stock than available."""
    pass


class Inventory:
    """Manages stock levels and reservations by SKU."""

    def __init__(self) -> None:
        # Track total stock added per SKU
        self._stock: Dict[str, int] = {}
        # Track total quantity reserved per SKU
        self._reserved: Dict[str, int] = {}
        # Track individual reservations: {reservation_id: (sku, qty)}
        self._reservations: Dict[str, Tuple[str, int]] = {}

    def add_stock(self, sku: str, qty: int) -> None:
        """Add qty units of stock for the given SKU."""
        if sku not in self._stock:
            self._stock[sku] = 0
        self._stock[sku] += qty

    def available(self, sku: str) -> int:
        """Return the quantity available (not reserved) for the given SKU."""
        if sku not in self._stock:
            return 0
        reserved = self._reserved.get(sku, 0)
        return self._stock[sku] - reserved

    def reserve(self, sku: str, qty: int) -> str:
        """Reserve qty units of stock for the given SKU.

        Returns a unique, opaque reservation ID.

        Raises ValueError if qty <= 0.
        Raises InsufficientStock if qty > available quantity.
        """
        if qty <= 0:
            raise ValueError("qty must be positive")

        available = self.available(sku)
        if qty > available:
            raise InsufficientStock(
                f"Cannot reserve {qty}; only {available} available for SKU {sku}"
            )

        # Create unique reservation ID
        reservation_id = str(uuid.uuid4())

        # Record the reservation
        self._reservations[reservation_id] = (sku, qty)

        # Update reserved totals
        if sku not in self._reserved:
            self._reserved[sku] = 0
        self._reserved[sku] += qty

        return reservation_id

    def release(self, reservation_id: str) -> None:
        """Release a reservation. No-op if reservation is unknown or already released."""
        if reservation_id not in self._reservations:
            return

        sku, qty = self._reservations[reservation_id]
        del self._reservations[reservation_id]
        self._reserved[sku] -= qty
