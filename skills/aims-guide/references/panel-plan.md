# panel — three axis-focused Workers over one shared objective, merged

This is the opening-round mechanism. The Guide sets **one** objective the ordinary way
(`references/objective-selection.md`: a design outcome, adversarial exit criteria, the hard decision at
its core). Then, instead of a single Worker, **three Workers** work that *same* objective
**independently**, each given one added instruction — optimize one fixed axis of software quality — and a
**merge agent** composes the good from each into one result (`decisions/0008`). It is the generate-side
sibling of `references/review-panel.md`: that panel *measures* a result; this one *produces* the design
the review will then measure. Neither gates; both inform.

**Evidence.** `experiments/plan-diversity/` (blind, three judges) found three stance-seeded passes +
merging beat a single pass for every judge, and edged plain repetition. `decisions/0005` records the
convening decision; `decisions/0006` records who owns the axis definition below; `decisions/0008` records
the internal division (objective set once and shared; the Workers fan out only the design; the merge agent
composes, and does not invent an objective).

## When it convenes

- **Auto mode:** automatically, on the **opening design round** of a new product or of a newly
  received product change. Every subsequent round runs single-pass, as `SKILL.md` step 2 describes.
- **Stepped mode:** **only** via the explicit `panel-plan` command (`commands/aims-panel-plan.md`).
  `/aims-plan` stays single-pass, unchanged, in every round.

Convening on a non-opening auto round, or having a plain `/aims-plan` convene it, is a failure of this
mechanism — the cost (about four design passes instead of one) is accepted only for the round that sets a
product's or a product-change's direction.

## The axes — operating definition

This section is the trio's **one operating owner** (`decisions/0006`): the text a Worker actually
optimizes toward. `decisions/0005` records why this trio and what was rejected, frozen as of its date and
not authoritative for operation — refer to it for rationale, never restate it as the definition.

Each Worker **optimizes** its axis — pulls toward it, not merely attends to it — which is what preserves
the divergence the merge agent later harvests. Each axis pairs a canonical, well-known literature term (a
bare name is too diffuse a target) with the pointed pulls it subsumes:

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

Assemble it **once** per round, then hand it to each Worker **byte-identical except the axis block**:

- **the Guide's one objective** — the design outcome, its adversarial exit criteria, and the hard
  decision at its core, set before the fan-out (the panel does not generate the objective);
- the product change + grounded facts from discovery, and the resolved product decisions;
- constraints, what to preserve, explicit non-goals;
- the `references/design-principles.md` pointer;
- the Worker's **one** axis (name + pointed pulls, from above).

Explicitly **absent** from every package: any other Worker's output, any prior draft design, the Guide's
own leanings. Because the three packages differ only in the axis block, any divergence between the three
results is attributable to the axes themselves — not to uneven context or a different objective.

## Isolation per mode

**Worker independence is an invariant, not a preference**: during a panel round, no Worker sees another
Worker's output. Sequential passes sharing one context are excluded outright — a later Worker cannot unsee
an earlier one.

- **Auto mode.** Spawn the three Workers as parallel subagents; the merge agent composes in the Guide's
  own context. Isolation holds by construction (`references/modes.md` already permits subagents in auto).
- **The explicit `panel-plan` command (stepped).** The three Workers run as parallel subagents **on the
  currently selected model**; the **merge agent runs inline**, in this session. This is the one declared
  exception to "explicit commands run inline, no subagent" (`references/modes.md`), because that
  convention protects two things and this round can only keep one in full: the user's **model choice** is
  preserved in full (Workers run on the selected model); their ability to **watch the phase turn by turn**
  is preserved only for the merge — the composition stays watchable — while the three Worker drafts are
  **inspectable after the fact**, written raw to `.aims/panel/<date>-<slug>/worker-<axis>.md`, which is
  strictly weaker than watching them being written. This is a **declared downgrade, not an equivalence**:
  the user trades turn-by-turn visibility of the generation step for the independence that makes convening
  the panel worth its cost. Inline sequential drafting cannot preserve independence at all — a later pass
  cannot unsee an earlier one — so the invariant outranks the convention's letter here, and the exception
  is declared next to the rule it qualifies (`references/modes.md`).
- **No subagent facility.** `panel-plan` **declines honestly**: state that independent Workers cannot be
  simulated in one shared context, and fall back to single-pass `plan`. Never run sequential
  pseudo-Workers — fabricated independence is worse than none.

## The merge agent — objectives

You receive the three axis-focused Worker results — one per axis (clean code / correct encapsulation /
correct genericity). Each was produced by a Worker given the **one shared objective** (the Guide's, set
before the fan-out) plus a single instruction to optimize its axis. Your job is **not to pick a winner**;
it is to author one holistic result stronger than any of the three alone.

1. **Read each result for what its focus let it see.** For each of the three, name:
   - its genuine **strengths** — the concrete moves its axis earned;
   - the **problems it steered away from** — the pitfalls its focus made it avoid;
   - and, above all, the **requirements, problems, and needs it surfaced** that a single generalist pass
     would likely have missed. This is the whole point of the per-axis focus: it is a *discovery
     instrument* — a sharper, more focused way to surface what the design must satisfy. Treat each result
     as discovery, not as a finished candidate.

2. **Compose one holistic result from that raw material.** The strengths, avoided pitfalls, and surfaced
   requirements/needs across all three are your raw material. Design one correct, clean result that
   carries the genuine strength of each **at full force** — better than any single-axis result on its
   own. Refuse the three failure modes:
   - **winner-picking** — crowning one and dropping the rest (that takes the best *among*, not the best
     *from each*);
   - **union** — keeping everything, a patchwork;
   - **averaging** — a compromise that dilutes every strength.

   Where two strengths seem to collide, first **harmonize** (a structure that satisfies both); decide
   only a genuinely irreconcilable conflict, with a stated reason: *chosen-over-rejected + why*.

**Authorship bound.** The merge agent may author the connective tissue the composition needs — each glue
element justified by the strengths it joins — but may not add new capability of its own; a gap present in
all three results is filed as a **gap note for the Guide**, never silently patched in. Run a
**subtractive pass** (`references/review.md`) over the composition — this is where a union that crept in
gets caught. The merged result **conforms to the Guide's one shared objective**; the merge agent does not
invent an objective. **No score, no accept/reject** — the panel informs the Guide's direction, exactly as
the review panel does.

## Where the outputs land

- **`.aims/state.md`** — the Guide's objective (unchanged by the panel) + the merged handoff, under the
  existing schema contract (headings/markers unchanged), cursor set to `planned:awaiting-build`. The
  existing build command consumes it with zero special-casing.
- **The round's ADR**, in the target project's `decisions/` — carries the **strengths harvest** (what
  each axis contributed to the composition, attributed to its Worker) and, in the alternatives section,
  **every axis split the round actually had**, in one of two shapes:
  - a **decided conflict** — *"chose X over Y because Z"* (the irreconcilable case);
  - a **harmonization** — *"axis A pulled toward X, axis B toward Y; this shape satisfies both, and
    here is the mechanism that made that possible."*

  Both shapes are filed — a split resolved by harmonizing is filed exactly as durably as one resolved
  by choosing, because it is real, developed knowledge and not a straw-man alternative. Append-only,
  navigable later, per the house record rules (`references/design-record.md`).
- **`.aims/panel/<date>-<slug>/worker-<axis>.md`** — one file per Worker: the raw, inspectable drafts.
  Run-state by-products, like `state.md` — outside the design records, not anchored, not filed as
  knowledge.
- **The plan report** (stepped mode) gains one section: the strengths harvest per axis, the
  harmonizations, and each decided conflict's reason — alongside the report's usual contents
  (`references/modes.md`, "Presenting the plan report").

## Not a gate, never a score

The panel informs the Guide's direction; it gates nothing and grades nothing. It produces one merged
result and one handoff like any other opening round — the difference is how that result was arrived at,
not a new kind of approval it must clear.
