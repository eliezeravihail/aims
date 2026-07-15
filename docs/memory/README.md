# aims — memory tree

Navigable, hand-curated documentation of what lives where, why it's
shaped the way it is, and what you should know before editing it.
Maintained automatically per ADR-0007 + ADR-0009 + ADR-0028: the
`post-edit-marker` hook flags leaves as `dirty` when their referenced
source changes; the throttled `Stop` hook injects an in-band
consolidation prompt (delta-append by default, full compaction only
past size thresholds) that the active Claude Code session executes via
Edit — no external API key required.

This tree is a **navigator** over other memory sources. It references
`CLAUDE.md` sections, ADRs, plans, and tests — it never copies them.

## Tags

- **discipline/** — the slash commands defining the aims workflow
  (`/plan`, `/install-on`; historical breadcrumbs for retired commands).
- **hooks/** — context-injection hooks outside the memory subsystem
  (session-start, prompt-submit, pre-write, exit-plan-mode). All
  inform-only per ADR-0020. The memory-subsystem hooks
  (`post-edit-marker`, `stop-consolidate`, `session-end`, `pre-compact`)
  live under **memory/** instead.
- **memory/** — the ADR-0007 subsystem itself: helpers, Phase A marker,
  Phase B throttled in-band consolidation.
- **installer/** — the clone-and-bootstrap path (`/install-on` + the
  `templates/*.tmpl` files it substitutes).
- **testing/** — bash smoke tests for the marker + consolidation
  pipeline.

## Index

The list below is generated from each node's frontmatter + first
`## Purpose` line by `readme-sync.sh` (runs on every
`mark.sh <node> consolidated`; checked by `lint.sh`). Do not edit it by
hand — edit the node's Purpose line instead.

<!-- BEGIN NODE INDEX -->
- `discipline/adr` — The ADR convention and its shipped templates (`templates/adr-*.tmpl`,
- `discipline/done` — Historical breadcrumb for the removed `/done` slash command (plan
- `discipline/grunt` — Historical breadcrumb for the removed `/grunt` slash command — the
- `discipline/plan` — The `/plan` slash command. Per ADR-0022, planning is a project
- `hooks/exit-plan-mode` — PostToolUse hook on the harness's `ExitPlanMode` tool — bridges the
- `hooks/pre-write` — PreToolUse hook on `Edit | Write | MultiEdit | NotebookEdit`.
- `hooks/prompt-submit` — UserPromptSubmit hook — two jobs in **one** `additionalContext`
- `hooks/session-start` — SessionStart hook — informational only, never blocks. Surfaces:
- `installer/install-on` — `/install-on` — the clone-and-bootstrap installer (renamed from
- `installer/templates` — The `.tmpl` files under `templates/` that `/install-on` substitutes
- `memory/commands` — Historical breadcrumb for the memory tree's former user-facing
- `memory/helpers` — The bash helpers forming the deterministic substrate for the memory
- `memory/phase-a-marker` — Phase A of the two-phase maintenance design: a PostToolUse hook on
- `memory/phase-b-consolidation` — Phase B: the throttled Stop-hook pass that keeps node bodies current.
- `testing/smoke-tests` — Bash smoke tests for aims internals — no Anthropic API, no network.
<!-- END NODE INDEX -->

## Navigation

Read this README, then `cat` the leaf you need directly:

    cat docs/memory/<tag>/<leaf>.md

To check tree health: `bash .claude/memory/lint.sh`.
