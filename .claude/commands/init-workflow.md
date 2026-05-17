---
description: Bootstrap aims workflow into a target project (clone-and-bootstrap install model)
argument-hint: "<target-project-path> [--mode=nudge|block|off]"
---

# /init-workflow

You are bootstrapping the **aims** workflow **into a target project**.

## How this command is used

The user is running you from inside the **aims source repository** (the
checkout they downloaded or cloned). They pass the **target project's path**
as the argument:

```
/init-workflow /home/me/projects/my-app
```

You install aims into `/home/me/projects/my-app`. After you're done, that
target project becomes self-sufficient: opening Claude Code there picks up
aims's hooks, commands, and CLAUDE.md automatically. Nothing is installed
globally; the aims source repo can be discarded or kept for future re-installs.

`$ARGUMENTS` carries the target path (and optional `--mode=…`). If the path is
missing or doesn't exist, ask the user for it before doing anything else.

Define two roots:

- `AIMS_ROOT` = the current working directory (the aims source repo). This is
  where `templates/` and `commands/` live and where you read **from**.
- `TARGET` = the resolved absolute path from `$ARGUMENTS`. This is where you
  write **to**.

You must never write outside `TARGET` (except for chmod on files you just
created there). You must never read mutate-style under `AIMS_ROOT`.

## Phase 1 — Sniff (read-only, on TARGET)

Read these inside `TARGET` if present, do not modify:

- Build/test/lint config:
  `package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, `pom.xml`,
  `Makefile`, `justfile`, `.eslintrc*`, `ruff.toml`, `.pre-commit-config.yaml`
- Layout signals: `src/`, `lib/`, `tests/`, `__tests__/`, `spec/`, `docs/`
- Existing docs: `README.md`, `ARCHITECTURE.md`, `docs/adr/`, `CLAUDE.md`
- Existing Claude config: `.claude/settings.json`, `.claude/hooks/`,
  `.claude/commands/`
- Recent activity: `git -C "$TARGET" log --oneline -20` (if it's a git repo)

Note explicitly what you found. Do **not** invent commands that aren't in the
files. If a tool is missing, mark it `unknown` and ask.

## Phase 2 — Interview (only fill gaps)

Use AskUserQuestion to confirm/fill (one question per gap, defaults pre-filled):

1. **Test command** — propose what you sniffed (e.g. `pytest -q`); ask to confirm.
2. **Lint/format command** — same.
3. **Type check command** (if applicable) — same.
4. **ADR location** — default `docs/adr/`. Confirm or override.
5. **Hook aggressiveness** — `nudge` (default) | `block` | `off`.
   - `nudge`: hooks print reminders, never block tools.
   - `block`: `pre-write` blocks Edit/Write while a planning lock exists or
     when changing `src/` paths without an in-progress plan.
   - `off`: hooks not installed.
6. **Snapshot** — offer a one-time codebase summary at `TARGET/.claude-context.md`
   (gitignored). Default: skip; user can run `/snapshot` later.

Skip any question whose answer is unambiguous from sniffing.

## Phase 3 — Show plan, do not write yet

Present a **diff preview**: list every file you'd CREATE under `TARGET/` and
every section you'd MERGE into existing files. State explicitly what you will
NOT touch (`TARGET/src/`, `TARGET/tests/`, `TARGET/README.md`, package
manifests, etc.).

Then ask: `Approve?  [yes / show-full-diff / abort]`

## Phase 4 — Apply (only after approval)

Copy from `AIMS_ROOT` into `TARGET`. Substitute `{{VARS}}` while writing.

| Created path                                              | Read from                          |
|-----------------------------------------------------------|------------------------------------||
| `TARGET/docs/adr/README.md`                               | `AIMS_ROOT/templates/adr-readme.md.tmpl`   |
| `TARGET/docs/adr/_template.md`                            | `AIMS_ROOT/templates/adr-template.md.tmpl` |
| `TARGET/docs/adr/0001-record-architecture-decisions.md`   | `AIMS_ROOT/templates/adr-0001.md.tmpl`     |
| `TARGET/.claude/hooks/session-start.sh` (if hooks ≠ off)  | `AIMS_ROOT/templates/hooks/session-start.sh`  |
| `TARGET/.claude/hooks/prompt-submit.sh` (if hooks ≠ off)  | `AIMS_ROOT/templates/hooks/prompt-submit.sh`  |
| `TARGET/.claude/hooks/pre-write.sh` (if hooks ≠ off)      | `AIMS_ROOT/templates/hooks/pre-write.sh`      |
| `TARGET/.claude/settings.json` (merge if exists)          | `AIMS_ROOT/templates/settings.json.tmpl`      |
| `TARGET/.claude/aims-mode`                                 | one line: the chosen hook mode               |
| `TARGET/.claude/commands/{adr,done,grunt,plan}.md`        | `AIMS_ROOT/templates/commands/{adr,done,grunt,plan}.md` |

Notes:

- **`init-workflow.md` is NOT copied** to the target. It's the installer,
  not part of the discipline. The target's only access to `/init-workflow`
  is through the global plugin install (if the user has it) or by running
  `claude` from the aims source repo when they need to re-bootstrap.
- The 4 discipline commands live under `AIMS_ROOT/templates/commands/`,
  not `AIMS_ROOT/commands/`. This keeps them out of the global plugin
  surface — `commands/init-workflow.md` is the only globally-visible file.
- Hook scripts must be executable: `chmod +x TARGET/.claude/hooks/*.sh`.

### CLAUDE.md merge rules (section-aware, on TARGET)

- If `TARGET/CLAUDE.md` does not exist: create from `templates/CLAUDE.md.tmpl`.
- If exists: read, locate sections by `## ` headings.
  - **Append missing** sections from the template, marked
    `<!-- added by aims -->` … `<!-- /aims -->`.
  - **Never overwrite** an existing same-named section. If a conflict exists,
    print the proposed section to stdout and ask the user to resolve manually.

### TARGET/.claude/settings.json merge rules

- If no file: write from template.
- If exists: deep-merge `hooks` keys only. Do not touch other keys.
  Conflicting hook commands → leave existing, print suggestion.

### TARGET/.gitignore

Append (only if missing):
```
.claude-context.md
.claude/.planning-lock
```

Never add anything else.

## Phase 5 — Doctor

Print a short report:

```
aims installed into <TARGET>:
  hooks: nudge | block | off
  ADR root: docs/adr/  (3 files)
  CLAUDE.md: created | merged (+N sections) | unchanged
  commands: 4 copied to .claude/commands/  (no global pollution)
  next: cd <TARGET> && claude
        try `/plan <task>` for non-trivial work
```

## Variables to substitute in templates

When writing template contents, replace:

- `{{PROJECT_NAME}}` — basename of `TARGET`
- `{{TEST_CMD}}` — the confirmed test command
- `{{LINT_CMD}}` — the confirmed lint/format command (or omit section)
- `{{TYPECHECK_CMD}}` — the confirmed typecheck command (or omit)
- `{{ADR_DIR}}` — usually `docs/adr`
- `{{HOOK_MODE}}` — `nudge` | `block` | `off`
- `{{DATE}}` — today's date as `YYYY-MM-DD`

## Hard rules

- Idempotent: re-running this command on an already-initialized target must be
  a no-op (or merge-only) — never duplicate sections, never re-create existing
  files. Detect via presence of `TARGET/.claude/aims-mode`.
- Read-only on `TARGET/src/`, `TARGET/tests/`, `TARGET/lib/`, package
  manifests, `TARGET/README.md`, `TARGET/LICENSE`.
- Read-only on `AIMS_ROOT` entirely (you only read from it).
- `$ARGUMENTS` may carry `--mode=…` after the path. If present, skip the
  hook-mode question.
- If user aborts at Phase 3, write nothing. Print `Aborted. No changes made.`
- If `TARGET == AIMS_ROOT`, refuse: this is the source repo, not a target.
  Print: `Refusing to install aims into its own source repo. Pass a different path.`
