---
title: "architecture"
date: 2026-09-16
---

## Boundaries & seams
- **skills/aims-guide** — the design method (produces knowledge). **knowledge/** — where knowledge is
  written and how drift is detected (format + anchor tool + read hook). The method calls the tool; it
  does not embed hashing.
- `knowledge/anchor.py` (write) and `knowledge/staleness_hook.py` (read) share the derivation +
  hashing so read-time and write-time always agree; the hook imports the tool.

- **panel (opening-round design fan-out)** — the Guide sets **one** objective, then three axis-focused
  **Workers** work it independently and a **merge agent** composes one result, *before* the review
  measures it; distinct from the review panel, which *measures* after. The axis trio has exactly one
  **operating** owner — `skills/aims-guide/references/panel-plan.md` §Axes, the shipping surface a target
  project actually reads. `decisions/0005` records the original decision; `decisions/0006` the ownership
  split; `decisions/0008` the internal division (objective set once and shared; Workers fan only the
  design; the merge agent composes and does not invent an objective). Nothing else restates the trio —
  everything else refers.

## Invariants
- Design knowledge is co-located: a source file's knowledge is in its same-named companion; system-wide
  knowledge is a root record. Nothing stores a path — pairing is by name.
- The read hook is advisory: never blocks, fail-open.
- **Worker independence**: during a panel round no Worker sees another Worker's output. The merge agent
  composes **the best from each of the three axes at full strength** — strengths attributable to their
  Workers, merge-authored content limited to integration glue, irreconcilable conflicts decided with a
  stated reason — never a winner-pick (the best *among*), a union, or an average. The panel informs
  direction; it gates nothing.
