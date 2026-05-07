# ADR-0005: AIS repo requires /init-workflow bootstrap before full AIS workflow is available

Status: proposed
Date: 2026-05-07
Supersedes: —
Superseded by: —

## Context

AIS is dogfooded: its own repo uses its hooks and slash commands during
development. However, three AIS workflow commands (`/plan`, `/done`, and
the docs-based plan lifecycle) depend on `docs/plans/` existing —
a directory that `/init-workflow` creates as part of bootstrap.

During a hands-on experiment (2026-05-07) we discovered that `docs/plans/`
did not exist in the AIS repo, so:

- `/done` could not locate any in-progress plan and exited with an error.
- `/plan` would write a plan to `docs/plans/` only if that directory exists;
  otherwise Claude Code's native plan mode (`~/.claude/plans/`) is the
  silent fallback.
- The planning-lock (`pre-write.sh:38-47`) still protected edits correctly,
  so safety was not compromised — only the AIS plan-file lifecycle was absent.

This means a developer who clones AIS and starts using it without running
`/init-workflow` gets partial workflow: planning-lock protection + hooks, but
no durable plan files, no `/done`, and no ADR prompting from plan closure.

## Decision

We will require `/init-workflow` as an explicit bootstrap step before
starting non-trivial AIS development. The repo's CLAUDE.md documents this
under "Workflow". Until bootstrapped, only the planning-lock and hook nudges
are active; the full plan/done lifecycle is unavailable.

## Consequences

- ✅ Developers know immediately what to run first; no silent fallback.
- ✅ `docs/plans/` created deterministically by `/init-workflow`, so `/plan`
  and `/done` work on first use after bootstrap.
- ⚠️ Adds one manual step on a fresh clone. Acceptable because this is a
  developer tool with an explicit setup story.
- 🔒 Closes the door on relying on Claude Code native plan mode as a
  long-term substitute; `~/.claude/plans/` plans don't surface in `/done`
  and bypass the AIS plan lifecycle.

## Alternatives considered

- **Auto-create `docs/plans/` inside `/plan`** — rejected: hides the fact
  that `/init-workflow` was skipped; other init artifacts (CLAUDE.md section,
  `.claude/ais-mode`) would still be missing.
- **Accept Claude Code plan mode as a valid fallback** — rejected: it
  bypasses `/done`, plan-file ADR prompting, and the status lifecycle.
  Developers would silently get half the system.

## Verification

- `docs/plans/` exists: `Test-Path docs/plans` returns `True`.
- `docs/adr/` and `docs/adr/README.md` exist.
- `.claude/ais-mode` contains `nudge` or `block`.
- Run: `bash -n .claude/hooks/*.sh && echo hooks-ok`
