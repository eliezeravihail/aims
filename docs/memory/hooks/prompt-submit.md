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

- Always exits 0. Must never block — UserPromptSubmit hooks that exit non-zero are treated as errors by Claude Code.
- Suppression order (first match wins): slash-prefixed prompt → skip; planning-lock active → skip; short follow-up (< 120 chars) during an active plan → skip; empty prompt → skip.
- Intent classification uses a first-match regex chain on the lowercased prompt. `bug` patterns take highest priority.

## Editing considerations

- All intent-matching patterns operate on `lower=$(... | tr '[:upper:]' '[:lower:]')`. Write new patterns in lowercase.
- The `router_text` heredoc uses `__INTENT__` as a placeholder replaced by `${router_text//__INTENT__/$intent}`. Do not use `$intent` directly inside the heredoc — it won't expand.
- The `jq` path and the hand-escape sed/awk fallback must produce equivalent JSON. If you change the output schema, update both branches.

## Deliberations & history

## Open questions
