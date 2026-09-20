"""In-memory inventory reservation service.

A single-module service that tracks available stock per SKU and lets callers
reserve and release units. Reservations are opaque, unique handles that hold a
fixed quantity until released; releasing is idempotent.

Reservations may optionally carry a time-to-live. An expired reservation holds
zero units from its expiry instant onward, returning them to availability
automatically. The module reads no real clock: the caller injects ``now``.
"""

from __future__ import annotations

import uuid


class InsufficientStock(Exception):
    """Raised when a reservation asks for more units than are available."""


class Inventory:
    """Tracks total stock and outstanding reservations, in memory."""

    def __init__(self) -> None:
        # SKU -> total units ever added (the ceiling on availability).
        self._stock: dict[str, int] = {}
        # reservation id -> (sku, qty, expiry); expiry is None (never expires)
        # or the instant at/after which the reservation holds zero units.
        self._reservations: dict[str, tuple[str, int, float | None]] = {}

    def add_stock(self, sku: str, qty: int) -> None:
        """Add ``qty`` (>0) available units of ``sku``."""
        if qty <= 0:
            raise ValueError("qty must be > 0")
        self._stock[sku] = self._stock.get(sku, 0) + qty

    def _held(self, sku: str, now: float) -> int:
        """Units of ``sku`` held by reservations still active at ``now``.

        A reservation with ``expiry <= now`` has expired and holds zero units.
        """
        return sum(
            qty
            for res_sku, qty, expiry in self._reservations.values()
            if res_sku == sku and (expiry is None or expiry > now)
        )

    def available(self, sku: str, *, now: float = 0.0) -> int:
        """Return units of ``sku`` available at time ``now`` (0 for an unknown
        SKU). A reservation whose expiry is ``<= now`` holds zero units."""
        return self._stock.get(sku, 0) - self._held(sku, now)

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
        ttl_seconds`` and its units become available again automatically from
        that instant. ``ttl_seconds=None`` never expires.

        Raises ``ValueError`` if ``qty <= 0`` and ``InsufficientStock`` if
        ``qty`` exceeds availability at ``now``. On failure nothing changes.
        """
        if qty <= 0:
            raise ValueError("qty must be > 0")
        avail = self.available(sku, now=now)
        if qty > avail:
            raise InsufficientStock(
                f"cannot reserve {qty} of {sku!r}; only {avail} available"
            )
        expiry = None if ttl_seconds is None else now + ttl_seconds
        reservation_id = uuid.uuid4().hex
        self._reservations[reservation_id] = (sku, qty, expiry)
        return reservation_id

    def release(self, reservation_id: str) -> None:
        """Drop a reservation so its units are no longer held. Idempotent no-op
        for an unknown or already-released id.

        Releasing an already-expired reservation is likewise a no-op for
        availability: an expired reservation already holds zero units, so
        dropping it returns nothing and cannot double-count."""
        self._reservations.pop(reservation_id, None)
