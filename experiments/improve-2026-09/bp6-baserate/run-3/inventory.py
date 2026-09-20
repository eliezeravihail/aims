"""Inventory management with stock and reservation tracking."""

from uuid import uuid4


class InsufficientStock(Exception):
    """Raised when a reservation quantity exceeds available stock."""
    pass


class Inventory:
    """Manages stock levels and reservations per SKU.

    Availability is computed as: total_added - sum(reserved quantities).
    """

    def __init__(self) -> None:
        """Initialize empty inventory."""
        self._stock = {}  # sku -> total qty added
        self._reservations = {}  # reservation_id -> (sku, qty)

    def add_stock(self, sku: str, qty: int) -> None:
        """Add qty units to stock for sku."""
        if sku not in self._stock:
            self._stock[sku] = 0
        self._stock[sku] += qty

    def available(self, sku: str) -> int:
        """Return the number of units available for reservation.

        Available = total_added - sum of reserved quantities.
        Returns 0 for unknown SKUs.
        """
        if sku not in self._stock:
            return 0

        reserved_qty = sum(
            qty for res_sku, qty in self._reservations.values()
            if res_sku == sku
        )
        return self._stock[sku] - reserved_qty

    def reserve(self, sku: str, qty: int) -> str:
        """Reserve qty units of sku and return a unique reservation ID.

        Raises ValueError if qty <= 0.
        Raises InsufficientStock if qty > available(sku).
        """
        if qty <= 0:
            raise ValueError("Quantity must be positive")

        if qty > self.available(sku):
            raise InsufficientStock(
                f"Cannot reserve {qty} units of {sku}: only {self.available(sku)} available"
            )

        reservation_id = str(uuid4())
        self._reservations[reservation_id] = (sku, qty)
        return reservation_id

    def release(self, reservation_id: str) -> None:
        """Release a reservation by ID.

        No-op if reservation_id is unknown or already released.
        """
        self._reservations.pop(reservation_id, None)
