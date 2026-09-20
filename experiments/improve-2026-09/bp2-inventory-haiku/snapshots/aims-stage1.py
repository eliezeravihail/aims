"""
Inventory reservation service.

Core responsibility: maintain the availability invariant — available units
never go negative and never exceed total added minus outstanding reserved.
"""

import uuid
from typing import Dict, Tuple


class InsufficientStock(Exception):
    """Raised when a reservation quantity exceeds available stock."""
    pass


class Inventory:
    """
    In-memory inventory manager with reservation semantics.

    Encapsulates the availability invariant: for each SKU, available units
    are computed as (total_added - sum_of_reserved), ensuring the value
    never goes negative and never exceeds added stock.
    """

    def __init__(self) -> None:
        """Initialize an empty inventory."""
        # Per-SKU total stock added
        self._stock_added: Dict[str, int] = {}
        # Reservation ID → (SKU, qty) mapping
        self._reservations: Dict[str, Tuple[str, int]] = {}

    def add_stock(self, sku: str, qty: int) -> None:
        """
        Add qty units of a SKU to inventory.

        Args:
            sku: Stock keeping unit identifier
            qty: Quantity to add (must be positive)

        Raises:
            ValueError: if qty <= 0
        """
        if qty <= 0:
            raise ValueError(f"qty must be positive, got {qty}")

        self._stock_added[sku] = self._stock_added.get(sku, 0) + qty

    def available(self, sku: str) -> int:
        """
        Return available units for a SKU.

        Available is computed as: total_added - sum_of_reserved.
        For unknown SKUs, returns 0.

        Args:
            sku: Stock keeping unit identifier

        Returns:
            Non-negative count of available units
        """
        total_added = self._stock_added.get(sku, 0)
        reserved_qty = sum(
            qty for res_sku, qty in self._reservations.values()
            if res_sku == sku
        )
        return total_added - reserved_qty

    def reserve(self, sku: str, qty: int) -> str:
        """
        Reserve qty units of a SKU.

        Generates a unique, opaque reservation ID. The reserved quantity is
        held until released. If qty > available, raises InsufficientStock
        and makes no state change (atomic).

        Args:
            sku: Stock keeping unit identifier
            qty: Quantity to reserve (must be positive)

        Returns:
            Unique reservation ID (opaque string)

        Raises:
            InsufficientStock: if qty > available(sku)
            ValueError: if qty <= 0
        """
        if qty <= 0:
            raise ValueError(f"qty must be positive, got {qty}")

        # Check precondition before any state change (atomicity)
        if qty > self.available(sku):
            raise InsufficientStock(
                f"Cannot reserve {qty} units of {sku}; "
                f"only {self.available(sku)} available"
            )

        # Precondition passed; now mutate state
        reservation_id = str(uuid.uuid4())
        self._reservations[reservation_id] = (sku, qty)
        return reservation_id

    def release(self, reservation_id: str) -> None:
        """
        Release a reservation, returning units to available.

        If the reservation ID is unknown or already released, this is a no-op
        (idempotent).

        Args:
            reservation_id: ID returned by reserve()
        """
        # No-op if unknown or already released
        self._reservations.pop(reservation_id, None)
