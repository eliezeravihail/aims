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
  - { path: docs/adr/0015-auto-plan-and-draft-on-disk.md,       kind: adr, why: auto-engage /plan on edit intents (classifier half superseded by 0029) }
  - { path: docs/adr/0016-prompt-memory-injection.md,           kind: adr, why: per-prompt memory node body auto-injection }
owners:
  - ema
dirty: false
last_touched: 2026-07-15T09:17:01Z
last_consolidated: 2026-07-15T09:17:01Z
---

## Purpose

UserPromptSubmit hook — two jobs in **one** `additionalContext`
emission: (1) **shape-gated convention note** (ADR-0029): a task-shaped
prompt (length ≥ 30 chars ∧ ≤ 4096 ∧ no ``` fence ∧ not ending in `?`)
gets the factual planning-convention paragraph — no intent classes, no
keyword lists, language-neutral; (2) **memory injector** (ADR-0016):
every node whose `code:` glob is plausibly referenced by the prompt has
its body injected. Suppression first: slash-prefix → short prompt
during an in-progress plan → empty prompt.

## Invariants & gotchas

- Must always `exit 0` and never create a lock — advisory only
  (ADR-0020).
- **Length is measured in characters, not bytes**: the hook forces a
  UTF-8 `LC_ALL` when available, because bash `${#str}` counts bytes
  under POSIX/C and a ~22-char Hebrew prompt (42 bytes) would falsely
  clear the 30-char gate. Load-bearing for the shape gate.
- The grep fallback for `plans_with_status` (when `_lib.sh` is absent)
  is header-blind by design — sandbox tests that exercise Track D must
  copy `_lib.sh` in.
- Memory matching: literal prefix of each `code:` glob (cut at first
  `*?[`) substring-tested against the prompt; bare-basename word match
  (≥5 chars) for non-glob entries. Per-session de-dup at
  `.claude/memory/.injected-<session_id>` (pruned after 7 days); total
  injection capped at `SIZE_CAP=8192`.
- Convention note + memory injection are independent; a question can
  get memory injection with no note.
- open: a `!`-prefix hook-time opt-out (`!fix typo`) — deferred until
  friction reported.

## Pointers

- ADR-0029 — shape gate replaces the intent classifier.
- ADR-0016 — memory auto-injection.
- ADR-0025 — injected node bodies are fenced as data.
- tests/router-auto-plan.sh — eight smoke cases.

## Deltas

- 2026-06-11: jq-less prompt extraction fixed (regex on the `prompt`
  field instead of whole payload); `grep -qwF --` dash-safety — 91fe2bd.
- 2026-07-15: ~200-line regex intent classifier (incl. Hebrew
  interrogative list) replaced by the 4-condition shape gate; the old
  "imperative questions auto-engage" false positive dissolved by
  design (questions = trailing `?` only) — ADR-0029.
- 2026-07-15: in-progress-plan suppression switched to header-scoped
  `plans_with_status` — docs/plans/2026-07-15-memory-subsystem-diet.md.
