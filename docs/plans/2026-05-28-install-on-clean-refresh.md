# Plan: install-on clean refresh of system + scaffolding docs
Status: completed
Started: 2026-05-28
Completed: 2026-05-28

## TL;DR
Today `/install-on` refreshes the *system* layer (hooks, memory scripts, the
two commands) but treats **all** of `docs/adr/` as sacred — so stale
aims-shipped scaffolding (the `0001-record-architecture-decisions.md`
bootstrap, the ADR `README.md` prose, `_template.md`) lingers forever, still
referencing the retired `/adr` command (exactly what the install transcript
hit). It also never deletes *stale* system files (e.g. an old `new-leaf.sh`)
or stale `settings.json` hook entries, so "up to date" isn't guaranteed. This
plan edits the `/install-on` spec (all 3 identical copies) to: (a) **refresh
aims-shipped ADR scaffolding** while preserving the README's `## Index` rows
and never touching authored ADRs (0002+); (b) **delete stale system files**
(`*.sh` not in the current shipped set, commands other than the two); (c)
**refresh aims-owned hook entries** in `settings.json`; (d) make Phase 1 /
doctor honest about a prior-aims re-install. Pure spec/markdown change → one
ADR superseding the idempotency parts of ADR-0010.

## Goal
`/install-on` on a project carrying an old aims version leaves the entire
system + aims-shipped docs fully current, deletes obsolete aims files, and
still never touches user-authored ADRs, plans, memory node bodies, or
CLAUDE.md sections.

## Decision
- **The system is fully replaced, documentation is preserved — with a precise
  seam:**
  - **aims-shipped ADR scaffolding** = `0001-record-architecture-decisions.md`
    + `_template.md` → overwrite from template. On `0001`, preserve a
    user-changed `Status:` pointer (supersede edits are allowed per the
    append-only rule).
  - **`docs/adr/README.md`** → refresh the aims prose sections; **preserve
    every row of the `## Index` table** (user data).
  - **User-authored ADRs** (`0002+`, any `NNNN-*.md` that isn't the bootstrap)
    → never touch. Plans, memory node bodies, CLAUDE.md sections → never touch.
- **Clean the system layer:** delete any `*.sh` in `TARGET/.claude/{hooks,memory}/`
  not in the current shipped set; delete any `TARGET/.claude/commands/*.md`
  other than `install-on.md`/`plan.md` (subsumes the named obsolete list).
  Scope deletion to `*.sh` so runtime state files are safe.
- **settings.json:** replace aims-owned hook entries with the current template
  definitions; preserve non-aims keys and any user-added hooks (today's "keep
  existing on conflict" leaves stale aims hooks behind).
- **Honesty:** Phase 1 sets a `prior-aims` flag when scaffolding/obsolete
  files exist so the doctor report says "re-install (scaffolding refreshed)"
  instead of "fresh".

## Steps
1. Edit `commands/install-on.md` Phase 3 table: replace the two ADR rows +
   obsolete-cleanup row with the refined scaffolding/authored/stale-cleanup
   rules; add a "stale system files" row and a "settings.json hooks refresh"
   rule.
2. Edit Phase 4 (apply) + sub-rules: ADR-scaffolding refresh (README
   index-preservation, `_template`/`0001` overwrite w/ status preservation),
   stale-`*.sh` deletion, command pruning, settings.json aims-hook replacement.
3. Edit Phase 1 (add `prior-aims` detection) and Phase 6 doctor report
   (scaffolding-refreshed / stale-removed lines + fresh|re-install honesty).
4. Edit the Hard rules to state the new seam crisply.
5. Propagate identical edits to `templates/commands/install-on.md` and
   `.claude/commands/install-on.md`; verify all three byte-identical (md5sum).
6. Close-out: write the ADR (supersedes idempotency parts of ADR-0010), add
   its index row, run hook syntax check, consolidate `installer/` memory node.

## Verification
- `md5sum commands/install-on.md templates/commands/install-on.md .claude/commands/install-on.md`
  → three identical hashes.
- `grep -n "Refresh from template" commands/install-on.md` → scaffolding rule;
  `grep -ni "index" commands/install-on.md` → README index-preservation rule.
- `grep -ni "create only if missing" commands/install-on.md` → **no** match
  for the ADR scaffolding rows (old rule gone).
- `bash -n templates/hooks/*.sh && bash -n .claude/hooks/*.sh` → clean.
- New `docs/adr/00NN-*.md` exists, status `proposed`,
  `Supersedes: ADR-0010 (idempotency rules)`; index row added.

## Risks / unknowns
- **README index preservation is the sharp edge** — the refresh must rewrite
  prose but splice the existing `## Index` table back verbatim. Spec instructs:
  keep from `## Index` to EOF, replace everything above. Mis-implementation =
  lost ADR index. Stated as a hard rule.
- **Stale-`*.sh` deletion** assumes `.claude/{hooks,memory}/` are aims-owned.
  True by design; a user custom script there would be removed. Mitigation:
  scope to `*.sh`, list deletions in the Phase 3 approval gate.
- **`0001` status preservation**: if a user superseded the bootstrap ADR,
  overwrite must keep the `Status:`/`Superseded by:` lines. Edge case; called
  out in the spec.
- Spec (prompt) change — behavior depends on the model following it. No
  executable test covers runtime semantics; hook syntax check is the only
  mechanical gate.

## ADRs to record after implementation
- [x] ADR-0011: Re-install refreshes aims-shipped scaffolding and prunes stale
  system files; authored docs stay sacred (supersedes the
  "create-only-if-missing / never-touch-all-ADRs" idempotency rules in
  ADR-0010). → `docs/adr/0011-reinstall-refreshes-scaffolding.md`

## Outcome
Edited `/install-on` spec in all 3 byte-identical copies (`commands/`,
`templates/commands/`, `.claude/commands/`): Phase 1 gains a `PRIOR_AIMS`
re-install flag; Phase 3 table replaces the blanket "never touch ADRs /
create-only-if-missing" rows with a precise seam (refresh aims-shipped
scaffolding, preserve the README `## Index` rows, never touch authored ADRs)
plus a stale-`*.sh` cleanup row and a settings.json aims-hook-replacement
rule; Phase 4 adds clean-stale-files + ADR-scaffolding-refresh + index-aware
README sub-rules and the new settings.json merge; Phase 6 doctor report and
the Hard rules state the seam. Wrote ADR-0011 (supersedes the idempotency
parts of ADR-0010); updated ADR-0010's `Superseded by:` pointer and the ADR
index. Consolidated the `installer/init-workflow` memory node + tag README
(were stale: `/init-workflow`, "five phases").

## Closing checks
- `md5sum` of the 3 command copies → identical (`c8a2eb95…`).
- `bash -n templates/hooks/*.sh && bash -n .claude/hooks/*.sh` → hooks OK.
- `bash .claude/memory/lint.sh` → clean (14 nodes).
- `bash .claude/memory/doctor.sh` → lint clean, 0 dirty, 0 nodes > 4 KB.
- `grep "create only if missing"` on the spec → only the legitimate
  `.claude/aims-mode` row remains; ADR rows no longer use it.
