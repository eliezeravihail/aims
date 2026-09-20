---
title: "I5 result — the record confirmed but did not change the outcome (null; honest limitation noted)"
date: 2026-09-20
---

# I5 — record-layer trap continuity: NULL

Pre-registered (`plan.md`): the record is load-bearing iff the **with-record** arm PASSES (new split preserves
`sum == total`) where the **no-record** arm FAILS (introduces an independent-rounding split). Both same = null.

## Outcome — both arms passed, by reusing `allocate`

Scored mechanically on the delivered code (`target-with-record/allocate.py`, `target-no-record/allocate.py`):

| arm | delivered `split_shipping` | `split_shipping(1000,[1,1,1])` | verdict |
|---|---|---|---|
| with-record | `return allocate(fee_cents, line_totals)` | `[334,333,333]` sum **1000** | **PASS** |
| no-record | `return allocate(fee_cents, line_totals)` | `[334,333,333]` sum **1000** | **PASS** |

Both arms delegated to `allocate` (largest-remainder), so neither re-introduced the independent-rounding
trap. **Null** — the record did not change the outcome.

- The **with-record** arm cited the companion's D1 explicitly ("any new place that splits money must go
  through `allocate`... never a fresh independent-rounding loop") and avoided the trap knowingly.
- The **no-record** arm reached the same code by following the **in-code precedent**: it saw
  `allocate_discount` already delegating to `allocate` and treated that as "the established grain," adding
  `split_shipping` as a third sibling delegate.

## The honest limitation (why this null is weak evidence, not strong)

This experiment did **not** cleanly isolate the record's value: the target carried a **visible in-code
precedent** (`allocate_discount` delegating to `allocate`) in *both* snapshots. That precedent — not the
record — is the most likely reason the no-record arm reused `allocate`. So the record's marginal signal was
**swamped by a signal already present in the code**. A sharper test would strip the in-code precedent so the
*only* thing telling a fresh session "reuse the owner, don't independently round" is the co-located record;
then a no-record arm that writes a fresh `round(fee*w/total)` loop would fail while a with-record arm passes.

That sharper test is **not** run here, and deliberately not chased until a win — but the limitation is the
finding: **at any scale where the code itself carries the pattern, the record confirms rather than changes
the outcome**, which is exactly the paper's honest position (the record layer is unproven in *outcomes*
because every tested codebase was re-derivable / carried its own signal). Isolating the record's outcome
value needs a codebase large or opaque enough that the pattern is *not* visible in the code — the paper's
stated frontier, which a design-only or single-small-module A/B cannot reach.

**Verdict:** null; no method change. Consistent with `../../refactoring-continuity/` (record adds legibility,
not a different outcome, at re-derivable scale).
