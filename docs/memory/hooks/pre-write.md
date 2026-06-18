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
last_touched: 2026-06-18T09:31:44Z
last_consolidated: 2026-06-18T09:31:44Z
---

## Purpose

PreToolUse hook on `Edit | Write | MultiEdit | NotebookEdit`.
**Inform-only since ADR-0020** — it NEVER blocks and always returns
`permissionDecision:"allow"`. Its single effect is to inject, once per
session, a factual planning-convention NOTE on the first source edit
when no plan is in progress. The NOTE is **state-aware** (ADR-0023): it
names the file being edited and the missing plan, anchoring the
"first action = write a draft" convention to the moment of first edit
to close the conversational-drift skip mode.

## Design rationale

- Discipline by awareness, not by gate (ADR-0020). The hook describes
  the convention factually; it does not refuse, so no carve-outs,
  locks, or `exit 2` paths are needed anymore.
- The NOTE is descriptive, never imperative — an imperative
  ("CRITICAL: do X") trips Claude's prompt-injection defense.
- Emits via `jq` when present; the jq-less fallback now routes through
  the shared `json_escape` helper from `_lib.sh` so tabs/CR/other C0
  control chars in the NOTE can't produce invalid `additionalContext`
  JSON (M2, commit 9973146). Falls back to the old `\`/`"` sed escaper
  only if the helper can't be sourced.

## Invariants & gotchas

- Never block, never `exit 2`. Always `exit 0` with an `allow`
  decision (ADR-0020). The historical exit-2 surfacing contract below
  is obsolete.
- `target` extraction handles both `tool_input.file_path` and
  `tool_input.path` — the latter is how `NotebookEdit` reports.
- The NOTE injects at most once per session; `tests/inform-never-block.sh`
  guards both the never-block and once-per-session invariants.

## Known issues

- fixed (ADR-0019, historical): the plan-draft carve-out matched
  `target` against `docs/plans/*.md` as a relative pattern, but Claude
  Code passes absolute paths, so even legitimate `/plan` draft writes
  were blocked. Normalized via `git rev-parse --show-toplevel`. The
  carve-out itself was removed when ADR-0020 dropped all blocking.

## Pointers

- ADR-0020 — hooks inform, never block; removed all gating (the former
  three-responsibility blocking model — planning-lock hard-block,
  memory-node sidecar-lock refusal, `block`-mode source soft-block —
  is fully superseded).
- ADR-0023 — state-aware NOTE naming the file + missing plan.
- ADR-0003 / ADR-0017 / ADR-0019 — historical blocking design (default
  nudge, plan-draft carve-out, sidecar-lock refusal + path
  normalization); retained as breadcrumbs only.
- `templates/hooks/pre-write.sh:84` — the NOTE string.
- `tests/inform-never-block.sh` — never-block + once-per-session tests.
- External: docs/adr/0003-hooks-default-nudge-lock-always-blocks.md updated since last consolidation — review for impact
- External: docs/adr/0017-pre-write-carves-out-plan-drafts.md updated since last consolidation — review for impact
- External: docs/adr/0019-sidecar-lockfiles-for-memory-nodes.md updated since last consolidation — review for impact
- External: CLAUDE.md "Hooks" updated since last consolidation — review for impact

## Open questions
