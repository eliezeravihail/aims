---
node: hooks/pre-write
kind: module
code:
  - templates/hooks/pre-write.sh
  - .claude/hooks/pre-write.sh
commits: []
sessions: []
parents: []
children: []
related:
  - discipline/plan
claude_md_refs:
  - "Hooks"
external_refs:
  - { path: docs/adr/0003-hooks-default-nudge-lock-always-blocks.md, kind: adr, why: default mode = nudge; planning-lock always hard-blocks regardless of mode }
  - { path: docs/adr/0017-pre-write-carves-out-plan-drafts.md,        kind: adr, why: lock carves out docs/plans/*.md so /plan auto-engage can write the draft }
  - { path: docs/adr/0019-sidecar-lockfiles-for-memory-nodes.md,      kind: adr, why: pre-write refuses memory-node edits while another session holds the sidecar .lock; same patch normalizes absolute paths against the repo root so the docs/plans carve-out actually fires }
owners:
  - ema
dirty: false
last_touched: 2026-07-15T09:17:01Z
last_consolidated: 2026-07-15T09:17:01Z
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
- "Source" is defined by exclusion: `docs/*`, `*.md`, `*.txt`,
  tests, and `.claude/*` get nothing; everything else counts. No
  project path is hardcoded.
- Plan-state detection is **header-scoped** via `plans_with_status`
  from `_lib.sh` (first 5 lines only); the grep fallback (when
  `_lib.sh` is absent) is deliberately the old header-blind behavior.
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
  longer counts) — docs/plans/2026-07-15-memory-subsystem-diet.md.
