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
last_touched: 2026-06-08T10:41:36Z
last_consolidated: 2026-06-08T10:41:36Z
---

## Purpose

UserPromptSubmit hook — runs three jobs in **one** `additionalContext`
emission: (1) intent classification → a FACTUAL `/plan`-convention note on
actionable intents (bug, feature, refactor, decision, mechanical, ambiguous);
no lock, no auto-engage (ADR-0020); (2) **memory injector** (ADR-0016) —
for every memory node whose `code:` glob is plausibly referenced by the
prompt, inject that node's body (purpose, invariants, pointers, known
issues) so the model has node context without being asked; (3) the
suppression gate (slash / lock / short follow-up / empty). `question` is
the only intent that bypasses /plan but still triggers memory injection
when files are mentioned.

## Design rationale

- Actionable intents get a single FACTUAL planning-convention note;
  questions get none. No lock, no imperative text — aims informs, never
  blocks (ADR-0020).
- Non-English prompts that match no English keyword fall through to the
  **ambiguous** bucket, so they still get the note instead of being
  missed; the note is bilingual.

## Requirements & invariants

- Requirements: none recorded beyond CLAUDE.md. Before editing, re-verify
  against CLAUDE.md and ask the user.

- **Suppression rules in order**: slash-prefix → short prompt during an
  in-progress plan → empty prompt. Any one short-circuits to `exit 0`.
- A code-paste-looking prompt (contains a triple-backtick fence) is
  treated as not-actionable to avoid auto-engaging on review/discussion
  pastes.
- The hook must always `exit 0` — UserPromptSubmit hooks cannot
  meaningfully block a prompt and the contract is "advisory only".
- **Router note + memory injection are independent** (ADR-0016): a question
  that references a tracked file gets memory injection only; an actionable
  prompt gets both, in one emission.
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
- Payload parsing tolerates non-JSON: with `jq` present it reads
  `.prompt`, but if the payload is not valid JSON it falls back to
  treating raw stdin as the prompt. Production always sends JSON; this
  only helps jq-free callers and the `tests/inform-never-block.sh`
  raw-text cases.

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
