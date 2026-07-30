---
kind: code
title: "PreToolUse hook on `Edit | Write | MultiEdit | NotebookEdit`."
created: 2026-07-15
updated: 2026-07-29
code_globs: ["templates/hooks/pre-write.sh", ".claude/hooks/pre-write.sh"]
tags: [hooks]
---

## Purpose

PreToolUse hook on `Edit | Write | MultiEdit | NotebookEdit`.
**Inform-only since ADR-0020** — always `permissionDecision:"allow"`.
Its single effect: on the first source edit of a session with no
in-progress plan, inject once a **state-aware** factual
planning-convention NOTE naming the file being edited and the missing
plan (ADR-0023), anchoring "first action = write a draft" to the
moment of first edit.

## Invariants & gotchas

- Never block, never `exit 2` — always exit 0 with `allow` (ADR-0020).
- "Source" is defined by exclusion: `.capsa/*`, `docs/*`, `*.md`,
  `*.txt`, tests, and `.claude/*` get nothing; everything else counts.
  No project path is hardcoded.
- Plan-state detection reads the Capsa plan frontmatter `status:`
  (value `in_progress`) via `plans_with_status` from `_lib.sh`; the
  grep fallback (when `_lib.sh` is absent) is frontmatter-anchored too.
- `target` extraction handles both `tool_input.file_path` and
  `tool_input.path` (NotebookEdit); absolute paths normalize against
  `$PWD` / git toplevel, cross-platform (Windows drive letters, MSYS).
- The NOTE injects at most once per session
  (`.claude/.aims-plan-note-<sid>`); `tests/inform-never-block.sh`
  guards never-block + once-per-session.

## Pointers

- ADR-0020 — hooks inform, never block; removed this hook's former
  blocking model (planning-lock hard-block, memory-node sidecar-lock
  refusal, `block`-mode source soft-block).
- ADR-0023 — the state-aware NOTE + approval-semantics rule
  ("yes" approves Phase 2, not Phase 4).
- ADR-0003 / ADR-0017 / ADR-0019 — historical blocking design,
  breadcrumbs only.
- tests/inform-never-block.sh — invariant tests.

## Deltas

- 2026-06-11: jq-less emitter routed through shared `json_escape`
  (tabs/CR-safe additionalContext) — 9973146.
- 2026-07-15: in-progress-plan check switched to header-scoped
  `plans_with_status` (body text quoting "Status: in-progress" no
  longer counts) — plan 0017 (memory-subsystem-diet).
- 2026-07-29: reads `.capsa/plans/` (`status: draft`/`in_progress` YAML)
  instead of `docs/plans/`; `.capsa/*` added to the allow-set; NOTE
  wording Capsa-ised — f62ef11 (decision 0031).
