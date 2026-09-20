"""Inventory reservation service."""

import uuid
from typing import Dict


class InsufficientStock(Exception):
    """Raised when attempting to reserve more stock than available."""
    pass


class Inventory:
    """Manages stock availability and reservations."""

    def __init__(self) -> None:
        """Initialize the inventory."""
        self._stock: Dict[str, int] = {}  # sku -> total added quantity
        self._reserved: Dict[str, int] = {}  # sku -> total reserved quantity
        self._reservations: Dict[str, Dict[str, any]] = {}  # reservation_id -> {sku, qty}

    def add_stock(self, sku: str, qty: int) -> None:
        """Add available units of a SKU.

        Args:
            sku: Stock keeping unit identifier
            qty: Quantity to add (must be > 0)
        """
        if qty <= 0:
            raise ValueError("Quantity must be positive")
        self._stock[sku] = self._stock.get(sku, 0) + qty

    def available(self, sku: str) -> int:
        """Get units available for reservation.

        Args:
            sku: Stock keeping unit identifier

        Returns:
            Number of available units (0 for unknown SKU)
        """
        total = self._stock.get(sku, 0)
        reserved = self._reserved.get(sku, 0)
        return total - reserved

    def reserve(self, sku: str, qty: int) -> str:
        """Reserve units of a SKU.

        Args:
            sku: Stock keeping unit identifier
            qty: Quantity to reserve (must be > 0)

        Returns:
            Unique reservation identifier

        Raises:
            ValueError: If qty <= 0
            InsufficientStock: If qty > available units (no state changes)
        """
        if qty <= 0:
            raise ValueError("Quantity must be positive")

        if self.available(sku) < qty:
            raise InsufficientStock(
                f"Insufficient stock for {sku}: requested {qty}, available {self.available(sku)}"
            )

        # Generate unique opaque reservation ID
        reservation_id = str(uuid.uuid4())

        # Record the reservation
        self._reservations[reservation_id] = {"sku": sku, "qty": qty}

        # Update reserved count
        self._reserved[sku] = self._reserved.get(sku, 0) + qty

        return reservation_id

    def release(self, reservation_id: str) -> None:
        """Release a reservation, returning units to available stock.

        Args:
            reservation_id: The reservation to release

        Note:
            Unknown or already-released IDs are no-ops (idempotent).
        """
        if reservation_id not in self._reservations:
            return  # Idempotent: unknown ID is a no-op

        # Get reservation details
        reservation = self._reservations[reservation_id]
        sku = reservation["sku"]
        qty = reservation["qty"]

        # Return units to available
        self._reserved[sku] -= qty

        # Clean up reservation record
        del self._reservations[reservation_id]
