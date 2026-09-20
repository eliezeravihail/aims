---
title: "architecture"
date: 2026-09-20
---
## Insights
- Two elements, layered as a functional core behind an imperative shell:
  - `Interval` — an immutable half-open value object that owns two rules: **validity**
    (`end > start`, enforced at construction so an invalid `Interval` cannot exist) and the
    **overlap relation** between two intervals (`a.start < b.end and b.start < a.end`).
  - `Calendar` — holds the list of reservations and owns the **occupancy query** (`_is_free`): does a
    candidate overlap anything reserved. `is_free` and `book` are the public boundary.

## Decisions
- **The public seam is the two methods `book` / `is_free` speaking raw `int`s.** `Interval` is an
  internal value object; it is not part of the public contract, so the API stays primitive-typed while
  the domain logic still lives on a real type.
- **One owner per rule.** Overlap geometry lives only on `Interval.overlaps`. Request validity lives
  only in `Interval.__post_init__`, reached through the single boundary translator `Calendar._as_interval`
  (raw request -> `Interval | None`). The occupancy rule lives only in `Calendar._is_free`; both public
  methods route through it, so `is_free` and `book` can never disagree.
- **Command/query split.** `is_free` is a pure query (no mutation); `book` is the only mutator. A
  refused `book` appends nothing, so the calendar is unchanged — atomicity is structural, not guarded.
- **Boundary vocabulary.** `Interval` fails fast with `ValueError` on an invalid interval (core trusts
  its inputs); the calendar boundary catches that once and translates it into the API's
  "invalid -> not bookable / not free" contract. Validity is decided in exactly one place.

## Discussions
- **Change axes considered.** The only foreseeable variation is the reservation *store* (a list today;
  a sorted structure or interval tree if the reservation count ever grew). That variation is confined
  inside `Calendar` behind `_is_free`; `Interval` and the public seam are unaffected by it. No seam was
  added for it now (YAGNI at this scale) — the confinement already exists.
- **Rejected: an interval-tree / sorted index** for sub-linear overlap search. No stated performance
  requirement and no evidence of scale; a linear scan is correct and clearest. Recorded as the first
  place to change if a scale requirement ever appears.
