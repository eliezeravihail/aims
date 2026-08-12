---
title: "capsa layer (durable knowledge + staleness)"
status: active
created: 2026-08-12
code_globs: ["vendor/capsa/**", "docs/format-profile.md", "tools/**", "hooks/**"]
shape:
  root: "tools"
  children_hash: "sha256:4344d3d48a984740bdb3cd8792006004672b3468ed9e21012ae2fd7229a0bc6d"
  depth: 1
---

## Purpose
The durable-knowledge substrate: the vendored capsa format, the aims profile (which record types +
the anchors:/shape: fields), and the two moving parts — the write-time anchor stamper and the
read-time staleness advisory.

## Boundaries & seams
`docs/format-profile.md` is the contract the method writes against. `tools/aims_anchor.py` (write) and
`hooks/staleness_read.py` (read) share their hashing so the two always agree; that shared hashing is
the seam, kept in the tool and imported by the hook.

## Invariants
- An aims capsule stays a conforming capsa capsule: `anchors:`/`shape:` are unknown keys capsa
  preserves, never grammar the validator must know.
- The read hook is advisory: never blocks, fail-open.
- A record is content-anchored OR structure-anchored, not both (the claim is one kind).
