# Architecture

- `_allocate(total, shares)` — the single owner of how the total is divided, where the remainder lands, and
  which rows are emitted at all.
- `Settlements` — keyed by settlement id; holds the most recent computed result for that id.

Three things in here read as defects to a newcomer and are not. Each has an ADR. Before "fixing" any of them,
read `decisions/`. Every one of the three was, at some point, "fixed" by someone acting on instinct, and each
fix caused the incident described in its ADR.

Expected change axes: new deduction kinds (fees), preview/dry-run entry points. Both go through `_allocate`.
