---
title: "goals"
date: 2026-09-16
---

## Primary goal
Make the quality of the code and its architecture an explicit optimization goal at the design stage —
a first-class objective the agent optimizes toward, not a byproduct of shipping features — and keep the
resulting design knowledge co-located with the code so a later clean session reads prior conclusions
and builds on them instead of re-deriving.

## Use scenarios
- **A new product under the method** — the developer runs `/aims-plan-and-build "<product>"` in an
  empty project. aims grounds the product by asking for one concrete start-to-useful-result scenario
  and the day-zero substrate, then loops direct → build → measure per objective, pausing only for open
  product decisions. Ends with working code whose structure was the objective, plus the records
  stating why it is shaped that way.
- **One objective, supervised** — `/aims-plan "<task>"` → read the plan report → `/aims-build` →
  `/aims-review`. The same loop with a stop at every phase, for a developer who wants to approve each.
- **Measuring a change aims did not build** — `/aims-review <branch | diff | path>` over ordinary
  work: reproduced readings against the design principles plus the subtractive pass, with no aims
  history required.
- **Continuing months later** — a fresh session handed a task on `src/render.py` opens
  `src/render.py.md` and the root records, reads the decisions in force, and builds on them instead of
  re-deriving; a source changed since filing makes the read advise re-verification.
- **Adopting aims on an existing project** — `/install-on .` puts the two hooks and the anchor tool
  under `.aims/` and wires `.claude/settings.json`, touching no code and no existing record.

## Evidence status
The primary goal above is a hypothesis under test, not an established result. The blind design-only pilot
`experiments/aims-vs-openspec/` (vs OpenSpec, n=1) has now been run three times as the method was sharpened:

- **v1** — found **no design-quality advantage for aims**, and it reopened the most of its own structure
  across the evolution (survival 11); see `decisions/0007`. Root cause: the explanation ledger's
  `Adjustment` interface was calibrated (floor/ceiling, `design-principles.md` §2) for one kind of thing —
  a step that changes a running value — and tax, a genuinely different concept (a decomposition: shares of
  a total, not a delta), was crammed into that same interface as a technically-valid but foreign field
  (`Adjustment(delta=0)`) rather than segregated into its own type. §2 already named this failure mode (the
  value-correct cram); nothing made it fire at the interface-design moment.
- **v2** (§2 sharpened) — survival churn halved (11→5) but design quality was still a wash: the cram
  persisted because the check still fired only after the interface already existed, not while it was being
  calibrated.
- **v3** (the **concept-fit pass** added to `references/review.md`, run on the design before code) — the
  interface-cram fault is **gone** from both aims arms: tax is segregated into its own type, a decomposition
  beside the promotion walk rather than crammed into `Adjustment`; no wrong number on any case. Survival:
  aims-panel **1** (decisive best), aims-single 5, OpenSpec 5 — trajectory 11→5→1. Two opposite-prior
  substantive judges **split**: a consequence/future-cost lens ranks the aims arms above OpenSpec; an
  accidental-complexity lens ranks OpenSpec's single-mechanism spec above them. See
  `experiments/aims-vs-openspec/results-v3.md`.

**⚠️ v3 was a flawed experiment** (the design arms could reach `decisions/0007`, which names the exact
fault being tested for) and is superseded by **v4**, a full clean re-run (stages 1→2→3 from scratch, both
aims arms rooted where `/home/user/aims` was never reachable):

- Survival: aims-panel **7** (best), OpenSpec 8, aims-single 10.
- Both aims arms independently caught concept-fit mismatches with **zero exposure** to the tax example —
  including aims-panel drafting the v1/v2 cram itself, mid-derivation, and reversing it unprompted. The
  pass generalizes; this is no longer merely plausible.
- Two opposite-prior substantive judges **both rank aims-panel first** (v3's split did not reproduce
  clean).
- **But** aims-panel's own design has a confirmed, real bug in its SOUTH tax mechanism (reads a per-line
  field that its own earlier stage never populates with what tax needs) — both judges correctly call it
  non-ranking-inverting, but it is real, and fixing it likely erases part of the survival advantage credited
  above. See `experiments/aims-vs-openspec/results-v4.md` for the full, unhedged picture.

Honest current reading: aims **materially improved change-absorption** and the concept-fit pass **causes**
(not merely measures) avoidance of the architectural fault — demonstrated clean in v4, including the pass
firing in real time inside a single design session. Against OpenSpec specifically, v4 is the strongest
result either aims arm has produced — but it ships with a real, acknowledged defect, so "aims wins" is true
of this pilot's measures, not yet of a design anyone should build from unmodified. The co-located record
layer's payoff remains narrow and real: a durable append-only trail of *why a superseded decision no longer
holds*.

## Non-goals
- Not a background daemon or self-maintaining store: nothing runs between turns except one advisory
  read hook.
- Not an enforcement gate: the method directs and measures; the staleness hook advises, never blocks.
