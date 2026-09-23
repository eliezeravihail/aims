# Task: a simple booking calendar

Build a Python module `calendar.py`. No external dependencies. Integer time units.

## API (names are contractual — a hidden test suite imports exactly these)

- `Calendar()` — a new, empty calendar.
- `calendar.book(start: int, end: int) -> bool` — reserve the **half-open interval `[start, end)`**
  (includes `start`, excludes `end`). Return `True` if the reservation is made, `False` if it **overlaps**
  any existing booking. A request with `end <= start` is invalid and returns `False`.
- `calendar.is_free(start: int, end: int) -> bool` — return whether `[start, end)` could be booked right now,
  **without** modifying the calendar. `end <= start` returns `False`.

## Examples
- `book(10, 20)` → `True`. Then `book(15, 25)` → `False` (overlaps [10,20)). Then `book(30, 40)` → `True`
  (clearly separate).
- `book(12, 18)` after `book(10, 20)` → `False` (fully inside).

## Notes
- Keep it clean and correct. `is_free` must be a pure query (no mutation).
- Unknown/empty calendar: any valid request is bookable.
