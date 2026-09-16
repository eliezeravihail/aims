# panel-plan — three fixed-axis advisor planners, merged by a master planner

This is the PLAN phase's opening-round mechanism: instead of one single-pass plan, **three advisor
planners** each plan the same round **independently**, optimizing one fixed axis of software quality,
and a **master planner** composes their strengths into one coherent objective + Worker handoff. It is
the plan-side sibling of `references/review-panel.md` — that panel *measures* a result after build;
this one *generates* the objective before build. Neither gates; both inform.

**Evidence.** `experiments/plan-diversity/` (blind, three judges) found three stance-seeded passes +
merging beat a single plan pass for every judge, and edged plain repetition. `decisions/0005` records
the decision; `decisions/0006` records who owns what text below.

## When it convenes

- **Auto mode:** automatically, on the **opening design round** of a new product or of a newly
  received product change. Every subsequent round plans single-pass, as `SKILL.md` step 2 already
  describes.
- **Stepped mode:** **only** via the explicit `panel-plan` command (`commands/aims-panel-plan.md`).
  `/aims-plan` stays single-pass, unchanged, in every round.

Convening on a non-opening auto round, or having a plain `/aims-plan` convene it, is a failure of this
mechanism — the cost (about four planning passes instead of one) is accepted only for the round that
sets a product's or a product-change's direction.

## The axes — operating definition

This section is the trio's **one operating owner** (`decisions/0006`): the text an advisor actually
plans from. `decisions/0005` records why this trio and what was rejected, frozen as of its date and
not authoritative for operation — refer to it for rationale, never restate it as the definition.

Each advisor **optimizes** its axis — pulls toward it, not merely attends to it — which is what
preserves the divergence the master planner later arbitrates. Each axis pairs a canonical,
well-known literature term (a bare name is too diffuse a target) with the pointed pulls it subsumes:

1. **Clean code** — absence of code smells (feature envy, shotgun surgery, duplication that is real
   coupling, size without a one-sentence reason) and a **minimal dependency footprint**. Pointed pull:
   minimize moving parts; hunt smells; keep the dependency diet lean.
2. **Correct encapsulation** — information hiding done right: Tell-Don't-Ask boundaries, no
   implementation type leaking across a public seam, every stated rule owned and enforced in exactly
   one place. Pointed pull: verifiability by construction — one enforced, unforgeable owner per rule;
   no seam leaks.
3. **Correct genericity** — the abstraction level calibrated from both ends
   (`references/design-principles.md` §2): generic enough to be complete for its consumers (the
   floor), no more specific than every producer can honestly supply (the ceiling); no decorative
   interfaces, no speculative generality. Pointed pull: absorb the known change axes; no more, no
   less.

## The grounding package — identical, three times

Assemble it **once** per round, from the plan phase's step-1 output (`SKILL.md` step 1: discovery,
resolved product decisions, the foundational substrate where relevant), then hand it to each advisor
**byte-identical except the axis block**:

- the product change + grounded facts from discovery;
- the resolved product decisions;
- constraints, what to preserve, explicit non-goals;
- the `references/design-principles.md` pointer;
- the advisor's **one** axis (name + pointed pulls, from above).

Explicitly **absent** from every package: any other advisor's output, any prior draft objective, the
Guide's own leanings. Because the three packages differ only in the axis block, any divergence
between the three drafts is attributable to the axes themselves — not to uneven context.

## Isolation per mode

**Advisor independence is an invariant, not a preference**: during a panel-plan round, no advisor sees
another advisor's output. Sequential advisor passes sharing one context are excluded outright — a
later advisor cannot unsee an earlier one.

- **Auto mode.** Spawn the three advisors as parallel subagents; the master planner composes in the
  Guide's own context. Isolation holds by construction (`references/modes.md` already permits
  subagents in auto).
- **The explicit `panel-plan` command (stepped).** The three advisors run as parallel subagents **on
  the currently selected model**; the **master planner runs inline**, in this session. This is the one
  declared exception to "explicit commands run inline, no subagent" (`references/modes.md`), because
  that convention protects two things and this round can only keep one in full: the user's **model
  choice** is preserved in full (advisors run on the selected model); their ability to **watch the
  phase turn by turn** is preserved only for the arbitration — the master's composition stays
  watchable — while the three advisor drafts are **inspectable after the fact**, written raw to
  `.aims/panel/<date>-<slug>/advisor-<axis>.md`, which is strictly weaker than watching them being
  written. This is a **declared downgrade, not an equivalence**: the user trades turn-by-turn
  visibility of the generation step for the independence that makes convening the panel worth its
  cost. Inline sequential drafting cannot preserve independence at all — a later pass cannot unsee an
  earlier one — so the invariant outranks the convention's letter here, and the exception is declared
  next to the rule it qualifies (`references/modes.md`).
- **No subagent facility.** `panel-plan` **declines honestly**: state that independent advisors cannot
  be simulated in one shared context, and fall back to single-pass `plan`. Never run sequential
  pseudo-advisors — fabricated independence is worse than none.

## The master planner — strength harvest, then a best-of-all-three composition

1. **Read** the three drafts.
2. **Harvest strengths.** Per plan, name the concrete structural moves its axis genuinely earned —
   where that plan is *excellent*, not a summary of it. Note the unanimous spine (choices all three
   share) as robust, and keep it.
3. **Compose.** Build **one** coherent design that carries every harvested strength **at full
   strength, simultaneously** — a plan at the top of all three axes at once, not a plan good at one
   and adequate at the others. Where two strengths collide, first try to **harmonize** — adapt the
   mechanism so both hold. Only a genuinely irreconcilable conflict is decided by choice, with a
   stated reason: *chosen-over-rejected + why*. Three failure modes are each a fail here:
   - **winner-picking** — crown one plan, sprinkle tokens from the others;
   - **union** — keep everything, producing a patchwork;
   - **averaging** — a compromise that dilutes every strength.
4. **Glue-only authorship.** The master may author the connective tissue the composition needs — each
   glue element justified by the strengths it joins — but may not add new capability of its own. A gap
   present in all three drafts is filed as a **gap note for the Guide**, never silently patched in.
5. **Subtractive pass** (`references/review.md`) over the composition — this is where the union
   failure mode, if it crept in, gets caught.
6. Assemble the round's single objective + Worker handoff. **No score, no accept/reject** anywhere in
   this output — the panel informs the Guide's direction, exactly as the review panel does.

## Where the outputs land

- **`.aims/state.md`** — the merged objective + drafted handoff, under the existing schema contract
  (headings/markers unchanged), cursor set to `planned:awaiting-build`. The existing build command
  consumes it with zero special-casing.
- **The round's ADR**, in the target project's `decisions/` — carries the **strengths harvest** (what
  each axis contributed to the composition, attributed to its advisor) and, in the alternatives
  section, **every axis split the round actually had**, in one of two shapes:
  - a **decided conflict** — *"chose X over Y because Z"* (the irreconcilable case);
  - a **harmonization** — *"axis A pulled toward X, axis B toward Y; this shape satisfies both, and
    here is the mechanism that made that possible."*

  Both shapes are filed — a split resolved by harmonizing is filed exactly as durably as one resolved
  by choosing, because it is real, developed knowledge and not a straw-man alternative. Append-only,
  navigable later, per the house record rules (`references/design-record.md`).
- **`.aims/panel/<date>-<slug>/advisor-<axis>.md`** — one file per advisor: the raw, inspectable
  drafts. Run-state by-products, like `state.md` — outside the design records, not anchored, not
  filed as knowledge.
- **The plan report** (stepped mode) gains one section: the strengths harvest per axis, the
  harmonizations, and each decided conflict's reason — alongside the report's usual contents
  (`references/modes.md`, "Presenting the plan report").

## Not a gate, never a score

The panel-plan mechanism informs the Guide's direction; it gates nothing and grades nothing. It
produces one objective and one handoff like any other plan round — the difference is how that
objective was arrived at, not a new kind of approval it must clear.
