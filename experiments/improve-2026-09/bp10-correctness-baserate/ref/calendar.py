"""Reference implementation for BP10 — validates the hidden tests only. Not shown to any arm.

The load-bearing corner: intervals are HALF-OPEN [start, end). Two bookings that merely
touch (one ends exactly when the next begins) DO NOT overlap. The correct overlap predicate
is strict: a.start < b.end AND b.start < a.end."""


class Calendar:
    def __init__(self) -> None:
        self._bookings = []  # list of (start, end)

    def book(self, start: int, end: int) -> bool:
        """Book [start, end) (half-open). Return True if booked, False if it overlaps an
        existing booking. A zero-or-negative-length request (end <= start) is invalid -> False.
        Touching an existing booking at a single point is NOT an overlap."""
        if end <= start:
            return False
        for (s, e) in self._bookings:
            if start < e and s < end:  # strict half-open overlap
                return False
        self._bookings.append((start, end))
        return True

    def is_free(self, start: int, end: int) -> bool:
        """True if [start, end) could be booked now (does not mutate)."""
        if end <= start:
            return False
        return all(not (start < e and s < end) for (s, e) in self._bookings)
