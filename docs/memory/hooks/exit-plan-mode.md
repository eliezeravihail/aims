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
last_touched: 2026-07-15T09:17:01Z
last_consolidated: 2026-07-15T09:17:01Z
---

## Purpose

PostToolUse hook on the harness's `ExitPlanMode` tool — bridges the
harness's inline plan presentation into a
`docs/plans/<UTC-date>-<slug>.md` file with `Status: in-progress`, so
close-out + memory consolidation see it the same way they would after
a `/plan` flow. Without it, harness-native plans never reach disk and
Phase 5 close-out would no-op.

## Invariants & gotchas

- Exits 0 always — PostToolUse hooks must not block.
- Empty body → no file written (defense against an empty payload).
- Filename collisions are a **no-op skip**, never an overwrite — the
  draft on disk stays authoritative even if `ExitPlanMode` fires after.
  Same-day re-runs of one plan therefore collide and skip (accepted v1
  behavior per ADR-0015).
- Slug: first `# ` heading (or first non-blank line), lowercased,
  non-alphanumerics collapsed to `-`, capped at 6 words; non-ASCII
  titles squash to dashes — fine for path hygiene.

## Pointers

- ADR-0015 — auto-plan + draft-on-disk + this bridge.
- templates/settings.json.tmpl — wires the PostToolUse matcher.
- tests/exit-plan-mode.sh — four smoke cases.

## Deltas
