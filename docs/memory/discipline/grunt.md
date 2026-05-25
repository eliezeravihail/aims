---
node: discipline/grunt
kind: module
code:
  - templates/commands/grunt.md
  - .claude/commands/grunt.md
commits: []
sessions: []
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

## Logical rules & invariants

## Editing considerations

## Deliberations & history

## Open questions
