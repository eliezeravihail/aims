"""Tests for calendar.py. Stdlib unittest only, no external dependencies.

Each test states one decision the calendar makes, including paths that already
look correct (regression guards), per the aims testing discipline.
"""

import unittest

from calendar import Calendar, Interval


class BookingTest(unittest.TestCase):
    def setUp(self) -> None:
        self.cal = Calendar()

    # --- the spec's worked examples --------------------------------------

    def test_spec_examples(self) -> None:
        self.assertTrue(self.cal.book(10, 20))
        self.assertFalse(self.cal.book(15, 25))  # overlaps [10,20)
        self.assertTrue(self.cal.book(30, 40))  # disjoint

    def test_contained_request_is_rejected(self) -> None:
        self.assertTrue(self.cal.book(10, 20))
        self.assertFalse(self.cal.book(12, 18))  # strictly inside [10,20)

    # --- overlap geometry -------------------------------------------------

    def test_left_overlap_rejected(self) -> None:
        self.assertTrue(self.cal.book(10, 20))
        self.assertFalse(self.cal.book(5, 15))  # spills across start

    def test_right_overlap_rejected(self) -> None:
        self.assertTrue(self.cal.book(10, 20))
        self.assertFalse(self.cal.book(18, 25))  # spills across end

    def test_exact_duplicate_rejected(self) -> None:
        self.assertTrue(self.cal.book(10, 20))
        self.assertFalse(self.cal.book(10, 20))

    def test_superset_request_rejected(self) -> None:
        self.assertTrue(self.cal.book(10, 20))
        self.assertFalse(self.cal.book(5, 25))  # fully contains an existing booking

    def test_adjacent_bookings_allowed_both_sides(self) -> None:
        # Half-open intervals that only touch at a boundary do not overlap.
        self.assertTrue(self.cal.book(10, 20))
        self.assertTrue(self.cal.book(20, 30))  # touches on the right
        self.assertTrue(self.cal.book(0, 10))  # touches on the left

    # --- validity ---------------------------------------------------------

    def test_empty_interval_is_invalid(self) -> None:
        self.assertFalse(self.cal.book(20, 20))
        self.assertFalse(self.cal.is_free(20, 20))

    def test_reversed_interval_is_invalid(self) -> None:
        self.assertFalse(self.cal.book(20, 10))
        self.assertFalse(self.cal.is_free(20, 10))

    def test_negative_units_are_ordinary(self) -> None:
        # Integers may be negative; only ordering matters.
        self.assertTrue(self.cal.book(-10, -5))
        self.assertFalse(self.cal.book(-7, -3))  # overlaps
        self.assertTrue(self.cal.book(-5, 0))  # adjacent, allowed

    # --- empty calendar ---------------------------------------------------

    def test_empty_calendar_anything_valid_is_free(self) -> None:
        self.assertTrue(self.cal.is_free(0, 1))
        self.assertTrue(self.cal.is_free(-100, 100))
        self.assertFalse(self.cal.is_free(5, 5))  # still must be valid


class QueryPurityTest(unittest.TestCase):
    def setUp(self) -> None:
        self.cal = Calendar()

    def test_is_free_does_not_mutate(self) -> None:
        # Querying a free slot must not reserve it: a later book still succeeds.
        self.assertTrue(self.cal.is_free(10, 20))
        self.assertTrue(self.cal.is_free(10, 20))  # repeatable
        self.assertTrue(self.cal.book(10, 20))  # slot was never taken

    def test_is_free_agrees_with_book(self) -> None:
        self.cal.book(10, 20)
        # is_free predicts book's answer for both a busy and a free slot.
        self.assertFalse(self.cal.is_free(15, 25))
        self.assertFalse(self.cal.book(15, 25))
        self.assertTrue(self.cal.is_free(20, 30))
        self.assertTrue(self.cal.book(20, 30))

    def test_rejected_book_leaves_calendar_unchanged(self) -> None:
        self.assertTrue(self.cal.book(10, 20))
        self.assertFalse(self.cal.book(15, 25))  # rejected
        self.assertFalse(self.cal.book(0, 0))  # rejected (invalid)
        # The failed attempts reserved nothing, so the gaps remain bookable.
        self.assertTrue(self.cal.is_free(20, 30))
        self.assertTrue(self.cal.book(20, 25))


class IntervalTest(unittest.TestCase):
    def test_rejects_non_positive_length(self) -> None:
        with self.assertRaises(ValueError):
            Interval(5, 5)
        with self.assertRaises(ValueError):
            Interval(5, 4)

    def test_overlap_is_symmetric(self) -> None:
        a, b = Interval(10, 20), Interval(15, 25)
        self.assertTrue(a.overlaps(b))
        self.assertTrue(b.overlaps(a))

    def test_touching_intervals_do_not_overlap(self) -> None:
        self.assertFalse(Interval(10, 20).overlaps(Interval(20, 30)))
        self.assertFalse(Interval(20, 30).overlaps(Interval(10, 20)))

    def test_interval_is_immutable(self) -> None:
        with self.assertRaises(Exception):
            Interval(10, 20).start = 0  # type: ignore[misc]


if __name__ == "__main__":
    unittest.main()
