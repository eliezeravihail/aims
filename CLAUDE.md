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

**aims hooks inform; they never block.** There is no planning lock and no
`block` mode — a hook's only effect is to inject **factual** context
(`additionalContext`), never to stop an edit (ADR-0020). Discipline is
achieved by awareness:

- `UserPromptSubmit` injects the relevant memory node and, for an actionable
  prompt, a factual planning-convention note.
- `PreToolUse` (`pre-write`) never blocks; on the first source edit of a
  session with no in-progress plan it injects the planning convention once.
- `PostToolUse` (`post-edit-marker`) marks the affected memory leaf `dirty`,
  injects a factual note naming the node to update, and stamps an advisory
  marker (`<leaf>.lock` = session-id + mtime; NOT a block). Concurrency: same
  session refreshes silently; another session's marker older than
  `AIMS_NODE_LOCK_STALE_SEC` (default 3600s) is taken over; a fresher one is
  reported as a possible concurrent edit (ask the user before updating).

Injected text MUST be factual, never imperative ("CRITICAL: do X"). Behavior
guard: `tests/inform-never-block.sh` (jq-free) + `tests/router-auto-plan.sh`.

## Plugin-specific notes (not from template)

- The plugin's distributable hook sources live under `templates/hooks/`.
- The locally-installed copies live under `.claude/hooks/` (for dogfooding).
- If you change a hook in `templates/`, refresh `.claude/hooks/` by
  running `/install-on .` — self-install is the dogfooding refresh path.
- This repo has no `src/`, `lib/`, or `app/` paths, so the `pre-write` hook
  in `block` mode would be a no-op here. `nudge` is the appropriate default.
