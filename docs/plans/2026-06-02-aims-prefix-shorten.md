# Plan: Shorten the AIMS internal reply marker to `===[aims: <msg>]===`
Status: completed
Started: 2026-06-02
Completed: 2026-06-02

## TL;DR

Replace the heavy wrapper `==== AIMS (internal) ====` / `==== /AIMS ====`
with a single-line marker `===[aims: <message>]===`. User found the
two-line wrapper too prominent for what is meant to be a terse
plumbing report. Convention scope is unchanged (still only the Stop /
consolidation-update hook's result; ADR-0021 still applies).

## Changes

### templates/hooks/stop-consolidate.sh — convention text (applied)

```sh
Reply-format: report this consolidation pass to the user as a single
short line in the form `===[aims: <message>]===` — examples:
`===[aims: nodes updated]===`, `===[aims: queue drained]===`,
`===[aims: 4 dirty]===`. One line only, no per-node prose unless the
user asks, no opening/closing wrapper.
```

### templates/hooks/session-start.sh — standing convention bullet

Update the reply-format bullet under "Project conventions (factual)"
to reference the new single-line form.

### .claude/hooks/{stop-consolidate,session-start}.sh — mirror refresh

### README.md — convention paragraph

Replace the `==== AIMS (internal) ====` example with
`===[aims: nodes updated]===` and drop the closing-marker mention.

### docs/adr/0021-aims-internal-reply-prefix.md — Status pointer

Append a short paragraph noting the marker was shortened on 2026-06-02
from the four-`=` wrapper to the single-line `===[aims: <msg>]===`
form. Body stays append-only (ADR voice).

## Open design questions

None — single textual format change.

## Verification

- `grep -r '==== AIMS (internal) ====' templates/ .claude/ README.md docs/`
  returns no live references (only historical mentions in ADR-0021
  paragraph and old plan files, which are OK).
- `bash -n templates/hooks/*.sh && bash -n .claude/hooks/*.sh` → OK.
- `bash .claude/memory/lint.sh` → clean.

## Close-out checklist

- ADR: NONE — minor format tweak within ADR-0021 scope; ADR-0021 gets
  a short trailing paragraph instead of a superseding ADR.
- Nodes: UPDATE — memory/phase-b-consolidation (the Stop hook node),
  hooks/session-start (the conventions block).
- CLAUDE.md: NONE — convention details live in README + ADR.
- Tests: EXISTING — no behavior change, only string content.
- TODO: NONE

## Outcome

Marker shortened from the two-line `==== AIMS (internal) ====` /
`==== /AIMS ====` wrapper to a single line `===[aims: <msg>]===`.
ADR-0021 amended in place with a 2026-06-02 amendment paragraph (no
new ADR — Decision/scope unchanged, only literal form). Hooks
`session-start.sh` + `stop-consolidate.sh` carry the new convention;
`.claude/` mirrors refreshed. ADR-0021 index row updated.

## Closing checks

- Plan: docs/plans/2026-06-02-aims-prefix-shorten.md → completed
- Verification:
  - `grep '==== AIMS (internal) ====' templates/ .claude/ README.md`
    → no live hits (only ADR-0021's historical/amendment paragraph).
  - `bash -n templates/hooks/*.sh && bash -n .claude/hooks/*.sh` → OK.
  - `bash .claude/memory/lint.sh` → clean (15 nodes).
  - `bash .claude/memory/find-dirty.sh` → empty.
- ADR:      NONE — amendment to ADR-0021 instead (scope unchanged).
- Nodes:    UPDATE — hooks/session-start, memory/phase-b-consolidation
            (both consolidated + marked clean).
- CLAUDE.md: NONE
- Tests:    EXISTING — no behavior change, only injection-string content.
- TODO:     NONE
