"""A simple interval-booking calendar over integer time units.

Bookings are half-open intervals ``[start, end)``: the start is included and
the end is excluded, so ``[10, 20)`` and ``[20, 30)`` do not overlap.
"""

from bisect import bisect_right


class Calendar:
    """Reserves non-overlapping half-open integer intervals."""

    def __init__(self) -> None:
        # Bookings kept sorted by start; disjoint by construction.
        self._bookings: list[tuple[int, int]] = []

    def is_free(self, start: int, end: int) -> bool:
        """Return whether ``[start, end)`` could be booked right now.

        This is a pure query and never mutates the calendar. An interval with
        ``end <= start`` is invalid and is reported as not free.
        """
        if end <= start:
            return False

        bookings = self._bookings
        # Index of the first booking that starts strictly after `start`.
        i = bisect_right(bookings, (start, end))

        # The booking just before could straddle `start`.
        if i > 0 and bookings[i - 1][1] > start:
            return False
        # The next booking must begin at or after our end.
        if i < len(bookings) and bookings[i][0] < end:
            return False
        return True

    def book(self, start: int, end: int) -> bool:
        """Reserve ``[start, end)``.

        Return True if reserved, or False if the interval is invalid
        (``end <= start``) or overlaps an existing booking.
        """
        if not self.is_free(start, end):
            return False

        i = bisect_right(self._bookings, (start, end))
        self._bookings.insert(i, (start, end))
        return True
