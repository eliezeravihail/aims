---
title: "Cut the memory-tree subsystem; co-located records + one read hook replace it"
date: 2026-08-12
---

Pre-capsa aims maintained a memory tree with marker/consolidation/lint/doctor machinery and several
hooks (docs/adr/0006-0012, 0018-0019, 0024, 0027-0030 are the frozen history). Removed: relevance is
now structural (walk the co-located tree), so there is no mutable store to keep coherent. The only
active machinery is one advisory read-time staleness hook.
