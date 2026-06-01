# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# aims

This repository **is** the `aims` plugin. Working on it = developing the
plugin itself. The plugin is also installed locally (under `.claude/`)
so its hooks and conventions apply to its own development. Dogfooding.

<!-- aims-managed sections below; safe to edit, but keep the section headings stable. -->

## Build & test commands

This plugin has no language toolchain — it is markdown + bash.

- **Syntax check (quick):** `bash -n templates/hooks/*.sh && bash -n .claude/hooks/*.sh`
- **Marker hook tests:** `bash tests/marker.sh` (pure bash, no API required)
- **Consolidation hook tests:** `bash tests/consolidate.sh` (requires `python3` + `jq`; spins up a mock Anthropic endpoint)

Run all of the above before declaring work complete.

## Architecture

aims is a **template installer**, not a runtime library. The key mental model:

- `AIMS_ROOT` (this repo) contains templates and the installer command.
- `TARGET` (any project) is where files get written during `/init-workflow`.
- Nothing runs from this repo at target runtime — all hooks, commands, and scripts are copied flat into `TARGET/.claude/`.

**Distribution split** (enforced by directory layout):
- `commands/init-workflow.md` — the only globally-installable surface (via plugin marketplace).
- `templates/commands/` — copied per-target; never globally registered.
- `templates/hooks/` — hook scripts copied to `TARGET/.claude/hooks/` and made executable.
- `templates/memory/` — memory-tree helpers copied to `TARGET/.claude/memory/` only when memory tree is enabled during init.

**Template variable substitution:** When `/init-workflow` copies template files it replaces `{{PROJECT_NAME}}`, `{{TEST_CMD}}`, `{{LINT_CMD}}`, `{{TYPECHECK_CMD}}`, `{{ADR_DIR}}`, `{{HOOK_MODE}}`, and `{{DATE}}` inline.

**CLAUDE.md merge is section-aware:** `/init-workflow` never overwrites existing same-named `## ` sections. Missing sections are appended and wrapped in `<!-- added by aims -->` markers. Conflicting sections are printed to stdout for manual resolution.

**settings.json merge:** Only `hooks` keys are deep-merged. All other keys in an existing settings.json are left untouched.

## Memory tree (ADR-0007)

The memory tree is an optional layer (`docs/memory/`) that survives context compaction. Key pieces:

- `templates/memory/_lib.sh` — shared frontmatter helpers (`fm_get`, `fm_set`) used by all other memory scripts.
- `templates/hooks/post-edit-marker.sh` — PostToolUse hook; sets `dirty: true` on leaves whose `code:` entries match the edited file path. Unknown paths go to `docs/memory/_inbox.md`.
- `templates/hooks/stop-consolidate.sh` — Stop hook; calls the Anthropic API to rewrite dirty leaves. Throttled by `AIMS_MEMORY_DIRTY_MAX` (default 5) and `AIMS_MEMORY_INTERVAL_SEC`. Bypass with `--force`.
- `templates/hooks/session-end.sh` — SessionEnd hook; runs `classify-inbox.sh` to route inbox entries to leaves.

When changing a memory hook in `templates/`, also update the copy in `.claude/hooks/` to keep dogfooding accurate.

## Decision records

Architecture decisions live in `docs/adr/`. Index: `docs/adr/README.md`.

- New decision → `/adr <title>`
- Past decisions are append-only. To change one, write a new ADR that
  supersedes it; do not edit the old.

## Workflow

- Non-trivial change → `/plan <task>` first. Plans live in `docs/plans/`.
- Mechanical work (renames, formatting, log/config edits) → `/grunt`.
- Closing a plan → `/done` (verifies steps and prompts for ADRs).

## Models policy

- Planning, ADR, closing → **Opus** (auto via slash command frontmatter).
- Implementation → **Sonnet** (run `/model sonnet` once per session).
- Mechanical / log / config edits → `/grunt` runs on **Haiku**.
- Override anytime with `/model <name>`.

## Hooks

Mode: `nudge` (configured at `.claude/aims-mode`). Change with:
```
echo nudge > .claude/aims-mode    # warn only
echo block > .claude/aims-mode    # block source edits without active plan
```
The planning lock (`.claude/.planning-lock`) always blocks edits regardless
of mode — this is what makes `/plan` actually read-only.

## Plugin-specific notes (not from template)

- The plugin's distributable hook sources live under `templates/hooks/`.
- The locally-installed copies live under `.claude/hooks/` (for dogfooding).
- If you change a hook in `templates/`, also re-copy it to `.claude/hooks/`
  to keep dogfooding accurate. (A future ADR may automate this.)
- This repo has no `src/`, `lib/`, or `app/` paths, so the `pre-write` hook
  in `block` mode would be a no-op here. `nudge` is the appropriate default.
