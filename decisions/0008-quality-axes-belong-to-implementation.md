---
title: "the quality-axis fan-out belongs to implementation, not planning — clean rebuild"
date: 2026-09-16
---

**Context.** The self-review (`reviews/2026-09-16-aims-self-review.md`) measured the panel-plan
mechanism and found (Part I.1) that it emits a merged *design* but assembles the *objective* with none
of the exit-criteria / hard-decision / Kind discipline that defines a correct objective — the terms
never appear in `references/panel-plan.md`. Working that finding to its root exposed a deeper mistake,
which this ADR records and decides on.

**The root finding — the panel split the wrong phase.** aims' spine is: the Guide sets an *objective*
(a design outcome, behavior as constraint), and the Worker produces the *design/implementation*. The
**conceptual objective is grounded from the product and is known before any fan-out** — three advisors
do not help discover that "this boundary needs an owner". What genuinely diverges under the three
quality axes — **clean code · correct encapsulation · correct genericity** — are properties of the
*realized structure*, and they diverge only once the structural decisions are actually being made. That
is **implementation**, not objective-setting.

The evidence confirms the mislocation. `experiments/plan-diversity/` and `experiments/aims-vs-openspec/`
were **design-only**: every "planning pass" there in fact *produced an architecture* — Worker/build work
in aims' own role split. So the diversity value the experiments measured was diversity in **design
production**, not in objective-setting. The mechanism mislabeled design-production as "planning"
(`decisions/0005`), placed the fan-out in the PLAN phase, and then could not emit a correct objective
because it was doing the wrong job in the wrong phase. `decisions/0005:73-77` already recorded, without
seeing the consequence, that the shipped axis trio was swapped in "at the cost of somewhat less built-in
opposition between advisors" — diversity reduced at exactly the phase where it was misapplied.

**Decision.**

1. **Clean rebuild, not patches.** The corrected method is re-derived around the correct spine below.
   The panel-plan artifacts — `references/panel-plan.md`, `commands/aims-panel-plan.md`, and the
   plan-phase convening wiring in `SKILL.md` / `modes.md` / `aims-plan-and-build.md` — are **superseded**;
   they are rebuilt or removed in the clean build, not amended in place.

2. **The objective is set once.** A single Guide, grounded from the product, frames one objective that
   **optimizes code quality** with behavior as a constraint — carrying adversarial exit criteria and the
   hard decision at its core (`references/objective-selection.md`, its single owner). No fan-out at
   objective-setting: the conceptual goal is known, so splitting it is cost without value.

3. **The three-axis fan-out moves to implementation.** Where multiple realizations are worth producing,
   they are produced at the phase where the axes actually diverge — the *implementation/design-of-
   internals* — each optimizing one axis, composed best-of-all-three by a master. Advisor independence,
   the named merge-failure modes, and the honest decline (the sound parts of `0005`) are preserved, but
   relocated to this phase.

4. **Measurement is of code quality, matched to the abstraction level of what was produced.** The review
   measures whether the *structure* is right for the phase's deliverable — not behavior/performance alone.
   "It passes the tests" is a performance metric; "each truth lives in one place, each invariant is owned
   once, the boundaries sit on the real change axes" is the quality metric this method exists to optimize.
   The measurement is taken against the quality objective, at the objective's Kind lens.

**Consequences.**
- The plan-phase panel is retired; a build-phase axis mechanism replaces it in the clean build.
- The objective-quality discipline stays owned by `objective-selection.md` and is reached in the ordinary
  plan flow — nothing needs to be bolted onto a plan-phase panel.
- The clean build discards the panel-plan build (PR #57) as the *operative* mechanism; its reasoning and
  evidence remain in the records (`0005`, `panel-plan.md`, the review) as superseded history.
- **Re-measurement owed:** the diversity value was measured in design production, which is
  implementation-level work here, so it is expected to transfer to the build-phase fan-out — but it must
  be re-measured there, not assumed. This is carried as an open assumption, not a filed fact.

**Alternatives.**
- *Patch `panel-plan.md` to add the objective-quality discipline* — rejected by the user: patches, not a
  clean build; and it leaves the fan-out in the wrong phase.
- *Keep the fan-out at PLAN and set the objective separately alongside it* — rejected: the conceptual
  objective is known before the fan-out, so splitting objective-setting is cost without value.
- *Keep `0005` operative and treat this as a wording fix* — rejected: `0005` places the mechanism in the
  wrong phase; that is a design error, not wording. `0005` is append-only, so this ADR supersedes its
  placement decision rather than rewriting it.
