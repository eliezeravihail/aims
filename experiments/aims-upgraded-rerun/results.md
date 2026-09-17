---
title: "upgraded-aims re-run of the checkout-pricing pilot — same product, method before/after"
date: 2026-09-17
---

# Re-running the pilot aims lost, with upgraded aims

The frozen [`../aims-vs-openspec`](../aims-vs-openspec/results.md) pilot (ran 2026-09-15/16, on aims commit
`3eab41d`) had aims place **third of three on design quality** and **reopen the most of its own structure**
(survival = 11) on a **checkout pricing service** evolved across three staged cards. Between that pilot and
the [marketplace change-absorption probe](../marketplace-change-absorption/results.md) (2026-09-17), aims was
**substantially upgraded** — the self-redesign refactor of the panel role model (`panel-plan.md`) and the
measurement lens (`review-panel.md`) merged via #60 on 2026-09-16/17.

This is the clean **same-product before/after** that isolates the upgrade from the product: **re-run only the
aims arm, with the upgraded method, on the pilot's identical cards, and apply the same judging.** The
plain and OpenSpec arms are reused unchanged from the pilot, so the only variable is the aims method version.

> **n = 1, and read the two readings separately.** This is one run of one arm. It is not PROTOCOL-grade in
> isolation; its value is the before/after against a frozen prior run on the same cards.

## How it was run

The upgraded aims **panel** produced a design per stage (three axis Workers — clean-code / encapsulation /
genericity — reading `panel-plan.md` §axes + `design-principles.md`, then a merge agent reading
`panel-plan.md` §"The merge agent"), all as real subagents. Stage 1's objective was set blind to the later
stages (as the pilot requires); stages 2 and 3 extended the prior merged design against the next card.
Oracle clarifications were supplied verbatim from the pilot's `hidden/spec-and-oracle.md`. The arm's three
designs: [`arm/stage-1.md`](arm/stage-1.md), [`arm/stage-2.md`](arm/stage-2.md), [`arm/stage-3.md`](arm/stage-3.md).
Judging (blind, method-anonymized) in [`judges.md`](judges.md).

## Result — split cleanly by reading

### Q2 survival (the pilot's declared PRIMARY reading): decisive win for the upgrade

| arm (same product, same 3 cards) | s1→s2 | s2→s3 | **total reopened+discarded** |
|---|---|---|---|
| OpenSpec (pilot) | 4 | 4 | 8 |
| plain (pilot) | 3 | 6 | 9 |
| **aims — OLD (pilot, `3eab41d`)** | 4 | 7 | **11** |
| **aims — UPGRADED (this run)** | 1 | 0 | **1** |

The pilot's **disqualifying falsifier** (README §8: "the aims arm reopens more than OpenSpec → the central
claim fails on this product") fired at 11 > 8. The upgraded arm reopens **1** — the fewest of any arm, and
the decisive tax/market stage that cost old aims **7** reopens cost the upgraded arm **0**. On the reading
the pilot itself calls primary, the upgrade reverses the loss decisively.

### Q1 design quality (two opposite dispositions): still third — and now the judges agree why

Both blind judges again place the upgraded aims arm **last**:

| disposition | pilot verdict (old aims) | this run (upgraded aims = "Design R") |
|---|---|---|
| YAGNI / simplicity | OpenSpec; aims third | **OpenSpec (Q); R third** |
| invariant ownership | plain; aims third | **P & Q co-lead; R clearly behind** |

In the **pilot the two dispositions split** (so the top verdict was "a taste artifact"). **Here they agree**,
and pin R to the *same* structural fault: it models **NORTH tax as a movement (a delta folded into the
explanation chain) but SOUTH tax as a decomposition** — two structures for one concept (VAT). The
invariant-ownership judge additionally found a **correctness gap**: R assigns no owner for apportioning a
cart-level discount onto lines, so its own stated SOUTH figure (C2: line 10.80, tax 1.80) is unreachable
from its pipeline (line stays 12.00, tax 2.00). Both judges credited R's `Market` interface as a genuinely
*earned* abstraction — but it "does not buy back the concept-fit fault."

## What this actually shows

- **The upgrade is real and substantial — on change-absorption.** Same product, same cards: old aims
  reopened 11, upgraded aims reopened 1. That is the reading the pilot built itself around, and the reading
  whose failure the pilot named disqualifying. So the earlier "it depends on the product" framing was wrong
  for the reason the user gave: **the method changed between the two probes, and on the primary reading the
  change moved aims from worst to best on this very product.**
- **The upgrade did NOT fix the design-quality third place**, and this time it is not a taste artifact — the
  two opposite dispositions agree on the deciding fact. The **failure mode changed**: old aims *dissolved*
  the delta-sum invariant by folding tax into the explanation chain; upgraded aims *preserves* the invariant
  but **splits one tax concept into two shapes** (NORTH movement / SOUTH decomposition) and misses cart-
  discount apportionment for SOUTH.
- **The tension is the real lesson.** The choice that won the survival count is the one the quality judges
  fault: reusing the existing delta chain for NORTH VAT is why stage 3 reopened nothing *and* is the
  value-correct cram the concept-fit pass targets. Optimizing change-locality and optimizing concept-fit
  pulled in opposite directions here, and the panel took the change-locality side.

## Validity / deviations (declared)

- **n = 1**, one arm, one product. The plain/OpenSpec arms are the pilot's originals (not re-run), so only
  the aims version varies — good for isolating the upgrade, but still a single sample.
- **Panel on every stage.** Real aims runs the panel only on the *opening* round; stages 2–3 would be
  single-pass `/aims-plan`. This run used the panel on all three stages, so the arm got **more** design
  effort than real aims gives at stages 2–3. This favors the arm — which makes the Q1 third place a
  **conservative** negative, and means the Q2 win may be partly effort, not only method (though the decisive
  stage-3 move — tax localized to a new `Market` seam — is a structural choice, not an effort artifact).
- **Model.** The pilot's Q1 judges ran on Opus 4.8; this run's judges ran on the current default subagent
  model — a possible model difference in the Q1 comparison. Q2 is a count, largely model-robust.
- **Operator consolidation.** The arm's stage-3 design was consolidated by the operator from the merge
  agent's output into a method-neutral standalone doc for blind judging (the pilot's own anonymization step);
  the plain/OpenSpec docs are the arms' originals. The judges were told length is not a merit (R is ~150
  lines to P's 2009 / Q's 1251).
- **This does not overturn the pilot.** The pilot stands as run. This is a separate, later, single-arm
  re-run showing the upgrade's effect on the same cards — decisive on survival, null-to-negative on Q1.
