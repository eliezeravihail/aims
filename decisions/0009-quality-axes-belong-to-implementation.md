---
title: "the plan-panel keeps its phase; correct its internal division, by refactoring"
date: 2026-09-16
---

> **Note.** An earlier same-session draft of this ADR (unmerged, binding no artifact) proposed relocating
> the axis fan-out out of the plan phase into a separate build-phase mechanism, as a ground-up "clean
> rebuild". That was overreach and is **not** the decision. Corrected in place before it bound anything;
> the actual decision is below.

**Context.** The self-review (`reviews/2026-09-16-aims-self-review.md`, Part I.1) found the plan-panel
emits a merged *design* but assembles the *objective* with none of the correct-objective discipline
(adversarial exit criteria, the hard decision, Kind) — the terms never appear in
`references/panel-plan.md`. Working the finding out with the user clarified where the fault actually is.

**The root finding — the panel's *internal division* is wrong, not its placement.** The plan-panel is in
the right phase and should keep working as it does. What is miscut is *inside* it: the panel effectively
triplicates the **whole plan** — objective and design together — across three advisors. But the
**conceptual objective is known and shared**; three advisors do not help discover it. What genuinely
diverges under the three quality axes (clean code · correct encapsulation · correct genericity) is the
**design** — the structural decisions the axis bears on. So the fan-out should vary only the axis-borne
design over one shared objective, not re-derive the objective three times.

**Decision.**

1. **The plan-panel keeps its phase and keeps working as usual.** No relocation to a build phase, no new
   mechanism. The opening-round convening rule (`decisions/0005`) stands.

2. **Correct the internal division.** The objective — the conceptual goal, with the correct-objective
   discipline (adversarial exit criteria + the hard decision, owned by `references/objective-selection.md`)
   — is framed **once** and shared identically to all three advisors. The three axis-advisors fan out only
   the **design** their axis bears on; the master merges those designs best-of-all-three and emits the
   handoff **conforming to the one shared objective**, not inventing an objective at the end.

3. **The change is a refactoring.** Fix/rewrite the wrong internal parts in **small, targeted** steps;
   leave everything else untouched; aims keeps working throughout. This is neither a ground-up rebuild nor
   a minimal restart — it is the refactoring rule: touch only what is wrong, keep the system running at
   every step.

4. **Measurement — quality as quality, performance never its proxy** (unchanged, correct). Behavior
   matters and the code must work; behavior is the constraint the objective carries. What the review must
   refuse is a **performance metric standing in as an estimator of code quality** — "it passes the tests,
   therefore it is well-designed." Quality is measured on its own terms (does each truth live in one
   place, is each invariant owned once, do the boundaries sit on the real change axes), matched to the
   phase's deliverable and its Kind lens. A green suite is evidence of behavior, never on its own of
   structure. Both are measured; neither substitutes for the other.

**Consequences.**
- `references/panel-plan.md`, `commands/aims-panel-plan.md`, and the plan-phase wiring are **kept and
  refactored in place** — not removed. (Corrects the withdrawn draft's "rebuilt or removed".)
- The correct-objective discipline is reached by **reference** to `objective-selection.md` (its single
  owner) from the panel's shared-objective step — no second copy of the discipline.
- Each refactoring step leaves a runnable method; no big-bang.
- The measurement-contract gaps the self-review found (design-lens evidence rule; a Kind with no lens;
  outcomes with no cursor home) are separate small refactors, not bundled into the panel change.

**Alternatives.**
- *Relocate the fan-out to a separate build phase (the withdrawn draft)* — rejected: the panel is
  correctly placed; the fault is an internal division, fixable in place.
- *Minimal restart — objective → single implementation → measure* — rejected by the user: no need to
  start small; refactor the existing mechanism.
- *Band-aid patches that leave the wrong internal split standing* — rejected: refactoring means real
  structural fixes, not symptom cover ("clean, not patches").
