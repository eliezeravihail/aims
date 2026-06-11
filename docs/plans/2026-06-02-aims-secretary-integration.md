---
Status: draft
Date: 2026-06-02
---

# Plan: aims → secretary one-way integration (v4)

## Context

v3 specified a **bidirectional** integration: Direction A (aims's
SessionStart hook reads secretary's `todo.md` + daily-log tail via
env-var/dotfile) and Direction B (an explicit registry secretary reads
at session-open so it can append suggestions to a per-project inbox).

The user has now narrowed scope drastically:

1. "אני רוצה רק כיון 2" — keep only Direction 2 (secretary becomes
   aims-aware in aims-managed cwd's). Direction 1 is **dropped entirely**.
2. "בתוספת הצעה בעת התקנת אימס להתקין גם את סקרטרי" — at install time,
   offer to install secretary if missing.
3. "ובלי שום מנגנון תקשורת מאיימס לסקרטרי" — no *runtime* channel from
   aims to secretary.
4. "רק הסקרטרי צריך להכיר את איימס. לא הפוך" — awareness is one-way;
   aims must not know about secretary at runtime.

Reconciliation note: registering the project's cwd inside `~/.claude/`
at install time is **not** a runtime channel. It is a **one-shot
install-time bootstrap**: install-on writes one line, once, and aims
never touches secretary's state again. No daemon, no shared file aims
keeps updating, no aims-side hook that calls secretary.

## Goal

When the user runs `/install-on <path>` in a project, that project
becomes *known* to a globally-installed secretary, so that secretary —
the next time it opens in that exact cwd — can apply aims-aware
behavior. If secretary is not installed, install-on offers to install
it. Nothing else about aims's runtime changes.

## Non-goals

- No SessionStart hook reading secretary state (Direction 1 dropped).
- No `SECRETARY_WORK_DIR` env var, no `~/.secretary-work-dir` dotfile.
- No registry file *inside* the aims repo.
- No aims-side knowledge of secretary at runtime: hooks, commands,
  memory scripts — all untouched.
- No specification of what secretary actually *does* when it sees the
  cwd match; that is a separate spec the user owns, in secretary's repo.
- No prefix / glob / ancestor matching. Strict absolute-path equality.

## Approach

Two additive blocks inside `/install-on`, both gated by Phase 3 approval
and run as part of Phase 4 (or a small Phase 4.5 — either is fine; this
plan describes them as a sub-phase of Phase 4 for simplicity).

### 1. Optional secretary install offer

secretary is distributed as a **slash command only** (confirmed by
inspecting `https://github.com/eliezeravihail/The_secretary`: the repo
contains `README.md` + `.claude/commands/secretary.md`, no `skills/`).

After the normal aims install steps, detect:

```bash
[ -f "$HOME/.claude/commands/secretary.md" ]
```

- **Present** → skip the offer; proceed to registration.
- **Absent** → AskUserQuestion: *"secretary is not installed. Install it
  now? [yes / no]"*.
  - `no` → skip silently.
  - `yes` → `git clone --depth 1 https://github.com/eliezeravihail/The_secretary`
    into a temp dir, then `cp <tmp>/.claude/commands/secretary.md
    ~/.claude/commands/secretary.md` (mkdir -p the parent). Wrap in error
    handling; on failure emit one factual line and continue. **Never
    fail the aims install because secretary install failed**
    (best-effort).

### 2. Register this project's cwd (idempotent, one-shot)

Regardless of which branch above ran, if secretary is now present:

Each line is `<absolute-cwd>\t<one-line-description>`: cwd followed by
a TAB and a free-form one-sentence description of the project (what it
is — secretary displays this next to the path on a match). install-on
asks the user for the description once, defaulting to the project's
directory basename if the user accepts the default.

```bash
REG="$HOME/.claude/secretary/aims-projects.txt"
mkdir -p "$(dirname "$REG")"
CWD="$(cd "$TARGET" && pwd)"
DESC="$(ask_user "One-line description of this project" "$(basename "$CWD")")"
touch "$REG"
# idempotent: match on the cwd column only (first field, tab-separated)
awk -F'\t' -v p="$CWD" '$1==p{found=1} END{exit !found}' "$REG" \
  || printf '%s\t%s\n' "$CWD" "$DESC" >> "$REG"
```

One row per project. Append only if the cwd column is not already
present. Strict equality on cwd — no normalization beyond what
`cd && pwd` produces. If a row already exists with a different
description, the existing description is preserved (re-running
install-on does not silently overwrite the user's earlier description).

If secretary was absent and the user declined to install it, **do not
create the registry file**. (Nothing would read it.)

On success emit one factual line:

```
===[aims: registered <CWD> with secretary]===
```

(matches ADR-0021 reply-marker shape). On no-op (already present): no
marker.

### What is explicitly *not* done

- No aims-side hook that reads or writes `aims-projects.txt`.
- No SessionStart change.
- No new env var, no new dotfile.
- No `templates/hooks/lib/secretary-context.sh`.
- No inbox-count display in aims.
- No `tests/secretary-integration.sh` covering Direction A (none of it
  exists anymore).

## File-level changes

| File | Change |
|---|---|
| `commands/install-on.md` | Add a sub-section under Phase 4 (or a new Phase 4.5) describing the offer + registry write. |
| `templates/commands/install-on.md` | Same patch verbatim (the two install-on files are kept identical per `docs/memory/installer/install-on.md`). |
| `.claude/commands/install-on.md` | Refreshed from template via `/install-on .` after the edit. |
| `tests/install-on-secretary.sh` (NEW) | Smoke test for: (a) missing-secretary + decline → no registry file, (b) missing-secretary + accept → clone+install path invoked (mockable), (c) present-secretary → registry file appended, (d) re-run is idempotent (no duplicate line). |
| `README.md` (aims) | One-paragraph note under an "Optional integrations" heading describing the install-on offer + the one-shot registration. |
| `docs/adr/NNNN-aims-secretary-one-way-bootstrap.md` (close-out) | New ADR (proposed) recording the one-way, install-time-only contract; supersedes any prior bidirectional intent. |

No edits to `templates/hooks/*`, no edits to `.claude/hooks/*`.

## Secretary-side TODOs (separate repo, out of scope here)

Tracked for the user's follow-up work in `eliezeravihail/The_secretary`:

- At session-open, read `~/.claude/secretary/aims-projects.txt` if it
  exists.
- Compare each line with `pwd` using **strict `==`** equality.
- On match, apply aims-aware behavior (spec deferred to a separate
  session — user owns this).
- If the file is absent, unreadable, or has no matching line: behave
  exactly as today.

This plan does not prescribe what aims-aware behavior looks like on
secretary's side beyond "read the file, match the cwd."

## Risks

- **Secretary's repo URL and install layout are unknown from this
  repo.** Plan assumes they're knowable; user will confirm in the open
  questions below.
- **Auto-clone-and-install from install-on is non-trivial.** If the
  secretary repo is private, moves, or changes layout, install-on
  breaks. Mitigation: wrap in error handling, treat secretary install
  as best-effort, never fail the aims install over it.
- **Re-running install-on must not duplicate the cwd line.** Mitigation:
  `grep -Fxq` guard before append.
- **Registry file abandonment.** If the user deletes the project or
  uninstalls aims, the line remains. Acceptable in v1 — secretary will
  simply not match anything on that line in its own cwd. Removal flow
  deferred.
- **Strict equality is brittle to symlinks / alternate paths.**
  Acceptable; the path is what `cd && pwd` produces at install time.

## Test plan

- `bash -n templates/hooks/*.sh && bash -n .claude/hooks/*.sh` still
  passes (no hook changes, but kept as the project's standard check).
- `bash tests/install-on-secretary.sh` covers the four cases above,
  using a temp `HOME` and mocked `git clone`.
- Manual: on a real machine, run `/install-on .` with and without
  `~/.claude/commands/secretary.md` present; verify file contents and
  the marker line.

## Rollout

Single PR. No deprecation period — v3 was never implemented.

## Open questions

All four open questions from the earlier revision are resolved:

1. ✓ Repo URL: `https://github.com/eliezeravihail/The_secretary`.
2. ✓ Distribution: slash command only
   (`~/.claude/commands/secretary.md`); no `skills/` form.
3. ✓ Registry path: `~/.claude/secretary/aims-projects.txt`.
4. ✓ Row format: `<absolute-cwd>\t<one-line-description>` (TAB-separated,
   description is a free-form one-sentence explanation of the project,
   defaulting to the directory basename if the user accepts the
   default).

No outstanding blockers; awaiting Phase 3 approval to implement.
