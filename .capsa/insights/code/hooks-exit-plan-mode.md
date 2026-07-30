---
kind: code
title: "PostToolUse hook on the harness's `ExitPlanMode` tool — bridges the"
created: 2026-07-15
updated: 2026-07-29
code_globs: ["templates/hooks/exit-plan-mode.sh", ".claude/hooks/exit-plan-mode.sh"]
tags: [hooks]
---

## Purpose

PostToolUse hook on the harness's `ExitPlanMode` tool — bridges the
harness's inline plan presentation into a conforming Capsa plan record
`.capsa/plans/NNNN-slug.md` (frontmatter `status: in_progress`, `id`
auto-incremented from the max existing plan id), so close-out + insight
consolidation see it the same way they would after a `/plan` flow.
Without it, harness-native plans never reach disk and Phase 5 close-out
would no-op.

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
- If the harness body already opens with a `---` frontmatter block it is
  kept verbatim (assumed conforming); otherwise Capsa frontmatter is
  synthesized. Same-slug guard skips duplicates under any id.

## Pointers

- ADR-0015 — auto-plan + draft-on-disk + this bridge.
- templates/settings.json.tmpl — wires the PostToolUse matcher.
- tests/exit-plan-mode.sh — the covering smoke cases.
- decision 0031 — aims on the Capsa capsule format.

## Deltas

- 2026-07-29: retargeted to write Capsa plan records to `.capsa/plans/`
  (`status: in_progress`, auto-incremented `id`) instead of
  `docs/plans/<date>-<slug>.md` with `Status:` prose — f62ef11.
