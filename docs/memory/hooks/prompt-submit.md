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
dirty: false
last_touched: 2026-06-04T14:07:11Z
last_consolidated: 2026-06-04T14:07:11Z
---

## Purpose

UserPromptSubmit hook — runs three jobs in **one** `additionalContext`
emission: (1) intent classification + auto-engage `/plan` on actionable
intents (bug, feature, refactor, decision, mechanical, ambiguous) per
ADR-0015 (supersedes ADR-0004's menu); (2) **memory injector** (ADR-0016) —
for every memory node whose `code:` glob is plausibly referenced by the
prompt, inject that node's body (purpose, invariants, pointers, known
issues) so the model has node context without being asked; (3) the
suppression gate (slash / lock / short follow-up / empty). `question` is
the only intent that bypasses /plan but still triggers memory injection
when files are mentioned.

## Design rationale

- The pre-ADR-0015 menu had zero options to choose between once
  ADR-0010 collapsed the surface to `/plan` + `/install-on`. Auto-engage
  is the natural collapse.
- Engagement = creating `.claude/.planning-lock` (the same gate `/plan`
  Phase 1 sets) **plus** injecting a `[aims-router]` text that walks
  the model through Phases 1→5. The lock makes the next turn
  read-only-by-policy, not just convention. The Phase 2 text tells the
  model to draft via the `Write` tool directly — ADR-0017 carves
  `docs/plans/*.md` out of the lock's pre-write block, so the prior
  Bash-heredoc workaround (fragile on apostrophes) is gone.
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
- **Lock + memory are independent** (ADR-0016). A pure-question prompt that
  references a tracked file gets memory injection only — no planning lock,
  no auto-engage text. An actionable prompt gets both, in the same emission.
- Memory matching derives a **literal prefix** from each `code:` glob (cut
  at the first `*`/`?`/`[`) and substring-tests the prompt; for non-glob
  entries it also word-matches the bare basename (≥5 chars). Compatible
  with ADR-0014's fnmatch semantics in the marker pipeline.
- Per-session de-dup state lives at `.claude/memory/.injected-<session_id>`
  and is pruned after 7 days. Total injection capped at `SIZE_CAP=8192`.
- **Length is measured in characters, not bytes.** The script forces a
  UTF-8 `LC_ALL` (first `*.utf-8` from `locale -a`) at the top when the
  inherited locale isn't already UTF-8, because bash `${#str}` counts
  bytes under POSIX/C. Without it a short non-ASCII prompt overcounts
  (Hebrew/CJK = 2-3 bytes/char) and trips the `plen >= 40` "actionable"
  ambiguous fallback — a 22-char Hebrew comment measured 42 bytes and got
  a spurious planning note. Falls back silently to POSIX if no UTF-8
  locale exists (heuristics may overcount, but never block).

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
