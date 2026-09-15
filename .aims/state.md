# aims Guide State

## Mode

stepped

## Loop cursor

ready-to-choose-next <panel-plan mechanism design — all 7 criteria met after the review amendments; next objective is the build>

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
- [x] **Independence by construction** — the design names, per mode, how each advisor plans with no access
      to another advisor's output, and explicitly excludes the tempting shortcut: sequential advisor passes
      in one shared context (a later advisor cannot unsee an earlier one).
- [x] **Composition = best-of-all-three, at full strength** — every harvested strength is attributable to
      its source advisor and survives undiluted; master-authored content is integration glue only, each
      element justified by the strengths it joins; an irreconcilable conflict is decided with a stated
      reason, never silently averaged. The three named shortcuts fail: winner-picking (one plan crowned,
      tokens from the others), union (patchwork of everything), averaging (all strengths diluted).
- [x] **Divergence durably filed** — each split axis lands as chosen-over-rejected-with-reason in that
      round's append-only ADR, navigable by a later session; divergence living only in the conversation
      fails. *(Met after amendment: the ADR now files harmonized splits as well as decided ones —
      `worker-result:70-83`.)*
- [x] **Drop-in output** — the merged result is written into `state.md` under the existing schema contract
      (headings/markers unchanged), parked at `planned:awaiting-build`, and the existing build command
      consumes it with zero special-casing.
- [x] **Convening falsifiers** — an auto loop convening the panel on a non-opening round fails; a stepped
      `/aims-plan` convening it fails; the `panel-plan` command convenes it every time.
- [x] **One owner for the axis trio** — the three axes are defined in exactly one place and referenced
      everywhere else; a second verbatim copy that can drift fails. *(Met after decision: `decisions/0006`
      splits ownership by kind — the shipping reference owns the operating definition, the ADR owns the
      rationale; `architecture.md` and `worker-result:92-101` now agree.)*
- [x] **No gate, no score** — the panel output carries no accept/reject stamp and no numeric score; it
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

- [x] After build: review with the `design` lens — buildability = a Worker could author the command/
      reference prose directly from the returned design. **Done** — see Last evaluated result. Buildable
      everywhere except `references/panel-plan.md` §Axes, where the design and `architecture.md` give a
      Worker contradictory instructions (reading 1).
- [ ] After the mechanism lands: consider a follow-up objective — should `/aims-plan-and-build` on a new
      product route its opening round through panel-plan automatically (auto-mode convening rule)?
- [ ] **Next objective (build):** author `skills/aims-guide/references/panel-plan.md` and
      `commands/aims-panel-plan.md` from the amended design, plus the one-line touches to `SKILL.md`,
      `modes.md` (the declared exception, stating the downgrade) and `aims-plan-and-build.md`. Design work
      is closed; this is execution against `worker-result-panel-plan.md`.

## Last evaluated result

**panel-plan mechanism design** (`design` lens, roles run inline per `references/modes.md`). Five of seven
exit criteria met. Four readings, each cited; no scores.

**1 — Two records each claim sole ownership of the axis trio. (blocks criterion 6)**
`architecture.md:15` states the trio has "exactly one owning definition — in
`decisions/0005-panel-plan-three-advisors.md`; it is not restated here or anywhere else," and the handoff
repeated it (`.aims/state.md:16`). The returned design relocates it:
`.aims/worker-result-panel-plan.md:78-80` makes `references/panel-plan.md` §Axes "the **operating
definition**" and demotes 0005 to "history." As written the design produces exactly the second
drift-capable copy criterion 6 fails on. **Counterevidence preserved — the relocation has a real force the
records did not anticipate:** `decisions/` is aims' own history and does not ship to a target project,
while `references/` does, so a target project running panel-plan would never see 0005; and `decisions/`
is append-only (CLAUDE.md), a poor home for a definition already revised once in-round (0005 line 12,
"revised in-round"). This is a genuine collision, not a Worker error — but the design picked a side
silently. Resolving it is a decision that amends either `architecture.md:15` or the design, not a wording
fix. Until it is made, a Worker authoring §Axes has contradictory instructions — the one place the design
is not buildable.

**2 — Harmonized divergences are never filed durably. (criterion 3 partial)**
Criterion 3 requires each split axis to land in the round's ADR, "divergence living only in the
conversation fails" (`.aims/state.md:39-41`). The design files only *decided conflicts* there
(`worker-result:66-68`); harmonizations go to the plan report (`worker-result:73-74`), which
`references/modes.md:58` defines as "compiled from the objective and the design docs … **not a new stored
file**" — ephemeral. Because §4 harmonizes first and decides only genuinely irreconcilable conflicts, the
*common* case is a real advisor split whose resolution reaches no durable record — and "two axes pulled
apart here; this shape satisfies both" is among the most valuable knowledge the panel produces. Met for
decided conflicts, unmet for harmonized ones.

**3 — Fidelity: the modes.md reconciliation claims more than it delivers.**
`references/modes.md:26-30` names two harms of a subagent under an explicit command: it "would run on a
different model **and** put the work behind a boundary they can't watch turn by turn."
`worker-result:38-47` preserves model choice, then substitutes after-the-fact *inspectability* (raw
drafts written to `.aims/panel/`) for *turn-by-turn watchability* while presenting the convention's
rationale as fully preserved. That is a narrowing, not an equivalence. Structurally the move is sound —
the design asks for an exception "declared next to the rule" rather than violating it silently — but the
amendment should state the downgrade plainly instead of claiming the rationale is intact.

**4 — Subtractive: `master-notes.md` has no named content and no stated consumer.**
`worker-result:71-72` introduces `.aims/panel/<date>-<slug>/advisor-<axis>.md` **+ `master-notes.md`**,
glossed "(inspectable raw drafts)" — which describes the advisor files, not it. No section says what it
holds or who reads it: the harvest goes to the ADR, the drafts to the advisor files, the reasoning to the
plan report. Deleting it damages no current rule, invariant, or boundary. (The `.aims/panel/` directory
itself earns its place — reading 3's reconciliation leans on it. Only the extra file is unforced.)

**What is solid.** Criterion 1 is the strongest part: §3 names isolation per mode, explicitly excludes
sequential-shared-context, and adds an honest decline when no subagent facility exists rather than
simulating independence. Criterion 2's merge procedure (harvest → harmonize-first → glue-only authorship →
subtractive pass, with winner-picking/union/averaging each a named failure) is a real mechanism, not a
restatement of the goal. Reusing the ADR's existing alternatives slot instead of inventing a record type
(§5) is the right subtractive instinct.

**Implication for direction.** Two gaps, of different kinds. Reading 1 needs a *decision* (which record
owns the trio) before any build can proceed — it is the one thing blocking buildability. Reading 2 needs a
*design amendment* (file harmonizations durably, most likely in the same ADR alternatives section).
Readings 3 and 4 are cheap corrections to fold into whichever round addresses the first two. The
mechanism's core — isolation and composition — measured sound; the gaps are at the record-keeping seam.

## Decision on the review readings (2026-09-15)

The Guide's decision at `reviewed:awaiting-decision`. All four readings mattered to the product and all four
are closed **before** any build — the blocking one by a recorded decision, the rest by amending the design.

1. **Axis-trio ownership (reading 1, blocking).** Decided in favor of the design's instinct, for the reason
   the design did not state: `decisions/` does not ship to a target project and `skills/` does, so a
   definition an advisor must operate from cannot live only in an ADR. Filed as
   `decisions/0006-shipping-surface-owns-operating-definitions.md` — ownership splits **by kind of text**
   (shipping surface owns the operating definition; the ADR owns the decision and its rationale, frozen as
   of its date). `architecture.md`'s panel-plan bullet is amended to match; `decisions/0005` is untouched
   (append-only) and 0006 carries the amendment. The rule generalizes past the trio.
2. **Harmonizations filed durably (reading 2).** Design amended — the round's ADR files every axis split in
   one of two named shapes, harmonization or decided conflict. The common case now lands durably.
3. **The `modes.md` reconciliation (reading 3).** Design amended to state the downgrade plainly:
   inspectable-after-the-fact advisor drafts are weaker than turn-by-turn watchability, and the exception
   declares the trade rather than claiming the rationale is intact.
4. **`master-notes.md` (reading 4).** Cut. `.aims/panel/` keeps the advisor drafts only.

Cursor moves `reviewed:awaiting-decision` → `ready-to-choose-next`. The design objective is reached; the
next objective is the **build** of the two prose artifacts, not more design.
