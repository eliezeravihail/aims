"""Calendar module with booking support."""


class Calendar:
    """A calendar that manages time slot bookings."""

    def __init__(self):
        """Initialize an empty calendar."""
        self._bookings = []

    def book(self, start: int, end: int) -> bool:
        """
        Reserve the half-open interval [start, end).

        Returns True if the interval was successfully booked, False if it overlaps
        with an existing booking or if the request is invalid (end <= start).
        """
        if end <= start:
            return False

        # Check for overlap with any existing booking
        for booked_start, booked_end in self._bookings:
            # Two intervals overlap if one starts before the other ends
            if start < booked_end and booked_start < end:
                return False

        # No overlap found, add the booking
        self._bookings.append((start, end))
        return True

    def is_free(self, start: int, end: int) -> bool:
        """
        Check whether [start, end) could be booked without modifying the calendar.

        Returns False if end <= start or if the interval overlaps with any booking.
        Returns True if the interval is free.
        """
        if end <= start:
            return False

        # Check for overlap with any existing booking
        for booked_start, booked_end in self._bookings:
            if start < booked_end and booked_start < end:
                return False

        return True
