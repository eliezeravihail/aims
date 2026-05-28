---
description: Install (or re-install) the aims workflow into a target project. Idempotent.
argument-hint: "<target-project-path> [--mode=nudge|block|off]"
model: opus
---

# /install-on

You are installing (or re-installing) the **aims** workflow into a
target project. The command is **idempotent and self-refreshing**:
re-running it on an existing aims install brings the whole system layer
up to date (hooks, memory scripts, the two slash commands, aims-owned
settings hook entries, and the aims-shipped ADR scaffolding) and deletes
stale aims files, after showing a diff — while never destroying
hand-edited content (authored ADRs, the ADR index, CLAUDE.md sections,
plans, memory node bodies, user settings keys).

## Roots

- `AIMS_ROOT` — current working directory (the aims source repo).
  Read-only **except** when `TARGET == AIMS_ROOT` (self-install /
  dogfooding refresh): then `.claude/` and `docs/memory/` under
  `AIMS_ROOT` may be written per the normal idempotency rules.
- `TARGET` — resolved absolute path from `$ARGUMENTS`. The place
  you may write.

If `$ARGUMENTS` is missing or the path doesn't exist, ask for it
first. **`TARGET == AIMS_ROOT` is allowed** — it is the dogfooding
refresh path: it copies `templates/hooks/*` → `.claude/hooks/*`,
`templates/memory/*` → `.claude/memory/*`, `templates/commands/*`
→ `.claude/commands/*`, and runs the memory augment pass. ADRs,
plans, `CLAUDE.md`, and existing memory node bodies are still
never overwritten.

## Phase 1 — Detect install state

Set `EXISTING=1` if **any** of these are present in `TARGET`:

- `TARGET/.claude/aims-mode`
- `TARGET/.claude/hooks/session-start.sh`
- `TARGET/docs/memory/README.md`

Also set `PRIOR_AIMS=1` if any aims-shipped remnant exists even when the
markers above don't — e.g. `TARGET/docs/adr/0001-record-architecture-decisions.md`,
an obsolete command under `TARGET/.claude/commands/`, or a stale `*.sh` in
`TARGET/.claude/{hooks,memory}/`. A `PRIOR_AIMS` target is a **re-install**
(report it as such, never as "fresh"), even if `EXISTING=0`.

Sniff also (read-only):

- Build/test/lint config: `package.json`, `pyproject.toml`,
  `Cargo.toml`, `go.mod`, `Makefile`, `justfile`, etc.
- Layout signals: `src/`, `lib/`, `tests/`, `__tests__/`, `spec/`.
- Existing `CLAUDE.md`, `docs/adr/`, `.claude/settings.json`.
- Git activity (if a repo): `git -C "$TARGET" log --oneline -20`.

## Phase 2 — Interview (skip questions answered by sniffing)

Use `AskUserQuestion`, one question per gap, with sniffed defaults:

1. Test command.
2. Lint/format command.
3. Type check command (if applicable).
4. ADR location (default `docs/adr/`).
5. Hook aggressiveness — `nudge` (default) | `block` | `off`. Only
   ask on fresh install; on re-install, keep the value already in
   `TARGET/.claude/aims-mode`.

**Memory tree is always installed.** Not optional.

## Phase 3 — Show planned changes per class

Group the planned actions by class. For each class state the rule
you'll apply and the affected paths. Then ask once:
`Approve all? [yes | per-class | abort]`.

The guiding seam: **the system layer is fully replaced and stale aims files
are deleted; user-authored documentation is never touched. aims-shipped
scaffolding docs are refreshed too — they are part of the system.**

| Class                        | Rule                                                                 |
|------------------------------|----------------------------------------------------------------------|
| Hooks & memory scripts       | Overwrite from template; show unified diff first if content differs. |
| Stale system files           | Delete any `*.sh` in `TARGET/.claude/{hooks,memory}/` not in the current shipped set (Phase 4). Scope to `*.sh` so runtime state files survive. |
| Slash commands (the two)     | Overwrite `install-on.md`, `plan.md`.                               |
| Obsolete-command cleanup     | Delete every `TARGET/.claude/commands/*.md` other than `install-on.md` and `plan.md` (subsumes `done,adr,grunt,remember,memory-init,memory-augment`). |
| aims-shipped ADR scaffolding | Refresh from template: overwrite `docs/adr/0001-record-architecture-decisions.md` and `docs/adr/_template.md`. On `0001`, preserve a user-changed `Status:` / `Superseded by:` pointer. |
| `docs/adr/README.md`         | Refresh aims prose **above** `## Index`; **preserve every row of the `## Index` table verbatim**. Create whole from template only if missing. |
| User-authored ADRs           | `docs/adr/NNNN-*.md` other than `0001` → never touch.               |
| `CLAUDE.md`                  | Never overwrite. Diff per section vs template; ask per section.      |
| `docs/plans/`                | Never touch.                                                         |
| `docs/memory/` (tree body)   | Never overwrite existing nodes. Augment-only (see Phase 5).          |
| `.claude/aims-mode`          | Create only if missing.                                              |
| `.claude/settings.json`      | Replace aims-owned hook entries with the current template; preserve all non-`hooks` keys and any user-added (non-aims) hook entries. |
| `.gitignore`                 | Append `.claude-context.md` and `.claude/.planning-lock` if missing. |

If user picks `per-class`, walk each class via `AskUserQuestion`. List every
file slated for **deletion** explicitly in this gate before applying.

## Phase 4 — Apply (only after approval)

Copy from `AIMS_ROOT` into `TARGET`, substituting `{{VARS}}`.

| Path in TARGET                                                                                 | Source under AIMS_ROOT                          |
|------------------------------------------------------------------------------------------------|-------------------------------------------------|
| `.claude/hooks/{session-start,prompt-submit,pre-write,post-edit-marker,stop-consolidate,session-end}.sh` | `templates/hooks/<same>`                 |
| `.claude/memory/{_lib,mark,new-node,find-dirty,lint,check-refs,consolidate,classify-inbox,doctor}.sh`     | `templates/memory/<same>`                |
| `.claude/commands/{install-on,plan}.md`                                                        | `templates/commands/<same>`                     |
| `.claude/settings.json` (merge if exists)                                                      | `templates/settings.json.tmpl`                  |
| `.claude/aims-mode`                                                                            | one line: chosen mode                           |
| `docs/adr/README.md`, `docs/adr/_template.md`, `docs/adr/0001-record-architecture-decisions.md`| `templates/adr-*.tmpl`                          |
| `CLAUDE.md`                                                                                    | `templates/CLAUDE.md.tmpl` (merge-only)         |

After copy: `chmod +x TARGET/.claude/hooks/*.sh TARGET/.claude/memory/*.sh`.

### Clean stale system files (after copy)

The current shipped set is the source of truth. Delete from `TARGET`:

- Any `*.sh` in `TARGET/.claude/hooks/` whose name is not in
  `templates/hooks/` (e.g. a renamed-away hook).
- Any `*.sh` in `TARGET/.claude/memory/` whose name is not in
  `templates/memory/` (e.g. a stale `new-leaf.sh`).
- Any `TARGET/.claude/commands/*.md` other than `install-on.md`, `plan.md`.

Only `*.sh` and the known command files are removed — never other files in
those directories (runtime state, user notes).

### ADR scaffolding refresh rules

- `docs/adr/0001-record-architecture-decisions.md`, `docs/adr/_template.md` →
  overwrite from template. **Exception:** on `0001`, if the existing file's
  `Status:` or `Superseded by:` line was changed by the user (it was
  superseded), keep those two lines and refresh only the body.
- `docs/adr/README.md` → if missing, create whole from template. If present,
  rewrite everything **above** the `## Index` heading from the template, and
  splice the existing `## Index` heading + all its rows back verbatim. Never
  drop or reorder index rows — they are the user's ADR log.
- `docs/adr/NNNN-*.md` for `NNNN != 0001` → never read for overwrite; never
  touched.

### CLAUDE.md merge rules

- Missing → create from template.
- Exists → locate sections by `## ` headings.
  - Append missing sections from template, wrapped
    `<!-- added by aims -->` … `<!-- /aims -->`.
  - Never overwrite an existing same-named section. Print diff and
    ask `AskUserQuestion: keep | replace | merge`.

### settings.json merge rules

- Missing → write from template.
- Exists → preserve every non-`hooks` key verbatim (`permissions`,
  `deniedMcpServers`, env, etc.). For `hooks`: **replace the aims-owned
  entries** (the six handlers in `templates/settings.json.tmpl`, identified
  by their `bash .claude/hooks/<name>.sh` command) with the current template
  definitions, so a stale aims hook can't survive a re-install. Keep any
  user-added hook entry that isn't one of aims' own.

## Phase 5 — Memory bootstrap or augment (inline, always)

Decide based on `TARGET/docs/memory/`:

### A) Tree missing → cold-start scan

Do this work yourself, in-band (no API key, per ADR-0009):

1. Read 30–80 of the most "central" code files in `TARGET`
   (entry points, big modules, anything cited from many places).
   Bias toward files in `src/`, `lib/`, top-level scripts.
2. Group into **tags** (top-level domains, e.g. `auth`, `cli`,
   `network`). 3–8 tags is normal.
3. Within each tag, identify the prominent modules → one **node**
   per module. Aim for ≤ ~12 nodes total on first pass; the tree
   grows via the consolidation loop.
4. Run `bash TARGET/.claude/memory/new-node.sh <tag>/<slug> <kind>`
   for each node. Then write a `docs/memory/<tag>/README.md` listing
   them.
5. Write `docs/memory/README.md` (root) listing tags.
6. Run `bash TARGET/.claude/memory/lint.sh`. Fix any issue
   interactively.
7. Leave node bodies empty (six ADR-0008 sections, no content).
   They fill via the consolidation loop as users work.

### B) Tree exists → augment

1. Collect all `code:` globs from existing nodes.
2. Identify code areas in `TARGET` not matched by any node
   (`src/`, `lib/`, top-level directories with > N files of source).
3. Propose new tags/nodes via `AskUserQuestion` — one batch, list
   form. Default to "create" for clear matches, "skip" otherwise.
4. For each approved proposal: `new-node.sh`. Then add to the
   appropriate tag `README.md`.
5. **Never overwrite existing node bodies.** Augmentation is
   additive only.
6. Run `lint.sh`; surface issues; do not auto-fix human content.

Memory phase is **non-fatal** — if it errors, install still
succeeds. Print the error and continue to Phase 6.

## Phase 6 — Doctor report

Report `re-install` whenever `EXISTING` **or** `PRIOR_AIMS` is set; only a
truly clean target is `fresh`.

```
aims installed into <TARGET> (<fresh|re-install>):
  hooks: nudge | block | off
  commands: install-on, plan  (obsolete removed: <list or none>)
  stale system files removed: <list or none>
  ADR root: docs/adr/ (<N> files)
    scaffolding: refreshed (0001, _template, README prose) | created | unchanged
    authored ADRs: <M> untouched
  CLAUDE.md: created | merged (+<N> sections) | unchanged
  memory tree: <fresh: T tags, N nodes> | <augmented: +M nodes> | <untouched>
  lint: clean | <K issues>
  next: cd <TARGET> && claude
        try `/plan <task>` for non-trivial work
```

## Variables substituted in templates

- `{{PROJECT_NAME}}` — basename of `TARGET`
- `{{TEST_CMD}}`, `{{LINT_CMD}}`, `{{TYPECHECK_CMD}}` — confirmed commands
- `{{ADR_DIR}}` — usually `docs/adr`
- `{{HOOK_MODE}}` — `nudge` | `block` | `off`
- `{{DATE}}` — today's date `YYYY-MM-DD`

## Hard rules

- **Idempotent + self-refreshing.** Re-runs leave the **system** fully
  current and remove stale aims files, but never destroy hand-edited
  content. The seam:
  - Refresh (overwrite from template): hooks, memory scripts, the two
    commands, aims-owned `settings.json` hook entries, and the
    aims-shipped ADR scaffolding (`0001-record-architecture-decisions.md`,
    `_template.md`, and the README prose above `## Index`).
  - Delete (stale): `*.sh` in `.claude/{hooks,memory}/` not in the shipped
    set; commands other than `install-on`/`plan`.
  - Never touch: user-authored ADRs (`NNNN-*.md`, `NNNN != 0001`), the ADR
    README `## Index` rows, `CLAUDE.md` sections, plan files, memory node
    bodies, and non-`hooks` settings keys.
- Read-only on `TARGET/src/`, `TARGET/tests/`, `TARGET/lib/`,
  package manifests, `TARGET/README.md`, `TARGET/LICENSE`.
- Read-only on `AIMS_ROOT` entirely.
- `$ARGUMENTS` may carry `--mode=…` after the path. If present,
  skip the hook-mode question.
- If user aborts at Phase 3, write nothing. Print
  `Aborted. No changes made.`
- `TARGET == AIMS_ROOT` (self-install) is allowed and intended for
  dogfooding refresh. The idempotency rules still hold — nothing
  hand-edited is destroyed.
- The only two commands installed into the target are `install-on`
  and `plan`. Everything else (close-plan, ADR creation, memory
  consolidation, mechanical edits) happens inline or via hooks.
