# ADR-0011: Re-install refreshes aims scaffolding and prunes stale system files
Status: proposed
Date: 2026-05-28
Supersedes: parts of ADR-0010 (the per-class idempotency rules)
Superseded by: —

## Context

ADR-0010 made `/install-on` idempotent with per-class rules: hooks, memory
scripts, and the two commands are overwritten; `CLAUDE.md` sections, ADRs,
plan files, and memory node bodies are never touched. Two gaps surfaced in a
real re-install (see `docs/plans/2026-05-28-install-on-clean-refresh.md`):

1. **aims ships scaffolding docs that the old rules froze forever.** The ADR
   bootstrap (`0001-record-architecture-decisions.md`), the ADR `_template.md`,
   and the prose of `docs/adr/README.md` are authored by aims, not the user.
   The "never touch any ADR" rule meant a re-install left them stale — still
   referencing the retired `/adr` command long after ADR-0010 removed it.
2. **Stale system files were never deleted.** A renamed-away script (e.g.
   `new-leaf.sh` → `new-node.sh`, ADR-0008) or a leftover obsolete command, or
   a stale aims hook entry in `settings.json`, would survive a re-install. So
   "re-install brings the system up to date" was not actually guaranteed.

The `docs/adr/README.md` complication: its `## Index` table accumulates one
row per user ADR, so it cannot be overwritten wholesale without destroying the
user's decision log.

## Decision

We refine the idempotency seam: **the system layer is fully replaced and
stale aims files are deleted; user-authored documentation stays sacred;
aims-shipped scaffolding docs are refreshed because they are part of the
system, not the user's writing.**

- **Refresh (overwrite from template):** hooks, memory scripts, the two
  commands, aims-owned `settings.json` hook entries, `docs/adr/_template.md`,
  `docs/adr/0001-record-architecture-decisions.md` (preserving a user-changed
  `Status:` / `Superseded by:` pointer), and the prose of `docs/adr/README.md`
  **above** its `## Index` heading.
- **Delete (stale):** any `*.sh` in `.claude/{hooks,memory}/` not in the
  current shipped set; any command other than `install-on`/`plan`. Scoped to
  `*.sh` and the known command files so runtime state is safe. Deletions are
  listed in the Phase 3 approval gate.
- **Never touch:** user-authored ADRs (`NNNN-*.md`, `NNNN != 0001`), the ADR
  README `## Index` rows, `CLAUDE.md` sections, plan files, memory node
  bodies, and non-`hooks` settings keys.

Detection gains a `PRIOR_AIMS` flag so a target with only stale scaffolding is
reported as a `re-install`, never `fresh`.

## Consequences

- ✅ A re-install over an old aims version yields a fully current system and
  current shipped docs — no stale `/adr` references, no orphaned scripts.
- ✅ The user's ADR log, decisions, plans, and memory writing remain
  untouched; the README index is preserved row-for-row.
- ⚠️ The README refresh is index-aware: a buggy implementation could drop
  index rows. Mitigated by an explicit hard rule (keep `## Index` to EOF
  verbatim) and the Phase 3 deletion/preview gate.
- ⚠️ Stale-file deletion assumes `.claude/{hooks,memory}/` are aims-owned; a
  user custom `*.sh` placed there would be removed. Accepted — those dirs are
  aims-managed by design.
- 🔒 Rules out the old "create-only-if-missing / never-touch-all-ADRs"
  behavior for aims-shipped scaffolding.

## Alternatives considered

- **Leave all of `docs/adr/` untouched (status quo).** Rejected: freezes
  aims' own shipped docs at install-time forever; the transcript showed this
  is actively misleading.
- **Overwrite `docs/adr/README.md` wholesale from template.** Rejected:
  destroys the user's `## Index` rows.
- **Delete and re-copy the whole `.claude/{hooks,memory}/` dirs.** Rejected:
  risks nuking runtime state files; scoping to `*.sh` is safer and sufficient.

## Verification

- `commands/install-on.md` Phase 3 lists an "aims-shipped ADR scaffolding"
  refresh row and a "Stale system files" delete row; the ADR rows no longer
  say "create only if missing".
- `grep -n "preserve every row of the \`## Index\`" commands/install-on.md`
  matches.
- All three command copies are byte-identical
  (`md5sum commands/install-on.md templates/commands/install-on.md .claude/commands/install-on.md`).
- ADR-0010's `Superseded by:` pointer names ADR-0011 for the idempotency rules.
