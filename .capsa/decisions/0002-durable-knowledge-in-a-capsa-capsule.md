---
id: 2
title: "Durable design knowledge lives in a capsa capsule, placement = scope"
status: accepted
date: 2026-08-12
tags: [capsa, documentation]
anchors:
- {path: "skills/aims-guide/references/design-record.md", hash: "sha256:678ea195fb0b5ec32610ef15c7ccab83ea24a97e9ee91711eb1b7d986e0bc0a5"}
---

## Context
Balash kept durable design in three flat files (GOALS/ARCHITECTURE/BASE-DEPENDENCIES) maintained by
hand. They bloat (read-whole) and drift (hand-kept truth).

## Decision
File design knowledge as capsa records — one per fact, placed in the tree at the node it governs, so
relevance is derived from placement and a reader loads only what is in force where it works. The
mapping is skills/aims-guide/references/design-record.md.

## Consequences
A later clean session reads in-scope records and continues instead of re-deriving. No monolith to read
whole.

## Alternatives considered
Documentation coupled to each source file — rejected (fragile: code moves orphan the note; a boundary
belongs to no single file). A central tool-owned folder — rejected (bloats).
