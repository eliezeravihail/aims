"""In-memory inventory reservation service (stage 2 — expiring reservations).

The load-bearing invariant is the *availability rule*:

    available(sku, now) ==
        units_added(sku) - units_held_by_live_reservations(sku, now)

It has exactly one owner, `Inventory.available`, and it is *derived*, never stored.
`Inventory` keeps only two ground facts:

  * `_added[sku]`        — total units ever added for a sku (only grows, via add_stock);
  * `_reservations[id]`  — the ledger of outstanding holds,
                           id -> Reservation(sku, qty, expiry).

Availability is computed from those two facts on demand, at an *injected* time `now`
(the module reads no real clock). A reservation carries an optional `expiry` instant;
from `expiry` onward (expiry <= now) it holds zero units — its expiry is a ground fact
on the ledger entry, but "expired" is *derived* against `now`, never stored, exactly as
availability itself is. Because no availability *number* and no expired-*state* is ever
stored, neither can drift out of agreement with the ledger, and the rules follow
structurally:

  R1  available is never negative and never exceeds added-minus-reserved — it *is*
      that quantity by construction; reserve only records a hold when it fits, and
      release only removes a hold, so reserved units stay within [0, added].
  R2  a reservation holds exactly its qty until its id is removed from the ledger
      *or* its expiry instant is reached (expiry <= now), whichever comes first.
  R3  ids are unique (regeneration guards against collision) and opaque (uuid4 hex).
  R4  reserve validates against availability *before* recording anything, so an
      InsufficientStock (or a bad-qty ValueError) leaves the ledger untouched.
  R5  at time `now`, a reservation whose expiry <= now holds zero units.
  R6  results are deterministic in the injected `now`; no wall clock is read.
  R7  releasing an already-expired reservation is a no-op — it already held zero
      units at `now`, so removing it from the ledger cannot double-count them.
"""

from __future__ import annotations

from typing import Dict, NamedTuple, Optional
from uuid import uuid4


class InsufficientStock(Exception):
    """Raised when a reservation asks for more units than are available."""


class _Reservation(NamedTuple):
    """An outstanding hold of `qty` units against `sku`. Immutable.

    `expiry` is the instant from which the hold lapses (it holds zero units once
    `expiry <= now`); `None` means the hold never expires.
    """

    sku: str
    qty: int
    expiry: Optional[float] = None


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

    def available(self, sku: str, *, now: float = 0.0) -> int:
        """Units available for `sku` at time `now` (0 for an unknown sku).

        The sole owner of the availability rule: added units minus the units held by
        live reservations for this sku — a reservation whose expiry <= now holds zero
        units (R5). `now` is injected; no real clock is read (R6).
        """
        return self._added.get(sku, 0) - self._reserved(sku, now)

    def reserve(
        self,
        sku: str,
        qty: int,
        ttl_seconds: Optional[float] = None,
        *,
        now: float = 0.0,
    ) -> str:
        """Reserve `qty` units of `sku`; return a unique, opaque reservation id.

        If `ttl_seconds` is given the hold expires at `now + ttl_seconds`, freeing its
        units automatically from that instant (R5); `ttl_seconds=None` never expires.
        Availability is checked at `now`, so units freed by already-expired holds count.

        Raises ValueError if qty <= 0, InsufficientStock if qty exceeds availability.
        On either error nothing is recorded (R4).
        """
        if qty <= 0:
            raise ValueError(f"qty must be positive, got {qty}")
        current = self.available(sku, now=now)
        if qty > current:
            raise InsufficientStock(
                f"cannot reserve {qty} of {sku!r}: only {current} available"
            )
        expiry = None if ttl_seconds is None else now + ttl_seconds
        reservation_id = self._new_id()
        self._reservations[reservation_id] = _Reservation(sku, qty, expiry)
        return reservation_id

    def release(self, reservation_id: str) -> None:
        """Return a reservation's units to availability. No-op for an unknown or
        already-released id (idempotent)."""
        self._reservations.pop(reservation_id, None)

    # ── internals ────────────────────────────────────────────────────────────
    def _reserved(self, sku: str, now: float) -> int:
        """Units held by live reservations for `sku` at time `now`.

        A reservation counts only while it is unexpired (expiry is None, or expiry >
        now); one whose expiry <= now holds zero units (R5).
        """
        return sum(
            r.qty
            for r in self._reservations.values()
            if r.sku == sku and (r.expiry is None or r.expiry > now)
        )

    def _new_id(self) -> str:
        """A fresh opaque id, guaranteed not to collide with a live reservation."""
        reservation_id = uuid4().hex
        while reservation_id in self._reservations:
            reservation_id = uuid4().hex
        return reservation_id
