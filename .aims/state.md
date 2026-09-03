# aims Guide State

## Mode

stepped

## Loop cursor

executed:awaiting-review <panel-plan mechanism design — Worker result at .aims/worker-result-panel-plan.md>

## Current objective

**Kind:** design

**Objective:** Establish the **panel-plan mechanism** as part of the PLAN phase: three advisor planners on
the fixed axis trio — whose single owning definition is in `decisions/0005` (clean code / correct
encapsulation / correct genericity; not restated here) — planning **independently**, and a master planner that **harvests each plan's strengths and composes one
coherent design carrying the best of all three axes simultaneously, at full strength** — filing the
strengths harvest and any decided conflicts durably. The hard decision at the core: **how advisor isolation
is achieved in each mode** — auto (subagents permitted) vs the explicit `panel-plan` command, which must
reconcile the independence invariant with the "explicit commands run inline" convention
(`references/modes.md`) — and how the merged output enters the ordinary loop with zero special-casing.

**Why now:** `experiments/plan-diversity/` (blind, three judges) showed stance-seeded 3-pass + cross-
examination beats a single plan pass for every judge and edges plain repetition consistently; the user
decided convening (auto: opening design round of a product change; stepped: dedicated `panel-plan` command)
and fixed axes. The evidence is fresh and the decisions are filed (`decisions/0005`); designing the
mechanism now converts a measured result into method.

**Exit criteria:**
- [ ] **Independence by construction** — the design names, per mode, how each advisor plans with no access
      to another advisor's output, and explicitly excludes the tempting shortcut: sequential advisor passes
      in one shared context (a later advisor cannot unsee an earlier one).
- [ ] **Composition = best-of-all-three, at full strength** — every harvested strength is attributable to
      its source advisor and survives undiluted; master-authored content is integration glue only, each
      element justified by the strengths it joins; an irreconcilable conflict is decided with a stated
      reason, never silently averaged. The three named shortcuts fail: winner-picking (one plan crowned,
      tokens from the others), union (patchwork of everything), averaging (all strengths diluted).
- [ ] **Divergence durably filed** — each split axis lands as chosen-over-rejected-with-reason in that
      round's append-only ADR, navigable by a later session; divergence living only in the conversation
      fails.
- [ ] **Drop-in output** — the merged result is written into `state.md` under the existing schema contract
      (headings/markers unchanged), parked at `planned:awaiting-build`, and the existing build command
      consumes it with zero special-casing.
- [ ] **Convening falsifiers** — an auto loop convening the panel on a non-opening round fails; a stepped
      `/aims-plan` convening it fails; the `panel-plan` command convenes it every time.
- [ ] **One owner for the axis trio** — the three axes are defined in exactly one place and referenced
      everywhere else; a second verbatim copy that can drift fails.
- [ ] **No gate, no score** — the panel output carries no accept/reject stamp and no numeric score; it
      feeds the Guide's direction only.

**Preserve:**
- `.aims/state.md` schema contract (headings + markers).
- `/aims-plan` stays single-pass in stepped mode; existing commands' behavior unchanged.
- `references/review-panel.md` untouched; the design states the relationship (plan-panel generates and
  merges *before* build; review-panel measures *after*).
- No active machinery: prose only — no new hooks, no runtime code; stdlib-only (`decisions/0004`) stands.
- `decisions/` append-only.

**Do not optimize for:**
- A configurable axis registry or a variable advisor count (three fixed axes; no ensemble framework).
- Numeric scoring inside the merge (the house forbids scores; the merge argues per axis).
- Reusing the review-panel roles for generation — measuring and generating are different jobs.

## Worker handoff (drafted — do not execute before the build command)

ROLE — You are the implementation Worker, a senior engineer as capable as the Guide. The design is the
deliverable. If evidence invalidates the objective, report it instead of expanding scope.

DESIGN GOAL — The structure of the panel-plan mechanism as prose artifacts of this plugin: which files
exist or change (a command, a reference, templates — your call), the identical grounding package an advisor
receives, the isolation mechanism per mode honoring the independence invariant, the master planner's composition
procedure (strength harvest → best-of-all-three, glue-only authorship), and where each output lands
(state.md, the round's ADR). The how is
yours; the invariants are not.

BEHAVIOR IT MUST SATISFY — The convening rule and fixed axis trio of `decisions/0005`; the exit criteria
above, each of which the design must demonstrably meet.

WHAT "GOOD" AIMS AT — `references/design-principles.md`, as a target, not a checklist. §9 (one enforced
owner) and §10 (duplication vs wrong abstraction) bear directly here.

RELEVANT CONTEXT / PRESERVE / NON-GOALS — `decisions/0005-panel-plan-three-advisors.md`,
`architecture.md` (panel-plan seam + advisor-independence invariant), `references/modes.md` (the inline
convention you must reconcile with), `references/review-panel.md` (the measure-side sibling — untouched),
`experiments/plan-diversity/` (the evidence). Preserve and non-goals as listed in the objective.

RETURN TO GUIDE — The design + a short account of the key decisions (especially the isolation-vs-inline
reconciliation and the merge procedure), result status against the design goal, new facts or risks.

## Open Guide TODO

- [ ] After build: review with the `design` lens — buildability = a Worker could author the command/
      reference prose directly from the returned design.
- [ ] After the mechanism lands: consider a follow-up objective — should `/aims-plan-and-build` on a new
      product route its opening round through panel-plan automatically (auto-mode convening rule)?

## Last evaluated result

<!-- none — first objective of this product change; decisions 0005 filed this round -->
