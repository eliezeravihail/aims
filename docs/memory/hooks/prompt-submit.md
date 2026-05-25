---
node: hooks/prompt-submit
kind: module
code:
  - templates/hooks/prompt-submit.sh
  - .claude/hooks/prompt-submit.sh
commits: []
sessions: []
related:
  - hooks/session-start
claude_md_refs:
  - "Hooks"
external_refs:
  - { path: docs/adr/0004-router-via-hook-injected-context.md, kind: adr, why: prompt-submit is the per-turn context-injection channel }
owners:
  - ema
dirty: false
last_touched: 2026-05-25T11:46:53Z
last_consolidated: 2026-05-25T11:46:53Z
---

## Purpose

UserPromptSubmit hook — runs before each user prompt is sent to the model. Currently surfaces routing hints (e.g. reminders about in-progress plans) per ADR-0004's hook-injected-context model.

## Logical rules & invariants

## Editing considerations

## Deliberations & history

## Open questions
