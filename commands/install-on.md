---
description: Install (or re-install) the aims workflow into a target project. Idempotent.
argument-hint: "<target-project-path> [--mode=nudge|block|off]"
model: opus
---

# /install-on

You are installing (or re-installing) the **aims** workflow into a
target project. The command is **idempotent**: re-running it on an
existing aims install must never destroy hand-edited content; it
only adds what's missing and refreshes deterministic infrastructure
(hooks, scripts, the two slash commands) after showing a diff.

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

| Class                        | Rule                                                                 |
|------------------------------|----------------------------------------------------------------------|
| Hooks & memory scripts       | Overwrite from template; show unified diff first if content differs. |
| Slash commands (the two)     | Overwrite `install-on.md`, `plan.md`. Delete obsolete commands.      |
| Obsolete-command cleanup     | Delete `TARGET/.claude/commands/{done,adr,grunt,remember,memory-init,memory-augment}.md` if present. |
| `CLAUDE.md`                  | Never overwrite. Diff per section vs template; ask per section.      |
| `docs/adr/_template.md`, `docs/adr/README.md` | Create only if missing.                              |
| Existing ADRs                | Never touch.                                                         |
| `docs/plans/`                | Never touch.                                                         |
| `docs/memory/` (tree body)   | Never overwrite existing nodes. Augment-only (see Phase 5).          |
| `.claude/aims-mode`          | Create only if missing.                                              |
| `.claude/settings.json`      | Merge `hooks` keys only; never touch other keys.                     |
| `.gitignore`                 | Append `.claude-context.md` and `.claude/.planning-lock` if missing. |

If user picks `per-class`, walk each class via `AskUserQuestion`.

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

### CLAUDE.md merge rules

- Missing → create from template.
- Exists → locate sections by `## ` headings.
  - Append missing sections from template, wrapped
    `<!-- added by aims -->` … `<!-- /aims -->`.
  - Never overwrite an existing same-named section. Print diff and
    ask `AskUserQuestion: keep | replace | merge`.

### settings.json merge rules

- Missing → write from template.
- Exists → deep-merge `hooks` keys only. Conflicting hook command →
  keep existing, print suggestion.

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

```
aims installed into <TARGET> (<fresh|re-install>):
  hooks: nudge | block | off
  commands: install-on, plan  (obsolete removed: <list or none>)
  ADR root: docs/adr/ (<N> files)
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

- **Idempotent.** Re-runs never destroy hand-edited content.
  Specifically: never overwrite `CLAUDE.md` sections, ADRs, plan
  files, memory node bodies, or user-edited settings keys.
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
