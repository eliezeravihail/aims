---
title: "anchor.py"
date: 2026-08-12
hash: "sha256:edc087493cc02c2aee6f2b061308cb18c92b35840d03a679af021bb7fae070d6"
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
