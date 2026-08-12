---
title: "aims-guide (the design method)"
date: 2026-08-12
code: skills/aims-guide
shape: "sha256:cbffb0dc9fea38d946db5fbd401c472b2552ce01f2941739a4cba538b37de9b9"
---

## Purpose
The design method: a Guide hands a Worker one design/quality objective at a time (feature as a
constraint), measures the result, chooses the next.

## Boundaries & seams
The method produces knowledge; where it lands is the capsa-layer's concern. The seam is
`references/design-record.md`: method output → record → placement → anchor.

## Invariants
- Design is the objective; the feature is a constraint.
- The substrate is asked of the user, never silently chosen.
- decisions/ are append-only.
