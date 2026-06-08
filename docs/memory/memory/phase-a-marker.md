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
parents: []
children: []
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
last_touched: 2026-06-08T11:09:39Z
last_consolidated: 2026-06-08T11:09:39Z
---

## Purpose

Phase A of the two-phase maintenance design: a PostToolUse hook that
runs after every Edit/Write/MultiEdit/NotebookEdit and flips
`dirty: true` on every node whose `code:` list references the edited
file. Pure bash + sed; ~27 ms per call on a tiny tree. Unknown paths
go to `docs/memory/_inbox.md` for later classification. It also
**surfaces each matched node's `## Requirements & invariants` section**
as factual `additionalContext` (ADR-0021) so the constraints are visible
at the moment the code is edited. The hook never blocks and always exits 0.

## Design rationale

- The marker is dumb on purpose: it doesn't try to summarize the
  change, only flag it. All judgment is deferred to Phase B
  (ADR-0007) and now runs in-band (ADR-0009).
- `mark.sh` carries the inverse `consolidated` subcommand used by
  the in-band model to flip the same flag clean after a successful
  body rewrite — keeps both transitions in one helper.
- Per ADR-0019, `mark.sh consolidated` ALSO removes the per-node
  sidecar `<leaf>.lock` that the Stop hook created during multi-session
  serialization. The marker (`post-edit-marker.sh`) never touches the
  sidecar — only the Stop hook creates it and `mark.sh consolidated`
  (or the Stop hook's EXIT trap) removes it.
- Requirements surfacing (ADR-0021) is factual, not imperative
  (ADR-0020): the note lists the recorded requirements and asks the
  model to verify the change against them, escalate a conflict to the
  user, and ask before recording any newly-stated constraint. Capped at
  2500 bytes per matched node via `fm_section` (enough to surface a
  complex module's full current invariant set without truncation).

## Requirements & invariants

- Requirements: none recorded beyond CLAUDE.md. Before editing, re-verify
  against CLAUDE.md and ask the user.

- Never blocks. Never exits non-zero. A broken marker must not
  block the user's edit.
- `path_matches` (in `_lib.sh`) handles trailing slashes and the
  optional `:line` suffix in `code:` entries; don't reimplement
  matching elsewhere.

## Known issues

## Pointers

- ADR-0007 — Phase A specification.
- ADR-0009 — adds the `consolidated` mode to `mark.sh`.
- ADR-0019 — `mark.sh consolidated` removes the `<leaf>.lock`
  sidecar alongside the dirty/timestamp bumps; supersedes ADR-0018.
- ADR-0021 — marker surfaces node requirements at edit time (the
  `reqblock` path + `fm_section`).
- `templates/memory/mark.sh:34-46` — `consolidated` subcommand.

## Open questions
