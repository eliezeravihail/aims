---
kind: code
title: "UserPromptSubmit hook — two jobs in **one** `additionalContext`"
created: 2026-07-15
updated: 2026-07-29
code_globs: ["templates/hooks/prompt-submit.sh", ".claude/hooks/prompt-submit.sh"]
tags: [hooks]
---

## Purpose

UserPromptSubmit hook — two jobs in **one** `additionalContext`
emission: (1) **shape-gated convention note** (ADR-0029): a task-shaped
prompt (length ≥ 30 chars ∧ ≤ 4096 ∧ no ``` fence ∧ not ending in `?`)
gets the factual planning-convention paragraph — no intent classes, no
keyword lists, language-neutral; (2) **insight injector** (ADR-0016):
every Capsa insight whose `code_globs` is plausibly referenced by the
prompt has its body injected. Suppression first: slash-prefix → short
prompt during an in_progress plan → empty prompt.

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
- Insight matching: literal prefix of each `code_globs` entry (cut at
  first `*?[`) substring-tested against the prompt; bare-basename word
  match (≥5 chars) for non-glob entries. Per-session de-dup at
  `<state-dir>/.injected-<session_id>` (outside the capsule, §1.5;
  pruned after 7 days); total injection capped at `SIZE_CAP=8192`.
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
  `plans_with_status` — plan 0017 (memory-subsystem-diet).
- 2026-07-29: memory injector reads Capsa `code_globs` from
  `.capsa/insights/`; injected-state moved outside the capsule; plan
  state reads `.capsa/plans/` `status:` — f62ef11 (decision 0031).
