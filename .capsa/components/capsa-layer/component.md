---
title: "capsa layer (durable knowledge + staleness)"
date: 2026-08-12
code: tools
shape: "sha256:3e7e4644efe1ced819eca55daaf28155f8786b61ca246eb9252587e7eed3842e"
---

## Purpose
The durable-knowledge substrate: the aims capsule format (docs/format-profile.md), the write-time
anchor stamper (tools/), and the read-time staleness advisory (hooks/). The vendored grammar is under
vendor/capsa/.

## Boundaries & seams
tools/aims_anchor.py (write) and hooks/staleness_read.py (read) share their hashing so the two always
agree; the hook imports the tool. (Note: this layer's code spans tools/ + hooks/ + vendor/ — a mild
cohesion cost in the repo layout, anchored here at its core, tools/.)

## Invariants
- An aims capsule stays a conforming capsa capsule; anchor fields are unknown keys capsa preserves.
- The read hook is advisory: never blocks, fail-open.
