"""
Inventory management system with stock tracking and reservations.
"""


class InsufficientStock(Exception):
    """Raised when attempting to reserve more stock than available."""
    pass


class Inventory:
    """
    Manages product inventory with stock tracking and reservation capabilities.

    Thread safety: not thread-safe. Use external locking if needed.
    """

    def __init__(self) -> None:
        """Initialize an empty inventory."""
        self._stock = {}          # sku -> int (total quantity added)
        self._reservations = {}   # reservation_id -> (sku, qty)
        self._next_id = 0         # counter for unique reservation IDs

    def add_stock(self, sku: str, qty: int) -> None:
        """
        Add stock for a given SKU.

        Args:
            sku: Stock keeping unit identifier
            qty: Quantity to add (may be positive or negative to adjust)
        """
        if sku not in self._stock:
            self._stock[sku] = 0
        self._stock[sku] += qty

    def available(self, sku: str) -> int:
        """
        Get the available (unreserved) quantity for a SKU.

        Args:
            sku: Stock keeping unit identifier

        Returns:
            Available quantity (total stock - reserved quantity)
        """
        total = self._stock.get(sku, 0)
        reserved = sum(
            qty for res_sku, qty in self._reservations.values()
            if res_sku == sku
        )
        return total - reserved

    def reserve(self, sku: str, qty: int) -> str:
        """
        Reserve stock for a SKU.

        Args:
            sku: Stock keeping unit identifier
            qty: Quantity to reserve (must be positive)

        Returns:
            Unique opaque reservation ID

        Raises:
            ValueError: If qty <= 0
            InsufficientStock: If available quantity < qty
        """
        if qty <= 0:
            raise ValueError("Reservation quantity must be positive")

        if self.available(sku) < qty:
            raise InsufficientStock(
                f"Insufficient stock for SKU '{sku}': "
                f"requested {qty}, available {self.available(sku)}"
            )

        reservation_id = str(self._next_id)
        self._next_id += 1
        self._reservations[reservation_id] = (sku, qty)
        return reservation_id

    def release(self, reservation_id: str) -> None:
        """
        Release a reservation, returning stock to available pool.

        If the reservation ID is unknown or already released, this is a no-op.

        Args:
            reservation_id: ID returned by reserve()
        """
        self._reservations.pop(reservation_id, None)
