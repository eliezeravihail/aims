---
id: 3
title: "Cut the memory-tree subsystem; the capsule + one read hook replace it"
status: accepted
date: 2026-08-12
supersedes: null
tags: [capsa, cut]
anchors:
- {path: ".claude/settings.json", hash: "sha256:9be81244fba4e9604425bee385792972752822cd645f7d1565242140ec8ccd66"}
- {path: "hooks/staleness_read.py", hash: "sha256:796a6c76cb1928bbe35c023b90eb1636f1346021226794d55e32c16ecaab2690"}
---

## Context
Pre-capsa aims maintained a memory tree with marker/consolidation/lint/doctor machinery and several
hooks (the ADRs for it live in docs/adr/0006–0012, 0018–0019, 0024, 0027–0030 as frozen history).

## Decision
Remove the whole subsystem. capsa's placement-addressed, one-record-per-file grammar makes relevance
structural (a tree walk) rather than computed, so there is no mutable store to keep coherent. The only
active machinery becomes one advisory read-time staleness hook.

## Consequences
~1200 lines of shell and eight hooks deleted. Documentation stays current by construction (method
discipline) + detected drift (the anchor), not by background maintenance.

## Alternatives considered
Keeping a slimmed memory tree — rejected: it maintains a problem the format does not create.
