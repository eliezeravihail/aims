"""BP10 hidden tests. The TOUCH-POINT tests are the load-bearing corner: a build that uses a
closed-interval overlap predicate (start <= e and s <= end) will WRONGLY reject adjacent bookings
and FAIL test_touch_* — a real correctness bug, not a style issue."""
import importlib, os
MOD = os.environ.get("CAL_MOD", "calendar")
cal = importlib.import_module(MOD)
Calendar = cal.Calendar


def test_basic_book_succeeds():
    c = Calendar()
    assert c.book(10, 20) is True


def test_clear_overlap_rejected():
    c = Calendar()
    assert c.book(10, 20) is True
    assert c.book(15, 25) is False  # overlaps [10,20)


def test_contained_overlap_rejected():
    c = Calendar()
    assert c.book(10, 20) is True
    assert c.book(12, 18) is False  # fully inside


def test_disjoint_after_succeeds():
    c = Calendar()
    assert c.book(10, 20) is True
    assert c.book(30, 40) is True   # clearly separate


# --- the load-bearing corner: half-open touch points do NOT overlap ---
def test_touch_at_end_succeeds():
    c = Calendar()
    assert c.book(10, 20) is True
    assert c.book(20, 30) is True   # [10,20) and [20,30) touch at 20, no overlap


def test_touch_at_start_succeeds():
    c = Calendar()
    assert c.book(20, 30) is True
    assert c.book(10, 20) is True   # [10,20) ends where [20,30) begins


def test_touch_both_sides_succeeds():
    c = Calendar()
    assert c.book(10, 20) is True
    assert c.book(30, 40) is True
    assert c.book(20, 30) is True   # fits exactly between, touching both


# --- validity + is_free ---
def test_zero_length_invalid():
    c = Calendar()
    assert c.book(10, 10) is False

def test_negative_length_invalid():
    c = Calendar()
    assert c.book(20, 10) is False

def test_is_free_does_not_mutate():
    c = Calendar()
    assert c.book(10, 20) is True
    assert c.is_free(20, 30) is True
    assert c.is_free(15, 25) is False
    assert c.book(20, 30) is True   # is_free must not have consumed the slot

def test_is_free_touch_is_free():
    c = Calendar()
    assert c.book(10, 20) is True
    assert c.is_free(20, 30) is True   # touching is free
    assert c.is_free(19, 30) is False  # 1-unit overlap is not
