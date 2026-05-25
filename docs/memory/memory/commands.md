---
node: memory/commands
kind: module
code:
  - templates/commands/memory-init.md
  - templates/commands/remember.md
  - .claude/commands/memory-init.md
  - .claude/commands/remember.md
commits: []
sessions:
  - docs/plans/memory-tree-system.md
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
last_touched: 2026-05-25T11:46:53Z
last_consolidated: 2026-05-25T11:46:53Z
---

## Purpose

User-facing entry points to the memory tree. /memory-init (Sonnet, one-time) scans the codebase, proposes a tree, and seeds docs/memory/ after user approval. /remember (Haiku) files a note into the right leaf and section — does NOT write to CLAUDE.md (that path stays reserved for Claude-native /memory).

## Logical rules & invariants

## Editing considerations

## Deliberations & history

## Open questions
