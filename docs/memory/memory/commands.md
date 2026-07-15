---
node: memory/commands
kind: module
code:
  - templates/commands/install-on.md
  - .claude/commands/install-on.md
# (was: memory-init.md, memory-augment.md, remember.md — all removed per ADR-0010;
#  memory bootstrap + augment moved inline into /install-on Phase 5;
#  note-filing into nodes is now ordinary Edit work)
commits: []
sessions:
  - docs/plans/memory-tree-system.md
parents: []
children: []
related:
  - discipline/done
  - memory/phase-a-marker
  - memory/phase-b-consolidation
claude_md_refs:
  - "Workflow"
  - "Models policy"
external_refs:
  - { path: docs/adr/0007-tree-based-memory-with-auto-maintenance.md, kind: adr, why: defines the cold-start (/memory-init) and note-filing (/remember) UX }
owners:
  - ema
dirty: false
last_touched: 2026-07-15T09:17:02Z
last_consolidated: 2026-07-15T09:17:02Z
---

## Purpose

Historical breadcrumb for the memory tree's former user-facing
commands. `/memory-init` (cold-start scan) and `/memory-augment`
(refresh) moved into `/install-on` Phase 5; `/remember` (note-filing)
became ordinary Edit work. `templates/commands/remember.md` no longer
exists.

## Invariants & gotchas

- Note-filing must NOT write to CLAUDE.md (that path stays reserved
  for Claude-native `/memory`) and must NOT create a new node for a
  one-off note — file under the nearest existing node's section.
- No aims command opens the Anthropic API (ADR-0009); filing and
  consolidation are Edit work by the active session.

## Pointers

- ADR-0007 — defined the original cold-start + note-filing UX.
- ADR-0009 — no-API-key rule.
- ADR-0010 — removed the three commands; Phase 5 absorbed bootstrap.

## Deltas

- 2026-05-27: `/memory-init`, `/memory-augment`, `/remember` removed;
  bootstrap+augment folded into `/install-on` Phase 5 — ADR-0010.
