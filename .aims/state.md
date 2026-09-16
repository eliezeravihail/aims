# aims Guide State

Loop status only. Durable design lives in the records (`decisions/`, `architecture.md`, `goals.md`,
companions) and in `reviews/2026-09-16-aims-self-review.md`. This file is run-state, replaced each round.

## Mode

stepped

## Loop cursor

ready-to-choose-next <self-redesign round delivered and merged to master (PR #60): panel roles corrected, measurement contract completed + probe-regression fixed, machinery invariants restored, docs made honest, restatement consolidation done; merged with master's v2/v3/v4 evidence — ADRs renumbered 0009/0010 to clear the 0008 collision>

## Current objective

**Kind:** refactoring

**Objective:** By refactoring — small, targeted rewrites, the rest untouched, aims working at every step
(`decisions/0009`) — correct the plan-panel's **internal division** in `references/panel-plan.md` (and its
command), and close the measurement-contract gaps. Concretely:
1. **One shared, disciplined objective.** The conceptual objective is framed once and shared identically
   to all advisors, carrying the correct-objective discipline (adversarial exit criteria + the hard
   decision) **by reference** to `references/objective-selection.md` — no second copy. The master emits
   the handoff **conforming to** that shared objective, not inventing an objective at step 6.
2. **Axes fan only the design.** Make explicit that the three axis-focused Workers vary only the
   axis-borne *design* over the one shared objective — not re-derive the objective three times.
3. **Measurement contract** (`references/review-panel.md`) — the separate small fixes: a design artifact
   is a citable surface (so a design round is measurable); every declared Kind has a lens or is removed;
   every outcome (met / partial / invalidated / blocked) has a cursor value to park at.

The plan-panel keeps its phase and keeps working (`0005` convening rule stands). This is a refactor, not a
rebuild and not a restart.

**Why now:** `decisions/0009` fixed the hard decision (internal division, by refactoring; measure quality,
never proxied by performance). The panel already shares everything but the axis block, so the correction is
small and local — exactly the refactor's scope.

**Exit criteria** (each against the objective axis — quality optimization and its honest measurement):
- [ ] **The objective is disciplined and single-owned.** After the refactor, the panel's shared objective
      carries adversarial exit criteria + the hard decision **by reference** to `objective-selection.md`;
      a design in which the master still "assembles" an undisciplined objective, or a second restated copy
      of the discipline, **fails**.
- [ ] **Axes fan only the design.** The reference states that advisors vary the axis-borne design over one
      shared objective; a reading in which an advisor re-derives the objective **fails**.
- [ ] **Performance is never a proxy for quality.** Behavior is measured on its own terms (the
      constraint) — but a build that passes every test yet splits an owner or leaks a boundary must be
      measurable as **not meeting** the quality objective. "Passes the tests, therefore well-designed" is
      refused.
- [ ] **Every measurement outcome has a home.** Each declared Kind has a lens (no lens-less Kind), a
      design round is measurable (a design artifact is a citable surface), and every outcome parks
      somewhere in the cursor vocabulary.
- [ ] **Refactoring discipline held.** The diff touches only the panel's internal division and the
      measurement contract; the rest of the method is untouched; aims runs at every step (the three tests
      pass throughout). A change that rewrites unrelated surface **fails** this objective.
- [ ] **The panel still works as before** where it should: independence invariant, the three named
      merge-failure modes, honest decline, opening-round convening — all preserved.

**Preserve:**
- The plan-panel's phase and convening rule (`decisions/0005`); its independence invariant, named merge
  failures, and honest decline.
- `references/objective-selection.md` as the objective's single owner; `design-principles.md` as the
  quality target; the co-located record layer; `decisions/` append-only; the two existing tools only.
- **Everything outside the panel's internal division and the measurement contract — untouched this round.**

**Do not optimize for:**
- A rebuild or a relocation of the panel (withdrawn — `0009`).
- Using performance / behavior metrics as a **proxy for code quality** (performance matters and is
  measured as the behavior constraint — it just never estimates structural quality).
- Bundling the other self-review findings (README truth, the `0010`-supersedes-`0007` trail, hook
  fail-open, stale companions) into this refactor — they are separate objectives.

## Worker handoff (drafted — do not execute before the build command)

ROLE — Implementation Worker, a senior engineer as capable as the Guide, working under the refactoring
discipline: small targeted rewrites, the rest untouched, aims working at every step.

DESIGN GOAL — Refactor `references/panel-plan.md` (and `commands/aims-panel-plan.md` where it mirrors it)
so the panel frames one shared, disciplined objective (by reference to `objective-selection.md`) and the
advisors fan only the axis-borne design; then the separate small fixes to `references/review-panel.md`'s
measurement contract (design artifact citable; every Kind a lens; every outcome a cursor home). Internal
wording is yours; the single-owner constraint, the objective discipline, and the quality-vs-performance
measurement are not.

BEHAVIOR IT MUST SATISFY — `decisions/0009`; the exit criteria above; `decisions/0005` (the panel parts to
preserve); the self-review's Part I / Part II mechanism-2 findings.

WHAT "GOOD" AIMS AT — `references/design-principles.md`. The method optimizes and measures *this*, not
tests passing.

RELEVANT CONTEXT / PRESERVE / NON-GOALS — `0009`, `0005`, `objective-selection.md`, `review-panel.md`,
the self-review. Preserve and non-goals as listed above. Keep the three tests green at every step.

RETURN TO GUIDE — the refactored artifacts, a short account of each targeted rewrite (and proof the rest
is untouched — the diff scope), result status against the exit criteria, any new fact or risk.

## Open assumptions (unproven — carried, not filed)

- The diversity value measured in design-only pilots holds once the panel's advisors fan **only the
  design** over a shared objective (rather than the whole plan). Falsifier: a controlled comparison where
  fanning only the design shows no quality gain over a single axis-blind design pass. If false, the
  internal fan-out is unjustified and the panel reduces to one shared objective → one design.

## Open Guide TODO

- [x] Refactor the panel's internal division (Guide sets one objective; three axis-focused Workers fan the
      design; merge agent takes the best *from each*) + the measurement-contract fixes. **Done** — see the
      commit trail on `claude/aims-self-redesign`.
- [x] Measurement: design lens measures the full quality-requirements list by quotation; implementation
      lens adds requirement→check coverage (OpenSpec-inspired); experiment Kind has a lens; every outcome
      has a cursor home. **Done.**
- [x] System-wide self-review findings — README truth vs. the run pilots; `decisions/0010` gives `0007`
      its forward pointer through v4 (v4 has since been run on master — see `goals.md` / `results-v4.md`);
      hook fail-open + repo companions re-anchored + drift test; the dogfood-path leak + widened guard;
      `base-dependencies.md`; accept/not-accept; CLAUDE.md hook claim; record-templates wired;
      `/aims-panel-plan` made discoverable. **Done.**
- [x] Restatement consolidation — applied the subtractive pass to the prose: the one drift-prone
      near-verbatim duplication (substrate gate) was split by content (SKILL owns the imperative,
      discovery.md owns "what the substrate is"); the rest is deliberate reinforcement with a present
      force (template-vs-explanation, near-the-action) and is kept, not flattened.

## Last evaluated result

Prior round (panel-plan build) reviewed 7/7 conformance met. Its *placement* was then re-examined:
`decisions/0009` keeps the panel in place and corrects its internal division by refactoring, rather than
rebuilding. See the self-review and `0009`.
