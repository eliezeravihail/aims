"""Calendar module with booking support."""


class Calendar:
    """A calendar that manages time slot bookings."""

    def __init__(self):
        """Initialize an empty calendar."""
        self._intervals = []

    def book(self, start: int, end: int) -> bool:
        """
        Reserve the half-open interval [start, end).

        Returns True if the interval was successfully booked, False if it overlaps
        with an existing booking or if the request is invalid (end <= start).
        """
        if end <= start:
            return False

        # Check if this interval overlaps with any existing interval
        if not self.is_free(start, end):
            return False

        # Add the interval to our list of bookings
        self._intervals.append((start, end))
        return True

    def is_free(self, start: int, end: int) -> bool:
        """
        Check whether [start, end) could be booked without modifying the calendar.

        Returns False if end <= start or if the interval overlaps with any booking.
        Returns True if the interval is free.
        """
        if end <= start:
            return False

        for interval_start, interval_end in self._intervals:
            # Intervals [start, end) and [interval_start, interval_end) overlap if:
            # the first interval contains a point that the second interval contains
            if not (end <= interval_start or interval_end <= start):
                return False

        return True
