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
  - { path: docs/adr/0016-prompt-memory-injection.md,           kind: adr, why: per-prompt memory node body auto-injection }
owners:
  - ema
dirty: true
last_touched: 2026-06-11T07:18:22Z
last_consolidated: 2026-06-02T15:13:24Z
---

## Purpose

UserPromptSubmit hook — runs three jobs in **one** `additionalContext`
emission: (1) intent classification + factual planning-convention note
on actionable intents (bug, feature, refactor, decision, mechanical,
ambiguous) per ADR-0020/0022 (no lock, no imperative — descriptive
convention only); (2) **memory injector** (ADR-0016) — for every memory
node whose `code:` glob is plausibly referenced by the prompt, inject
that node's body (purpose, invariants, pointers, known issues) so the
model has node context without being asked; (3) the suppression gate
(slash / short follow-up / empty). `question` is the only intent that
gets no planning note but still triggers memory injection when files
are mentioned.

## Design rationale

- Per ADR-0020/0022 the router NEVER locks. For an actionable intent
  it injects a single factual `router_text` describing the full
  planning behavior — read-only discovery → draft to `docs/plans/` →
  approval → implementation → inline close-out — and notes that the
  `/plan` slash command is an OPTIONAL Opus-subagent shortcut. The
  convention is descriptive, not imperative (an imperative trips
  Claude's prompt-injection defense).
- Hebrew / non-English prompts that don't match any English keyword
  regex fall through to the **ambiguous** bucket and still receive the
  factual convention note.

## Invariants & gotchas

- **Suppression rules in order**: slash-prefix → short prompt during an
  in-progress plan → empty prompt. Any one short-circuits to `exit 0`.
  (No planning lock since ADR-0020.)
- A code-paste-looking prompt (contains a triple-backtick fence) is
  treated as not-actionable to avoid injecting on review/discussion
  pastes.
- The hook must always `exit 0` — UserPromptSubmit hooks cannot
  meaningfully block a prompt and the contract is "advisory only".
- **Convention + memory are independent.** A pure-question prompt that
  references a tracked file gets memory injection only — no convention
  note. An actionable prompt gets both, in the same emission.
- Memory matching derives a **literal prefix** from each `code:` glob (cut
  at the first `*`/`?`/`[`) and substring-tests the prompt; for non-glob
  entries it also word-matches the bare basename (≥5 chars). Compatible
  with ADR-0014's fnmatch semantics in the marker pipeline.
- Per-session de-dup state lives at `.claude/memory/.injected-<session_id>`
  and is pruned after 7 days. Total injection capped at `SIZE_CAP=8192`.

## Known issues

- False positives on imperatively-phrased questions ("explain the
  marker hook") still auto-engage. Mitigation: documented in-turn
  opt-out + the orphan-draft warning in session-start.

## Pointers

- `templates/hooks/prompt-submit.sh` — single source of truth.
- `templates/commands/plan.md` — the flow this hook engages.
- `tests/router-auto-plan.sh` — six smoke cases.
- ADR-0016 — per-prompt memory node body auto-injection.

## Open questions

- A `!`-prefix hook-time opt-out (`!fix typo`) could shave one
  abort-in-turn for power users; deferred until friction reported.
