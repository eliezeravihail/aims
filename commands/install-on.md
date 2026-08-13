---
description: Install (or re-install) aims' per-project pieces into a target project. Idempotent.
argument-hint: "<target-project-path>"
---

# /install-on

Install (or re-install) **aims** into a target project. aims' *method* (the `aims-guide` skill and the
`/aims-*` commands) is available whenever the plugin is enabled — it needs no per-project install. What
this command installs is the small per-project layer the method relies on: the session-start hook, the
read-time staleness hook, the anchor tool, and their settings wiring. Design records are **not**
scaffolded — the method files them co-located with the code as it works.

Idempotent and self-refreshing: re-running brings the installed layer up to date and removes stale aims
files, after showing a diff — while **never** destroying hand-edited content (the co-located design
records, `CLAUDE.md` sections, plans, user settings keys).

## Roots

- `AIMS_ROOT` — the aims source repo (current working directory). Read-only, **except** when
  `TARGET == AIMS_ROOT` (dogfooding self-refresh).
- `TARGET` — resolved absolute path from `$ARGUMENTS`. Ask for it if missing or nonexistent.

## Phase 1 — Detect state (read-only)

- `EXISTING=1` if `TARGET/.aims/anchor.py` or `TARGET/.claude/hooks/session-start.sh` is present.
- `PRIOR_AIMS=1` if any pre-capsa/pre-colocation remnant exists — a stale memory subsystem
  (`TARGET/.claude/memory/`, `TARGET/docs/memory/`), old hooks (`post-edit-marker.sh`,
  `stop-consolidate.sh`, `prompt-submit.sh`, …), an old `plan.md` command, a `TARGET/.claude/aims-mode`,
  or a separate `TARGET/.capsa/` tree from the mirror-tree era. A `PRIOR_AIMS` target is a **migration**:
  report it as such and remove the stale pieces (Phase 3). A `.capsa/` tree, if present, is reported for
  the user to migrate its records into the code tree — never deleted automatically.
- Sniff (read-only): `git -C "$TARGET" log --oneline -10`, existing `CLAUDE.md`, `.claude/settings.json`.

## Phase 2 — Show planned changes, ask once

Group actions by class, state the rule and paths, then ask `Approve all? [yes | per-class | abort]`.

| Class | Rule |
|---|---|
| Session hook | Overwrite `TARGET/.claude/hooks/session-start.sh` from `templates/hooks/`; diff first if it differs. |
| Anchor tool + staleness hook | Copy `knowledge/anchor.py` → `TARGET/.aims/anchor.py` and `knowledge/staleness_hook.py` → `TARGET/.aims/staleness_hook.py` (same dir, so the hook imports the tool). |
| Settings | In `TARGET/.claude/settings.json`, set aims' two hook entries (SessionStart → `session-start.sh`; PostToolUse/Read → `python3 .aims/staleness_hook.py`); preserve every non-aims key and hook. |
| CLAUDE.md | Never overwrite. Append a missing aims section from `templates/CLAUDE.md.tmpl`, wrapped `<!-- added by aims --> … <!-- /aims -->`; diff per existing same-named section and ask. |
| Stale remnants | Delete the memory subsystem (`TARGET/.claude/memory/`, `TARGET/docs/memory/`), the retired hooks (`post-edit-marker`, `stop-consolidate`, `prompt-submit`, `pre-write`, `pre-compact`, `session-end`, `exit-plan-mode`), the old `plan.md` command, and `TARGET/.claude/aims-{mode,summary-lang}`. List every deletion in the approval gate. A `.capsa/` tree is reported, never deleted. |
| `.gitignore` | Append `.aims/state.md` if missing (loop run-state is not committed). |

If `per-class`, walk each via `AskUserQuestion`. List every **deletion** explicitly before applying.

## Phase 3 — Apply (only after approval)

Copy from `AIMS_ROOT` into `TARGET` per the table above; `chmod +x TARGET/.claude/hooks/*.sh`. Then
delete the stale remnants listed in the gate — those, and only those. Read-only on `TARGET/src`,
`TARGET/tests`, `TARGET/lib`, manifests, `TARGET/README.md`, `TARGET/LICENSE`, and every existing design
record (`goals.md`, `architecture.md`, a companion `<file>.md`, anything under `decisions/`).

### settings.json merge

- Missing → write from `templates/settings.json.tmpl`.
- Exists → preserve every non-`hooks` key and every non-aims hook entry verbatim. Replace only aims'
  own two entries (identified by `session-start.sh` and `staleness_hook.py` in their commands) with the
  current template, so a stale aims hook can't survive a re-install.

## Phase 4 — Report

```
aims installed into <TARGET> (<fresh | re-install | migration>):
  hooks: session-start + staleness (advisory, never blocks)
  tool: .aims/anchor.py
  design records: co-located with the code — the method files them as it works
  removed (stale): <memory/, retired hooks, plan.md — or none>
  .capsa/ tree found: <path — migrate its records into the code tree | none>
  CLAUDE.md: created | merged (+<N> sections) | unchanged
  next: cd <TARGET> && claude ; then /aims-plan or /aims-plan-and-build
```

## Hard rules

- Idempotent + self-refreshing; never destroy hand-edited content (co-located design records,
  `CLAUDE.md` sections, plans, non-aims settings keys). Never auto-delete a `.capsa/` tree.
- The staleness hook is **advisory** and the install must keep it so — never wire it to block.
- `TARGET == AIMS_ROOT` (self-install) is allowed and is the dogfooding refresh path.
- If the user aborts, write nothing: `Aborted. No changes made.`
