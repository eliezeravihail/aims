---
title: "name the anemic-model / type-switch as a mixed-tier review gap"
date: 2026-09-20
---

- Context: the improvement run's build-pilot campaign (`experiments/improve-2026-09/`, rounds BP7–BP9)

## Decision

Add, to the mixed-tier "gaps a weaker executor leaves" list in `references/review.md`, the specific pattern:
a distinct concept the design would model as a first-class type left as an **anemic data-bag** while a
type-code switch (`isinstance` / kind tag) in a central function owns all its logic — the OCP-reopen the
one-owner rule was meant to prevent — and note that it is a *structural* gap that "tests pass" does not
surface. Extend the section's "Observed directly" note with the measured evidence.

## Why (measured, not asserted)

Three build pilots isolated this pattern as a real weak-executor failure mode and located the review as the
step that catches it:

- **BP7 / BP6:** the shortcut base rate is real and model-dependent — a cheaper Worker (haiku) centralized rule
  logic in an `isinstance` type-switch over anemic rule classes on ~2/6 builds of a rule-engine card; a strong
  model took it ~0/3. So the gap is concentrated exactly on the cheap-Worker tier the mixed-tier policy targets.
- **BP8:** injecting the concept-fit principle into the Worker's *prompt* did **not** lower that rate on the
  weak tier (2/6 → 2/6). Advice the model can ignore is not a fix.
- **BP9:** the real review instrument, run by a competent Guide over the branched weak-Worker builds, flagged
  the type-switch as a structural finding on **4/4** and named the polymorphic seam; applying it restored the
  extensible design with the spec still green (12/12). The review does what the prompt principle could not.

This is not a new gate and not a behavior change — the review already detects the pattern via §4/§8/§9. It
names an empirically-common gap so the mixed-tier fidelity review hunts it explicitly, and records why the
*review* (output inspection), not the *principle* (prompt advice), is the load-bearing step when the Worker is
cheap. It therefore rides on validation against unseen products (the branched builds) rather than being a
speculative addition — consistent with the run's discipline (a change enters the method only by beating base
on unseen inputs).

## Alternatives rejected

- **Gate the spec-named-change-axis reopen as S4.** Tempting (it would force the fix, not just surface it), but
  untested and risks over-blocking correct-but-simple code. Left as a recorded candidate requiring its own
  blind A/B before shipping (`experiments/improve-2026-09/SYNTHESIS.md`, honest-limits).
- **Ship an "aims-lite" principle-injection delivery.** BP8 shows it does not transfer on the weak tier where
  the edge is largest; not adopted.
