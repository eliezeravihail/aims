---
title: "I2 result — the falsification pass did NOT beat the shipped review (null; not adopted)"
date: 2026-09-20
---

# I2 — adversarial falsification review: NULL, not folded in

Pre-registered metric (`../plan.md`, I2): **I2 wins iff the falsification (attack) arm surfaces the seeded
corner S1 with a concrete failing case where the base-review arm misses it.** Both catching, or both missing,
is a null. One seeded first-draft (fixed-window rate limiter), reviews run blind, differing only by the
falsification-pass variant of `review.md`.

## Outcome — both arms caught the seeded corner. Base caught more.

| seed | base review (shipped `review.md`) | attack review (falsification-first variant) |
|---|---|---|
| **S1 primary** — fixed-window boundary burst (2N in a rolling 60 s) | **caught, S4, concrete input** (6 accepts in [30,90)) | **caught, S4, concrete input** (6 accepts in [59.7,60.2]) |
| S2 — clock non-monotonicity | **caught** (contract on `now`, fail-fast) | not surfaced |
| S3 — unbounded `counters` map | **caught** (noted under §13 resources) | not surfaced |

Both arms marked the design **BLOCKED** on the same S4, each tracing it to the §4 concept cram
(sliding window modelled as a fixed calendar bucket) and each producing a **reproducible failing input** —
exactly the "construct the input that breaks it" behavior. The base arm got there through the shipped §1
item **"trace the full input space (the procedure, not just the cases)"**, which already tells the reviewer
to check the R×boundary interaction no acceptance case exercises.

## Verdict: null → not adopted

The base did **not** miss S1, so I2 does not win by the pre-registered rule. Worse for the candidate: the
attack arm, by leading with a single constructed break, **tunneled on S1 and surfaced fewer** of the
secondary corners the base review caught (clock, memory). The falsification framing did not add correctness
coverage here and slightly narrowed it.

The honest reading: the shipped review's §1 "trace the full input space" pass **already is** a falsification
step — it demands a concrete wrong-output case for each R×X corner, and on this seed it produced exactly
that, unprompted by any new wording. Adding an explicit attack pass is redundant with a pass the method
already carries.

Per the discipline (a weakness-prompted method change must beat base on an unseen product before entering
the method — the same rule that kept the §7 wording out), **the falsification pass is not folded into
`review.md`.** n=1 seeded product; a second seed could still show value, but on the evidence in hand the
change is a null and stays out. `arm-attack-review.md` remains here as the recorded negative.
