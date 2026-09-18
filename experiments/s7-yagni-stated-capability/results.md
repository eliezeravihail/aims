---
title: "Result — the candidate §7 clause did NOT prove necessary on an unseen product (null)"
date: 2026-09-18
---

# Result: the §7 "stated capability is never a YAGNI cut" clause is NOT folded in

Run per [`README.md`](README.md): two aims arms, identical except for **one clause** in their
`design-principles.md` (**fixed** carries the "a capability named by an R/X/C item is a present force by
definition, never a YAGNI cut" wording; **unfixed** is the current shipped wording the plant→mineral builder
used), each designed the same fresh, unseen product — an **alerting rule engine** (`card.md`) whose stated
X-items include a band predicate (X2) and a **ranged event value** (X3), the same shape of capability the
plant→mineral aims arm cut. The measure is a §1 correctness fact against the frozen `inventory.md`: does the
arm's type model **represent** the ranged/band cases (C1–C5), or does the subtractive pass collapse them to a
point (the plant→mineral S4)? n = 2 (one arm per wording).

## Outcome — both arms kept the capability. The clause changed nothing.

| arm | event-value model | ranged case (C2/C3) | band overlap (X2) | C1–C5 representable | plant→mineral S4 reproduced? |
|---|---|---|---|---|---|
| **fixed** (with the clause) | one `Interval{lo≤hi}`; single = true point `[v,v]` | ✓ | ✓ (`Threshold`\|`Band` split; band = inclusive overlap) | ✓ all five | **no** |
| **unfixed** (shipped wording) | one `Reading[low,high]`; single = `[v,v]` | ✓ | ✓ (`Threshold`\|`Band` split; band = inclusive overlap) | ✓ all five | **no** |

Both arms independently reached the **same** correct model: the event value is a closed interval, a single
reading is the genuine degenerate `[v, v]` (not an inert cram), and the value predicate is a forced
`Threshold | Band` sum split because threshold-by-max and band-by-overlap are different rules. The unfixed
arm's own self-review reasoned the point explicitly — "`[v, v]` has no inert member … the cram would be
`Ranged(min=v, max=None)`; the design deliberately does not do that" — and did **not** cut the range. The
subtractive over-cut that lost plant→mineral **did not reproduce** on this product, with or without the
clause.

## Reading

1. **The clause is not validated as necessary, so it is NOT added to `design-principles.md`.** This is the
   discipline the whole experiment exists to honour: a method change prompted by a single loss must earn its
   place on a product it has not seen, not be inserted and self-confirmed on the round that produced it. Here
   the fixed arm did **not** catch a defect the unfixed arm shipped — the unfixed arm shipped no defect — so
   there is **no measured delta**. Folding the clause in would be adding weight to the central document on
   the strength of one loss it demonstrably does not prevent here. It stays out.

2. **The honest read of the plant→mineral S4 is a builder miss, not a documented doc gap.** The shipped
   §1 ("trace the full input space") and §7 (YAGNI resolves *by the change-axes* — X4 named the very feature)
   already point the correct way; the plant→mineral builder simply did not run §1 over X4 hard enough. On
   this unseen product, a different builder on the **same** shipped wording ran §1 over X3 and got it right.
   That is evidence the existing text is sufficient for a builder who applies it, which is exactly why a
   wording change cannot be justified from the one run where a builder didn't.

3. **A null is a real result and is recorded as one.** n = 2 is small, and it does not prove the clause
   *never* helps — only that it did not help here, on the nearest unseen analogue of the loss. If a future
   run reproduces the over-cut on stated capability under the shipped wording, this experiment reopens with
   that product as a third arm. Until then the central document is left unchanged, and the loss stays
   recorded in `../plant-mineral-id/` as a builder miss the instrument correctly caught.

Both arms' full designs (and the self-review / revise rounds that produced them) are in the run scratchpad;
this file is the durable reading.
