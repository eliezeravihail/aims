---
node: memory/phase-a-marker
kind: module
code:
  - templates/hooks/post-edit-marker.sh
  - .claude/hooks/post-edit-marker.sh
  - templates/memory/mark.sh
commits: []
sessions:
  - docs/plans/memory-tree-system.md
related:
  - memory/helpers
  - memory/phase-b-consolidation
claude_md_refs:
  - "Hooks"
external_refs:
  - { path: docs/adr/0007-tree-based-memory-with-auto-maintenance.md, kind: adr, why: Phase A specification — the cheap, deterministic flag flipper }
  - { path: tests/marker.sh, kind: test, why: six smoke cases for marker behaviour }
owners:
  - ema
dirty: false
last_touched: 2026-05-25T11:46:53Z
last_consolidated: 2026-05-25T11:46:53Z
---

## Purpose

Phase A of the two-phase maintenance design: a PostToolUse hook that runs after every Edit/Write/MultiEdit/NotebookEdit and flips `dirty: true` on every leaf whose `code:` list references the edited file. Pure bash + sed; ~27ms per call on a tiny tree. Unknown paths go to `docs/memory/_inbox.md` for later classification. The hook never blocks and always exits 0.

## Logical rules & invariants

- Never blocks. Always exits 0. Errors go to stderr only.
- Paths under `docs/memory/` and `.claude/` are skipped — editing the tree itself must not flip leaves dirty.
- If the edited path matches no leaf's `code:` list, append it to `_inbox.md` (de-duplicated: same path written only once).
- Path matching strips `:line-range` suffixes from `code:` entries before comparing (e.g., `src/foo.py:10-30` matches `src/foo.py`).

## Editing considerations

- The hook reads stdin exactly once (`payload=$(cat || true)`). Do not call `cat` again after the first read.
- Normalise the incoming path (strip leading `./`) before matching against `code:` entries.
- When changing the inbox append logic, ensure the de-dup check (`grep -qxF`) runs before writing.

## Deliberations & history

## Open questions
