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
last_touched: 2026-08-27T21:10:23Z
last_consolidated: 2026-08-27T21:10:23Z
---

## Purpose

PreToolUse hook on `Edit | Write | MultiEdit | NotebookEdit` — **inform-only
since ADR-0020**. On the first source-path edit of a session with no
`Status: draft`/`in-progress` plan in `docs/plans/`, it emits a single
`permissionDecision: "allow"` + a factual `additionalContext` NOTE naming
the file being edited and the missing plan (state-aware per ADR-0023).
Subsequent edits in the same session are silent (a `.claude/.aims-plan-note-*`
marker dedups). It never blocks, never locks, and always exits 0.

## Design rationale

- ADR-0020 removed all gating from this hook: the earlier three-responsibility
  model (planning-lock hard-block + memory-node lock refusal + `block`-mode
  soft-block) is gone. Discipline is achieved by awareness — the NOTE states
  the convention factually, never imperatively.
- The NOTE is **state-aware** (ADR-0023): it names the exact file and states
  that a brief conversational "yes" approves writing the draft (Phase 2),
  not skipping to implementation (Phase 4) — anchoring the planning
  convention to the moment of first source edit, which closed the
  conversational-drift skip mode.
- Source-path detection covers canonical roots (`src/`, `lib/`, `app/`,
  `server/`, `client/`, `packages/`); tests/docs/markdown never trigger the
  NOTE. Path normalization against `git rev-parse --show-toplevel` happens
  once (originated in the ADR-0019-era fix; still load-bearing).

## Invariants & gotchas

- The hook MUST always exit 0 and always emit `permissionDecision: "allow"` —
  any other decision would violate ADR-0020.
- Once-per-session: the NOTE fires only on the first matching edit;
  the `.aims-plan-note-<sid>` marker (pruned after 1 day) suppresses repeats.
- `target` extraction handles both `tool_input.file_path` and
  `tool_input.path` — the latter is how `NotebookEdit` reports.
- jq-less JSON emission routes through the shared `json_escape` helper
  when `_lib.sh` is present (M2); inline sed fallback otherwise.

## Known issues

- fixed: the pre-ADR-0020 carve-out matched `target` against
  `docs/plans/*.md` as a relative pattern while Claude Code passes absolute
  paths, blocking even legitimate `/plan` draft writes — normalized via
  `git rev-parse --show-toplevel` (ADR-0019 era; historical).
- fixed: jq-less escaper handled only `\` and `"`, producing invalid JSON
  when the NOTE carried a tab/CR — routed through shared `json_escape`
  (commit 9973146).

## Pointers

- ADR-0020 — hooks inform, never block; removed all gating from this hook.
- ADR-0023 — the state-aware NOTE and Phase-2-vs-Phase-4 approval semantics.
- ADR-0019 — path normalization origin (historical; superseded by 0024 for
  the lock protocol itself).
- `templates/hooks/pre-write.sh:84` — the NOTE string.
- `tests/inform-never-block.sh` — never-block + once-per-session invariants.
- External: docs/adr/0019-sidecar-lockfiles-for-memory-nodes.md updated since
  last consolidation — review for impact.

## Open questions
