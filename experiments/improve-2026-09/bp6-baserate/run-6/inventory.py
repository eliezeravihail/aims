import uuid
from typing import Dict, Tuple


class InsufficientStock(Exception):
    """Raised when attempting to reserve more stock than is available."""
    pass


class Inventory:
    """Manages stock and reservations for multiple SKUs."""

    def __init__(self) -> None:
        """Initialize an empty inventory."""
        self._stock: Dict[str, int] = {}  # sku -> total added
        self._reservations: Dict[str, Tuple[str, int]] = {}  # reservation_id -> (sku, qty)

    def add_stock(self, sku: str, qty: int) -> None:
        """Add stock for a given SKU."""
        if sku not in self._stock:
            self._stock[sku] = 0
        self._stock[sku] += qty

    def available(self, sku: str) -> int:
        """Return the available (unreserved) quantity for a SKU."""
        if sku not in self._stock:
            return 0

        total_added = self._stock[sku]
        reserved = sum(
            qty for res_sku, qty in self._reservations.values()
            if res_sku == sku
        )
        return total_added - reserved

    def reserve(self, sku: str, qty: int) -> str:
        """
        Reserve stock for a SKU.

        Returns a unique reservation ID.
        Raises ValueError if qty <= 0.
        Raises InsufficientStock if qty > available.
        """
        if qty <= 0:
            raise ValueError(f"Reservation quantity must be positive, got {qty}")

        if self.available(sku) < qty:
            raise InsufficientStock(
                f"Insufficient stock for {sku}: requested {qty}, available {self.available(sku)}"
            )

        reservation_id = str(uuid.uuid4())
        self._reservations[reservation_id] = (sku, qty)
        return reservation_id

    def release(self, reservation_id: str) -> None:
        """Release a reservation. No-op if the reservation does not exist or was already released."""
        self._reservations.pop(reservation_id, None)
