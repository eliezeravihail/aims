---
title: "the aims-vs-OpenSpec pilot found no design advantage, and one narrow continuity win"
date: 2026-09-16
---

**Context.** `experiments/aims-vs-openspec/` ran a three-arm, design-only, blind-judged pilot (aims /
OpenSpec / plain) on a checkout pricing service evolved across three staged requirements, each later stage
by a fresh no-memory session. Full result in that directory's `results.md`; this ADR records what the
finding means for aims' own claims, so a later session inherits the honest reading rather than re-running
the pilot or trusting the method's self-description.

**Finding.** On this product, judged blind against aims' own design principles:

- **Design (the home reading): aims lost.** Two opposite-disposition judges both ranked OpenSpec > plain >
  aims. The decision aims' method actively led it toward — make the explanation the single source of truth
  — is a real strength at stage 2 and became the wrong call at stage 3 (tax as a delta *inside* the chain,
  which broke aims' own delta-sum fold and forced a kind-filtered patch). aims lost its home reading under
  its home rubric.
- **Survival: aims reopened the most** (11 vs OpenSpec 8, plain 9). The falsifier the experiment named in
  advance ("aims reopens more than OpenSpec → the central claim fails on this product") fired.
- **Continuity: a tie on the main question, a narrow win on a sub-question.** All three arms' fresh
  sessions navigated their prior records rather than re-deriving. The plain arm did this with three
  markdown files and no machinery. aims' machinery uniquely delivered exactly one thing: a durable,
  append-only trail of *why a superseded decision no longer holds* (5 of 6 supersessions back-stamped in
  place; one missed). That is the whole measured payoff of the record layer on this pilot.
- **Cost: aims ≈ OpenSpec, both ~1.3–1.5× the plain arm.**

**Decision.** Record these as the current honest state of the evidence, not as a reason to change the
method yet. Specifically:

1. **Do not claim a design-quality advantage for aims.** The one direct, blind test of "design as the goal
   beats no-method / spec-first" came back negative on this product. Any future claim needs the *sequence*
   of pilots behind it (`PROTOCOL` §7), and this unit points the other way.
2. **The record layer's demonstrated value is narrow and real: the retired-decision trail.** That is what
   append-only `decisions/` + in-place supersession buys over a rewritten design document. It is worth
   keeping for that, and the pilot is too shallow (n=3 stages) to measure the compounding value `goals.md`
   claims for it at project scale.
3. **Watch the failure mode the pilot exposed in the method itself:** aims' "explanation is the pricing
   record" instinct generalised a stage-2 win into a stage-3 over-commitment. A method that makes one
   structure the single source of truth can push a later session to force an ill-fitting thing into it.
   Not fixed here; named for the next design round on the method.

**Consequences.**
- `goals.md` gains a use-scenario caveat pointing here, so the primary-goal claim is read next to its one
  blind test.
- This is n=1. A second pilot on a different product, ideally allowing a build (so OpenSpec's archived spec
  baseline actually exists and the product reading is available), would materially change confidence. The
  no-build constraint biased two of four readings against OpenSpec and removed the product reading entirely.

**Alternatives.**
- *Record only in the experiment folder, not as an ADR* — rejected: the experiment's own dogfooding rule is
  that cross-cutting findings live in a root record. A negative result about the method's central claim is
  exactly that.
- *Treat the loss as a product of the rubric/model deviations and discount it* — rejected: aims lost its
  home reading under its home rubric, and the deviations (Opus judges, no-build) bias toward aims or against
  OpenSpec, not against aims. Discounting the result would be reading the evidence backwards.
