class Calendar:
    """Manages bookings of time intervals using half-open interval semantics."""

    def __init__(self):
        """Initialize an empty calendar with no bookings."""
        self._bookings = []

    def book(self, start: int, end: int) -> bool:
        """
        Attempt to reserve the half-open interval [start, end).

        Returns True if the interval was successfully booked.
        Returns False if it overlaps with any existing booking or
        if the interval is invalid (end <= start).
        """
        # Validate input: start must be strictly less than end
        if end <= start:
            return False

        # Check for conflicts with existing bookings
        for existing_start, existing_end in self._bookings:
            # Two intervals overlap if they share any point
            # [a,b) and [c,d) overlap iff a < d AND c < b
            if start < existing_end and existing_start < end:
                return False

        # No conflicts, record the booking
        self._bookings.append((start, end))
        return True

    def is_free(self, start: int, end: int) -> bool:
        """
        Determine if [start, end) is available for booking.

        This is a non-mutating query that checks whether the interval
        could be booked without any conflicts.
        Returns True if free, False if occupied or invalid (end <= start).
        """
        # Validate input: start must be strictly less than end
        if end <= start:
            return False

        # Check for any overlapping bookings
        for existing_start, existing_end in self._bookings:
            if start < existing_end and existing_start < end:
                return False

        return True
