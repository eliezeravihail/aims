---
title: "iter-plan — does grade→correct→revise beat a long upfront brief?"
date: 2026-09-17
---

# iter-plan — iteration vs. upfront guidance

A probe of a planning method we called **iter-plan**: a *clean* agent is handed **product requirements
only** (deliberately **without** aims' design principles), produces a design, then a judge grades it and
returns a **correction list**; the agent revises; repeat until the review raises **no substantial
architecture comment**. The hypothesis under test was the uncomfortable one for aims: *if a clean,
unguided agent that iterates on its own output reaches the same quality — faster and cheaper — than an
agent handed a long principles brief up front, then aims' whole premise (guide the construction with the
design as the goal) is weaker than it claims.*

The product was the frozen checkout-pricing pilot (the same PCT/AMT/BOGO + NORTH/SOUTH-tax product the
re-grades use — [`../judging-rubric/checkout-spec-inventory.md`](../judging-rubric/checkout-spec-inventory.md)).
All arms were graded blind against the single source
([`../../skills/aims-guide/references/design-principles.md`](../../skills/aims-guide/references/design-principles.md)
§1–§18) with the scoring layer in [`../judging-rubric/quality-metrics.md`](../judging-rubric/quality-metrics.md)
and the fixed Step-0 inventory. Raw arm drafts were kept as run-state by-products (scratch, not filed as
knowledge, like `.aims/panel/`); only the readings and what they imply are recorded here.

## The 2×2 — guidance × iteration

Two levers, crossed: **guidance** (requirements only vs. requirements + the design principles up front)
and **iteration** (one single pass vs. grade→correct→revise to convergence).

| | single pass | iterate to convergence |
|---|---|---|
| **clean** (requirements only) | **2.0** | **3.5** |
| **guided** (requirements + principles up front) | **3.0** | **3.0** |

Reading, holding the product and judge fixed:

- **Iteration is the larger lever.** It lifted the clean arm **2.0 → 3.5** — from the field's worst to a
  tie with its best single-pass arm. That one grade jump is bigger than anything guidance did on its own.
- **Guidance helps a single pass** (2.0 → 3.0) — a real effect, smaller than iteration's.
- **The levers are substitutes at the top, not additive.** A guided arm that then iterated did **not**
  climb past 3.0 here: once the principles were in the brief, the revise loop found little more to
  correct, so clean+iterate essentially *caught up to* guided by a different route rather than the two
  stacking. The clean arm reached quality by discovering, through correction, what the guided arm was
  told at the start.

The honest conclusion for aims' premise: **iterating on a design is at least as strong a quality lever as
loading principles up front — and aims, as it stood, exercised guidance but not a forced revise loop.**
That is the gap this experiment closed (see "What we changed", below).

## Single-judge sweep — all six arms, one judge, one inventory

To remove cross-judge noise from the 2×2, one neutral judge re-graded all six designs (the four 2×2 cells
plus the two pilot reference arms, plain and OpenSpec) against the same inventory in one sitting:

| arm | grade |
|---|---|
| plain (pilot reference) | 3.9 |
| OpenSpec (pilot reference) | 3.5 |
| clean + iterate | 3.5 |
| guided + iterate | 3.0 |
| guided + single | 3.0 |
| clean + single | 2.0 |

Same order as the 2×2, and it places the iterated clean arm level with OpenSpec — a strong-but-not-top
result reached from requirements alone plus a correction loop.

## The panel-rescue — one review round on the worst arm

The most direct evidence for a *mandatory* revise round came from rescuing the checkout arm that had
placed **last** on the cross-experiment re-grade: the panel-built design capped at **2.0 by an S4**
(no cart-discount→line allocation, so SOUTH per-line tax fell on undiscounted amounts —
[`../judging-rubric/regrade-results.md`](../judging-rubric/regrade-results.md)). Given exactly **one**
review-and-revise round — measure, return the findings, revise once — that same arm went **2.0 → 3.5**:
the revise round surfaced and closed the allocation gap the single pass had shipped. One round, on the
worst arm, moved it from last to mid-field.

## Confounds — why none of these grades is trustworthy to ±0.5

This is n = 1 per cell, judged by an LLM, and three confounds are each **larger than the fine method
signal** they sit under. Stated plainly so no reader over-reads the tables:

- **Judge calibration noise (±0.5).** The same clean+iterate design scored **4.0** by its own loop-judge
  during the run and **3.5** by the single-judge sweep — no change to the artifact, only a different
  judge. A 0.5 swing with no qualitative disagreement is the floor of this instrument's precision, so a
  0.5 gap between two arms is inside the noise, not a ranking.
- **Artifact maturity.** The pilot reference designs (plain, OpenSpec) are mature ~1000–2000-line
  documents; the iter-plan drafts are ~35–150-line sketches. A judge reading a fuller artifact has more
  to credit and more to fault — the comparison is not like-for-like, and maturity plausibly moves a grade
  as much as method does.
- **Correction-round count.** "Iterate to convergence" is not a fixed dose: the clean arm took more
  correction rounds than the guided arm, so "clean+iterate vs guided+iterate" also varies the number of
  rounds, not only the starting guidance. The lever and its dose are entangled at n = 1.

So the tables show a **direction** (iteration is a large lever; guidance is a smaller one; they substitute
near the top), not a leaderboard. Any single grade is suggestive; the value is the repeated shape across
the 2×2, the sweep, and the rescue.

## What we changed in aims as a result

The finding — *a revise round is the single biggest quality lever, and aims exercised guidance but not a
forced revise loop* — is now built into the method: a design objective is never read as met on its first
pass. **At least one measure → return-findings → revise cycle is mandatory**, and the loop iterates until
a review raises no substantial architecture finding (convergence). This stays *direct-and-measure*, not a
gate: the findings are handed back as the next direction and the Worker revises; the Guide simply refuses
to declare "met" without having exercised the lever at least once. Recorded in
[`../../decisions/0011-mandatory-review-revise-round.md`](../../decisions/0011-mandatory-review-revise-round.md);
wired into [`../../skills/aims-guide/references/review.md`](../../skills/aims-guide/references/review.md)
and `SKILL.md` step 5.

## Status

- **n = 1** per cell, one product, LLM-judged; the three confounds above swamp any sub-0.5 gap.
- The claim this experiment supports is narrow and now acted on: **iterating a design measurably improves
  it, enough that a forced revise round belongs in the method.** It does **not** establish that unguided
  beats guided — the two substitute near the top, and guidance still lifts a single pass.
