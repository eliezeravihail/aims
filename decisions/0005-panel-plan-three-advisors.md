---
title: "panel-plan: three fixed-axis advisor planners merged by a master planner"
date: 2026-09-03
---

**Context.** The plan-diversity experiment (`experiments/plan-diversity/`, 2026-09-03; blind, three
independent judges, per-metric structural readings) measured where PLAN-phase value comes from: three
stance-seeded passes + a cross-examination beat a single plan pass for every judge; stance-seeding edged
plain same-model repetition for all three judges; an inter-model ensemble showed no real advantage once
judge self-preference was measured and discounted; and the cross-examination's divergence map proved to be
durable design knowledge in its own right. The user then decided the two open product choices: when the
panel convenes, and that the emphasis axes are fixed.

**Decision.** The PLAN phase gains a **panel-plan**: three **advisor planners**, each given the identical
grounding for the round and exactly one fixed emphasis axis of software quality — **this list is the trio's single owning
definition** (user decision, revised in-round after review of the plan report):

1. **clean code** — absence of code smells (feature envy, shotgun surgery, duplication that is real
   coupling, size without a one-sentence reason) and a **minimal dependency footprint**;
2. **correct encapsulation** — information hiding done right: Tell-Don't-Ask boundaries, no
   implementation type leaking across a public seam, every stated rule **owned and enforced in one
   place**;
3. **correct genericity** — the abstraction level calibrated from both ends (`design-principles.md` §2):
   generic enough to be complete for its consumers (the floor), no more specific than every producer can
   honestly supply (the ceiling); no decorative interfaces, no speculative generality.

Each advisor **optimizes** its axis — pulls toward it, not merely attends to it — which is what preserves
the divergence the master planner arbitrates. **Operationalization** (user observation, filed for the
Worker): the axis names are deliberately the **canonical, well-known literature terms** (user's stated intent) rather
than bespoke pointed labels; a general name alone is a diffuse optimization target
(the house's own objective-quality test rejects bare "clean"), so each advisor's framing pairs the general
axis with the pointed pulls it subsumes — clean code ⊇ *minimize moving parts* + smell hunt + dependency
diet; correct encapsulation ⊇ *verifiability by construction* (one enforced, unforgeable owner per rule; no
seam leaks); correct genericity ⊇ *absorbing the known change axes* (floor/ceiling calibration). General
names for coverage, pointed pulls for pressure. Each planning **independently** (no advisor sees another's output), followed by a **master planner** whose job is
**strength harvesting, not arbitration** (user decision, clarified in-round): it identifies, per plan, the
structural moves its axis genuinely earned — where that plan is *excellent* — and **composes one coherent
design that carries the best of all three axes simultaneously, at full strength**. Three named failure
modes it must avoid: *winner-picking* (crowning one plan and sprinkling tokens from the others), *union*
(keeping everything → patchwork bloat), and *averaging* (a compromise that dilutes every strength). Only a
genuinely irreconcilable conflict between harvested strengths is decided by choice, with a stated reason.
The round's records carry the **strengths harvest** (what each axis contributed) and the **decided
conflicts** (chosen-over-rejected-with-reason) in that round's ADR. The panel **informs direction; it gates
nothing** — same non-coercion stance as the review panel.

**Convening rule** (user decision): in **auto** mode the panel convenes automatically on the **opening
design round** of a new product or a newly received product change; subsequent rounds plan single-pass. In
**stepped** mode it convenes **only** via a dedicated explicit command (**panel-plan**); the existing plan
command stays single-pass and unchanged.

**Consequences.**
- An opening round costs ~4 planning passes instead of 1; that cost is the treatment and is accepted for
  opening rounds only.
- **Advisor independence is an invariant, not a preference**: sequential advisor passes in one shared
  context are excluded — a later advisor cannot unsee an earlier one. How isolation is achieved per mode is
  the Worker's design under that invariant (auto mode may spawn subagents per `references/modes.md`; the
  explicit panel-plan command must reconcile isolation with the "explicit commands run inline" convention —
  that reconciliation is the hard decision at the design objective's core).
- The axis trio is defined in **one owned place** and referenced everywhere else; no second copy that can
  drift.
- The composed plan is **attributable**: every harvested strength names its source advisor and survives at
  full strength; master-authored content is limited to the **integration glue** the composition needs (each
  glue element justified by the strengths it joins) — the master may not add new capability of its own.

**Alternatives.**
- *Inter-model advisor ensemble* — rejected: the experiment showed no advantage over fixed-stance
  single-model planning once judge self-preference was discounted, and it requires multiple subscriptions.
- *Plain n-runs (no stances)* — rejected: consistently weaker than stance-seeding for all three judges.
- *Convene on every round* — rejected by the user: cost without demonstrated per-round value.
- *Axes chosen per objective* — rejected by the user: a fixed trio is simpler and comparable across
  rounds.
- *The experiment's stance trio* (minimize moving parts / maximize extensibility / optimize
  verifiability) — superseded in-round by the user's principle-partition trio above. Evidentiary note:
  the experiment validates the **protocol** (three independent stances + a merging master), not any
  specific trio; the chosen trio maps directly onto `design-principles.md` (smells+dependencies /
  §1·§7·§9 / §2·§3), at the cost of somewhat less built-in opposition between advisors — mitigated by
  each advisor *optimizing* its axis.
