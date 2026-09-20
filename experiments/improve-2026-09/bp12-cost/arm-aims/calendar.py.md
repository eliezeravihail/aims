---
title: "calendar.py"
date: 2026-09-20
hash: "sha256:e2f147c814604bcbb140a1100fe021e017cd556f3edb967a208c1a87377bac6f"
---
## Insights
- The whole module is two elements: `Interval` (immutable half-open value object, owns validity +
  overlap) and `Calendar` (owns the reservation list and the occupancy query). Everything the module
  does is one of three rules, each with a single home — validity, overlap, occupancy.
- `is_free` and `book` share the private core `_is_free(Interval) -> bool`. `book` never re-runs the
  overlap scan itself; it parses once and asks `_is_free`, so the query and the command are guaranteed
  to agree. A refused `book` appends nothing, so "rejection leaves the calendar unchanged" is
  structural, not a separate guard to maintain.

## Decisions
- `Interval` is immutable (`@dataclass(frozen=True)`) and rejects `end <= start` in `__post_init__`, so
  an invalid interval cannot exist and the core may trust every `Interval` it holds.
- The public API speaks raw `int`s, not `Interval`. `Interval` is an internal value object; keeping it
  off the public seam lets the domain logic live on a real type without widening the contract.
- `Calendar._as_interval` is the single trust boundary: it turns `Interval`'s `ValueError` into
  `None` ("not bookable"), so request validity is decided in exactly one place and no `ValueError`
  escapes to a caller.

## Discussions
- **`book` returns a bool while also mutating — a deliberate Command/Query Separation (§2) exception.**
  The contract mandates a success status (`book -> bool`), the "try-reserve" idiom. Recorded as a
  conscious trade-off rather than hidden: the pure query `is_free` exists precisely so callers who want
  to look without acting are not forced through the mutating path.
- **Subtractive pass.** Considered inlining `Interval` back into `Calendar` as raw `(start, end)`
  tuples. Rejected: that reintroduces primitive obsession and the `(start,end)` data clump, and scatters
  the overlap/validity rules. `Interval` is the domain's core value object, not seam machinery, so it
  earns its place. `_is_free` was also challenged and kept — it is the one owner of the occupancy query
  that both public methods route through; deleting it forces either a double parse or a duplicated scan.
- **Concept-fit pass.** `Interval` is genuinely a half-open range (not a degenerate case of some other
  type); `Calendar` is genuinely a set of reservations. No concept is crammed into a neighbouring shape;
  no inert stand-in member exists.
- Linear overlap scan (`any(... for existing ...)`) is O(n) per call. No stated performance requirement;
  correctness and clarity win. If scale ever matters, replace the list inside `Calendar` (see
  `architecture.md`) without touching `Interval` or the public seam.
