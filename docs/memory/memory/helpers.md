---
node: memory/helpers
kind: module
code:
  - templates/memory/_lib.sh
  - templates/memory/mark.sh
  - templates/memory/new-leaf.sh
  - templates/memory/find-dirty.sh
  - templates/memory/lint.sh
  - templates/memory/check-refs.sh
  - templates/memory/consolidate.sh
  - templates/memory/classify-inbox.sh
  - .claude/memory/_lib.sh
commits: []
sessions:
  - docs/plans/memory-tree-system.md
related:
  - memory/phase-a-marker
  - memory/phase-b-consolidation
claude_md_refs:
  - "Plugin-specific notes (not from template)"
external_refs:
  - { path: docs/adr/0007-tree-based-memory-with-auto-maintenance.md, kind: adr, why: the design these helpers implement }
  - { path: tests/marker.sh, kind: test, why: covers mark/find-dirty + the marker hook }
  - { path: tests/consolidate.sh, kind: test, why: covers consolidate.sh + the Stop hook against a mocked Anthropic endpoint }
owners:
  - ema
dirty: false
last_touched: 2026-05-25T11:46:53Z
last_consolidated: 2026-05-25T11:46:53Z
---

## Purpose

The eight bash helpers that form the deterministic substrate for the memory tree. _lib.sh owns the frontmatter parsing/edit primitives (fm_get, fm_set, fm_list, list_leaves). The other seven are thin commands built on top: mark, new-leaf, find-dirty, lint, check-refs, consolidate, classify-inbox. All are POSIX-friendly (mawk/BSD-awk compatible) and degrade gracefully when ANTHROPIC_API_KEY is missing.

## Logical rules & invariants

## Editing considerations

## Deliberations & history

## Open questions
