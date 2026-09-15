---
title: "architecture"
date: 2026-08-12
---

## Boundaries & seams
- **skills/aims-guide** — the design method (produces knowledge). **knowledge/** — where knowledge is
  written and how drift is detected (format + anchor tool + read hook). The method calls the tool; it
  does not embed hashing.
- `knowledge/anchor.py` (write) and `knowledge/staleness_hook.py` (read) share the derivation +
  hashing so read-time and write-time always agree; the hook imports the tool.

- **panel-plan (plan-side panel)** — generates three independent fixed-axis candidate designs and merges
  them *before* build; distinct from the review panel, which *measures* after build. The axis trio has
  exactly one **operating** owner — `skills/aims-guide/references/panel-plan.md` §Axes, the shipping
  surface a target project actually reads. `decisions/0005` records the decision and its rationale as
  dated history; `decisions/0006` records the ownership split (shipping surface owns the operating
  definition, the ADR owns the rationale). Nothing else restates the trio — everything else refers.

## Invariants
- Design knowledge is co-located: a source file's knowledge is in its same-named companion; system-wide
  knowledge is a root record. Nothing stores a path — pairing is by name.
- The read hook is advisory: never blocks, fail-open.
- **Advisor independence**: during a panel-plan round no advisor sees another advisor's output. The master
  composes **the best of all three axes at full strength** — harvested strengths attributable to their
  advisors, master-authored content limited to integration glue, irreconcilable conflicts decided with a
  stated reason — never a winner-pick, a union, or an average. The panel informs direction; it gates
  nothing.
