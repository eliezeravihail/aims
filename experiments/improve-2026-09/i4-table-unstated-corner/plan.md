---
title: "I4 — the sharper, fair test of the input-space table: an IMPLIED-but-UNSTATED corner"
date: 2026-09-20
status: pre-registered before any arm ran; distinct hypothesis from I1 (the I1 null stands)
---

# Why this exists

I1 tested the input-space table on products whose change-axes were **stated**, and found a null — both base
and table arms traced the stated corners correctly. That leaves the table's *intended* value untested: the
plant→mineral loss was a corner a builder skipped. So the sharper, fair question is:

> **Does the mechanical table catch a corner that is IMPLIED by the rules but NOT stated as a case or a
> change-axis — where a prose §1 trace might skip it?**

This is a **distinct hypothesis**, not a re-roll of I1. It is **one shot** (n=1, one product), reported
**whatever it shows**. A win here is **suggestive only** (n=1) and does not by itself adopt the table; a null
closes the table question decisively. The I1 n=2 null is unaffected either way.

# Product (design-only): an appointment-slot checker
- **R1** Bookings are half-open intervals `[start, end)` on a single resource; `is_free(s, e)` answers
  whether a requested `[s, e)` conflicts with any booking.
- **R2** A conflict is a real overlap; `is_free` returns false iff the request overlaps some booking.
- **X1** later, multiple resources; **X2** later, recurring bookings.
- **C1** request `[13:00,14:00)` with a booking `[13:30,14:30)` → not free (clear overlap).
- **C2** request `[09:00,10:00)` with a booking `[15:00,16:00)` → free (clearly disjoint).

The card states the half-open rule and gives only a **clearly-overlapping** and a **clearly-disjoint** case.
It never states the **touch-point** or **zero-length** cases — they are implied by half-open semantics.

# Hidden probes (frozen; arms never see them) — the UNSTATED implied corners
| # | corner | request vs booking | required output | correct iff the design… |
|---|---|---|---|---|
| U1 (primary) | adjacency / touch-point | `[12:00,13:00)` vs booking `[13:00,14:00)` | **free** (half-open: end==start is not overlap) | uses a strict half-open overlap `s < e2 ∧ s2 < e`, not `≤` |
| U2 | adjacency other side | `[14:00,15:00)` vs `[13:00,14:00)` | **free** | same predicate |
| U3 | zero-length request | `[13:00,13:00)` vs `[13:00,14:00)` | defined (empty request occupies nothing → free, or rejected at construction) — not a crash | the empty interval has a defined handling |
| U4 | exact-cover | `[13:00,14:00)` vs `[13:00,14:00)` | **not free** (identical → overlap) | predicate reports overlap for equal intervals |

**Metric (fixed now).** Score = # of U1–U4 the delivered design handles **correctly** (right output, read
from the design's stated overlap predicate / interval type). **I4 is suggestive-for-the-table iff the table
arm handles strictly more unstated corners than base** (esp. U1, the classic half-open off-by-one). Both
correct, or both wrong, is a null. Arms run aims as-is; the only variable is the §1 input-space-table
variant (`../i1-input-space-table/arm-table-design-principles.md`).
