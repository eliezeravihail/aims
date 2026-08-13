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

## Non-goals
- Not a background daemon or self-maintaining store: nothing runs between turns except one advisory
  read hook.
- Not an enforcement gate: the method directs and measures; the staleness hook advises, never blocks.
