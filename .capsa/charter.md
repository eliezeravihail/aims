---
updated: 2026-08-12
---

# aims — charter

## Primary goal
Make design the goal of coding-agent work, and make the design knowledge durable: a design method
files ADRs, requirements, components, and insights into a capsa capsule so a later clean session reads
prior conclusions and builds on them instead of re-deriving from scratch.

## Use scenarios
- Build or evolve a product through the `/aims-*` loop; the round's design lands as capsa records.
- Months later, a fresh session at some part of the code reads the in-scope records and continues.
- A record's code drifts; the read-time hook flags it so the reader re-verifies rather than trusting.

## Non-goals
- Not a background daemon or a self-maintaining store: nothing runs between turns except one advisory
  read hook. No memory tree, no consolidation, no lint/doctor machinery.
- Not an enforcement gate: the method directs and measures; the staleness hook advises, never blocks.
