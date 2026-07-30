---
kind: code
title: "Historical breadcrumb for the memory tree's former user-facing"
created: 2026-07-15
updated: 2026-07-29
code_globs: ["templates/commands/install-on.md", ".claude/commands/install-on.md"]
tags: [memory]
---

## Purpose

Historical breadcrumb for the memory tree's former user-facing
commands. `/memory-init` (cold-start scan) and `/memory-augment`
(refresh) moved into `/install-on` Phase 5; `/remember` (note-filing)
became ordinary Edit work. `templates/commands/remember.md` no longer
exists.

## Invariants & gotchas

- Note-filing must NOT write to CLAUDE.md (that path stays reserved
  for Claude-native `/memory`) and must NOT create a new node for a
  one-off note — file under the nearest existing node's section.
- No aims command opens the Anthropic API (ADR-0009); filing and
  consolidation are Edit work by the active session.

## Pointers

- ADR-0007 — defined the original cold-start + note-filing UX.
- ADR-0009 — no-API-key rule.
- ADR-0010 — removed the three commands; Phase 5 absorbed bootstrap.

## Deltas

- 2026-05-27: `/memory-init`, `/memory-augment`, `/remember` removed;
  bootstrap+augment folded into `/install-on` Phase 5 — ADR-0010.
- 2026-07-29: `/install-on` Phase 5 now bootstraps `.capsa/insights/`
  (via `new-insight.sh`) instead of a `docs/memory/` tree — f62ef11.
