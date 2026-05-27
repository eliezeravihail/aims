# ADR-0010: Two-command surface; idempotent install; auto plan close-out
Status: proposed
Date: 2026-05-27
Supersedes: parts of ADR-0002, ADR-0007 (the user-facing command lists)
Superseded by: —

## Context

The aims plugin grew to **eight** user-facing slash commands
(`/plan`, `/done`, `/adr`, `/grunt`, `/remember`, `/memory-init`,
`/memory-augment`, `/init-workflow`). Each was a thin wrapper around
work the active Claude model could already do; the surface bloat was
the cost, not the value. Users repeatedly forgot which to use;
discipline split into too many lanes; the model had multiple places
to "ask for ADR" or "consolidate memory" with slightly different
phrasing.

In parallel the install command (`/init-workflow`) was documented as
idempotent but the body left key questions open — does re-install
overwrite `CLAUDE.md`? memory node bodies? a hand-edited ADR? The
answer needed to be "no, never" but wasn't explicit in the prompt.

## Decision

We will reduce the user-facing slash-command surface to **two**:
`/plan` and `/install-on`. Everything previously fronted by `/done`,
`/adr`, `/grunt`, `/remember`, `/memory-init`, and `/memory-augment`
moves inline:

- **Plan close-out** (verify steps + run `## Verification` + decide
  ADRs + mark `completed` + consolidate memory) runs at the end of
  the implementation session itself, nudged by the existing Stop
  hook when an `in-progress` plan exists.
- **ADR creation** is auto-decided per item by the implementation
  session: create when the change is a clear architectural
  commitment, skip when bug/refactor/doc/test/mechanical, ask only
  when borderline. ADRs always start `proposed`.
- **Memory bootstrap** runs at the end of `/install-on` against the
  target (cold-start scan when missing, augment-only when present).
  Memory maintenance after that is the existing ADR-0009 loop.
- **Mechanical edits** (`/grunt`) and **notes** (`/remember`) become
  ordinary inline actions; no command needed.

`/install-on` (renamed from `/init-workflow` for clarity) is
**strictly idempotent** with documented per-class rules:

- Overwrite (with diff preview): hooks, memory scripts, the two
  slash commands.
- Delete: obsolete commands left over from a previous install.
- Never touch: existing `CLAUDE.md` sections, ADRs, plan files,
  memory node bodies.
- Augment-only: `docs/memory/` when it already exists.

## Consequences

**Better.** Users only need to remember two commands. There is one
authoritative place where each lifecycle step happens. Re-installs
are guaranteed non-destructive — `/install-on` becomes the upgrade
path too.

**Worse.** Existing users with muscle memory for `/done` or `/adr`
will get "unknown command" and have to re-learn. The auto-ADR rule
may occasionally miss a borderline case (mitigated: rule biases to
ask; ADRs are always `proposed` and reviewable).

**Possible.** Inline close-out makes it easier to skip steps when
in a hurry; the hook nudge is advisory, not enforcing. If that
becomes a problem, a future ADR can promote close-out from advisory
to required (e.g., a `block`-mode session-end hook).

## Alternatives considered

- **A — Keep all 8 commands, just better docs.** Rejected: the
  cost isn't documentation, it's branching the model's decision
  tree on every prompt.
- **B — Merge `/memory-init` + `/memory-augment` into `/memory`,
  keep the rest.** Rejected: still six commands; the ADR/close-out
  flow stays manual.
- **C — Eliminate slash commands entirely; rely on hooks + CLAUDE.md.**
  Rejected: `/plan` is a real mode boundary (read-only +
  planning-lock) that needs an explicit user signal; `/install-on`
  needs a target argument that doesn't fit a hook.

## Verification

- `ls .claude/commands/` lists exactly `install-on.md plan.md`.
- `ls templates/commands/` lists the same two.
- `grep -rE '/(done|adr|grunt|remember|memory-(init|augment)|init-workflow)\b' .claude templates CLAUDE.md`
  returns only historical references (this ADR, prior plans, prior ADRs).
- `templates/hooks/stop-consolidate.sh` includes an `IN_PROGRESS_PLAN`
  branch that emits a close-out nudge.
- `/plan` template (`.claude/commands/plan.md`) leads with `## TL;DR`
  and embeds the Phase 4 close-out flow.
- `/install-on` template documents the per-class idempotency rules in
  its Phase 3 table.
