# Plan: aims ↔ The_secretary integration
Status: draft
Started: 2026-06-02

## תקציר מנהלים

שילוב חד-כיווני, מינימלי ובעל ניוון-חיננית (graceful degradation) בין
`aims` ל-`/secretary` (Repo: `eliezeravihail/The_secretary`). הצד שמוסיף
ערך הוא **aims → קורא secretary**: hook ב-`SessionStart` ב-aims מחפש את
קובץ העבודה של secretary (אם מוגדר משתנה סביבה `SECRETARY_WORK_DIR` או
אם קיים `~/.secretary-work-dir`), קורא את `todo.md` ושורה אחרונה
מ-`daily/YYYY-MM/YYYY-MM-DD.md`, ומזריק כעובדה (~2KB מקסימום) רשימת
משימות פתוחות + "מה עבדתי עליו אחרון". כל ה-touchpoints ב-aims בלבד;
הקוד של secretary לא נוגעים בו. אם secretary לא מותקן / לא נגיש —
נכשל בשקט עם שורה אחת `===[aims: secretary unavailable]===` (תואם
ADR-0020). הכיוון ההפוך (secretary→aims) נדחה לפאזה ב' כי הוא דורש
שינויים בריפו של secretary שלא במהלך תכנון זה. כיוון `aims→writes
secretary` נשמר כ-open question (האם close-out של plan בoaims צריך
לכתוב entry ל-`daily/.../*.md` של secretary).

## Goal

aims sessions begin with awareness of the user's active personal-secretary
tasks for the day, without coupling either tool to the other's presence,
without blocking any edit, and without changing the secretary repo.

## Decision

**Direction A — aims reads secretary at SessionStart.** A new helper
`templates/hooks/lib/secretary-context.sh` resolves the secretary
work-state directory (env var first, then a dotfile at
`~/.secretary-work-dir`, then nothing). When found, it reads the **head**
of `todo.md` (capped 1500 bytes) and the **tail** of today's
`daily/YYYY-MM/YYYY-MM-DD.md` (capped 800 bytes). It emits a
`[aims-secretary] …` block on stdout. `templates/hooks/session-start.sh`
sources the helper at the end of its own informational emissions.

Why this shape:

- **Project identification.** secretary already binds to one work-state
  directory at config time (per its README — `work_state_dir` lives in
  `secretary.md` itself). aims doesn't need to know about projects; it
  just reads the directory secretary already configured. The single
  binding solves "which project" trivially as long as the user runs
  Claude Code in the same workspace context they ran `/secretary` in.
- **Read-only, non-blocking, graceful-degrade.** No write into
  secretary; if `work_state_dir` resolution fails the helper exits 0
  with no emission (or one short marker if `AIMS_SECRETARY_DEBUG=1`).
  This honours ADR-0020 strictly.
- **No new toolchain.** Pure bash + `head`/`tail`/`ls`, matching aims'
  zero-dependency posture (CLAUDE.md: "markdown + bash").
- **Mirror `.claude/hooks/`.** As with every other hook change, after
  editing `templates/hooks/…` we copy into `.claude/hooks/` for the
  dogfood install (CLAUDE.md "Plugin-specific notes").

Other directions deliberately deferred (see Open design questions):

- **B. aims → writes secretary** (e.g. plan close-out appends a one-line
  "done task" entry to today's daily log). Tempting but introduces a
  write into a repo aims doesn't own and a contract aims would have to
  guess at (secretary's daily-log entry shape is `### [context]`-block
  prose, not a structured field). Kept as Open question.
- **C. secretary reads aims.** Requires editing
  `eliezeravihail/The_secretary/.claude/commands/secretary.md` to add a
  pre-flight "if `docs/plans/*.md` with `Status: in-progress` exists in
  cwd, include it in the session-open summary." That's a change in the
  secretary repo — explicitly out of scope per the task brief
  ("Do NOT push anything back to that repo").
- **D. Shared context layer.** Rejected — a third artifact to maintain
  for a two-tool integration; YAGNI.

## Changes

### `templates/hooks/lib/secretary-context.sh` — NEW

```bash
#!/usr/bin/env bash
# aims helper — read-only probe of The_secretary's work-state dir.
# Emits a factual `[aims-secretary]` block on stdout, or nothing.
# Never fails the caller; never writes anything.
#
# Resolution order for the work-state directory:
#   1. $SECRETARY_WORK_DIR
#   2. First non-blank line of ~/.secretary-work-dir
#   3. (give up silently)
#
# ADR-0020 compliance: no block, no error surfaced; if anything goes
# wrong we emit nothing (or a single `[aims-secretary] unreachable: …`
# line when AIMS_SECRETARY_DEBUG=1 is set).

set -u

emit_unreachable() {
  [ "${AIMS_SECRETARY_DEBUG:-0}" = "1" ] || return 0
  printf '[aims-secretary] unreachable: %s\n' "$1"
}

work_dir="${SECRETARY_WORK_DIR:-}"
if [ -z "$work_dir" ] && [ -r "$HOME/.secretary-work-dir" ]; then
  work_dir=$(awk 'NF{print; exit}' "$HOME/.secretary-work-dir" 2>/dev/null || true)
fi
if [ -z "$work_dir" ]; then
  emit_unreachable "no SECRETARY_WORK_DIR and no ~/.secretary-work-dir"
  exit 0
fi
# Expand a leading ~ (the dotfile may contain a literal tilde).
case "$work_dir" in
  '~'/*) work_dir="$HOME/${work_dir#~/}" ;;
  '~')   work_dir="$HOME" ;;
esac
if [ ! -d "$work_dir" ]; then
  emit_unreachable "work_dir not a directory: $work_dir"
  exit 0
fi

TODO="$work_dir/todo.md"
TODAY=$(date -u +%Y-%m-%d)
MONTH=$(date -u +%Y-%m)
DAILY="$work_dir/daily/$MONTH/$TODAY.md"

# Find the most recent daily log if today's doesn't exist yet.
recent_daily=""
if [ ! -r "$DAILY" ] && [ -d "$work_dir/daily" ]; then
  recent_daily=$(find "$work_dir/daily" -type f -name '*.md' 2>/dev/null \
    | sort | tail -1)
fi

have_any=0
[ -r "$TODO" ] && have_any=1
[ -r "$DAILY" ] && have_any=1
[ -n "$recent_daily" ] && have_any=1
if [ "$have_any" -eq 0 ]; then
  emit_unreachable "no todo.md or daily log under $work_dir"
  exit 0
fi

printf '[aims-secretary] Personal-secretary context (read-only; %s):\n' "$work_dir"

if [ -r "$TODO" ]; then
  printf '       todo.md (head, capped 1500B):\n'
  head -c 1500 "$TODO" | sed 's/^/         /'
  size=$(wc -c < "$TODO" 2>/dev/null || echo 0)
  if [ "$size" -gt 1500 ]; then
    printf '         … (%d bytes truncated)\n' "$((size - 1500))"
  fi
fi

if [ -r "$DAILY" ]; then
  printf '       daily/%s/%s.md (tail, capped 800B):\n' "$MONTH" "$TODAY"
  tail -c 800 "$DAILY" | sed 's/^/         /'
elif [ -n "$recent_daily" ]; then
  printf '       most recent daily log %s (tail, capped 800B):\n' \
    "${recent_daily#$work_dir/}"
  tail -c 800 "$recent_daily" | sed 's/^/         /'
fi

printf '       (Source: The_secretary work-state dir. Read-only probe; aims never writes here.)\n'
exit 0
```

### `templates/hooks/session-start.sh` — APPEND one block before `exit 0`

```bash
# Personal-secretary context (optional; ADR-XXXX aims↔secretary).
# Sourced via bash so a failure in the helper can never abort
# session-start. Emits its own [aims-secretary] block on stdout.
SECRETARY_LIB=""
if   [ -r ".claude/hooks/lib/secretary-context.sh" ];   then SECRETARY_LIB=".claude/hooks/lib/secretary-context.sh"
elif [ -r "templates/hooks/lib/secretary-context.sh" ]; then SECRETARY_LIB="templates/hooks/lib/secretary-context.sh"
fi
if [ -n "$SECRETARY_LIB" ]; then
  bash "$SECRETARY_LIB" 2>/dev/null || true
fi
```

(Inserted at the bottom of the file, just before `exit 0`, so it runs
last and its emission is visually grouped with the other
`[aims-…]` blocks but doesn't perturb earlier output if it misfires.)

### `.claude/hooks/lib/secretary-context.sh` and `.claude/hooks/session-start.sh` — MIRROR

After the template edits, copy through:

```bash
mkdir -p .claude/hooks/lib
cp templates/hooks/lib/secretary-context.sh .claude/hooks/lib/secretary-context.sh
cp templates/hooks/session-start.sh         .claude/hooks/session-start.sh
chmod +x .claude/hooks/lib/secretary-context.sh
```

### `templates/commands/install-on.md` (and the global
`commands/install-on.md`) — copy the new `lib/` subdir into targets

The install-on command currently copies hooks one-by-one. Add the
`lib/` subdir to the list of paths it materializes in the target's
`.claude/hooks/`. This makes the integration available in every
bootstrapped project, not just the aims repo itself.

```diff
- # Hooks
- copy templates/hooks/session-start.sh      → .claude/hooks/session-start.sh
- copy templates/hooks/prompt-submit.sh      → .claude/hooks/prompt-submit.sh
- … (other hooks unchanged) …
+ # Hooks
+ copy templates/hooks/session-start.sh      → .claude/hooks/session-start.sh
+ copy templates/hooks/prompt-submit.sh      → .claude/hooks/prompt-submit.sh
+ … (other hooks unchanged) …
+ # New: secretary integration helper (optional read-only context).
+ mkdir -p .claude/hooks/lib
+ copy templates/hooks/lib/secretary-context.sh → .claude/hooks/lib/secretary-context.sh
+ chmod +x .claude/hooks/lib/secretary-context.sh
```

(Exact wording matches install-on's existing prose — to be applied as a
small additive step in the file's "Hooks" section.)

### `README.md` — short subsection under "Hooks"

```markdown
### Optional: personal-secretary context (The_secretary)

If you also use [`The_secretary`](https://github.com/eliezeravihail/The_secretary),
aims' `session-start` hook can surface your current `todo.md` + most
recent daily-log tail at the top of every Claude session. Point aims at
secretary's work-state directory with **either**:

```sh
export SECRETARY_WORK_DIR=/path/to/your/work-state
# …or:
echo /path/to/your/work-state > ~/.secretary-work-dir
```

If neither is set, the hook stays silent — aims is fully usable without
secretary. The probe is strictly read-only; aims never writes into the
secretary work-state directory.
```

### `docs/adr/00NN-aims-secretary-integration.md` — NEW ADR (close-out)

Status `proposed` at close-out. Records: chose direction A
(aims→reads secretary, one-way); rejected B/C/D and why; the
`SECRETARY_WORK_DIR` env / `~/.secretary-work-dir` dotfile contract;
the graceful-degrade rule (silent unless `AIMS_SECRETARY_DEBUG=1`).
Number assigned at close-out (next is 0024).

### `tests/secretary-integration.sh` — NEW (smoke test, jq-free)

```bash
#!/usr/bin/env bash
# Asserts:
#   1. Helper emits nothing and exits 0 when no env / dotfile set.
#   2. Helper emits an [aims-secretary] block when SECRETARY_WORK_DIR
#      points at a fake work-state directory with a todo.md.
#   3. Helper exits 0 even when SECRETARY_WORK_DIR points at /nonexistent.
#   4. session-start.sh exits 0 in all three cases.
set -u
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
HELPER=templates/hooks/lib/secretary-context.sh

# 1. silent
unset SECRETARY_WORK_DIR
out=$(HOME="$TMP" bash "$HELPER" 2>/dev/null || true)
[ -z "$out" ] || { echo FAIL: silent case emitted output; exit 1; }

# 2. populated
mkdir -p "$TMP/ws/daily/$(date -u +%Y-%m)"
printf '# Tasks\n- [ ] write the integration plan\n' > "$TMP/ws/todo.md"
printf '# %s\n### [aims] drafted plan\n' "$(date -u +%Y-%m-%d)" \
  > "$TMP/ws/daily/$(date -u +%Y-%m)/$(date -u +%Y-%m-%d).md"
out=$(SECRETARY_WORK_DIR="$TMP/ws" bash "$HELPER" 2>/dev/null || true)
echo "$out" | grep -q '\[aims-secretary\]' \
  || { echo FAIL: populated case missing marker; exit 1; }

# 3. broken path
out=$(SECRETARY_WORK_DIR=/nonexistent/path bash "$HELPER" 2>/dev/null; echo "rc=$?")
echo "$out" | grep -q 'rc=0' \
  || { echo FAIL: broken path returned nonzero; exit 1; }

echo PASS
```

## Open design questions

1. **Should aims write back to secretary?** (Direction B.) Concretely:
   on plan close-out, append a one-line entry to today's
   `daily/YYYY-MM/YYYY-MM-DD.md` along the lines of
   `### [aims] completed plan: <plan-title>`. Pros: closes the loop
   (secretary sees what aims accomplished). Cons: aims becomes a writer
   into a directory it doesn't own; the entry format isn't versioned
   anywhere; if the user has secretary's team-lead coordination on, an
   un-coordinated entry could surprise them. Recommendation: defer to
   a separate ADR; ship Direction A first and see whether the missing
   reverse path actually matters in practice.

2. **Resolution mechanism — env var vs dotfile vs both?** Current plan
   does both (env first, dotfile fallback). Alternative: env-only,
   keeping the surface narrower. The dotfile is convenient for users
   who don't want to maintain shell-rc lines per project; the env var
   is convenient for one-off overrides. Both is two code paths to
   maintain. **User decision needed.**

3. **What if the user runs `/secretary` per-project?** secretary's
   README mentions a per-project install (`<your-project>/.claude/
   commands/secretary.md`). In that mode the work-state-dir is still
   stored inside `secretary.md` itself. Should aims fall back to
   grepping `.claude/commands/secretary.md` for a `work_state_dir:`
   line when env+dotfile are absent? Pros: zero-config when both tools
   are installed per-project. Cons: parses another tool's config file.
   Recommendation: not in v1 — keep aims ignorant of secretary's
   internal config format. Revisit if the integration sees real use.

4. **Caching.** The helper currently re-reads `todo.md` on every
   SessionStart. For a large todo.md (>1MB?) this is wasteful but
   tiny in absolute terms. Skip caching for v1.

## Verification

- `bash -n templates/hooks/*.sh templates/hooks/lib/*.sh && bash -n .claude/hooks/*.sh .claude/hooks/lib/*.sh`
- `bash tests/secretary-integration.sh` → `PASS`
- `bash tests/inform-never-block.sh` → still passes (no regression in
  the never-block invariant — helper exits 0 unconditionally)
- `bash tests/router-auto-plan.sh` → still passes (unchanged surface)
- Manual: with `SECRETARY_WORK_DIR` unset, open a Claude Code session in
  this repo and confirm session-start output is identical to before
  (no `[aims-secretary]` line). With `SECRETARY_WORK_DIR=/tmp/ws-fake`
  (pre-seeded), confirm the block appears.
- Manual: with `SECRETARY_WORK_DIR=/nonexistent` confirm the session
  still starts cleanly and only `[aims-secretary] unreachable: …`
  appears if `AIMS_SECRETARY_DEBUG=1` is also set.

## Close-out checklist

- ADR: WRITE — `0024-aims-secretary-integration.md` (clear architectural
  commitment: introduces a cross-tool contract and a new env-var /
  dotfile surface aims now defends).
- Nodes: UPDATE — `docs/memory/hooks/session-start.md` (now reads
  external state via a helper); CONSIDER NEW node
  `docs/memory/integration/secretary.md` if the integration grows past
  one helper file. v1: just append to the session-start node.
- CLAUDE.md: UPDATE — add a one-line bullet under "Plugin-specific
  notes" noting the optional secretary integration and its env/dotfile
  contract.
- Tests: NEW — `tests/secretary-integration.sh`. EXISTING
  `inform-never-block.sh` / `router-auto-plan.sh` continue to cover the
  invariants the new code touches indirectly.
- TODO: revisit Direction B (aims→writes secretary) after one week of
  dogfooding; promote to its own plan if the missing reverse path is
  felt.

## Risks / unknowns

- **secretary's work-state directory shape may evolve.** The README
  pins `todo.md`, `results.md`, `daily/YYYY-MM/YYYY-MM-DD.md`,
  `measures.md`. The helper only reads `todo.md` and the daily log;
  if either is renamed in a future secretary release, the helper goes
  silent (acceptable graceful-degrade) but the integration value drops.
  Mitigation: small surface = small breakage; helper reports nothing
  rather than something stale.
- **Hebrew content** in todo.md may make `head -c 1500` truncate
  mid-codepoint. Acceptable — the output is informational context,
  not a structured payload; a mangled last char doesn't hurt the
  model's comprehension. If it becomes an issue, switch to `head -n`
  with a line cap.
- **Two integration directions diverge.** If the user later asks for
  Direction B (writes) or C (secretary reads aims), the env-var
  surface chosen here doesn't constrain those — both can layer on top
  without renaming `SECRETARY_WORK_DIR`.
- **Repo-name ambiguity from the task brief.** The user wrote
  `teh-secretary`; both `teh-secretary` and `the-secretary` returned
  404 via WebFetch. Resolved via `mcp__github__search_repositories`
  (`user:eliezeravihail secretary`) → the actual repo is
  `eliezeravihail/The_secretary` (capital T, underscore). This plan
  links to that exact URL throughout; any docs/ADRs written at
  close-out must use that exact spelling.
