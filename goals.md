---
title: "goals"
date: 2026-08-12
---

## Primary goal
Make the quality of the code and its architecture an explicit optimization goal at the design stage —
a first-class objective the agent optimizes toward, not a byproduct of shipping features — and keep the
resulting design knowledge co-located with the code so a later clean session reads prior conclusions
and builds on them instead of re-deriving.

## Non-goals
- Not a background daemon or self-maintaining store: nothing runs between turns except one advisory
  read hook.
- Not an enforcement gate: the method directs and measures; the staleness hook advises, never blocks.
