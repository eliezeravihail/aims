# Worker result — panel-plan mechanism design (Kind: design)

*Deliverable: the structure of the panel-plan mechanism as prose artifacts of the plugin — buildable: the
command/reference prose can be authored directly from this design. Status and reasoning at the end.*

## 1. Files — what exists or changes

| Artifact | Change | Owns |
|---|---|---|
| `skills/aims-guide/references/panel-plan.md` | **new** | the whole mechanism; the axis trio's **living definition** |
| `commands/aims-panel-plan.md` | **new** | the stepped-mode explicit entry |
| `skills/aims-guide/SKILL.md` | one sentence at step 2 | auto-mode convening rule → points at the reference |
| `skills/aims-guide/references/modes.md` | one qualifier | the advisor-subagent exception, declared beside the inline convention |
| `commands/aims-plan-and-build.md` | one line | routes the opening design round through the reference |
| `commands/aims-plan.md` | **untouched** | stays single-pass (user decision) |

## 2. The grounding package (identical, three times)

Assembled **once** per round from the plan phase's step-1 output, then handed to each advisor
**byte-identical except the axis block**: the product change + grounded facts from discovery, the resolved
product decisions, constraints/preserve/non-goals, the `design-principles.md` pointer, and the advisor's
**one axis** — its canonical name plus the pointed pulls it subsumes (per the trio's owning definition).
Explicitly absent: any other advisor's output, any prior draft objective, the Guide's own leanings. Since
the packages differ only in the axis block, any divergence between drafts is attributable to the axes —
not to uneven context.

## 3. Isolation per mode — the hard decision, resolved

- **Auto mode:** three advisor subagents spawned **in parallel**; the master runs in the Guide's own
  context. Isolation holds by construction (`references/modes.md` already permits subagents in auto).
- **The explicit `panel-plan` command (stepped):** advisors run as three parallel subagents **on the
  currently selected model**; the **master planner runs inline**, in-session. Reconciliation with the
  "explicit commands run inline" convention: that convention protects two things — the user's model choice
  and their ability to watch the phase. Advisors-on-the-selected-model preserves the first; the
  arbitration — where the judgment actually happens — running inline preserves the second; and every raw
  advisor draft is written to `.aims/panel/` (below), so nothing is hidden. What inline execution cannot
  preserve is *un-seeing*: a later sequential pass cannot unsee an earlier one, and independence is the
  measured source of the panel's value. The invariant therefore outranks the letter of the convention, and
  `modes.md` gets the exception **declared next to the rule** it qualifies.
- **No subagent facility:** `panel-plan` **declines honestly** — states that independent advisors cannot be
  simulated in one context, and offers single-pass `plan`. It never runs sequential pseudo-advisors;
  fabricated independence is worse than none.

## 4. The master planner — strength harvest, then a best-of-all-three composition

1. **Read** the three drafts. 2. **Harvest strengths:** per plan, name the concrete structural moves its
axis genuinely earned — where this plan is *excellent* (specific mechanisms, not a summary). The unanimous
spine (choices all three share) is noted as robust and kept. 3. **Compose:** build ONE coherent design that
carries every harvested strength **at full strength, simultaneously** — the goal is a plan at the top of
all three axes at once. Where two strengths collide, first try to **harmonize** (adapt the mechanism so
both hold); only a genuinely irreconcilable conflict is decided by choice, with a stated reason, recorded
as *chosen-over-rejected + why*. Three named failure modes are each a fail: **winner-picking** (crown one
plan, sprinkle tokens from the others), **union** (keep everything → patchwork), **averaging** (a
compromise that dilutes every strength). 4. **Glue-only authorship:** the master may author the connective
tissue the composition needs — each glue element justified by the strengths it joins — but may not add new
capability of its own; a perceived gap in all three plans is filed as a **gap note for the Guide**, never
silently patched in. 5. **Subtractive pass** (`references/review.md`) over the composition — the patchwork
failure mode is caught here. 6. Assemble the round's single objective + Worker handoff. **No score, no
accept/reject** anywhere in the output — the panel informs the Guide's direction.

## 5. Where the outputs land

- **`.aims/state.md`** — the merged objective + drafted handoff under the existing schema contract
  (headings/markers unchanged), cursor `planned:awaiting-build`. The existing build command consumes it
  with zero special-casing.
- **The round's ADR in the target project** — carries the **strengths harvest** (what each axis
  contributed to the composition, attributed) and, in the ADR's alternatives section, the **decided
  conflicts**: each filed as *"chose X over Y because Z."* No new record type; the panel's contribution is
  that the alternatives are **real** — actually developed by an advisor — rather than straw men.
  Append-only, navigable later, per the house record rules.
- **`.aims/panel/<date>-<slug>/advisor-<axis>.md` + `master-notes.md`** — run-state by-products
  (inspectable raw drafts), like `state.md` outside the design records: not anchored, not records.
- **The plan report** (stepped) gains one section: the strengths harvest per axis, the harmonizations, and
  each decided conflict's reason.

## 6. The axis trio's living owner

`references/panel-plan.md` §Axes is the **operating definition** — the three canonical names (clean code,
incl. absence of smells + minimal dependencies · correct encapsulation · correct genericity) each paired
with its pointed pulls. `decisions/0005` in the aims repo records the decision and rationale (history);
commands and `SKILL.md` **refer, never restate**.

## 7. Exit-criteria traceability

| Criterion | Met by |
|---|---|
| Independence by construction | §3 — parallel subagents per mode; sequential-shared-context explicitly excluded; honest decline when no facility |
| Composition = best-of-all-three, full strength | §4 steps 2–5 — harvest + harmonize-first; glue-only authorship; the three named shortcuts each fail; subtractive pass |
| Divergence durably filed | §5 — the round's ADR alternatives section, append-only |
| Drop-in output | §5 — state.md schema untouched; build consumes unchanged |
| Convening falsifiers | §1 — `aims-plan` untouched; SKILL.md sentence scopes auto-convening to the opening design round; the command always convenes |
| One owner for the trio | §6 — reference owns; ADR records; everything else refers |
| No gate, no score | §4 step 6 — stated in the reference's output shape |

## 8. Skeletons (buildability)

**`references/panel-plan.md`:** When it convenes (auto rule / the command) → The axes (owning definition +
pointed pulls) → The grounding package → Isolation per mode (incl. the declared exception + honest decline)
→ The master procedure (6 steps) → Outputs (state.md / ADR-alternatives / `.aims/panel/` / plan-report
section) → Not a gate, never a score.

**`commands/aims-panel-plan.md`:** mirrors `aims-plan.md` — stepped mode, steps 1–3 — with objective
drafting routed through the panel per the reference; same stops (no delegation, no code), same plan report
+ the panel section; park at `planned:awaiting-build`.

## 9. Design reasoning returned to the Guide

- **Key decisions:** the isolation reconciliation (user's-model subagents + inline master + honest decline
  — independence outranks the inline convention's letter while preserving its rationale); **divergence
  reuses the ADR's alternatives section** instead of inventing a record type — the record system already
  had the right slot, the panel just guarantees it is filled with genuinely developed alternatives; the
  **glue-only authorship rule**, which keeps the master a composer of others' strengths rather than a
  fourth advisor — it may join, harmonize, and connect, never add capability of its own.
- **Risks / new facts:** whether a spawned subagent actually runs on the user's selected model is
  host-dependent — if the host cannot honor it, the command should say which model advisors ran on;
  `.aims/panel/` by-products accumulate across rounds (cheap; cleanup is out of scope and should not
  become machinery).
- **Result: met** against the design goal, pending the Guide's review (the `design` lens: structure +
  buildability).
