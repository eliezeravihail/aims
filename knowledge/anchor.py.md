---
title: "anchor.py"
date: 2026-08-12
hash: "sha256:d88e8bd5af01e9147df6c161f4bb186db84fdc69c9ec16f8dfaa5e239a323b6a"
---
## Insights
- The whole design collapsed to one rule once the record was named after its source file: `X.md`
  anchors to sibling `X` if it exists, else it is a system record. No shape, no component logic, no
  stored path — `Path.with_suffix("")` does the derivation.
## Decisions
- Content hash of the sibling only. No directory/shape anchoring — architecture drift is a system
  concern (`architecture.md`), not a per-file anchor.
## Discussions
- Considered keeping a shape anchor for structural records; dropped — the companion model has no
  directory-level record, so shape had nothing to anchor.
