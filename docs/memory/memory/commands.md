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
last_touched: 2026-05-31T14:26:12Z
last_consolidated: 2026-05-31T14:26:12Z
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

- superseded by ADR-0010: `/memory-init`, `/memory-augment`, and
  `/remember` are removed. Cold-start scan and augment-only refresh
  moved into `/install-on` Phase 5 (runs at the end of every
  install or re-install). Note-filing into a node is just an
  ordinary Edit.
- fixed: `/remember` guidance referenced an "Anthropic API" rule
  that no longer made sense after consolidation moved in-band;
  the obsolete bullet was removed (commit 0c0852f).

## Pointers

- ADR-0007 — defines the cold-start (`/memory-init`) and note-filing
  (`/remember`) UX.
- ADR-0009 — clarifies that no aims command opens the Anthropic API.
- `templates/commands/remember.md` — the command itself.

## Open questions
