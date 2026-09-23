"""In-memory inventory reservation service (stage 1).

The load-bearing invariant is the *availability rule*:

    available(sku) == units_added(sku) - units_held_by_outstanding_reservations(sku)

It has exactly one owner, `Inventory.available`, and it is *derived*, never stored.
`Inventory` keeps only two ground facts:

  * `_added[sku]`        — total units ever added for a sku (only grows, via add_stock);
  * `_reservations[id]`  — the ledger of outstanding holds, id -> Reservation(sku, qty).

Availability is computed from those two facts on demand. Because no availability
*number* is ever stored, it cannot drift out of agreement with the ledger, and the
rules follow structurally:

  R1  available is never negative and never exceeds added-minus-reserved — it *is*
      that quantity by construction; reserve only records a hold when it fits, and
      release only removes a hold, so reserved units stay within [0, added].
  R2  a reservation holds exactly its qty until its id is removed from the ledger.
  R3  ids are unique (regeneration guards against collision) and opaque (uuid4 hex).
  R4  reserve validates against availability *before* recording anything, so an
      InsufficientStock (or a bad-qty ValueError) leaves the ledger untouched.
"""

from __future__ import annotations

from typing import Dict, NamedTuple
from uuid import uuid4


class InsufficientStock(Exception):
    """Raised when a reservation asks for more units than are available."""


class _Reservation(NamedTuple):
    """An outstanding hold of `qty` units against `sku`. Immutable."""

    sku: str
    qty: int


class Inventory:
    """An in-memory store of stock plus the outstanding reservations against it.

    Availability is derived from stock added and reservations held; it is the single
    owned rule of this class and is never cached as a separate number.
    """

    def __init__(self) -> None:
        self._added: Dict[str, int] = {}
        self._reservations: Dict[str, _Reservation] = {}

    def add_stock(self, sku: str, qty: int) -> None:
        """Add `qty` (> 0) available units of `sku`. Rejects a non-positive qty."""
        if qty <= 0:
            raise ValueError(f"qty must be positive, got {qty}")
        self._added[sku] = self._added.get(sku, 0) + qty

    def available(self, sku: str) -> int:
        """Units available for `sku` (0 for an unknown sku).

        The sole owner of the availability rule: added units minus the units held by
        outstanding reservations for this sku.
        """
        return self._added.get(sku, 0) - self._reserved(sku)

    def reserve(self, sku: str, qty: int) -> str:
        """Reserve `qty` units of `sku`; return a unique, opaque reservation id.

        Raises ValueError if qty <= 0, InsufficientStock if qty exceeds availability.
        On either error nothing is recorded (R4).
        """
        if qty <= 0:
            raise ValueError(f"qty must be positive, got {qty}")
        current = self.available(sku)
        if qty > current:
            raise InsufficientStock(
                f"cannot reserve {qty} of {sku!r}: only {current} available"
            )
        reservation_id = self._new_id()
        self._reservations[reservation_id] = _Reservation(sku, qty)
        return reservation_id

    def release(self, reservation_id: str) -> None:
        """Return a reservation's units to availability. No-op for an unknown or
        already-released id (idempotent)."""
        self._reservations.pop(reservation_id, None)

    # ── internals ────────────────────────────────────────────────────────────
    def _reserved(self, sku: str) -> int:
        """Units held by outstanding reservations for `sku`."""
        return sum(r.qty for r in self._reservations.values() if r.sku == sku)

    def _new_id(self) -> str:
        """A fresh opaque id, guaranteed not to collide with a live reservation."""
        reservation_id = uuid4().hex
        while reservation_id in self._reservations:
            reservation_id = uuid4().hex
        return reservation_id
