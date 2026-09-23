class Calendar:
    """A simple calendar for booking time intervals."""

    def __init__(self):
        """Initialize an empty calendar."""
        self.bookings = []

    def book(self, start: int, end: int) -> bool:
        """
        Reserve the half-open interval [start, end).

        Returns True if successfully reserved, False if it overlaps with
        any existing booking or if the interval is invalid (end <= start).
        """
        # Reject invalid intervals
        if end <= start:
            return False

        # Check for overlap with any existing booking
        for booked_start, booked_end in self.bookings:
            # Two half-open intervals [a,b) and [c,d) overlap iff a < d and c < b
            if start < booked_end and booked_start < end:
                return False

        # No conflict found, add the booking
        self.bookings.append((start, end))
        return True

    def is_free(self, start: int, end: int) -> bool:
        """
        Check whether [start, end) could be booked right now without modifying the calendar.

        Returns True if the interval is available (no overlaps), False otherwise.
        Returns False for invalid intervals (end <= start).
        """
        # Reject invalid intervals
        if end <= start:
            return False

        # Check if any existing booking overlaps
        for booked_start, booked_end in self.bookings:
            if start < booked_end and booked_start < end:
                return False

        return True
