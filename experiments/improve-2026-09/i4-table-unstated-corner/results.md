---
title: "I4 result — the table did NOT beat shipped §1 even on an unstated corner (null; table decisively closed)"
date: 2026-09-20
---

# I4 — input-space table on an implied-but-unstated corner: NULL

Pre-registered (`plan.md`): does the mechanical table catch a corner **implied but not stated** — the
half-open touch-point (adjacency) and zero-length request — that a prose §1 trace might skip? One shot,
appointment-slot checker, base vs table, aims-as-is.

## Score — both arms handled every unstated corner. Tie.

| probe | base arm | table arm |
|---|---|---|
| U1 adjacency `[12,13)` vs `[13,14)` → free | ✓ strict `<` overlap (`s<d ∧ c<e`) → meets = free | ✓ strict `<` overlap → touch = free |
| U2 adjacency other side → free | ✓ met-by = free | ✓ free |
| U3 zero-length `[13,13)` → defined | ✓ `Interval` invariant `start<end` rejects at construction | ✓ same (rejected, open decision flagged) |
| U4 identical `[13,14)`=`[13,14)` → not free | ✓ both conjuncts true → conflict | ✓ conflict |
| **total** | **4 / 4** | **4 / 4** |

Both arms independently pinned the **strict half-open overlap predicate `s < other.end ∧ other.start < self.end`**,
explicitly reasoned that `≤` would wrongly report touching as overlap, and enumerated the full relative-position
space (the base arm listed all Allen relations; the table arm listed the boundary rows). The base arm reached
this via the shipped §1 "trace the full input space" + concept-fit passes, **without** the mechanical table.

## Verdict: null → the input-space table is decisively not adopted

Across **three** unseen products now (P1 shipping, P2 discount, and this sharper unstated-corner slot
checker), the table arm never represented or handled a corner the base arm missed. The classic half-open
off-by-one — the corner most likely to slip a prose trace — did **not** slip it: a strong model running the
shipped §1 traces the relative-position space and pins strict `<`.

The honest, consolidated finding: **the shipped §1 "trace the full input space (the procedure, not just the
cases)" already produces the enumeration the input-space table was meant to force** — on stated axes and on
implied-but-unstated corners alike. The table is redundant machinery. It is not folded into
`design-principles.md`. This closes the I1/I4 question: the plant→mineral loss it was inspired by was a
builder slip, not a documented gap a table fixes.
