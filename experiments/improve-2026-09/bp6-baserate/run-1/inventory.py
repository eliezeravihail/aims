"""
Inventory management module with reservation support.

Provides a simple inventory system that tracks stock levels and manages
reservations to ensure units cannot be double-booked.
"""


class InsufficientStock(Exception):
    """Raised when attempting to reserve more units than are available."""
    pass


class Inventory:
    """
    Manages inventory stock levels and reservations.

    Tracks available units per SKU and maintains a ledger of reservations
    to ensure accurate availability calculations.
    """

    def __init__(self) -> None:
        """Initialize an empty inventory."""
        self._stock = {}  # sku -> total units added
        self._reservations = {}  # reservation_id -> (sku, qty)
        self._counter = 0  # for generating unique reservation IDs

    def add_stock(self, sku: str, qty: int) -> None:
        """
        Add qty available units of a SKU.

        Args:
            sku: Stock Keeping Unit identifier.
            qty: Number of units to add (expected to be > 0).
        """
        if sku not in self._stock:
            self._stock[sku] = 0
        self._stock[sku] += qty

    def available(self, sku: str) -> int:
        """
        Get the number of units available for a SKU.

        Returns 0 for unknown SKUs. Available is never negative.

        Args:
            sku: Stock Keeping Unit identifier.

        Returns:
            Number of unreserved units, or 0 if SKU is unknown.
        """
        if sku not in self._stock:
            return 0
        total = self._stock[sku]
        reserved = sum(qty for r_sku, qty in self._reservations.values() if r_sku == sku)
        return total - reserved

    def reserve(self, sku: str, qty: int) -> str:
        """
        Reserve qty units of a SKU.

        Args:
            sku: Stock Keeping Unit identifier.
            qty: Number of units to reserve.

        Returns:
            A unique, opaque reservation ID.

        Raises:
            ValueError: If qty <= 0.
            InsufficientStock: If qty > available units for the SKU.
        """
        if qty <= 0:
            raise ValueError("qty must be > 0")
        if qty > self.available(sku):
            raise InsufficientStock(f"Insufficient stock for {sku}")

        self._counter += 1
        reservation_id = f"res_{self._counter}"
        self._reservations[reservation_id] = (sku, qty)
        return reservation_id

    def release(self, reservation_id: str) -> None:
        """
        Release a reservation, returning units to available stock.

        Unknown or already-released reservation IDs are silently ignored (no-op).

        Args:
            reservation_id: The ID returned by a previous reserve() call.
        """
        if reservation_id in self._reservations:
            del self._reservations[reservation_id]
