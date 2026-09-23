"""Calendar module with booking support."""


class Calendar:
    """A calendar that manages time slot bookings."""

    def __init__(self):
        """Initialize an empty calendar."""
        self._reserved = []

    def book(self, start: int, end: int) -> bool:
        """
        Reserve the half-open interval [start, end).

        Returns True if the interval was successfully booked, False if it overlaps
        with an existing booking or if the request is invalid (end <= start).
        """
        if end <= start:
            return False

        # Check each reserved interval for overlap
        for res_start, res_end in self._reserved:
            # No overlap only if: either this booking ends before or at the start
            # of the reserved interval, or it starts at or after the reserved ends
            if res_start < end and start < res_end:
                return False

        # Successfully book this interval
        self._reserved.append((start, end))
        return True

    def is_free(self, start: int, end: int) -> bool:
        """
        Check whether [start, end) could be booked without modifying the calendar.

        Returns False if end <= start or if the interval overlaps with any booking.
        Returns True if the interval is free.
        """
        if end <= start:
            return False

        # Check for conflicts with reserved intervals
        for res_start, res_end in self._reserved:
            # Overlap occurs if the start of one interval is strictly before
            # the end of the other, and vice versa
            if res_start < end and start < res_end:
                return False

        return True
