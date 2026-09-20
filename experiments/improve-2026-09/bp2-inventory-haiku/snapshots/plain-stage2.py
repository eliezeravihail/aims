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
        self._reservations: Dict[str, Dict[str, any]] = {}  # reservation_id -> {sku, qty, expiry?}

    def add_stock(self, sku: str, qty: int) -> None:
        """Add available units of a SKU.

        Args:
            sku: Stock keeping unit identifier
            qty: Quantity to add (must be > 0)
        """
        if qty <= 0:
            raise ValueError("Quantity must be positive")
        self._stock[sku] = self._stock.get(sku, 0) + qty

    def available(self, sku: str, *, now: float = 0.0) -> int:
        """Get units available for reservation at time `now`.

        Args:
            sku: Stock keeping unit identifier
            now: Current time; reservations with expiry <= now hold zero units

        Returns:
            Number of available units (0 for unknown SKU)
        """
        total = self._stock.get(sku, 0)

        # Calculate reserved units, excluding expired reservations
        reserved = 0
        for res_id, res_data in self._reservations.items():
            if res_data["sku"] == sku:
                expiry = res_data.get("expiry")
                # Only count as reserved if not expired
                if expiry is None or expiry > now:
                    reserved += res_data["qty"]

        return total - reserved

    def reserve(self, sku: str, qty: int, ttl_seconds: float | None = None, *, now: float = 0.0) -> str:
        """Reserve units of a SKU.

        Args:
            sku: Stock keeping unit identifier
            qty: Quantity to reserve (must be > 0)
            ttl_seconds: Time-to-live in seconds; if provided, reservation expires at now + ttl_seconds
            now: Current time (default 0.0)

        Returns:
            Unique reservation identifier

        Raises:
            ValueError: If qty <= 0
            InsufficientStock: If qty > available units (no state changes)
        """
        if qty <= 0:
            raise ValueError("Quantity must be positive")

        if self.available(sku, now=now) < qty:
            raise InsufficientStock(
                f"Insufficient stock for {sku}: requested {qty}, available {self.available(sku, now=now)}"
            )

        # Generate unique opaque reservation ID
        reservation_id = str(uuid.uuid4())

        # Record the reservation with optional expiry
        reservation_data: Dict[str, any] = {"sku": sku, "qty": qty}
        if ttl_seconds is not None:
            reservation_data["expiry"] = now + ttl_seconds
        self._reservations[reservation_id] = reservation_data

        # Update reserved count
        self._reserved[sku] = self._reserved.get(sku, 0) + qty

        return reservation_id

    def release(self, reservation_id: str, *, now: float = 0.0) -> None:
        """Release a reservation, returning units to available stock.

        Args:
            reservation_id: The reservation to release
            now: Current time (default 0.0)

        Note:
            Unknown, already-released, or expired IDs are no-ops (idempotent).
        """
        if reservation_id not in self._reservations:
            return  # Idempotent: unknown ID is a no-op

        # Get reservation details
        reservation = self._reservations[reservation_id]
        expiry = reservation.get("expiry")

        # Idempotent: releasing an expired reservation is a no-op
        if expiry is not None and expiry <= now:
            return

        sku = reservation["sku"]
        qty = reservation["qty"]

        # Return units to available
        self._reserved[sku] -= qty

        # Clean up reservation record
        del self._reservations[reservation_id]
