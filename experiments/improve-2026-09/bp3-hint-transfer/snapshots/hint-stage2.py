"""Inventory reservation service.

Availability is never stored as its own field. The ground truth is two maps:
the total stock added per SKU, and the set of outstanding (unreleased)
reservations. Availability is derived on demand as
``added[sku] - sum(qty of outstanding reservations for sku)``. Because there is
no separate mutable "available" counter, reserve/release cannot drift out of
sync with it, and the invariants fall out of the arithmetic.
"""

import uuid


class InsufficientStock(Exception):
    """Raised when a reservation asks for more units than are available."""


class Inventory:
    def __init__(self) -> None:
        # SKU -> total units ever added (monotonic).
        self._added: dict[str, int] = {}
        # reservation id -> (sku, qty, expiry) for reservations still held.
        # expiry is None (never expires) or an absolute time in the injected
        # clock; the reservation holds units only while expiry > now.
        self._reservations: dict[str, tuple[str, int, float | None]] = {}

    def add_stock(self, sku: str, qty: int) -> None:
        """Add ``qty`` (> 0) available units of ``sku``."""
        if qty <= 0:
            raise ValueError("qty must be positive")
        self._added[sku] = self._added.get(sku, 0) + qty

    def available(self, sku: str, *, now: float = 0.0) -> int:
        """Units available for ``sku`` at time ``now`` (0 for an unknown SKU).

        Derived from ground-truth state: total added minus everything reserved
        for this SKU that still holds its units at ``now``. A reservation whose
        expiry is ``<= now`` holds zero units (its stock is available again),
        so it does not count against availability.
        """
        added = self._added.get(sku, 0)
        reserved = sum(
            q
            for s, q, expiry in self._reservations.values()
            if s == sku and (expiry is None or expiry > now)
        )
        return added - reserved

    def reserve(
        self,
        sku: str,
        qty: int,
        ttl_seconds: float | None = None,
        *,
        now: float = 0.0,
    ) -> str:
        """Reserve ``qty`` units of ``sku`` and return a unique reservation id.

        If ``ttl_seconds`` is given, the reservation expires at ``now +
        ttl_seconds`` and its units become available again from that instant;
        ``ttl_seconds=None`` never expires. The availability check is evaluated
        at ``now``, so already-expired reservations do not block a new one.

        Raises ``ValueError`` if ``qty <= 0`` and ``InsufficientStock`` if
        ``qty`` exceeds availability at ``now`` (in which case nothing changes).
        """
        if qty <= 0:
            raise ValueError("qty must be positive")
        if qty > self.available(sku, now=now):
            raise InsufficientStock(
                f"cannot reserve {qty} of {sku!r}; "
                f"only {self.available(sku, now=now)} available"
            )
        expiry = None if ttl_seconds is None else now + ttl_seconds
        reservation_id = uuid.uuid4().hex
        self._reservations[reservation_id] = (sku, qty, expiry)
        return reservation_id

    def release(self, reservation_id: str) -> None:
        """Return a reservation's units. Idempotent: unknown or already-released
        ids are a no-op."""
        self._reservations.pop(reservation_id, None)
