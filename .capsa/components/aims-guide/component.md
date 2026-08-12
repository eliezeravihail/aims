---
title: "aims-guide (the design method)"
status: active
created: 2026-08-12
code_globs: ["skills/aims-guide/**"]
shape:
  root: "skills/aims-guide"
  children_hash: "sha256:cbffb0dc9fea38d946db5fbd401c472b2552ce01f2941739a4cba538b37de9b9"
  depth: 2
---

## Purpose
Balash's design method: a Guide hands a Worker one design/quality objective at a time (feature as a
constraint), measures the result, and chooses the next. Discovery, a feasibility gate, ownership/
encapsulation, a subtractive pass, a review panel.

## Boundaries & seams
The method produces knowledge; where that knowledge lands is the capsa-layer's concern. The seam is
`references/design-record.md`: method output → record type → placement → anchor. The method never
writes a bespoke store.

## Invariants
- Design is the objective handed to the Worker; the feature is a constraint (SKILL "the fact").
- The substrate is asked of the user, never silently chosen (SKILL step 1 gate).
- `decisions/` are append-only; a change is a superseding ADR.

## What it must not know
The internal hashing of the staleness layer; it calls `tools/aims_anchor.py` and never computes a hash.
