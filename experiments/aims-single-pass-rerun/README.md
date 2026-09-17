---
title: "aims single-pass re-run of the checkout pilot, building to the corrected principles"
date: 2026-09-17
---

# aims single-pass re-run — checkout pricing

The aims arm re-run on the pilot's checkout-pricing product using **single-pass planning** (one designer,
`/aims-plan` — **not** the panel), building to the corrected single-source principles
([`../../skills/aims-guide/references/design-principles.md`](../../skills/aims-guide/references/design-principles.md),
now including §13 functional correctness) with the build-side discipline in
[`../judging-rubric/quality-metrics.md`](../judging-rubric/quality-metrics.md). Stage 1 was designed blind to
later stages; each stage ran the §13 correctness trace **over the full input space**, not just the listed
cases.

The point of the run: the earlier **panel** version placed last on a re-grade because of an S4 — it never
allocated a cart-level discount to lines, so SOUTH per-line tax fell on undiscounted amounts
([`../aims-upgraded-rerun`](../aims-upgraded-rerun/results.md), [`../judging-rubric/regrade-results.md`](../judging-rubric/regrade-results.md)).
This single-pass run tests whether **building to §13** (with the mandated full-space trace) catches that gap
on its own — with less machinery than the panel.

- [`arm/stage-1.md`](arm/stage-1.md) — price a cart (blind to later stages).
- [`arm/stage-2.md`](arm/stage-2.md) — explanations + non-stackable.
- [`arm/stage-3.md`](arm/stage-3.md) — markets + tax.

**Result of the §13 trace at stage 3:** the single-pass designer discovered, from the requirement (not from a
stated case), that a multi-line SOUTH cart carrying a cart-level discount needs the discount **allocated
across the lines** so per-line tax falls on the discounted amount — and built the allocation (proportional to
gross, leftover pennies by largest remainder, line finals summing exactly to the cart net). SOUTH tax is
modeled as a **decomposition** of the already-final inclusive amount (not a delta); NORTH VAT is one appended
adjustment. So the stage-2 "deltas sum exactly / amount == explanation" invariant is preserved in both
markets.

The blind neutral grade of this arm under the same rubric + fixed inventory is recorded alongside the other
arms in [`../judging-rubric/regrade-results.md`](../judging-rubric/regrade-results.md).
