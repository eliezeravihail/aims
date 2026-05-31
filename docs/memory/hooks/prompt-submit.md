---
node: hooks/prompt-submit
kind: module
code:
  - templates/hooks/prompt-submit.sh
  - .claude/hooks/prompt-submit.sh
commits: []
sessions: []
parents: []
children: []
related:
  - hooks/session-start
  - hooks/exit-plan-mode
  - discipline/plan
claude_md_refs:
  - "Hooks"
external_refs:
  - { path: docs/adr/0004-router-via-hook-injected-context.md, kind: adr, why: original menu-based router (superseded) }
  - { path: docs/adr/0015-auto-plan-and-draft-on-disk.md,       kind: adr, why: auto-engage /plan on edit intents }
owners:
  - ema
dirty: false
last_touched: 2026-05-31T14:23:43Z
last_consolidated: 2026-05-31T14:23:43Z
---

## Purpose

UserPromptSubmit hook — classifies user intent and **auto-engages
`/plan`** on every actionable intent (bug, feature, refactor, decision,
mechanical, ambiguous). `question` is the only intent that bypasses the
flow. Per ADR-0015 (supersedes ADR-0004's menu).

## Design rationale

- The pre-ADR-0015 menu had zero options to choose between once
  ADR-0010 collapsed the surface to `/plan` + `/install-on`. Auto-engage
  is the natural collapse.
- Engagement = creating `.claude/.planning-lock` (the same gate `/plan`
  Phase 1 sets) **plus** injecting a `[aims-router]` text that walks
  the model through Phases 1→5. The lock makes the next turn
  read-only-by-policy, not just convention.
- Hebrew / non-English prompts that don't match any English keyword
  regex fall through to the **ambiguous** bucket and auto-engage; the
  injected text documents the per-prompt opt-out in both languages.

## Invariants & gotchas

- **Suppression rules in order**: slash-prefix → lock already exists →
  short prompt during an in-progress plan → empty prompt. Any one
  short-circuits to `exit 0`.
- A code-paste-looking prompt (contains a triple-backtick fence) is
  treated as not-actionable to avoid auto-engaging on review/discussion
  pastes.
- The hook must always `exit 0` — UserPromptSubmit hooks cannot
  meaningfully block a prompt and the contract is "advisory only".

## Known issues

- False positives on imperatively-phrased questions ("explain the
  marker hook") still auto-engage. Mitigation: documented in-turn
  opt-out + the orphan-draft warning in session-start.

## Pointers

- `templates/hooks/prompt-submit.sh` — single source of truth.
- `templates/commands/plan.md` — the flow this hook engages.
- `tests/router-auto-plan.sh` — six smoke cases.

## Open questions

- A `!`-prefix hook-time opt-out (`!fix typo`) could shave one
  abort-in-turn for power users; deferred until friction reported.
