class Calendar:
    """A calendar system for managing time interval bookings."""

    def __init__(self):
        """Create a new, empty calendar."""
        self._reserved_intervals = []

    def book(self, start: int, end: int) -> bool:
        """
        Reserve the half-open interval [start, end).

        Attempts to book the interval and returns True if successful.
        Returns False if the interval overlaps with an existing booking
        or if the interval is invalid (end <= start).
        """
        # Invalid interval: end must be strictly greater than start
        if end <= start:
            return False

        # Check each existing reservation for overlap
        for res_start, res_end in self._reserved_intervals:
            # Intervals [a,b) and [c,d) overlap unless b <= c or d <= a
            if not (end <= res_start or start >= res_end):
                return False

        # No overlaps detected, add reservation
        self._reserved_intervals.append((start, end))
        return True

    def is_free(self, start: int, end: int) -> bool:
        """
        Query whether [start, end) is available for booking.

        This is a pure query that does not modify the calendar.
        Returns True if the interval is available, False if it overlaps
        with any existing booking or is invalid (end <= start).
        """
        # Invalid interval: end must be strictly greater than start
        if end <= start:
            return False

        # Check each reservation for overlap
        for res_start, res_end in self._reserved_intervals:
            # Intervals overlap if neither ends before the other starts
            if not (end <= res_start or start >= res_end):
                return False

        return True
