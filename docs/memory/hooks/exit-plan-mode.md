---
node: hooks/exit-plan-mode
kind: module
code:
  - templates/hooks/exit-plan-mode.sh
  - .claude/hooks/exit-plan-mode.sh
commits: []
sessions: []
parents: []
children: []
related:
  - hooks/prompt-submit
  - hooks/session-start
  - discipline/plan
claude_md_refs:
  - "Hooks"
external_refs:
  - { path: docs/adr/0015-auto-plan-and-draft-on-disk.md, kind: adr, why: defines this hook as the harness-native-ExitPlanMode bridge }
owners:
  - ema
dirty: false
last_touched: 2026-05-31T14:25:01Z
last_consolidated: 2026-05-31T14:25:01Z
---

## Purpose

PostToolUse hook on the harness's `ExitPlanMode` tool — bridges the
harness's inline plan presentation into a `docs/plans/<UTC-date>-<slug>.md`
file with `Status: in-progress`, so close-out + memory consolidation see
it the same way they would after a `/plan` flow.

## Design rationale

- The `/plan` slash command writes the draft itself (ADR-0015 Phase 2),
  but the harness has a native `ExitPlanMode` path that bypasses
  `/plan`. Without a bridge, plans presented that way would never reach
  disk and Phase 5 close-out would no-op.
- Slug is derived from the first `# `-heading of the plan body, or the
  first non-blank line; capped at 6 hyphen-separated words for path
  stability.
- Filename collisions are a **no-op skip**, not an overwrite. This
  preserves the `/plan` invariant that the draft on disk is the
  authoritative artifact even if the model calls `ExitPlanMode` after.

## Invariants & gotchas

- Exits 0 always — PostToolUse hooks must not block.
- Empty body → no file written (defense against an empty harness
  payload).
- Slug uses `[:lower:]` + non-alphanumeric → `-` collapse; non-ASCII
  characters get squashed to dashes, which is fine for path hygiene
  even when the title is in Hebrew.

## Known issues

- Same-day re-runs of the same plan collide on slug and skip. ADR-0015
  documents this as accepted v1 behavior.

## Pointers

- ADR-0015 — auto-plan + draft-on-disk + this bridge.
- `templates/settings.json.tmpl` — wires the `PostToolUse` matcher.
- `tests/exit-plan-mode.sh` — four smoke cases.

## Open questions

None.
