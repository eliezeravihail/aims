# aims Guide State

Loop status only. Durable design lives in the records (`decisions/`, `architecture.md`, `goals.md`,
companions) and in `reviews/2026-09-16-aims-self-review.md`. Prior rounds' output (the panel-plan design
`0005`, its build, and the self-review) is preserved there — this file is run-state, replaced each round.

## Mode

stepped

## Loop cursor

planned:awaiting-build <clean method spine: objective-once → axis-fanned implementation → phase-matched quality measurement>

## Current objective

**Kind:** design

**Objective:** Design the **corrected method spine** as a buildable architecture of the plugin,
conforming to `decisions/0008`. The spine has three phases and the design must fix all three concretely:
1. **Set one objective** — single Guide, grounded from the product, framing one objective that
   *optimizes code quality* with behavior as a constraint (adversarial exit criteria + the hard decision,
   owned by `references/objective-selection.md`). No fan-out here.
2. **Axis-fanned implementation** — where multiple realizations pay, they are produced at the build
   phase, each optimizing one quality axis (clean code / correct encapsulation / correct genericity),
   composed best-of-all-three by a master (independence invariant, named merge-failure modes, honest
   decline — relocated from `0005`).
3. **Phase-matched quality measurement** — the review measures whether the *structure* is right for the
   phase's deliverable, against the quality objective, at its Kind lens — **distinct from behavior /
   performance**.
The deliverable is the artifact map (which skills/references/commands exist, change, or are removed) and,
centrally, the operational definition of *what code quality is and how it is measured at each Kind's
abstraction level*. The how of the internals is the Worker's; the spine and the quality-measurement
contract are not.

**Why now:** `decisions/0008` made the hard decision (axes → implementation; objective set once; measure
quality, not performance). Nothing in the clean build can be authored until the spine and its
quality-measurement contract are fixed — everything else conforms to them.

**Exit criteria** (each stated against the objective axis — quality optimization and its measurement):
- [ ] **Quality is operationally defined, not gestured at.** A spine that says "set a good objective,
      build it well, review it" without defining what quality *is* and how each phase is measured against
      it **fails** — that diffuse target is the exact failure aims exists to prevent.
- [ ] **Performance is never a proxy for quality.** Behavior matters and is measured on its own terms
      (the objective's constraint) — but a **performance metric must never estimate code quality**. Name a
      concrete case — a build that passes every test yet splits an owner or leaks a boundary — and the
      design must make that measurably **not meeting** the quality objective. "Passes the tests, therefore
      well-designed" is the substitution the measurement must refuse.
- [ ] **Fan-out is at the build phase, falsifiably.** A design that convenes the three axes at
      objective-setting **fails** (`0008`); one that produces the objective single-pass and fans out only
      the implementation passes.
- [ ] **The objective carries the correct-objective discipline, single-owned.** Adversarial exit
      criteria + the hard decision, owned once in `objective-selection.md`; a second restated copy fails.
- [ ] **Every measurement outcome has a home.** The review's Kind lens covers every declared Kind (no
      Kind without a lens), and every outcome (met / partial / invalidated / blocked) has a cursor value
      to park at — closing the self-review's mechanism-2 gaps.
- [ ] **Buildable.** A Worker could author the skill/reference/command prose directly from the artifact
      map. Abstract boundaries with no artifact map = principles, not a plan = fail.
- [ ] **Composition preserved at its new home.** Independence, the three named merge-failure modes
      (winner-pick / union / average each fail), and the honest decline hold at the build-phase fan-out;
      measurement carries no score and is reproduced-or-cited.

**Preserve:**
- The sound parts of `0005` (advisor independence, named merge failures, honest decline) — relocated to
  build, not discarded.
- `references/design-principles.md` as the quality target; `references/objective-selection.md` as the
  objective owner; the co-located record layer; `decisions/` append-only.
- No new runtime machinery: prose + the two existing tools (`decisions/0004` stands).

**Do not optimize for:**
- Preserving the panel-plan artifacts (`panel-plan.md`, `aims-panel-plan.md`, the plan-phase wiring) —
  they are superseded by `0008` and are rebuilt or removed, not patched.
- Using performance / behavior metrics as a **proxy for code quality** (performance matters and is
  measured as the behavior constraint — it just never stands in as the estimator of structural quality).
- A configurable axis registry or variable advisor count.

## Worker handoff (drafted — do not execute before the build command)

ROLE — Implementation Worker, a senior engineer as capable as the Guide. The design is the deliverable.
If evidence invalidates the objective, report it instead of expanding scope.

DESIGN GOAL — The corrected method spine as prose artifacts of this plugin: the three-phase loop of
`0008`, the artifact map (which files exist / change / are removed), and the operational
quality-measurement contract (what quality is per Kind, how it is measured distinct from performance,
where each outcome parks). The internal wording is yours; the spine, the single-owner constraints, and
the quality-vs-performance measurement are not.

BEHAVIOR IT MUST SATISFY — `decisions/0008`; the exit criteria above; the self-review's Part IV findings
it touches (`reviews/2026-09-16-aims-self-review.md`).

WHAT "GOOD" AIMS AT — `references/design-principles.md`, as target not checklist. The whole point is that
the method optimizes and measures *this*, not tests passing.

RELEVANT CONTEXT / PRESERVE / NON-GOALS — `decisions/0008` (the decision), `0005` (superseded panel-plan,
for the parts to relocate), `references/objective-selection.md` and `review-panel.md` (the owners this
spine wires), the self-review. Preserve and non-goals as listed above.

RETURN TO GUIDE — The spine design + artifact map + quality-measurement contract, a short account of the
key structural decisions, result status against the design goal, and any new fact or risk (especially
the re-measurement owed on whether build-phase fan-out reproduces the diversity value).

## Open assumptions (unproven — carried, not filed)

- The diversity value measured in *design production* (`plan-diversity`, `aims-vs-openspec`) transfers to
  the **build-phase** axis fan-out. Falsifier: a build-phase panel that shows no quality gain over a
  single axis-blind Worker on a controlled comparison. If false, the fan-out is unjustified anywhere and
  the spine reduces to objective-once → single implementation → quality measurement.

## Open Guide TODO

- [ ] Build the spine design (next: the build command) against the exit criteria above.
- [ ] After the spine is designed and measured: sequence the clean rebuild of the artifacts (remove/replace
      the superseded panel-plan surfaces) as its own implementation objective — not folded into the design.
- [ ] Carry the system-wide self-review findings (README truth, `decisions/0008`-vs-`0007` trail, the two
      false invariants — hook fail-open, stale companions) as separate objectives, not silently bundled.

## Last evaluated result

Prior round (panel-plan build) reviewed 7/7 conformance met, then **superseded** by `decisions/0008`:
the mechanism was correctly built but placed in the wrong phase. See the self-review and `0008`.
