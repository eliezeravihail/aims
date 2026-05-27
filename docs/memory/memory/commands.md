---
node: memory/commands
kind: module
code:
  - templates/commands/memory-init.md
  - templates/commands/remember.md
  - templates/commands/memory-augment.md
  - .claude/commands/memory-init.md
  - .claude/commands/remember.md
  - .claude/commands/memory-augment.md
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
last_touched: 2026-05-27T18:41:28Z
last_consolidated: 2026-05-27T18:41:28Z
---

## Purpose

User-facing entry points to the memory tree. `/memory-init` (Sonnet,
one-time) scans the codebase, proposes a tree, and seeds
`docs/memory/` after user approval. `/remember` (Haiku) files a note
into the right node and section — does NOT write to CLAUDE.md (that
path stays reserved for Claude-native `/memory`).

## Design rationale

- `/remember` is a structural file-edit only — pick the right node
  and section, then Edit. It does not synthesize content with the
  Anthropic API and does not need network access. (Consolidation,
  which DOES rewrite bodies, runs in-band via the Stop hook per
  ADR-0009; `/remember` is the lightweight cousin.)

## Invariants & gotchas

- `/remember` MUST NOT write to CLAUDE.md.
- `/remember` MUST NOT create a new node for a one-off note — file
  under the nearest existing node's appropriate section instead, or
  suggest `/memory-augment` if the topic genuinely deserves its own
  node.

## Known issues

- fixed: `/remember` guidance referenced an "Anthropic API" rule
  that no longer made sense after consolidation moved in-band;
  the obsolete bullet was removed (commit 0c0852f).

## Pointers

- ADR-0007 — defines the cold-start (`/memory-init`) and note-filing
  (`/remember`) UX.
- ADR-0009 — clarifies that no aims command opens the Anthropic API.
- `templates/commands/remember.md` — the command itself.

## Open questions
