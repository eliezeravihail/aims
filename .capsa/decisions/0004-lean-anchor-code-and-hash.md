---
title: "Lean records: declare code once, the anchor is a single tool-stamped hash"
date: 2026-08-12
code: tools/aims_anchor.py
hash: "sha256:fd9bad9c0846166cc4bf66978337c3ded9349c9c41256ee59da07b6136fa808e"
---

Context: capsa's per-type required fields (id/level/status/opened/verification, and an anchors list of
{path,hash}) are heavy for durable design notes and restate the concerned path twice.

Decision: a record is title + date + body; the kind comes from its folder; other capsa fields are
optional. A record concerning code declares it once in `code:` (a single cohesive target), and the
tool stamps a single `hash:` (content) or `shape:` (structure) — never hand-written. Supersedes the
earlier two-anchors/{path,hash}-list design.

Consequences: minimal ceremony; the path lives once (single home). A `code:` that cannot name one
cohesive target is treated as an architecture smell and a refactoring objective, not a scattered list.
