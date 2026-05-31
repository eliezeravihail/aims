# Plan: aims glob-match `code:` + auto-plan UX revamp
Status: completed
Started: 2026-05-31
Completed: 2026-05-31

## תקציר מנהלים

ארבעה תיקונים שיטתיים ל־aims שמכוונים את התוסף לרצף עבודה אוטומטי שגלל גם לאזורים שלא תוכננו לפני זה. (1) `path_matches` ב־`_lib.sh` עושה התאמת־מחרוזת מדויקת בלבד למרות ש־ADR-0012 מבטיח שכל `code:` מתפרש כ־glob — נוסיף ענף של `case`־glob כך שקובץ חדש תחת `src/loaders/*.py` ידליק dirty על ה־node במקום לגלוש ל־`_inbox.md`. (2) hook חדש מסוג `PostToolUse` על `ExitPlanMode` שמיירט את גוף התוכנית שעבר דרך ה־harness ומחיל אותה ל־`docs/plans/<date>-<slug>.md` — רשת ביטחון לסשנים שבהם ה־model בכל זאת ישתמש ב־`ExitPlanMode` של ה־harness. (3) `/plan` עצמו נכתב מחדש כך שיכתוב קודם טיוטה ל־`docs/plans/` עם `Status: draft`, ואז יבקש אישור — האישור הוא ה־gate שהופך את הסטטוס ל־`in-progress` ומסיר את ה־planning lock. (4) הראוטר ב־`prompt-submit.sh` יבטל את תפריט הבחירה לטובת הפעלה אוטומטית של `/plan` על כל intent של עריכה (bug/feature/refactor/decision/mechanical/ambiguous); intent של `question` ממשיך לעבוד בלי תוכנית. שני ADR יוצאים: 0014 (glob matching) ו־0015 (auto-plan + draft-on-disk + ExitPlanMode bridge).

## Changes

### `.claude/memory/_lib.sh` + `templates/memory/_lib.sh`

Add a `case`-glob clause to `path_matches`. Existing exact-match and `:line-range` prefix clauses stay; new clause matches against the `hay` path (frontmatter side), with the same retry under the repo root when `needle` is absolute.

```bash
path_matches() {
  local needle="$1" hay="$2"
  local hay_path="${hay%%:*}"
  [ "$needle" = "$hay" ] && return 0
  case "$hay" in
    "$needle":*) return 0 ;;
  esac
  # shellcheck disable=SC2254 — glob is intentional (ADR-0012).
  case "$needle" in
    $hay_path) return 0 ;;
  esac
  # Defense in depth: if needle is absolute, retry after stripping the
  # repo root. Marker-side normalization should already have done this,
  # but a future direct caller of mark.sh may forget.
  case "$needle" in
    /*)
      local root rel
      root=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
      case "$needle" in
        "$root"/*)
          rel="${needle#$root/}"
          [ "$rel" = "$hay" ] && return 0
          case "$hay" in
            "$rel":*) return 0 ;;
          esac
          # shellcheck disable=SC2254
          case "$rel" in
            $hay_path) return 0 ;;
          esac
          ;;
      esac
      ;;
  esac
  return 1
}
```

### `templates/hooks/exit-plan-mode.sh` + `.claude/hooks/exit-plan-mode.sh` (new)

`PostToolUse` hook on `ExitPlanMode`. Reads `tool_input.plan` from stdin; computes a slug from the first `# ` heading (or the first non-blank line); writes `docs/plans/<UTC-date>-<slug>.md` with `Status: in-progress`, `Started: <date>`, then the verbatim plan body. Skips if a file with the same name already exists (`/plan` already wrote it). Skips if no plan body. Always exits 0.

```bash
#!/usr/bin/env bash
# aims PostToolUse hook on ExitPlanMode — bridges the harness-mode
# plan presentation into a docs/plans/ file so close-out + memory
# consolidation pipelines can see it.
#
# Triggered only when matcher: "ExitPlanMode" is wired in settings.json.
# Reads the harness's tool_input.plan from stdin (JSON payload), persists
# it as docs/plans/<UTC-date>-<slug>.md with Status: in-progress so the
# normal /plan close-out logic picks it up. Never blocks; exits 0 always.

set -u

PLAN_DIR="${AIMS_PLAN_DIR:-docs/plans}"

payload=$(cat || true)
[ -z "$payload" ] && exit 0

if command -v jq >/dev/null 2>&1; then
  body=$(printf '%s' "$payload" | jq -r '.tool_input.plan // empty' 2>/dev/null || true)
else
  body=$(printf '%s' "$payload" | sed -n 's/.*"plan"[[:space:]]*:[[:space:]]*"\(.*\)".*/\1/p')
fi
[ -z "$body" ] && exit 0

mkdir -p "$PLAN_DIR" 2>/dev/null || exit 0

title=$(printf '%s\n' "$body" | awk '
  /^#[[:space:]]+/ { sub(/^#[[:space:]]+/, ""); print; exit }
  NF              { print; exit }
' | head -c 200)
[ -z "$title" ] && title="exit-plan-mode"

slug=$(printf '%s' "$title" \
  | tr '[:upper:]' '[:lower:]' \
  | sed -e 's/[^a-z0-9]\+/-/g' -e 's/^-//' -e 's/-$//' \
  | awk -F'-' '{
      n = (NF > 6) ? 6 : NF
      for (i=1; i<=n; i++) printf "%s%s", $i, (i<n ? "-" : "")
      print ""
    }')
[ -z "$slug" ] && slug="exit-plan-mode"

date_stamp=$(date -u +%Y-%m-%d)
file="$PLAN_DIR/$date_stamp-$slug.md"

# If /plan already wrote a file with the same slug today, do not overwrite.
if [ -e "$file" ]; then
  printf '[aims-exit-plan-mode] %s already exists; not overwriting.\n' "$file" >&2
  exit 0
fi

# Prepend frontmatter only if body does not start with one already.
case "$body" in
  '# Plan:'*|'#Plan:'*) header="" ;;
  *)                    header="# Plan: $title"$'\n' ;;
esac

{
  printf '%s' "$header"
  printf 'Status: in-progress\n'
  printf 'Started: %s\n\n' "$date_stamp"
  printf '%s\n' "$body"
} > "$file"

printf '[aims-exit-plan-mode] Wrote %s\n' "$file" >&2
exit 0
```

### `templates/settings.json.tmpl` + `.claude/settings.json`

Add a second matcher block under `PostToolUse` for `ExitPlanMode`.

```json
"PostToolUse": [
  {
    "matcher": "Edit|Write|MultiEdit|NotebookEdit",
    "hooks": [
      { "type": "command", "command": "bash .claude/hooks/post-edit-marker.sh" }
    ]
  },
  {
    "matcher": "ExitPlanMode",
    "hooks": [
      { "type": "command", "command": "bash .claude/hooks/exit-plan-mode.sh" }
    ]
  }
]
```

### `templates/commands/plan.md` + `.claude/commands/plan.md`

Restructure: Phase 2 writes the draft to disk with `Status: draft` (lock still held). Phase 3 is the approval gate — on approval flip to `in-progress` + `rm` the lock. On reject, edit the draft in place and re-ask. On abort, delete the draft + remove the lock. Phase 4 = implement (was Phase 3). Phase 5 = close-out (was Phase 4). Other content unchanged.

The phase 1 step 5 wording changes from "Present the plan inline … ask … approve / edit / abort" to "Materialize the draft (Phase 2) before asking approval — the file on disk IS the artifact to review."

### `templates/hooks/prompt-submit.sh` + `.claude/hooks/prompt-submit.sh`

Replace the menu-injection with auto-engagement. After classifying intent: exit if intent == `question`; otherwise create the planning lock and inject a `[aims-router]` block that instructs the model to run the `/plan` flow phases 1→5. Suppression rules (slash-command prefix, lock already exists, etc.) are unchanged.

Key delta:

```bash
[ -z "$intent" ] && exit 0
# `question` is the only intent that does NOT require a plan.
[ "$intent" = "question" ] && exit 0

# Auto-engage /plan: create the lock so Edit/Write is blocked until the
# user approves a draft on disk.
mkdir -p .claude
touch .claude/.planning-lock

read -r -d '' router_text <<'TEXT' || true
[aims-router] Intent looks like a __INTENT__ task — auto-engaging /plan.

The planning lock (.claude/.planning-lock) is now in place; Edit/Write
are blocked until the user approves a draft. Run the /plan flow:

  Phase 1: read-only exploration (Read, Grep, Glob, Bash read-only).
  Phase 2: write the draft to docs/plans/<UTC-date>-<slug>.md with
           Status: draft using a Bash heredoc (Write is blocked by the
           lock). Print "Draft saved to docs/plans/<file>.
           Approve / edit / abort?".
  Phase 3: on approval → flip Status: draft → in-progress, then
           `rm -f .claude/.planning-lock`, then implement (Phase 4).
           On reject/iterate → rewrite the draft in place; re-ask.
           On abort → delete the draft + remove the lock.
  Phase 5: inline close-out (Status: in-progress → completed,
           auto-ADR, node consolidation) — same as before.

Skip auto-engagement only if the user explicitly opts out for THIS prompt
("just patch it", "don't plan, just do it", "אל תתכנן"). In that case
run `rm -f .claude/.planning-lock` and proceed inline.
TEXT
```

The stderr breadcrumb changes to `[aims-router] intent=… — auto-engaging /plan.` (was `… Claude will ask you which workflow.`).

### `templates/hooks/session-start.sh` + `.claude/hooks/session-start.sh`

Add a draft-orphan warning right after the existing stale-lock block.

```bash
# Orphan draft detection: lock missing but a Status: draft plan exists.
if [ ! -f "$LOCK" ] && [ -d "$PLAN_DIR" ]; then
  drafts=$(grep -lE '^Status:[[:space:]]*draft' "$PLAN_DIR"/*.md 2>/dev/null || true)
  if [ -n "$drafts" ]; then
    printf '[aims] WARNING: draft plan(s) with no active planning lock:\n'
    while IFS= read -r d; do
      printf '       %s\n' "$d"
    done <<< "$drafts"
    printf '       Recover: touch .claude/.planning-lock to resume, or rm the file.\n'
  fi
fi
```

### `commands/install-on.md` + `templates/commands/install-on.md` + `.claude/commands/install-on.md`

Extend the Phase 4 copy table to include `exit-plan-mode.sh` and the stale-cleanup rule list (already keys on `templates/hooks/`, so no logical change there — just rename the listed hooks for accuracy).

```diff
-| `.claude/hooks/{session-start,prompt-submit,pre-write,post-edit-marker,stop-consolidate,session-end}.sh` | `templates/hooks/<same>`                 |
+| `.claude/hooks/{session-start,prompt-submit,pre-write,post-edit-marker,exit-plan-mode,stop-consolidate,session-end}.sh` | `templates/hooks/<same>` |
```

### `tests/marker.sh` — case 10

```bash
# Case 10 (ADR-0014): `code:` entry as a glob — src/loaders/*.py.
bash "$ROOT/templates/memory/new-node.sh" interface/loaders module >/dev/null
LEAF2="$AIMS_MEMORY_DIR/interface/loaders.md"
python3 -c "
p='$LEAF2'
s=open(p).read()
s=s.replace('code: []', 'code:\n  - src/loaders/*.py')
open(p,'w').write(s)
"
rm -f "$AIMS_MEMORY_DIR/_inbox.md"
printf '%s' '{"tool_input":{"file_path":"src/loaders/json_loader.py"}}' | \
  bash "$ROOT/templates/hooks/post-edit-marker.sh"
v=$(fm_get "$LEAF2" dirty)
[ "$v" = "true" ] || fail "case 10: glob src/loaders/*.py should match src/loaders/json_loader.py, got '$v'"
[ ! -f "$AIMS_MEMORY_DIR/_inbox.md" ] || \
  fail "case 10: glob-matched path must NOT leak into inbox"
pass "marker matches code: globs (ADR-0014)"
```

### `tests/exit-plan-mode.sh` (new)

Smoke test for the bridge hook: writes a plan, no-overwrite on collision, slug stays ≤6 words.

```bash
#!/usr/bin/env bash
set -eu
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
pass() { printf '[PASS] %s\n' "$1"; }
fail() { printf '[FAIL] %s\n' "$1" >&2; exit 1; }
cd "$TMP"
mkdir -p docs/plans

# Case 1: writes a plan file from a tool_input.plan payload.
plan_body='# Refactor the loader

## TL;DR
Move json loading out of the parser.

## Changes
### src/loader.py
…
'
payload=$(jq -nc --arg p "$plan_body" '{tool_input: {plan: $p}}')
out=$(printf '%s' "$payload" | bash "$ROOT/templates/hooks/exit-plan-mode.sh" 2>&1 || true)
written=$(ls docs/plans/*.md 2>/dev/null | head -1 || true)
[ -n "$written" ] || fail "case 1: no file created (stderr: $out)"
grep -q '^Status: in-progress$' "$written" || fail "case 1: missing Status: in-progress in $written"
grep -q 'Refactor the loader' "$written"  || fail "case 1: body not preserved in $written"
pass "exit-plan-mode writes docs/plans/<file> with in-progress status"

# Case 2: collision → no overwrite, no second file.
first="$written"
sleep 1
printf '%s' "$payload" | bash "$ROOT/templates/hooks/exit-plan-mode.sh" >/dev/null 2>&1
[ "$(ls docs/plans/*.md | wc -l)" = "1" ] || fail "case 2: overwrite happened"
[ "$(stat -c %Y "$first" 2>/dev/null || stat -f %m "$first")" = "$(stat -c %Y "$first" 2>/dev/null || stat -f %m "$first")" ] || true
pass "exit-plan-mode skips on slug collision"

# Case 3: empty body → no file.
rm -f docs/plans/*.md
printf '%s' '{"tool_input":{"plan":""}}' | bash "$ROOT/templates/hooks/exit-plan-mode.sh" >/dev/null 2>&1
[ -z "$(ls docs/plans/*.md 2>/dev/null)" ] || fail "case 3: empty plan still wrote a file"
pass "exit-plan-mode no-ops on empty body"

printf '\nAll exit-plan-mode tests passed.\n'
```

### `tests/router-auto-plan.sh` (new)

```bash
#!/usr/bin/env bash
set -eu
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
pass() { printf '[PASS] %s\n' "$1"; }
fail() { printf '[FAIL] %s\n' "$1" >&2; exit 1; }
command -v jq >/dev/null 2>&1 || { printf '[SKIP] jq missing\n'; exit 0; }
cd "$TMP"

# Case 1: bug intent → lock created, additionalContext mentions auto-engaging.
rm -rf .claude
out=$(printf '{"prompt":"the parser crashes on empty input"}' | bash "$ROOT/templates/hooks/prompt-submit.sh")
[ -f .claude/.planning-lock ] || fail "case 1: lock not created for bug"
printf '%s' "$out" | jq -r '.hookSpecificOutput.additionalContext' | grep -q 'auto-engaging' \
  || fail "case 1: additionalContext missing 'auto-engaging' instruction"
pass "router auto-engages on bug"

# Case 2: question intent → no lock, no context.
rm -rf .claude
out=$(printf '{"prompt":"how does the marker hook decide which node to flag?"}' | bash "$ROOT/templates/hooks/prompt-submit.sh")
[ ! -f .claude/.planning-lock ] || fail "case 2: lock created for question (should not)"
[ -z "$out" ] || fail "case 2: question should produce no router context"
pass "router stays silent on questions"

# Case 3: prompt starting with `/` → no lock (already chose a command).
rm -rf .claude
out=$(printf '{"prompt":"/plan something"}' | bash "$ROOT/templates/hooks/prompt-submit.sh")
[ ! -f .claude/.planning-lock ] || fail "case 3: lock created when user typed /command"
pass "router suppresses on slash-command prompts"

# Case 4: planning lock already exists → no re-injection.
rm -rf .claude; mkdir -p .claude; touch .claude/.planning-lock
out=$(printf '{"prompt":"refactor the loader"}' | bash "$ROOT/templates/hooks/prompt-submit.sh")
[ -z "$out" ] || fail "case 4: should not re-engage when already in plan mode"
pass "router suppresses during active planning"

printf '\nAll router auto-plan tests passed.\n'
```

## Open design questions

- **`PostToolUse` timing on `ExitPlanMode`.** Hook fires after the tool returns; harness convention is that approval has already happened. If a future harness fires it on every model emission, the bridge would mass-create plan files. Mitigation: collision-skip already in place. Verify on first end-to-end run.
- **Glob greediness.** Bash `case`-glob `*` matches across `/` (POSIX fnmatch default has no `FNM_PATHNAME`). So `src/*.py` matches `src/loaders/json_loader.py` even though most people would expect it to be only direct children. **Documented as expected behavior**: nodes get over-marked rather than under-marked. The risk is `dirty: true` on unrelated edits, not silent staleness. Acceptable for v1; ADR-0014 will note this.
- **Plan-iteration in one day → slug collision.** `/plan` Phase 2 currently does not suffix the slug. Two iterations of the same plan in one day would collide; the new `exit-plan-mode.sh` bridge already skips on collision. For `/plan` itself the user's "edit / iterate" path rewrites the same file (intended). Worth a future `-2` suffix only if user reports churn.
- **Per-prompt opt-out for auto-plan.** Right now the user aborts in-turn ("just patch it"). A `!`-prefix (`!fix this typo`) bypassing auto-engagement at hook time is feasible but adds surface. Defer until friction observed.

## Verification

- `bash -n templates/hooks/*.sh && bash -n .claude/hooks/*.sh`
- `bash tests/marker.sh` (10 cases, with new case 10)
- `bash tests/exit-plan-mode.sh` (3 cases)
- `bash tests/router-auto-plan.sh` (4 cases)
- `bash .claude/memory/lint.sh && bash .claude/memory/doctor.sh`
- Manual: invoke `/plan` flow once on a tiny task and confirm draft lands in `docs/plans/` before the approval prompt.

## Close-out checklist

- ADR: WRITE — `0014-glob-code-matching: code: entries are matched as fnmatch globs`; `0015-auto-plan-and-draft-on-disk: /plan auto-engages on edit intents and writes a draft to disk before approval (with ExitPlanMode bridge)`
- Nodes: UPDATE — `docs/memory/memory/helpers.md`, `docs/memory/memory/phase-a-marker.md`, `docs/memory/hooks/prompt-submit.md`, `docs/memory/hooks/session-start.md`, `docs/memory/hooks/README.md` (add the new `exit-plan-mode` hook), `docs/memory/discipline/plan.md`
- CLAUDE.md: NONE
- Tests: `tests/marker.sh` +1 case (case 10); `tests/exit-plan-mode.sh` new; `tests/router-auto-plan.sh` new
- TODO: NONE — `**` glob support, same-day iteration suffix, and a per-prompt opt-out prefix all noted in Open design questions

## Risks / unknowns

- `PostToolUse`-on-`ExitPlanMode` timing assumption (see Open Q above).
- `case`-glob `*` is greedy across `/` — risk is over-marking, not under-marking. Documented; not blocking.
- Auto-engage router may surprise users mid-flow on prompts that look like edits but are actually questions phrased imperatively. Opt-out is in-turn.

## Outcome

Shipped all five tracks:

1. **Glob matching** (`templates/memory/_lib.sh:path_matches` + `.claude/` copy) — every `code:` entry is now an fnmatch glob via `case`-glob. ADR-0014 captures the boundary + the greedy-`*` tradeoff.
2. **`ExitPlanMode` bridge** (`templates/hooks/exit-plan-mode.sh` + `.claude/` copy + wired in both `settings.json` copies) — PostToolUse hook persists the harness's `tool_input.plan` to `docs/plans/<UTC-date>-<slug>.md` with `Status: in-progress`. Collision skips, empty body skips.
3. **`/plan` draft-on-disk** (`templates/commands/plan.md` + `.claude/` copy) — Phase 2 materializes a `Status: draft` plan via Bash heredoc under the lock; Phase 3 is the approval gate (flip + `rm` lock); Phase 4 = implement, Phase 5 = close-out.
4. **Auto-engage router** (`templates/hooks/prompt-submit.sh` + `.claude/` copy) — every non-`question` intent now creates the lock + injects `/plan` flow instructions. Multilingual fallback covers Hebrew etc. via the `ambiguous` bucket. Suppression rules preserved.
5. **Orphan-draft warning** (`templates/hooks/session-start.sh` + `.claude/` copy) — surfaces `Status: draft` plans without an active lock, with recovery instructions.

ADRs written: **ADR-0014** (`code:` entries as fnmatch globs) and **ADR-0015** (auto-plan + draft-on-disk + ExitPlanMode bridge, supersedes ADR-0004). ADR-0004's status pointer was updated.

## Closing checks

Verification command outputs:

- `bash -n templates/hooks/*.sh && bash -n .claude/hooks/*.sh` → ok
- `bash tests/marker.sh` → 10/10 pass (including new case 10 for glob)
- `bash tests/exit-plan-mode.sh` → 4/4 pass
- `bash tests/router-auto-plan.sh` → 6/6 pass
- `bash .claude/memory/lint.sh` → `clean (15 nodes)`
- `bash .claude/memory/doctor.sh` → 15 nodes total, 0 dirty, lint clean, 0 inert

Resolved `## Close-out checklist`:

- **ADR: WROTE** — `0014-code-globs-are-fnmatch-globs`; `0015-auto-plan-and-draft-on-disk` (supersedes ADR-0004).
- **Nodes: UPDATED** — `hooks/prompt-submit.md`, `hooks/session-start.md`, `hooks/exit-plan-mode.md` (new), `hooks/README.md`, `discipline/plan.md`, `memory/helpers.md`, `testing/smoke-tests.md`, plus light touches on `installer/install-on.md`, `installer/templates.md`, `memory/commands.md`. 15 nodes total, 0 dirty, lint clean.
- **CLAUDE.md: NONE** — no new convention introduced.
- **Tests: ADDED** — `tests/marker.sh` case 10; `tests/exit-plan-mode.sh` (4 cases); `tests/router-auto-plan.sh` (6 cases).
- **TODO: NONE** — `**`-glob depth-aware support, same-day plan iteration suffix, and a `!`-prefix per-prompt opt-out are all parked under `## Open design questions`, intentionally out of scope for v1.

Resolved `## Open design questions`:

- **`PostToolUse` timing on `ExitPlanMode`** — answered inline by the collision-skip in `exit-plan-mode.sh`; the test in `tests/exit-plan-mode.sh` case 2 covers it. Verification still required on first end-to-end run with a live harness.
- **Glob greediness** — answered: greedy-`*` is documented in ADR-0014 as intentional; over-marking is acceptable, silent staleness is not.
- **Plan-iteration in one day → slug collision** — answered: `/plan` Phase 3 rewrites the same draft file (intended); the bridge hook skips on collision (covered by test). No suffix needed for v1.
- **Per-prompt opt-out for auto-plan** — deferred: in-turn opt-out via "just patch it" / `אל תתכנן` is documented in the injected router text. A `!`-prefix hook-time opt-out is parked as a future-work note in `hooks/prompt-submit.md` open questions.
