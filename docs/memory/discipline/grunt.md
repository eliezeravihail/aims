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
  - { path: docs/adr/0002-single-dispatch-over-multi-agent.md, kind: adr, why: /grunt runs on Haiku — the cheapest tier of the model policy }
owners:
  - ema
dirty: false
last_touched: 2026-05-25T11:46:53Z
last_consolidated: 2026-05-25T11:46:53Z
---

## Purpose

Documents the /grunt slash command — the cheap, fast lane for mechanical edits (renames, log/config tweaks, format fixes) that require no architectural judgment. Runs on Haiku via slash-command frontmatter; never asks AskUserQuestion for architectural choices.

## Design rationale

## Invariants & gotchas

## Known issues

- superseded by ADR-0010: `/grunt` is removed. Mechanical edits
  (renames, log/config tweaks, format fixes) are now just ordinary
  inline work — no special command needed.


## Pointers

## Open questions
