---
title: "goals"
date: 2026-08-13
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
  across the evolution (survival 11); see `decisions/0007`. Root cause: a decomposition (tax) modelled as a
  movement inside the explanation ledger — a value-correct cram (`design-principles.md` §2).
- **v2** (§2 sharpened) — survival churn halved (11→5) but design quality was still a wash: §2 named the
  fault but nothing made its check fire at design time.
- **v3** (the **concept-fit pass** added to `references/review.md`, run on the design before code) — the
  concept fault is **gone** from both aims arms (tax modelled as a decomposition beside the walk; no wrong
  number on any case). Survival: aims-panel **1** (decisive best), aims-single 5, OpenSpec 5 — trajectory
  11→5→1. Two opposite-prior substantive judges **split**: a consequence/future-cost lens ranks the aims
  arms above OpenSpec; an accidental-complexity lens ranks OpenSpec's single-mechanism spec above them. See
  `experiments/aims-vs-openspec/results-v3.md`.

Honest current reading: aims **materially improved change-absorption** and the concept-fit pass **caused**
(not merely measured) the elimination of the architectural fault — but overall design quality against a
single-mechanism spec method is a **judge-dependent split, not a clean win**. The co-located record layer's
payoff remains narrow and real: a durable append-only trail of *why a superseded decision no longer holds*.

## Non-goals
- Not a background daemon or self-maintaining store: nothing runs between turns except one advisory
  read hook.
- Not an enforcement gate: the method directs and measures; the staleness hook advises, never blocks.
