---
title: "Durable design knowledge lives in a capsa capsule, placement = scope"
date: 2026-08-12
code: skills/aims-guide/references/design-record.md
hash: "sha256:cc19ea4bf60643c57bd7f259e2daab2b9d3f07f7b12429a151ffaa0c396d81f4"
---

Context: Balash kept durable design in three flat files maintained by hand; they bloat (read-whole)
and drift (hand-kept truth).

Decision: file design knowledge as capsa records — one per fact, placed at the node it governs, so
relevance is derived from placement. The mapping is references/design-record.md.

Consequences: a later clean session reads in-scope records and continues instead of re-deriving.
Alternatives: documentation coupled to each source file (fragile) or a central tool-owned folder
(bloats) — both rejected.
