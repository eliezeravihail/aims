"""An in-memory reservation calendar over half-open integer intervals.

No external dependencies. Time is measured in opaque integer units; the calendar
attaches no meaning to them beyond ordering. Two reservations may *touch* (share a
boundary point) but never *overlap* (share an interior point), because the intervals
are half-open.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Interval:
    """A half-open interval ``[start, end)``: includes ``start``, excludes ``end``.

    An ``Interval`` cannot exist in an invalid state — a non-positive-length
    interval (``end <= start``) is rejected at construction, so every ``Interval``
    that exists is well-formed and the rest of the code may trust it. A trust
    boundary that accepts raw user input translates that rejection into its own
    vocabulary rather than letting the exception escape (see ``Calendar``).
    """

    start: int
    end: int

    def __post_init__(self) -> None:
        if self.end <= self.start:
            raise ValueError(
                f"interval end ({self.end}) must be greater than start ({self.start})"
            )

    def overlaps(self, other: "Interval") -> bool:
        """Whether this interval shares an interior point with ``other``.

        Half-open intervals that only meet at a boundary — e.g. ``[10, 20)`` and
        ``[20, 30)`` — do **not** overlap: the shared endpoint is excluded from
        both, so it belongs to neither interval's occupied set.
        """
        return self.start < other.end and other.start < self.end


class Calendar:
    """A set of reserved intervals; reservations may touch but never overlap.

    ``book`` is the only operation that mutates the calendar; ``is_free`` is a
    pure query. The single rule — *a request may be booked iff it is valid and
    overlaps nothing already reserved* — has one home, the private core
    ``_is_free``. Both public entry points route through it, so the query and the
    command can never disagree about what "free" means.
    """

    def __init__(self) -> None:
        self._reservations: list[Interval] = []

    def is_free(self, start: int, end: int) -> bool:
        """Whether ``[start, end)`` could be booked right now. Never mutates.

        A request with ``end <= start`` is invalid and is never free.
        """
        requested = self._as_interval(start, end)
        return requested is not None and self._is_free(requested)

    def book(self, start: int, end: int) -> bool:
        """Reserve ``[start, end)``. Return True if reserved, False otherwise.

        A request is refused when it is invalid (``end <= start``) or overlaps an
        existing reservation. A refused request leaves the calendar unchanged.
        """
        requested = self._as_interval(start, end)
        if requested is None or not self._is_free(requested):
            return False
        self._reservations.append(requested)
        return True

    def _is_free(self, requested: Interval) -> bool:
        """The occupancy rule over a valid interval: overlaps nothing reserved.

        The functional core — it assumes a well-formed ``Interval`` and is the one
        place that decides freedom against the current reservations.
        """
        return not any(existing.overlaps(requested) for existing in self._reservations)

    @staticmethod
    def _as_interval(start: int, end: int) -> Interval | None:
        """Parse a raw request into an ``Interval``, or ``None`` if it is invalid.

        The calendar's trust boundary (the imperative shell): the sole place that
        turns ``Interval``'s construction rule into the API's "invalid -> not
        bookable" contract, so request validity is decided in exactly one place.
        """
        try:
            return Interval(start, end)
        except ValueError:
            return None
