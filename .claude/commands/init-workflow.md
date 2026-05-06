---
description: Bootstrap ais workflow in the current project (idempotent, merge-aware)
argument-hint: "[--mode=nudge|block|off] [--self-contained]  (hooks: default nudge; self-contained: also copy commands to .claude/commands/)"
---

# /init-workflow

You are bootstrapping the **ais** workflow in the current project. Goal: create the
minimum scaffolding for `/plan`, `/adr`, `/grunt`, `/done` to work, without
disturbing existing files. **Detect before create. Merge before overwrite. Ask before write.**

## Phase 1 — Sniff (read-only)

Read these if present, do not modify:

- Build/test/lint config:
  `package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, `pom.xml`,
  `Makefile`, `justfile`, `.eslintrc*`, `ruff.toml`, `.pre-commit-config.yaml`
- Layout signals: `src/`, `lib/`, `tests/`, `__tests__/`, `spec/`, `docs/`
- Existing docs: `README.md`, `ARCHITECTURE.md`, `docs/adr/`, `CLAUDE.md`
- Existing Claude config: `.claude/settings.json`, `.claude/hooks/`
- Recent activity: `git log --oneline -20`

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
6. **Self-contained mode** — ask:
   *"Copy ais commands into this project's `.claude/commands/` so they work
   even without the plugin installed globally? Useful for solo projects or
   when sharing the repo with collaborators who don't have ais installed."*
   Default: **no** (rely on global plugin install). If `--self-contained`
   was passed in $ARGUMENTS, skip the question.

7. **Snapshot** — offer a one-time codebase summary at `.claude-context.md`
   (gitignored). Default: skip; user can run `/snapshot` later.

Skip any question whose answer is unambiguous from sniffing.

## Phase 3 — Show plan, do not write yet

Present a **diff preview**: list every file you'd CREATE and every section you'd
MERGE into existing files. State explicitly what you will NOT touch
(`src/`, `tests/`, `README.md`, package manifests, etc.).

Then ask: `Approve?  [yes / show-full-diff / abort]`

## Phase 4 — Apply (only after approval)

Create only what's missing. For each file, use the templates under the plugin's
`templates/` directory as the starting content, then substitute `{{VARS}}`:

| Path created                                    | From template                          |
|-------------------------------------------------|----------------------------------------|
| `docs/adr/README.md`                            | `templates/adr-readme.md.tmpl`         |
| `docs/adr/_template.md`                         | `templates/adr-template.md.tmpl`       |
| `docs/adr/0001-record-architecture-decisions.md`| `templates/adr-0001.md.tmpl`           |
| `.claude/hooks/session-start.sh` (if hooks ≠ off)  | `templates/hooks/session-start.sh`     |
| `.claude/hooks/prompt-submit.sh` (if hooks ≠ off)  | `templates/hooks/prompt-submit.sh`     |
| `.claude/hooks/pre-write.sh` (if hooks ≠ off)      | `templates/hooks/pre-write.sh`         |
| `.claude/settings.json` (merge if exists)       | `templates/settings.json.tmpl`         |
| `.claude/commands/{adr,done,grunt,plan}.md` (if self-contained)  | the plugin's own `commands/*.md`, **except** `init-workflow.md` (no point re-installing the installer) |

Make hook scripts executable (`chmod +x`).

### CLAUDE.md merge rules (section-aware)

- If no `CLAUDE.md`: create from `templates/CLAUDE.md.tmpl`.
- If exists: read, locate sections by `## ` headings.
  - **Append missing** sections from the template, marked
    `<!-- added by ais -->` … `<!-- /ais -->`.
  - **Never overwrite** an existing same-named section. If a conflict exists,
    print the proposed section to stdout and ask the user to resolve manually.

### .claude/settings.json merge rules

- If no file: write from template.
- If exists: deep-merge `hooks` keys only. Do not touch other keys.
  Conflicting hook commands → leave existing, print suggestion.

### .gitignore

Append (only if missing):
```
.claude-context.md
.claude/.planning-lock
```

Never add anything else.

## Phase 5 — Doctor

Print a short report:

```
ais ready in <path>:
  hooks: nudge | block | off
  ADR root: docs/adr/  (3 files)
  CLAUDE.md: created | merged (+N sections) | unchanged
  commands: from plugin (global) | self-contained (copied to .claude/commands/)
  next: try `/plan <task>` for non-trivial work
```

## Variables to substitute in templates

When writing template contents, replace:

- `{{TEST_CMD}}` — the confirmed test command
- `{{LINT_CMD}}` — the confirmed lint/format command (or omit section)
- `{{TYPECHECK_CMD}}` — the confirmed typecheck command (or omit)
- `{{ADR_DIR}}` — usually `docs/adr`
- `{{HOOK_MODE}}` — `nudge` | `block` | `off`
- `{{DATE}}` — `YYYY-MM-DD`

## Hard rules

- Idempotent: re-running this command on an already-initialized project must be
  a no-op (or merge-only) — never duplicate sections, never re-create existing files.
- Read-only on `src/`, `tests/`, `lib/`, package manifests, README, LICENSE.
- `$ARGUMENTS` may carry `--mode=…` and/or `--self-contained`. If a flag is
  present, skip the corresponding question.
- If user aborts at Phase 3, write nothing. Print `Aborted. No changes made.`

## Discovering the plugin's own templates/

The plugin files (templates, hook sources) live in the directory where the
ais plugin was installed — typically `~/.claude/plugins/ais/templates/` or
similar. To locate them:

1. Try `${CLAUDE_PLUGIN_ROOT}/templates/` if the env var is set.
2. Else, scan `~/.claude/plugins/*/templates/hooks/session-start.sh` for a
   directory containing the expected templates layout.
3. Else, ask the user: `Could not auto-locate ais templates. Path?`

Once located, all CREATE/MERGE operations source from that directory.
