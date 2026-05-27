# aims

This repository **is** the `aims` plugin. Working on it = developing the
plugin itself. The plugin is also installed locally (under `.claude/`)
so its hooks and conventions apply to its own development. Dogfooding.

<!-- aims-managed sections below; safe to edit, but keep the section headings stable. -->

## Build & test commands

This plugin has no language toolchain — it is markdown + bash. The closest
thing to a test is a syntax check on the hook scripts:

- Test: `bash -n templates/hooks/*.sh && bash -n .claude/hooks/*.sh`
- Lint / Typecheck: n/a

(Run before declaring work complete.)

## Decision records

Architecture decisions live in `docs/adr/`. Index: `docs/adr/README.md`.
ADRs are proposed automatically during plan close-out (the implementation
session decides per a confidence rule; see `/plan` Phase 4). For ad-hoc
decisions outside a plan, write `docs/adr/NNNN-slug.md` directly with
status `proposed`. Past decisions are append-only — to change one, write
a new ADR that supersedes it.

## Workflow

Two slash commands only:

- `/plan <task>` — non-trivial change. Read-only planning, durable
  artifact in `docs/plans/`, then implementation, then **inline
  close-out** (verify, auto-ADR, mark completed, memory consolidation).
- `/install-on <path>` — install or re-install aims into a target
  project. Idempotent; never destroys hand-edited content.

Everything else (bug-fix patches, refactors with obvious scope,
mechanical edits, ad-hoc questions): just do the work inline. The
hooks layer keeps you honest.

## Models policy

- Planning + plan close-out → **Opus** (auto via slash command frontmatter).
- Implementation → any model — switch with `/model <name>` per preference.

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
