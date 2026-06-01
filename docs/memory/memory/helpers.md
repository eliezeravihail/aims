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

- `_lib.sh` must be sourced before calling `fm_get`, `fm_set`, `fm_list`, or `list_leaves`.
- All helpers operate on paths relative to the current working directory (TARGET root). Never pass absolute paths.
- Helpers degrade gracefully when `ANTHROPIC_API_KEY` is absent: `consolidate.sh` exits 0 and leaves the leaf dirty.
- The `AIMS_MEMORY_DIR` env var overrides the default `docs/memory/` path — used in tests to point to a temp directory.

## Editing considerations

- POSIX compatibility is required: mawk and BSD awk must work. Avoid GNU-specific awk extensions (no `gensub`, no `FPAT`).
- `find-dirty.sh` is called inside `mapfile` in `stop-consolidate.sh` and must output exactly one leaf path per line with no trailing whitespace.
- Any new helper that reads frontmatter must source `_lib.sh` first — do not reimplement frontmatter parsing inline.

## Deliberations & history

## Open questions
