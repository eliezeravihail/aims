---
title: "a design objective takes one mandatory review-and-revise round before it can read as met"
date: 2026-09-17
---

**Context.** aims' loop measured a returned design and, if the objective looked reached, could read it
**met on the first pass** — the revise step was latent (only "when the measurement shows the objective not
yet reached, continue toward it"), never forced. The iter-plan experiment
([`../experiments/iter-plan/README.md`](../experiments/iter-plan/README.md)) found a revise round to be the
**single largest quality lever measured**: iterating lifted the clean arm 2.0 → 3.5 (bigger than guidance's
2.0 → 3.0), and one review-and-revise round rescued the worst checkout arm from an S4 (2.0 → 3.5). aims
exercised *guidance* (design as the goal) but not a *forced revise loop* — so it was leaving its biggest
lever unpulled.

**Decision.** A **`design` objective is never read as met on its first returned pass.** **One**
**measure → return-findings → revise** cycle is mandatory before a design can read `met`. Concretely: after
the measurement (`references/review.md`, including the subtractive and concept-fit passes), the Guide
returns the findings as the refined direction, the Worker revises, and the revision is re-measured — one
round, taken even when the initial design looks good. The mandate is **one** round, not iteration to
convergence: that is what was requested, and the evidence covers exactly one round (the worst checkout arm
went 2.0 → 3.5 on a single review-and-revise pass). If that one round still leaves a substantial finding,
the ordinary loop continues toward the objective as it always could — nothing here forces convergence.

**This is direct-and-measure, not a new gate.** The findings are handed back as the next direction and the
Worker revises — the same move the loop already had for an unmet objective. What changes is only that the
Guide may **not** declare a design `met` without having exercised the revise lever at least once. It does
not police the Worker, stamp accept/reject, or add an enforcement pillar; the review still *reports* and
*informs direction* (`SKILL.md`, "Direct and measure — do not coerce"). It is **one** round — the floor and
the ceiling of the mandate; anything beyond it is the ordinary loop's ordinary judgement, not forced here.

**Scope.** `design` objectives (including the opening panel-plan round — the merged result is measured and
revised like any other design). `implementation` and `refactoring` objectives keep their existing single
measurement: their lens is correctness/conformance and behavior-preservation, not the open-ended design
search a revise round mines, and forcing a revise round there would just re-run passing checks.

**Consequences.**
- `references/review.md` gains the one-round revise rule as a first-class part of measuring a design.
- `SKILL.md` step 5 and `references/modes.md` (the `review` phase / loop cursor) state that a design parks
  back toward `build` for the one revise round, is re-measured, then `ready-to-choose-next`.
- The mixed-tier and fidelity guidance in `review.md` is unaffected — it already prescribes a repair pass;
  this makes the one revise round mandatory for design quality specifically.

**Alternatives.**
- *Leave the revise step latent (status quo)* — rejected: the experiment shows the unforced loop skipped
  the largest lever; a design that "looks met" is exactly the one a first revise round most improved.
- *Make it a hard gate that rejects the design until clean* — rejected: it would install the enforcement
  pillar `SKILL.md` explicitly refuses. Direct-and-measure achieves the same revise loop without coercion.
- *Force the loop on implementation/refactoring too* — rejected: those lenses measure conformance/
  behavior-preservation, where a revise loop re-runs passing checks rather than mining design space.
