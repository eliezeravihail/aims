# ais

This repository **is** the `ais` plugin. Working on it = developing the
plugin itself. The plugin is also installed locally (under `.claude/`)
so its hooks and conventions apply to its own development. Dogfooding.

<!-- ais-managed sections below; safe to edit, but keep the section headings stable. -->

## Build & test commands

This plugin has no language toolchain — it is markdown + bash. The closest
thing to a test is a syntax check on the hook scripts:

- Test: `bash -n templates/hooks/*.sh && bash -n .claude/hooks/*.sh`
- Lint / Typecheck: n/a

(Run before declaring work complete.)

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

Mode: `nudge` (configured at `.claude/ais-mode`). Change with:
```
echo nudge > .claude/ais-mode    # warn only
echo block > .claude/ais-mode    # block source edits without active plan
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
