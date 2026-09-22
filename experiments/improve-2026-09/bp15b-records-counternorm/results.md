---
title: "[WITHDRAWN] BP15b result — decision survival NULL again (4/4 both arms), for a NEW structural reason: nobody had to touch the decisions"
date: 2026-09-22
status: WITHDRAWN — the records in this run were written by hand, not filed by aims, so it tested that construction rather than aims (AUDIT-record-layer-claims.md).
---

# Result: 4/4 in both arms

| arm | decision survival | touched `_allocate`? | added an idempotency guard? |
|---|---|---|---|
| r1 / r2 / r3 (code **+ records**) | **4/4 each** | no — byte-identical | no |
| n1 / n2 / n3 (code only) | **4/4 each** | no — byte-identical | no |

This time the decisions were deliberately **counter-normative** (recompute-not-idempotent; whole remainder to
the largest share; drop zero rows) and the code *looked* like three defects. The no-records arm still preserved
all three.

# Why — and it is a different failure from BP15's

BP15 failed because the decisions were **industry norms**, so instinct preserved them. BP15b's decisions were
against the norm, so that explanation is gone. The actual reason here:

**The change never forced anyone into the decision-bearing code.** Every arm — both with and without records —
implemented the fee the same way: compute `fee = total * bps // 10000`, pass `total - fee` into the
**untouched** `_allocate`, append a platform row. And every arm added `settle_preview` as a **new** entry
point rather than editing `settle`. `_allocate` is byte-identical in all six files; `settle` never grew a
read-through guard.

So the three "traps" sat in a function nobody needed to re-derive. A modifier is conservative: **it wraps
rather than rewrites.** A decision that lives inside code the change can wrap is never at risk, no matter how
counter-intuitive it is.

Worth noting: the records **did** register — each records-arm agent cited the specific ADRs and stated it had
deliberately *not* "fixed" the three behaviours. They simply had no counterfactual effect, because the
no-records agents did not touch them either.

# The design requirement this yields (for any valid record-layer test)

A documented decision is only at risk when **both** hold:
1. **Counter-normative** — the competent default points the other way (BP15's missing condition); **and**
2. **Structurally unavoidable** — the change makes the existing code untenable, forcing the region that holds
   the decision to be **re-derived** rather than wrapped (BP15b's missing condition).

Changes that would satisfy (2) on this product: a **per-payee cap with redistribution** (forces re-deriving
remainder placement and the zero filter), or **settling a batch of settlements with one global remainder**
(forces rewriting `_allocate` outright). Wrapping is not available for either.

# Status

A second honest null — and, like the first, a null **about the instrument**, not a verdict on the record
layer. Two necessary conditions are now identified; a valid test needs both at once. The only positive
record-layer signal so far remains BP15's blind design-quality read (records 37/40 vs no-records 25/40, n=1
per arm) — i.e. records affected the **quality of the new code**, not the survival of old decisions.

# ADDENDUM — the blind design-quality read, with REAL n=3 independence

All six outputs were genuinely distinct this time (six distinct texts), so unlike BP15's addendum this is
n=3 per arm. Blind judge, design rubric, scored from the code:

| arm | scores /40 | mean | worst | best | spread |
|---|---|---|---|---|---|
| **records** (r1,r2,r3) | 38, 32, 30 | **33.3** | **30** | 38 | **8** |
| **no records** (n1,n2,n3) | 37, 30, 20 | **29.0** | **20** | 37 | **17** |

**The pattern is floor-raising / variance reduction, not a higher ceiling.**

- The worst design in the whole set — **20/40**, which the judge independently called "the clear outlier and
  the only design with a real structural defect" — is a **no-records** arm. Its defect: it patches the
  platform row's amount after allocation (`fee + unallocated`), so the fee row is no longer the fee and the
  sum invariant is enforced in **two places that can drift** — precisely what `architecture.md` and the
  companion warn against ("a deduction applied *after* allocation would break the exact-sum property").
- The records arm never fell below **30**; its spread is half the no-records spread (8 vs 17).
- The **best** no-records design (37) nearly ties the best records design (38). Records did not raise the
  ceiling.

This reproduces, on the design rubric and with real independence, the same shape the rest of the campaign
found by other routes: **aims' value is reliability of the structural choice — it prevents the bad design
rather than producing a better best.**

Honest limits: n=3 per arm, one product, one judge, overlapping ranges (37 vs 38 at the top). Suggestive, not
conclusive. And note this is the value of the records on the **quality of the new code** — decision *survival*
was null in both BP15 and BP15b for the two structural reasons documented above.
