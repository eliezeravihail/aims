---
description: Install (or re-install) the aims workflow into a target project. Idempotent.
argument-hint: "<target-project-path> [--mode=nudge|block|off]"
model: opus
---

# /install-on

You are installing (or re-installing) the **aims** workflow into a
target project. aims is the active self-maintenance layer over a passive
**Capsa capsule** (`.capsa/`; decision 0031). The command is
**idempotent and self-refreshing**: re-running it on an existing aims
install brings the whole system layer up to date (hooks, memory scripts,
the two slash commands, aims-owned settings hook entries, and the
vendored Capsa validator) and deletes stale aims files, after showing a
diff — while never destroying hand-edited content (capsule records, the
charter, CLAUDE.md sections, insight bodies).

## Roots

- `AIMS_ROOT` — current working directory (the aims source repo).
  Read-only **except** when `TARGET == AIMS_ROOT` (self-install /
  dogfooding refresh): then `.claude/` and `.capsa/` under `AIMS_ROOT`
  may be written per the normal idempotency rules.
- `TARGET` — resolved absolute path from `$ARGUMENTS`. The place you
  may write.

If `$ARGUMENTS` is missing or the path doesn't exist, ask for it first.
**`TARGET == AIMS_ROOT` is allowed** — it is the dogfooding refresh
path: it copies `templates/hooks/*` → `.claude/hooks/*`,
`templates/memory/*` → `.claude/memory/*`, `templates/commands/*` →
`.claude/commands/*`, refreshes the vendored `validator/` + `schema/`,
and runs the insight augment pass. Capsule records, `charter.md`,
`CLAUDE.md`, and existing insight bodies are never overwritten.

## Phase 1 — Detect install state

Set `EXISTING=1` if **any** of these are present in `TARGET`:

- `TARGET/.claude/aims-mode`
- `TARGET/.claude/hooks/session-start.sh`
- `TARGET/.capsa/capsule.yaml`

Also set `PRIOR_AIMS=1` if any aims remnant exists even when the markers
above don't — e.g. an obsolete command under `TARGET/.claude/commands/`,
a stale `*.sh` in `TARGET/.claude/{hooks,memory}/`, or a **pre-Capsa**
aims layout (`TARGET/docs/memory/README.md`, `TARGET/docs/adr/`). A
`PRIOR_AIMS` target is a **re-install** (report it as such, never as
"fresh"), even if `EXISTING=0`. If a pre-Capsa `docs/{adr,plans,memory}`
layout is present, note that migrating those into `.capsa/` is a separate
data step (this command bootstraps the capsule and tooling; it does not
auto-migrate old records) — surface it in the Phase 6 report.

Sniff also (read-only):

- Build/test/lint config: `package.json`, `pyproject.toml`,
  `Cargo.toml`, `go.mod`, `Makefile`, `justfile`, etc.
- Layout signals: `src/`, `lib/`, `tests/`, `__tests__/`, `spec/`.
- Existing `CLAUDE.md`, `.capsa/`, `.claude/settings.json`.
- Git activity (if a repo): `git -C "$TARGET" log --oneline -20`.

## Phase 2 — Interview (skip questions answered by sniffing)

Use `AskUserQuestion`, one question per gap, with sniffed defaults:

1. Test command.
2. Lint/format command.
3. Type check command (if applicable).
4. Hook aggressiveness — `nudge` (default) | `block` | `off`. Only ask on
   fresh install; on re-install, keep the value already in
   `TARGET/.claude/aims-mode`.
5. Plan executive-summary language (default `en`). Accepts ISO 639-1
   codes (`en`, `he`, `es`, `fr`, …) or a language name. Used by `/plan`
   for the TL;DR heading and body. On re-install, keep the value already
   in `TARGET/.claude/aims-summary-lang` and skip the question. Built-in
   heading translations: `en` → `## TL;DR`, `he` → `## תקציר מנהלים`;
   unknown codes fall back to `en`.

**The Capsa capsule (`.capsa/`) is always installed.** Not optional.

## Phase 3 — Show planned changes per class

Group the planned actions by class. For each class state the rule you'll
apply and the affected paths. Then ask once:
`Approve all? [yes | per-class | abort]`.

The guiding seam: **the system layer is fully replaced and stale aims files
are deleted; user-authored content (capsule records, charter, CLAUDE.md)
is never touched.**

| Class                        | Rule                                                                 |
|------------------------------|----------------------------------------------------------------------|
| Hooks & memory scripts       | Overwrite from template; show unified diff first if content differs. |
| Vendored validator/schema    | Overwrite `validator/` + `schema/` from `AIMS_ROOT` (they are shipped tooling, not user content). |
| Stale system files           | Delete any `*.sh` in `TARGET/.claude/{hooks,memory}/` not in the current shipped set (Phase 4). Scope to `*.sh` so runtime state files survive. |
| Slash commands (the two)     | Overwrite `install-on.md`, `plan.md`.                               |
| Obsolete-command cleanup     | Delete ONLY the **named** aims-historical commands if present: `done.md`, `adr.md`, `grunt.md`, `remember.md`, `memory-init.md`, `memory-augment.md`. Any other `.md` (user-authored) is left alone. |
| Capsule bootstrap            | Create `.capsa/{capsule.yaml, charter.md}` and the dirs `decisions/`, `plans/`, `insights/{code,dev,design}/` **only if missing**. Existing records and `charter.md` are NEVER overwritten. |
| `CLAUDE.md`                  | Never overwrite. Diff per section vs template; ask per section.      |
| `.capsa/` records            | Never overwrite existing decisions/plans/insights. Augment-only (Phase 5). |
| `.claude/aims-mode`          | Create only if missing.                                              |
| `.claude/settings.json`      | Replace aims-owned hook entries with the current template; preserve all non-`hooks` keys and any user-added (non-aims) hook entries. |
| `.gitignore`                 | Append `.claude-context.md`, `.claude/.planning-lock`, and `.claude/aims-state/` if missing. |

If user picks `per-class`, walk each class via `AskUserQuestion`. List every
file slated for **deletion** explicitly in this gate before applying.

## Phase 4 — Apply (only after approval)

Copy from `AIMS_ROOT` into `TARGET`, substituting `{{VARS}}`.

| Path in TARGET                                                                                 | Source under AIMS_ROOT                          |
|------------------------------------------------------------------------------------------------|-------------------------------------------------|
| `.claude/hooks/{session-start,prompt-submit,pre-write,post-edit-marker,exit-plan-mode,stop-consolidate,session-end,pre-compact}.sh` | `templates/hooks/<same>` |
| `.claude/memory/{_lib,mark,new-insight,find-dirty,lint,consolidate,classify-inbox,doctor}.sh`  | `templates/memory/<same>`                       |
| `.claude/commands/{install-on,plan}.md`                                                        | `templates/commands/<same>`                     |
| `validator/validate.py`, `schema/*.json`                                                       | `validator/`, `schema/`                          |
| `.claude/settings.json` (merge if exists)                                                      | `templates/settings.json.tmpl`                  |
| `.claude/aims-mode`                                                                            | one line: chosen mode                           |
| `.claude/aims-summary-lang`                                                                    | one line: chosen language code (default `en`)   |
| `.capsa/capsule.yaml`, `.capsa/charter.md`                                                     | `templates/capsule.yaml.tmpl`, `templates/charter.md.tmpl` (create only if missing) |
| `CLAUDE.md`                                                                                    | `templates/CLAUDE.md.tmpl` (merge-only)         |

After copy: `chmod +x TARGET/.claude/hooks/*.sh TARGET/.claude/memory/*.sh`.

### Clean stale system files (after copy)

The current shipped set is the source of truth. Delete from `TARGET`:

- Any `*.sh` in `TARGET/.claude/hooks/` whose name is not in
  `templates/hooks/`.
- Any `*.sh` in `TARGET/.claude/memory/` whose name is not in
  `templates/memory/` (e.g. a stale `new-node.sh`, `readme-sync.sh`, or
  `check-refs.sh` left by a pre-Capsa install).
- The **named** obsolete commands (`done.md`, `adr.md`, `grunt.md`,
  `remember.md`, `memory-init.md`, `memory-augment.md`), if present. **No
  other `.md` is touched** — user-authored slash commands stay put.

Only `*.sh` and the known command files are removed — never other files in
those directories (runtime state, user notes).

### Capsule bootstrap rules

- `.capsa/capsule.yaml` → create only if missing. Fill `project.name` /
  `project.slug` from the TARGET basename, `project.repo` from the git
  remote (if any), `project.created` = today, `status: active`.
- `.capsa/charter.md` → create only if missing (a short Capsa charter
  record describing the project's purpose and conventions). If present,
  never overwrite.
- Create the record dirs `decisions/`, `plans/`, `insights/{code,dev,design}/`
  if missing. Never delete or overwrite existing records.
- After bootstrap, run `python3 TARGET/validator/validate.py TARGET/.capsa`
  and expect "conforming capsule ✔".

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
  entries** (the handlers in `templates/settings.json.tmpl`, identified by
  their `bash .claude/hooks/<name>.sh` command) with the current template
  definitions, so a stale aims hook can't survive a re-install. Keep any
  user-added hook entry that isn't one of aims' own.

## Phase 5 — Insights (inline)

Decide the mode from `TARGET/.capsa/insights/`:

- **Missing or empty → A) cold-start** (always initialize).
- **Has records → freshness probe.** Read the newest insight `updated:`:
  ```bash
  # Walk every insight; take the max `updated:` date (ISO dates sort
  # lexically = chronologically). Use the FRONTMATTER value, not file
  # mtime — a fresh `git clone` resets mtimes and would falsely look new.
  newest=$(find "$TARGET/.capsa/insights" -type f -name '*.md' -print0 2>/dev/null \
    | xargs -0 grep -h '^updated:' 2>/dev/null \
    | sed 's/^updated:[[:space:]]*//' | grep -v '^null' | sort | tail -1)
  cutoff=$(date -u -d '7 days ago' +%Y-%m-%d 2>/dev/null \
    || date -u -v-7d +%Y-%m-%d)   # GNU | BSD
  ```
  - `newest > cutoff` (updated within 7 days) → **skip all insight work**;
    print `insights: fresh (updated <Nd ago>), skipped`. System files were
    already refreshed in Phase 4.
  - else (older, or none) → **B) audit & augment**.

Insight phase is **non-fatal** — if it errors, install still succeeds.
Print the error and continue to Phase 6.

### A) Insights missing → cold-start scan

Do this work yourself, in-band (no API key, per ADR-0009):

1. Read 30–80 of the most "central" code files in `TARGET`
   (entry points, big modules, anything cited from many places).
   Bias toward files in `src/`, `lib/`, top-level scripts.
2. Group into domains (e.g. `auth`, `cli`, `network`). Within each,
   identify the prominent modules → one **code insight** per module. Aim
   for ≤ ~12 insights on first pass; the set grows via the consolidation
   loop.
3. For each: `bash TARGET/.claude/memory/new-insight.sh code <slug> "<title>" <glob> [<glob>...]`.
   **Every code insight MUST get ≥1 `code_globs`** (the Capsa validator
   rejects a code insight with none, and without globs the
   `post-edit-marker` hook can never flag it stale). Use `dev`/`design`
   insights (no globs) for historical breadcrumbs or design rationale.
4. Leave insight bodies as the six-section scaffold (ADR-0028 sections,
   no content). They fill via the consolidation loop as users work.
5. Run `python3 TARGET/validator/validate.py TARGET/.capsa` (expect
   conforming) and `bash TARGET/.claude/memory/lint.sh`; fix any issue
   interactively.

### B) Insights exist → audit & augment

1. Collect all `code_globs` from existing code insights.
2. Identify code areas in `TARGET` not matched by any insight (`src/`,
   `lib/`, top-level directories with > N files of source).
3. Propose new insights via `AskUserQuestion` — one batch, list form.
   Default to "create" for clear matches, "skip" otherwise.
4. For each approved: `new-insight.sh code <slug> "<title>" <glob>...`
   (same glob rule as 5A.3).
5. **Never overwrite existing insight bodies.** Augmentation is additive.
6. Run the validator + `lint.sh`; surface issues; do not auto-fix human
   content.

## Phase 6 — Doctor report

Report `re-install` whenever `EXISTING` **or** `PRIOR_AIMS` is set; only a
truly clean target is `fresh`.

```
aims installed into <TARGET> (<fresh|re-install>):
  hooks: nudge | block | off
  commands: install-on, plan  (obsolete removed: <list or none>)
  stale system files removed: <list or none>
  capsule: .capsa/ (<conforming ✔ | N schema issues>)
    decisions: <N>   plans: <N>   insights: <N>
  validator: vendored (validator/validate.py)
  CLAUDE.md: created | merged (+<N> sections) | unchanged
  insights: <fresh-scan: N created> | <audited: +M created> | <fresh (updated <Nd ago>), skipped>
  pre-Capsa layout: <docs/{adr,plans,memory} present — migrate separately | none>
  plan summary language: <en|he|...>
  lint: clean | <K issues>
  next: cd <TARGET> && claude
        try `/plan <task>` for non-trivial work
```

## Variables substituted in templates

- `{{PROJECT_NAME}}` — basename of `TARGET`
- `{{PROJECT_SLUG}}` — slugified basename
- `{{REPO_URL}}` — git remote origin URL (or empty)
- `{{TEST_CMD}}`, `{{LINT_CMD}}`, `{{TYPECHECK_CMD}}` — confirmed commands
- `{{HOOK_MODE}}` — `nudge` | `block` | `off`
- `{{SUMMARY_LANG}}` — chosen summary language code, default `en`
- `{{DATE}}` — today's date `YYYY-MM-DD`

## Hard rules

- **Idempotent + self-refreshing.** Re-runs leave the **system** fully
  current and remove stale aims files, but never destroy hand-edited
  content. The seam:
  - Refresh (overwrite from template): hooks, memory scripts, the two
    commands, the vendored `validator/` + `schema/`, and aims-owned
    `settings.json` hook entries.
  - Delete (stale): `*.sh` in `.claude/{hooks,memory}/` not in the shipped
    set; commands other than `install-on`/`plan`.
  - Never touch: capsule records (`.capsa/{decisions,plans,insights}/`),
    `.capsa/charter.md`, `.capsa/capsule.yaml`, `CLAUDE.md` sections, and
    non-`hooks` settings keys.
- Read-only on `TARGET/src/`, `TARGET/tests/`, `TARGET/lib/`, package
  manifests, `TARGET/README.md`, `TARGET/LICENSE`.
- Read-only on `AIMS_ROOT` entirely (except the self-install case).
- `$ARGUMENTS` may carry `--mode=…` after the path. If present, skip the
  hook-mode question.
- If user aborts at Phase 3, write nothing. Print
  `Aborted. No changes made.`
- `TARGET == AIMS_ROOT` (self-install) is allowed and intended for
  dogfooding refresh. The idempotency rules still hold.
- The only two commands installed into the target are `install-on` and
  `plan`. Everything else (close-plan, ADR creation, insight
  consolidation, mechanical edits) happens inline or via hooks.
