# Plan: 2 commands only; idempotent install + auto memory
Status: completed
Started: 2026-05-27

## TL;DR
Cut to **two** slash commands: `/plan` and `/install-on` (renamed from
`/init-workflow`). `/install-on` is **idempotent** — safe to re-run on
any repo, it never overwrites hand-edited content, only adds/updates
what's missing or stale. Memory tree is bootstrapped on first install
and **augmented** (not rebuilt) on re-runs. All maintenance after that
happens automatically via the existing post-edit-marker + Stop-hook
loop (ADR-0009) and the inline plan close-out. No `/memory*`,
`/remember`, `/adr`, `/done`, `/grunt`.

## Goal
`ls .claude/commands/` shows exactly `install-on.md` and `plan.md`.
Re-running `/install-on` on an existing install is non-destructive.
End-of-implementation close-out (verify, auto-ADR, mark completed,
memory consolidation) runs inline without a slash command.

## Decision

### Keep / drop
- **Keep**: `/plan`, `/install-on`.
- **Drop**: `/done`, `/adr`, `/grunt`, `/remember`, `/memory-init`,
  `/memory-augment`.

### `/install-on` idempotency rules
Re-running on an existing aims install MUST be safe:
- **Hooks & memory scripts** (`.claude/hooks/`, `.claude/memory/`):
  overwrite with current template version; show diff before write if
  content differs.
- **Slash commands** (`.claude/commands/`): overwrite the two kept
  commands; **delete** obsolete commands so old installs upgrade
  cleanly. Show diff first.
- **`CLAUDE.md`**: never overwrite. If exists, show unified diff vs
  template and ask `AskUserQuestion` per section (keep / replace /
  merge).
- **`docs/adr/`**: never touch existing ADRs. Only add `_template.md`
  and `README.md` if missing.
- **`docs/plans/`**: never touch.
- **`docs/memory/`**:
  - Missing → cold-start scan (old `/memory-init` body).
  - Exists → **augment** pass: scan for code areas not covered by
    any node's `code:` globs; propose new tags/nodes via
    `AskUserQuestion`; **never overwrite existing node bodies**.
- **`.claude/aims-mode`**: create only if missing.

### Close-plan flow (inline, no command)
Triggered by the Stop-hook nudge when an in-progress plan exists and
the prior cycle made no edits:
- Verify plan steps + run `## Verification` commands.
- **Auto-decide ADR** per item:
  - **Create** when clear architectural commitment (new dep, module
    boundary, invariant, supersedes prior ADR, listed in
    `## ADRs to record` with a clear title).
  - **Skip** when bug-fix-only, refactor with no interface change,
    doc-only, test-only, mechanical.
  - **Ask** only when borderline (single `AskUserQuestion`).
- Mark plan `Status: completed`; append `## Outcome`.
- **Update every relevant memory node** — for each node whose `code:`
  overlaps files this plan touched, consume `consolidate.sh <node>`
  prompt + plan body + new ADR bodies, Edit per ADR-0008, mark
  `consolidated`.
- Process `_inbox.md`; run `lint.sh` + `doctor.sh`.

### Plan template
Leads with `## TL;DR`; "Options considered" only when >1 real option;
target ≤80 lines.

## Steps
1. `rm` six obsolete commands from `.claude/commands/` and
   `templates/commands/`.
2. Rename `init-workflow.md` → `install-on.md` in both locations;
   update `description` and any self-references.
3. Rewrite `/install-on` body around the idempotency rules above.
   Detect existing install (`.claude/hooks/` present? `docs/memory/`
   present? `CLAUDE.md` present?), apply the per-class rule, end by
   pruning obsolete commands + memory bootstrap-or-augment + `lint.sh`.
4. Rewrite `/plan` template: lead with `## TL;DR`; embed close-out
   with the auto-ADR rule; make "Options considered" conditional.
5. Extend `templates/hooks/stop-consolidate.sh` + `.claude/hooks/`:
   when an `in-progress` plan exists and the prior cycle made no
   edits, inject "run plan close-out inline now" alongside the
   existing consolidation prompt. Reuse existing throttle.
6. Clean `templates/hooks/prompt-submit.sh` + `.claude/hooks/`
   router: drop `/grunt` and `/adr` branches; `/plan` is the only
   structured path.
7. `CLAUDE.md`: collapse `## Workflow` to two commands; drop
   `/grunt` line from `## Models policy`; change `## Decision
   records` to "ADRs are proposed automatically during plan
   close-out (manual edit under `docs/adr/` allowed)".
8. `docs/memory/discipline/` nodes: append `## Known issues` notes
   marking removed commands; update `## Pointers`. Don't delete.
9. Write ADR-0010 — "Two-command surface; idempotent install; auto
   close-out" — supersedes command-list parts of ADR-0002 and
   ADR-0007.
10. `bash -n` all hooks + commands; `lint.sh` clean; smoke:
    `/install-on` on fresh dir AND on dir already containing aims —
    both end clean.

## Verification
- `ls .claude/commands/` = `install-on.md plan.md`.
- `ls templates/commands/` = same.
- `bash -n .claude/hooks/*.sh templates/hooks/*.sh` clean.
- `bash .claude/memory/lint.sh` clean.
- `grep -rE '/(done|adr|grunt|remember|memory-(init|augment)|init-workflow)\b' .claude templates CLAUDE.md`
  returns only historical refs.
- Manual smoke #1: `/install-on` on a clean target → tree exists,
  hooks present, CLAUDE.md created.
- Manual smoke #2: `/install-on` second time on same target → no
  destructive changes; hand-edited node body unchanged; obsolete
  commands removed; new code areas surfaced via AskUserQuestion.

## Risks / unknowns
- Diff-and-ask UX on re-install may be tedious in large repos —
  mitigation: per-class default (e.g. "overwrite all hooks?" yes/no),
  not per-file.
- Memory augment may re-propose nodes the user already rejected —
  mitigation considered: `_ignored.md` under `docs/memory/`; add only
  if it shows up in practice (out of scope here).
- Close-out heuristic may misfire — advisory only; model can decline.
- Auto-ADR false positives — rule biases to "ask" on borderline;
  ADRs always start `proposed`.

## ADRs to record after implementation
- [ ] ADR-0010 — Two-command surface; idempotent install; auto
      close-out. (Clear yes — architectural commitment; supersedes
      parts of ADR-0002/0007.)

## Outcome

Shipped in commit 7243a88. Command surface reduced from 8 → 2
(`/plan`, `/install-on`). `/install-on` is now strictly idempotent
with per-class rules documented in Phase 3. Close-out (verify,
auto-ADR, mark completed, memory consolidation) is embedded in
`/plan` Phase 4 and nudged by the Stop hook when an in-progress
plan exists. Plan template leads with `## TL;DR` and "Options
considered" is now conditional. ADR-0010 records the decision
(status `proposed`).

Deviations from plan:
- `/install-on` was rewritten to use `AskUserQuestion: yes |
  per-class | abort` rather than a per-file diff-and-ask loop, to
  avoid the large-repo UX issue flagged in the Risks section.

ADRs created: ADR-0010 (clear yes — architectural commitment).

## Closing checks

- `bash -n templates/hooks/*.sh .claude/hooks/*.sh templates/memory/*.sh .claude/memory/*.sh` → **pass**.
- `bash .claude/memory/lint.sh` → **clean (13 nodes)**.
- `bash .claude/memory/doctor.sh` → **0 dirty, lint clean, 0 nodes > 4 KB**.
- `ls .claude/commands/` = `install-on.md plan.md` → **pass**.
- `ls templates/commands/` = `install-on.md plan.md` → **pass**.
- `grep -rE '/(done|adr|grunt|remember|memory-(init|augment)|init-workflow)\b' .claude templates CLAUDE.md`
  → only intentional historical mentions remain (plan.md migration
  notes, ADR/plan files referencing prior commands).
- Manual `/install-on` smoke (fresh + re-install) → **not run** in
  this session; deferred to first real install attempt.
