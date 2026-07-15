---
node: discipline/grunt
kind: topic
code: []
# (was: templates/commands/grunt.md, .claude/commands/grunt.md — both removed per ADR-0010)
commits: []
sessions: []
parents: []
children: []
related: []
claude_md_refs:
  - "Models policy"
external_refs:
  - { path: docs/adr/0002-single-dispatch-over-multi-agent.md, kind: adr, why: /grunt ran on Haiku — the cheapest tier of the model policy }
owners:
  - ema
dirty: false
last_touched: 2026-07-15T09:17:01Z
last_consolidated: 2026-07-15T09:17:01Z
---

## Purpose

Historical breadcrumb for the removed `/grunt` slash command — the
cheap Haiku lane for mechanical edits (renames, log/config tweaks,
format fixes). Mechanical edits are now ordinary inline work; the
CLAUDE.md "Trivial-skip must be declared" convention covers the
judgment call.

## Invariants & gotchas

- None active — this node exists so the removal stays discoverable.

## Pointers

- ADR-0010 — removed `/grunt`.
- ADR-0002 — the single-dispatch model policy it belonged to.

## Deltas

- 2026-05-27: `/grunt` removed; mechanical edits are ordinary inline
  work — ADR-0010.
