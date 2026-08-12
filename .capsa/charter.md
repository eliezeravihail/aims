---
title: "aims — charter"
date: 2026-08-12
---

## Primary goal
Make design the goal of coding-agent work, and make the design knowledge durable: the method files
ADRs, requirements, components, and insights into a capsa capsule so a later clean session reads prior
conclusions and builds on them instead of re-deriving from scratch.

## Non-goals
- Not a background daemon or self-maintaining store: nothing runs between turns except one advisory
  read hook. No memory tree, no consolidation.
- Not an enforcement gate: the method directs and measures; the staleness hook advises, never blocks.
