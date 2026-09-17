---
title: "anchor.py"
date: 2026-08-12
hash: "sha256:c2c899eef50ee20a7fa19ebfb0a9ed305114c35dd465175522d239e6d37e9e91"
---
## Insights
- The whole design collapsed to one rule once the record was named after its source file: `X.md`
  anchors to sibling `X` if it exists, else it is a system record. No shape, no component logic, no
  stored path — `Path.with_suffix("")` does the derivation.
## Decisions
- Content hash of the sibling only. No directory/shape anchoring — architecture drift is a system
  concern (`architecture.md`), not a per-file anchor.
- anchor.py is the single owner of the anchor line — both **writing** it (`stamp`) and **reading** it
  (`read_hash`). The read hook imports `read_hash` instead of re-parsing frontmatter, so read-time and
  write-time can never disagree about the format (2026-09-17).
## Discussions
- Considered keeping a shape anchor for structural records; dropped — the companion model has no
  directory-level record, so shape had nothing to anchor.
