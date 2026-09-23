"""
Inventory management system with reservations.
"""

import uuid
from typing import Dict, Tuple


class InsufficientStock(Exception):
    """Raised when attempting to reserve more quantity than available."""
    pass


class Inventory:
    """
    Manages stock levels and reservations by SKU.

    Available quantity for a SKU = total stock added - sum of active reservations.
    Reservations are held until explicitly released.
    """

    def __init__(self) -> None:
        """Initialize empty inventory."""
        self._stock: Dict[str, int] = {}  # sku -> total quantity added
        self._reservations: Dict[str, Tuple[str, int]] = {}  # reservation_id -> (sku, qty)

    def add_stock(self, sku: str, qty: int) -> None:
        """Add qty units to stock for the given SKU."""
        if sku not in self._stock:
            self._stock[sku] = 0
        self._stock[sku] += qty

    def available(self, sku: str) -> int:
        """Return unreserved quantity for the given SKU."""
        if sku not in self._stock:
            return 0
        total = self._stock[sku]
        reserved = sum(
            res_qty
            for res_sku, res_qty in self._reservations.values()
            if res_sku == sku
        )
        return total - reserved

    def reserve(self, sku: str, qty: int) -> str:
        """
        Reserve qty units for the given SKU.

        Returns a unique reservation ID.
        Raises ValueError if qty <= 0.
        Raises InsufficientStock if qty > available.
        """
        if qty <= 0:
            raise ValueError("Reservation quantity must be positive")
        if self.available(sku) < qty:
            raise InsufficientStock(
                f"Insufficient stock for {sku}: "
                f"needed {qty}, available {self.available(sku)}"
            )
        reservation_id = str(uuid.uuid4())
        self._reservations[reservation_id] = (sku, qty)
        return reservation_id

    def release(self, reservation_id: str) -> None:
        """
        Release a reservation by its ID. No-op if the ID is unknown or already released.
        """
        self._reservations.pop(reservation_id, None)
