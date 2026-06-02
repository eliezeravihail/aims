# Plan: aims ↔ The_secretary bidirectional integration
Status: draft
Started: 2026-06-02

## תקציר מנהלים

שילוב **דו-כיווני** בין `aims` ל-`/secretary` (`eliezeravihail/The_secretary`),
מינימלי ובעל ניוון-חיננית (graceful degradation) בשני הכיוונים.

**כיוון א' (aims → קורא secretary)** — נשמר ללא שינוי. hook ב-`SessionStart`
של aims קורא את `todo.md` ו-tail של הלוג היומי מתוך work-state dir של
secretary, כשהמיקום נקבע ע"י `SECRETARY_WORK_DIR` (env) או
`~/.secretary-work-dir` (dotfile). שתי השאלות הפתוחות הקודמות
(env-vs-dotfile, fallback פר-פרויקט) נסגרו: **env+dotfile, ללא fallback
פר-פרויקט ב-v1**.

**כיוון ב' (secretary → כותב ל-inbox פר-פרויקט של aims)** — חדש,
**מבוסס רישום מפורש** (לא היוריסטיקה). הזרימה:

1. `/install-on` בודק האם secretary מותקן אצל המשתמש (קובץ הסקיל
   הגלובלי `~/.claude/commands/secretary.md`). אם **כן ורק אם כן**, שואל
   פעם אחת ב-AskUserQuestion: *"לרשום את הפרויקט הזה אצל secretary?"*.
2. על **yes** install-on מוסיף ערך לקובץ רישום JSON
   `~/.config/the-secretary/aims-projects.json` (XDG; namespace של
   secretary). הסכמה: `{"schema_version": 1, "projects": [{...}]}` עם
   `project_root`, `inbox_path`, `claude_md`, `adr_index`,
   `registered_at`, `aims_version`. כתיבה אטומית (`*.tmp` + `mv`).
3. PR על `eliezeravihail/The_secretary` מלמד את secretary לקרוא את
   הרישום בפתיחת סשן: אם `cwd` (או אב שלו) מופיע ברישום — לטעון את
   `CLAUDE.md`, `docs/adr/README.md`, ותכניות `Status: in-progress` של
   הפרויקט הרשום, ולכתוב הצעות ל-`inbox_path` כפי שמוגדר ברישום.
4. **ההיוריסטיקה הקודמת בוטלה** (`grep -q aims session-start.sh` —
   ירדה). רישום מפורש מחליף אותה לחלוטין; המשתמש שולט.

עיבוד ההצעות נשאר אצל המשתמש — aims רק מציג ספירת unread ב-SessionStart
(לא תוכן). secretary לעולם אינו עורך ADRs, CLAUDE.md, plans או memory
nodes ישירות. הזרימה מכבדת את חוק היסוד של aims: **שינוי-state רק
לאחר אישור המשתמש**.

ה-PR על secretary הוא **deliverable כתוכן בלבד** (קטעי קוד בתוך §B3 של
תכנית זו), לא כפעולה — סביבת התכנון הזו מוגבלת ל-`eliezeravihail/aims`.

## Goal

aims sessions begin with awareness of (1) the user's active personal-secretary
tasks for the day, and (2) any new suggestions secretary has dropped into the
project's inbox — without coupling either tool to the other's presence,
without blocking any edit, and without secretary ever mutating aims state
directly. Discovery of "which projects are aims-managed" is **explicit**: the
user opts each project in at install-time via a single AskUserQuestion. The
user remains the only actor who turns a suggestion into an ADR, a plan TODO,
or a memory update.

## Decision

### Direction A — aims reads secretary at SessionStart (unchanged from v2)

A new helper `templates/hooks/lib/secretary-context.sh` resolves the
secretary work-state directory:

1. `$SECRETARY_WORK_DIR` (env var) — **wins**.
2. First non-blank line of `~/.secretary-work-dir` — **fallback**.
3. Nothing — silent.

When found, it reads the head of `todo.md` (cap 1500B) and the tail of
today's `daily/YYYY-MM/YYYY-MM-DD.md` (cap 800B; falls back to the most
recent daily log if today's doesn't exist). Emits a single
`[aims-secretary]` block. The session-start hook sources it last so a
failure cannot perturb earlier output. A debug-only line
`===[aims: secretary unreachable]===` may be emitted on the helper side
when `AIMS_SECRETARY_DEBUG=1` (matches ADR-0021's reply-marker shape).

**Resolved (previously open):**
- *env vs dotfile vs both?* → **both** (env first, dotfile fallback).
- *fall back to per-project secretary.md grep?* → **no, not in v1**.

### Direction B redesigned — explicit registry (replaces v2's heuristic)

v2's `grep -q aims session-start.sh` heuristic is **deleted**. It was
fragile in both directions (false-pos on any copy-cat project; false-neg
on heavily customized installs) and surprising to the user (silent
behavior change based on file contents). v3 replaces it with an
**explicit registry** the user populates at install-time.

#### Detection check — "is secretary installed on this machine?"

**Pinned single check:**

```bash
[ -f "$HOME/.claude/commands/secretary.md" ]
```

**Justification.** secretary is distributed as a Claude Code slash
command, not a CLI binary. Its README (`Option A — Global`) instructs
copying the skill file to exactly `~/.claude/commands/secretary.md`.
There is no `~/.config/the-secretary/`, no `~/.the-secretary/`, no
installer, no binary; the skill file is the only signal. Pinning to one
check (rather than OR-ing with per-project copies under
`<TARGET>/.claude/commands/secretary.md`) is deliberate: the registry is
a **per-user** artifact, not a per-project one, so the per-user install
is the right gate.

#### Registry path and schema

**Path:** `~/.config/the-secretary/aims-projects.json`

XDG-compliant; lives under a directory clearly in secretary's namespace
(`the-secretary` matches the GitHub repo's slug). secretary has **no**
existing config-directory convention (config lives inline in the skill
file via auto-filled `work_state_dir: <path>` lines), so we are free to
pick — and an XDG dir avoids cluttering `$HOME`. The PR on secretary
(§B3) creates the directory lazily on first read attempt; install-on
creates it lazily on first write.

**Schema (top-level dict for forward-compat):**

```json
{
  "schema_version": 1,
  "projects": [
    {
      "project_root": "/home/avi/work/aims",
      "registered_at": "2026-06-02T14:31:07Z",
      "claude_md": "/home/avi/work/aims/CLAUDE.md",
      "adr_index": "/home/avi/work/aims/docs/adr/README.md",
      "inbox_path": "/home/avi/work/aims/docs/inbox/secretary-suggestions.md",
      "aims_version": "git:abc1234"
    }
  ]
}
```

Unknown top-level keys and unknown per-entry keys MUST be ignored by
readers (forward-compat: lets us add fields without a schema bump).
`claude_md` and `adr_index` may be `null` if missing at registration
time. `aims_version` is a git short-sha when aims is checked out from
git; otherwise the string `"unknown"`.

#### Append discipline — read-modify-write, atomic

The registry is JSON, not line-append. install-on uses `jq` when
available and falls back to `python3` (one of the two is universally
present on aims-supported platforms; aims is jq-optional per CLAUDE.md).
Write is atomic: write to `<registry>.tmp` then `mv` over the original.

#### Idempotency

If the project's `project_root` already exists in the registry,
install-on offers **update** (refresh `inbox_path`, `aims_version`,
`registered_at`) or **skip** via AskUserQuestion — never a blind
duplicate append.

#### Removal

Not in v1. If the user uninstalls aims from a project (or deletes the
directory), the registry entry stays; secretary looks up
`project_root`, finds nothing useful, and proceeds as for any
non-registered cwd. Documented in `## Risks`.

#### `/install-on` UX flow (additive)

A new Phase **3.5** ("Optional: register with secretary") inserted
between existing Phase 3 (show planned changes + approval gate) and
Phase 4 (apply). The phase number is pinned: 3.5 — between approval and
apply — so the registry write is gated by the same approval the user
already gave, but its question is asked only after the user has said
"yes, install" (avoiding a question they'd want to abandon if they're
about to abort the install).

If `[ ! -f "$HOME/.claude/commands/secretary.md" ]` → skip Phase 3.5
silently. install-on emits no question and no marker.

If secretary detected → AskUserQuestion with three options:

- `yes` — register this project (write/update registry entry).
- `no` — skip registration.
- `show details` — print a one-screen explanation of what gets
  written and where, then re-ask yes/no.

On `yes`-write success: emit single line `===[aims: registered with
secretary]===` (or `===[aims: secretary registration updated]===` on
idempotent update path). Matches ADR-0021's reply-marker convention.

### Direction B side of aims — surface unread count at SessionStart

**Unchanged from v2.** The aims SessionStart hook gains a block that
counts entries (lines matching `^## `) in
`docs/inbox/secretary-suggestions.md` and emits a single
`[aims-secretary] N unread suggestion(s)` line. Never dumps entry
content. Triage is the user opening the file. No `/secretary-inbox`
command in v1 (deferred).

### Why this shape

- **Boundary preserved.** secretary still never mutates aims state —
  the inbox is a proposal surface. The "user approves before aims
  state changes" invariant holds.
- **Explicit > implicit.** Registry replaces fingerprint — the user
  *consents* per-project. No surprise behavior based on file contents.
- **Mirrors `_inbox.md`.** Same shape as memory inbox: append-only,
  one entry per heading, processing is removal.
- **Graceful in both directions.**
  - secretary not installed: install-on asks nothing, registry never
    created.
  - aims project not registered: secretary's registry lookup misses,
    behaves as today.
  - Registry file absent: secretary treats as empty list, behaves as
    today.
  - Inbox file absent: SessionStart's count block is skipped silently.
- **No new toolchain.** Bash + (`jq` OR `python3`).

### Rejected directions

- **Heuristic fingerprint** (v2): too fragile, surprising. Replaced.
- **Shared context layer** (third artifact maintained by both tools):
  YAGNI.
- **secretary writes directly into `docs/adr/`, `CLAUDE.md`, …**:
  violates user-approves invariant.
- **aims auto-ingests inbox entries on close-out**: same reason.
- **Removal flow in v1**: deferred — stale registry entries cost nothing.

## Changes

### A. `templates/hooks/lib/secretary-context.sh` — NEW (unchanged from v2)

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

set -u

emit_unreachable() {
  [ "${AIMS_SECRETARY_DEBUG:-0}" = "1" ] || return 0
  printf '===[aims: secretary unreachable: %s]===\n' "$1"
}

work_dir="${SECRETARY_WORK_DIR:-}"
if [ -z "$work_dir" ] && [ -r "$HOME/.secretary-work-dir" ]; then
  work_dir=$(awk 'NF{print; exit}' "$HOME/.secretary-work-dir" 2>/dev/null || true)
fi
if [ -z "$work_dir" ]; then
  emit_unreachable "no SECRETARY_WORK_DIR and no ~/.secretary-work-dir"
  exit 0
fi
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

### A2. `templates/hooks/session-start.sh` — APPEND TWO blocks before `exit 0` (unchanged from v2)

```bash
# --- Personal-secretary context (Direction A; aims↔secretary, ADR-0024). ---
# Read secretary's work-state dir read-only. Helper exits 0 on any failure.
SECRETARY_LIB=""
if   [ -r ".claude/hooks/lib/secretary-context.sh" ];   then SECRETARY_LIB=".claude/hooks/lib/secretary-context.sh"
elif [ -r "templates/hooks/lib/secretary-context.sh" ]; then SECRETARY_LIB="templates/hooks/lib/secretary-context.sh"
fi
if [ -n "$SECRETARY_LIB" ]; then
  bash "$SECRETARY_LIB" 2>/dev/null || true
fi

# --- Secretary suggestions inbox (Direction B; aims↔secretary, ADR-0024). ---
INBOX_FILE="docs/inbox/secretary-suggestions.md"
if [ -r "$INBOX_FILE" ]; then
  n=$(grep -c '^## ' "$INBOX_FILE" 2>/dev/null || echo 0)
  if [ "$n" -gt 0 ]; then
    if [ "$n" -eq 1 ]; then
      printf '[aims-secretary] 1 unread suggestion in %s\n' "$INBOX_FILE"
    else
      printf '[aims-secretary] %d unread suggestions in %s\n' "$n" "$INBOX_FILE"
    fi
  fi
fi
```

(Inserted at the bottom of the file, just before `exit 0`. Both blocks
independent.)

### A3. `.claude/hooks/lib/secretary-context.sh` and `.claude/hooks/session-start.sh` — MIRROR

```bash
mkdir -p .claude/hooks/lib
cp templates/hooks/lib/secretary-context.sh .claude/hooks/lib/secretary-context.sh
cp templates/hooks/session-start.sh         .claude/hooks/session-start.sh
chmod +x .claude/hooks/lib/secretary-context.sh
```

Or `/install-on .`.

### A4. `templates/commands/install-on.md` — copy `lib/` (unchanged from v2)

```diff
 | `.claude/hooks/{session-start,prompt-submit,pre-write,post-edit-marker,exit-plan-mode,stop-consolidate,session-end}.sh` | `templates/hooks/<same>` |
+| `.claude/hooks/lib/secretary-context.sh` | `templates/hooks/lib/secretary-context.sh` |
```

And:

```diff
-After copy: `chmod +x TARGET/.claude/hooks/*.sh TARGET/.claude/memory/*.sh`.
+After copy: `chmod +x TARGET/.claude/hooks/*.sh TARGET/.claude/hooks/lib/*.sh TARGET/.claude/memory/*.sh`.
```

### B1. `templates/commands/install-on.md` AND `commands/install-on.md` — additive Phase 3.5 for secretary registration

**Both files receive the same patch verbatim.** The byte-identical
invariant from `docs/memory/installer/install-on.md` is honored: this
patch must be applied **once and identically** to each of:

- `/home/user/aims/templates/commands/install-on.md`
- `/home/user/aims/commands/install-on.md`

(Pre-existing note: as of v3 draft time, these two files already differ
slightly — the global has summary-lang Phase content the template
lacks. That pre-existing divergence is **out of scope for this plan**
and tracked separately; this plan only adds the Phase 3.5 section,
identically to both copies.)

The patch inserts a new section between existing `## Phase 3 — Show
planned changes per class` and `## Phase 4 — Apply` headings:

```markdown
## Phase 3.5 — Optional: register with secretary

Only runs if Phase 3 approval was given.

Detect whether [The_secretary](https://github.com/eliezeravihail/The_secretary)
is installed on this machine:

```bash
[ -f "$HOME/.claude/commands/secretary.md" ]
```

**If the file does not exist** — skip this entire phase silently. Emit
no question, no marker, no registry file.

**If the file exists** — ask the user (AskUserQuestion):

> *Register this project with secretary? secretary will then load this
> project's `CLAUDE.md`, ADR index, and in-progress plans as context
> when opened in this directory, and may append suggestions to
> `docs/inbox/secretary-suggestions.md`.*
>
> 1. `yes` — register.
> 2. `no` — skip.
> 3. `show details` — print what gets written and where, then re-ask.

If `show details` — print:

```
Registry file: ~/.config/the-secretary/aims-projects.json
Entry added:
  project_root: <TARGET absolute path>
  inbox_path:   <TARGET>/docs/inbox/secretary-suggestions.md
  claude_md:    <TARGET>/CLAUDE.md          (or null if absent)
  adr_index:    <TARGET>/docs/adr/README.md (or null if absent)
  registered_at: <current UTC ISO timestamp>
  aims_version: <git short-sha of aims source, or "unknown">

Nothing else is written. Registry is read-only by aims after this;
secretary reads it at session-open.
```

…then re-ask the yes/no question.

**On `no`** — skip. No marker emitted.

**On `yes`** — read-modify-write the registry:

```bash
REG="$HOME/.config/the-secretary/aims-projects.json"
mkdir -p "$(dirname "$REG")"
[ -f "$REG" ] || printf '{"schema_version": 1, "projects": []}\n' > "$REG"

# Compose the new entry.
PROOT="$(cd "$TARGET" && pwd)"
NOW="$(date -u +%FT%TZ)"
CMD_PATH="$PROOT/CLAUDE.md";       [ -f "$CMD_PATH" ] || CMD_PATH=""
ADR_PATH="$PROOT/docs/adr/README.md"; [ -f "$ADR_PATH" ] || ADR_PATH=""
INBOX="$PROOT/docs/inbox/secretary-suggestions.md"
AIMS_VER="$(git -C "$AIMS_ROOT" rev-parse --short HEAD 2>/dev/null || echo unknown)"
[ -n "$AIMS_VER" ] || AIMS_VER=unknown

# Read-modify-write atomically. Prefer jq; fall back to python3.
TMP="$REG.tmp"
if command -v jq >/dev/null 2>&1; then
  jq --arg pr "$PROOT" --arg now "$NOW" \
     --arg cmd "$CMD_PATH" --arg adr "$ADR_PATH" \
     --arg ibx "$INBOX" --arg ver "$AIMS_VER" '
    .projects |= (
      map(select(.project_root != $pr))
      + [{
          project_root:  $pr,
          registered_at: $now,
          claude_md:     (if $cmd == "" then null else $cmd end),
          adr_index:     (if $adr == "" then null else $adr end),
          inbox_path:    $ibx,
          aims_version:  $ver
        }]
    )
  ' "$REG" > "$TMP" && mv "$TMP" "$REG"
else
  python3 - "$REG" "$TMP" "$PROOT" "$NOW" "$CMD_PATH" "$ADR_PATH" "$INBOX" "$AIMS_VER" <<'PY'
import json, sys, os
reg, tmp, pr, now, cmd, adr, ibx, ver = sys.argv[1:]
with open(reg) as f: data = json.load(f)
data.setdefault("schema_version", 1)
data.setdefault("projects", [])
data["projects"] = [p for p in data["projects"] if p.get("project_root") != pr]
data["projects"].append({
    "project_root":  pr,
    "registered_at": now,
    "claude_md":     cmd or None,
    "adr_index":     adr or None,
    "inbox_path":    ibx,
    "aims_version":  ver,
})
with open(tmp, "w") as f: json.dump(data, f, indent=2)
os.replace(tmp, reg)
PY
fi
```

Idempotency: the `map(select(... != $pr)) + [new]` (or its python
equivalent) **replaces** any existing entry for the same
`project_root`. If a prior entry existed, emit:

```
===[aims: secretary registration updated]===
```

Otherwise:

```
===[aims: registered with secretary]===
```

(Detect "prior entry existed" by `jq '.projects | map(.project_root) |
index($pr)' "$REG"` BEFORE the write, or the python equivalent.)

Concurrency: writing through `$REG.tmp` + `mv` is atomic on POSIX. If a
second install-on session writes between our read and our `mv`, that
session's entry will be overwritten by ours. This is a known
limitation; install-on runs are interactive and effectively serial in
practice. See `## Risks`.

Phase 3.5 does NOT block Phase 4. On any failure (jq+python3 both
missing, write permission denied, etc.) emit a single
`===[aims: secretary registration failed: <reason>]===` line and
continue to Phase 4. The aims install is unaffected.
```

### B2. Registry schema and example

**Path:** `~/.config/the-secretary/aims-projects.json`

**Schema (`schema_version: 1`):**

```json
{
  "schema_version": 1,
  "projects": [
    {
      "project_root": "/home/avi/work/aims",
      "registered_at": "2026-06-02T14:31:07Z",
      "claude_md": "/home/avi/work/aims/CLAUDE.md",
      "adr_index": "/home/avi/work/aims/docs/adr/README.md",
      "inbox_path": "/home/avi/work/aims/docs/inbox/secretary-suggestions.md",
      "aims_version": "git:abc1234"
    },
    {
      "project_root": "/home/avi/work/other-aims-project",
      "registered_at": "2026-06-03T09:12:00Z",
      "claude_md": "/home/avi/work/other-aims-project/CLAUDE.md",
      "adr_index": null,
      "inbox_path": "/home/avi/work/other-aims-project/docs/inbox/secretary-suggestions.md",
      "aims_version": "unknown"
    }
  ]
}
```

**Field semantics:**

- `project_root` — absolute path. Lookup key. Unique within `projects[]`.
- `registered_at` — ISO 8601 UTC. Refreshed on update.
- `claude_md`, `adr_index` — absolute paths or `null`. secretary reads
  these as context if present and non-null.
- `inbox_path` — absolute path. secretary appends suggestions here.
- `aims_version` — git short-sha (`"git:abc1234"`) or `"unknown"`.

**Reader contract:** unknown top-level keys and unknown per-entry keys
MUST be ignored. New fields may be added in `schema_version: 1` without
a bump; only **breaking** changes (rename, remove, semantic change of
an existing key) bump to `schema_version: 2`.

### B3. PR on `eliezeravihail/The_secretary` — content (to be applied manually)

> **Note:** PR deliverable as content; this planning environment is
> restricted to `eliezeravihail/aims`. Once merged, link the PR URL
> into ADR-0024.

#### B3.1. Edit `.claude/commands/secretary.md` — add a new section

Insert between **Procedures** and **Boundaries**:

```markdown
## aims-managed projects (optional integration)

If the current working directory matches a project listed in the aims
registry (`~/.config/the-secretary/aims-projects.json`), this section
governs two additional behaviors. If the registry is missing, empty,
or contains no matching entry — ignore this entire section.

### Registry lookup at session-open

In addition to the normal Procedures (`Session open`), also run:

```bash
REG="$HOME/.config/the-secretary/aims-projects.json"
CWD="$(pwd)"
MATCH=""
if [ -r "$REG" ]; then
  if command -v jq >/dev/null 2>&1; then
    # Find the registry entry whose project_root is $CWD or an ancestor of $CWD.
    MATCH=$(jq -r --arg cwd "$CWD" '
      .projects // []
      | map(select(
          .project_root == $cwd
          or ($cwd | startswith(.project_root + "/"))
        ))
      | sort_by(.project_root | length) | reverse  # most-specific wins
      | (.[0] // empty) | @json
    ' "$REG")
  else
    MATCH=$(python3 - "$REG" "$CWD" <<'PY'
import json, sys, os
reg, cwd = sys.argv[1], sys.argv[2]
try:
    with open(reg) as f: d = json.load(f)
except Exception: sys.exit(0)
hits = [p for p in d.get("projects", [])
        if p.get("project_root") == cwd
        or cwd.startswith(p.get("project_root","") + "/")]
hits.sort(key=lambda p: len(p["project_root"]), reverse=True)
if hits: print(json.dumps(hits[0]))
PY
)
  fi
fi

if [ -n "$MATCH" ] && [ "$MATCH" != "null" ]; then
  # Extract paths and read context, suppressing errors.
  CLAUDE_MD=$(printf '%s' "$MATCH" | jq -r '.claude_md // empty' 2>/dev/null \
              || printf '%s' "$MATCH" | python3 -c 'import sys,json;d=json.load(sys.stdin);print(d.get("claude_md") or "")')
  ADR_IDX=$(printf '%s' "$MATCH"   | jq -r '.adr_index // empty' 2>/dev/null \
              || printf '%s' "$MATCH" | python3 -c 'import sys,json;d=json.load(sys.stdin);print(d.get("adr_index") or "")')
  PROOT=$(printf '%s' "$MATCH"     | jq -r '.project_root' 2>/dev/null \
              || printf '%s' "$MATCH" | python3 -c 'import sys,json;print(json.load(sys.stdin)["project_root"])')

  [ -n "$CLAUDE_MD" ] && [ -r "$CLAUDE_MD" ] && cat "$CLAUDE_MD"
  [ -n "$ADR_IDX" ]   && [ -r "$ADR_IDX" ]   && cat "$ADR_IDX"
  for p in "$PROOT"/docs/plans/*.md; do
    [ -r "$p" ] || continue
    head -10 "$p" | grep -qE '^Status:\s*in-progress' && cat "$p"
  done
fi
```

Hold these as session context. Do not summarize them aloud unless asked.

### Appending suggestions

When the conversation surfaces something that belongs in the project's
planning record — a recurring principle, a follow-up task, a note —
**do not** edit ADRs, CLAUDE.md, plans, or memory nodes. Instead, look
up the matched registry entry's `inbox_path` and append an entry:

```bash
INBOX=$(printf '%s' "$MATCH" | jq -r '.inbox_path' 2>/dev/null \
         || printf '%s' "$MATCH" | python3 -c 'import sys,json;print(json.load(sys.stdin)["inbox_path"])')
mkdir -p "$(dirname "$INBOX")"
NOW="$(date -u +%FT%TZ)"
cat >> "$INBOX" <<EOF

## $NOW — <short title>
source: secretary
kind: principle | task | note
cwd: $(pwd)

<prose body — one short paragraph, or a small bullet list>
EOF
```

Concrete entry example:

````markdown
## 2026-06-02T15:31:07Z — Bound retry loops by elapsed time, not count
source: secretary
kind: principle
cwd: /home/avi/work/aims

The user repeatedly hit cases where retry-by-count masked a stuck
upstream. Suggest a small principle in CLAUDE.md or a new ADR:
"Retry budgets are wall-clock-bounded, not count-bounded."
````

Append-only; never edit existing entries; never overwrite. Triage is
the user's job; Secretary's role ends at appending.

### Backwards-compatibility

If `~/.config/the-secretary/aims-projects.json` is absent, unreadable,
empty, or has no entry matching the current cwd — skip this entire
section. Secretary behaves exactly as it does for any non-aims project.

### Boundary

Secretary writes **only** to the registry entry's `inbox_path`. It must
never edit any of:

- `<project_root>/docs/adr/**`
- `<project_root>/CLAUDE.md`
- `<project_root>/docs/plans/**`
- `<project_root>/docs/memory/**`
- `<project_root>/.claude/**`
- The registry file itself (`~/.config/the-secretary/aims-projects.json`)

These belong to the user, to aims, and to install-on. The inbox is the
only write surface secretary has on the project side.
```

#### B3.2. Append a one-liner to `README.md`

```diff
 - Integrates with **Slack** (reading and summarising conversations)
+- Integrates with **[aims](https://github.com/eliezeravihail/aims)** projects via an opt-in registry (`~/.config/the-secretary/aims-projects.json`, populated by aims' `/install-on`): read-only context + append-only suggestion inbox
 - Optionally tracks **experiment results** (`measures.md`) — stripped at setup if not needed
```

#### B3.3. Backwards-compat note

No existing behavior changes. With no registry file or no matching
entry, the new section is fully inert. No new config keys in
`secretary.md`'s Config section.

### C. `README.md` (aims side) — expanded subsection under "Hooks"

```markdown
### Optional: The_secretary integration (bidirectional)

aims interoperates with [`The_secretary`](https://github.com/eliezeravihail/The_secretary)
in two directions; both gracefully degrade to no-ops if the other tool
isn't installed.

**aims → secretary (read-only).** aims' `session-start` hook can surface
secretary's current `todo.md` head + most recent daily-log tail. Point
aims at secretary's work-state directory with **either**:

```sh
export SECRETARY_WORK_DIR=/path/to/your/work-state
# …or:
echo /path/to/your/work-state > ~/.secretary-work-dir
```

If neither is set, the hook stays silent. Read-only; aims never writes
into secretary's work-state directory.

**secretary → aims (opt-in registry).** When `/install-on` detects
secretary is installed (`~/.claude/commands/secretary.md` exists), it
asks once whether to register the project. On `yes`, an entry is added
to `~/.config/the-secretary/aims-projects.json` naming this project's
`CLAUDE.md`, ADR index, and inbox path. secretary then loads that
context at session-open and may append suggestions to
`docs/inbox/secretary-suggestions.md`. Unregistered projects see no
change in either tool's behavior.

**Triage is manual.** Open `docs/inbox/secretary-suggestions.md`,
decide per entry: write an ADR, add a TODO to an active plan, fold
into a memory node, or delete the entry. (Same user-approves invariant
that gates plan Phase 4.)
```

### D. `docs/adr/00NN-aims-secretary-integration.md` — NEW ADR (close-out)

Status `proposed` at close-out. Number expected: **0024**. Records:

- Cross-tool contract: env+dotfile (aims→secretary); **explicit
  registry** (`~/.config/the-secretary/aims-projects.json`) +
  append-only inbox (secretary→aims).
- Detection check pinned: `[ -f "$HOME/.claude/commands/secretary.md" ]`.
- Registry schema (v1) and the forward-compat rule.
- Path-matching rule: ancestor match, most-specific wins.
- User-approves invariant.
- Graceful-degrade rules.
- Open: `/secretary-inbox` triage command — deferred.

### E. `tests/secretary-integration.sh` — NEW (smoke test, jq-free)

Covers Direction A (helper cases 1–3), Direction B inbox-count
(cases 4–5), and Direction B registry-write **shape** (case 6 — purely
file-based: simulate "user picked yes" by invoking the registry-write
bash directly with synthetic env vars and assert the registry file
parses and contains the expected `project_root`).

```bash
#!/usr/bin/env bash
set -u
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
HELPER=templates/hooks/lib/secretary-context.sh
HOOK=templates/hooks/session-start.sh

# --- Direction A ---
unset SECRETARY_WORK_DIR
out=$(HOME="$TMP" bash "$HELPER" 2>/dev/null || true)
[ -z "$out" ] || { echo "FAIL: silent case"; exit 1; }

mkdir -p "$TMP/ws/daily/$(date -u +%Y-%m)"
printf '# Tasks\n- [ ] x\n' > "$TMP/ws/todo.md"
printf '# %s\nentry\n' "$(date -u +%Y-%m-%d)" \
  > "$TMP/ws/daily/$(date -u +%Y-%m)/$(date -u +%Y-%m-%d).md"
out=$(SECRETARY_WORK_DIR="$TMP/ws" bash "$HELPER" 2>/dev/null || true)
echo "$out" | grep -q '\[aims-secretary\]' \
  || { echo "FAIL: populated case"; exit 1; }

out=$(SECRETARY_WORK_DIR=/nonexistent bash "$HELPER" 2>/dev/null; echo "rc=$?")
echo "$out" | grep -q 'rc=0' || { echo "FAIL: broken path"; exit 1; }

# --- Direction B inbox count ---
PROJ="$TMP/proj"; mkdir -p "$PROJ/docs/inbox"
cp "$HOOK" "$PROJ/session-start.sh"
cat > "$PROJ/docs/inbox/secretary-suggestions.md" <<'EOF'
## 2026-06-02T10:00:00Z — a
source: secretary
kind: note

x
## 2026-06-02T11:00:00Z — b
source: secretary
kind: principle

y
EOF
out=$(cd "$PROJ" && bash session-start.sh 2>/dev/null || true)
echo "$out" | grep -q '\[aims-secretary\] 2 unread suggestions' \
  || { echo "FAIL: count line: $out"; exit 1; }

rm "$PROJ/docs/inbox/secretary-suggestions.md"
out=$(cd "$PROJ" && bash session-start.sh 2>/dev/null || true)
echo "$out" | grep -q 'unread suggestion' \
  && { echo "FAIL: emitted inbox line when absent"; exit 1; }

# --- Direction B registry write (shape only) ---
REG="$TMP/aims-projects.json"
printf '{"schema_version": 1, "projects": []}\n' > "$REG"
PROOT="$PROJ"
NOW="2026-06-02T00:00:00Z"
INBOX="$PROOT/docs/inbox/secretary-suggestions.md"
if command -v jq >/dev/null 2>&1; then
  jq --arg pr "$PROOT" --arg now "$NOW" --arg ibx "$INBOX" '
    .projects += [{project_root:$pr, registered_at:$now,
                   claude_md:null, adr_index:null,
                   inbox_path:$ibx, aims_version:"test"}]' \
    "$REG" > "$REG.tmp" && mv "$REG.tmp" "$REG"
  jq -r '.projects[].project_root' "$REG" | grep -Fxq "$PROOT" \
    || { echo "FAIL: registry entry missing"; exit 1; }
elif command -v python3 >/dev/null 2>&1; then
  python3 - "$REG" "$PROOT" "$NOW" "$INBOX" <<'PY'
import json, sys
reg, pr, now, ibx = sys.argv[1:]
with open(reg) as f: d = json.load(f)
d["projects"].append({"project_root":pr,"registered_at":now,
  "claude_md":None,"adr_index":None,"inbox_path":ibx,"aims_version":"test"})
with open(reg,"w") as f: json.dump(d,f)
PY
  python3 -c "import json,sys;d=json.load(open('$REG'));assert any(p['project_root']=='$PROOT' for p in d['projects'])" \
    || { echo "FAIL: registry entry missing"; exit 1; }
fi

echo PASS
```

## Open design questions

1. **Registry path.** Default: `~/.config/the-secretary/aims-projects.json`
   (XDG-compliant; secretary's namespace). secretary has **no** existing
   config-directory convention, so we're free to pick. **Override only if
   you prefer a different location** (e.g. `~/.the-secretary/projects.json`
   matching a future dotfile dir).

2. **Path-matching for registry lookup.** Default: **ancestor match,
   most-specific wins** (secretary's session opened in any subdir of a
   registered project matches; nested registered projects pick the
   deepest). Alternative: strict `cwd == project_root`. Ancestor match
   is more useful in practice; strict is more predictable. **Confirm or
   override.**

3. **What aims tells the user when it asks the registration question.**
   Default: yes/no with a `show details` third option that prints what
   gets written and where, then re-asks yes/no. Alternative: just
   yes/no, no details option. Default keeps the user informed without
   forcing them through a wall of text. **Confirm or override.**

## Verification

- `bash -n templates/hooks/*.sh templates/hooks/lib/*.sh && bash -n .claude/hooks/*.sh .claude/hooks/lib/*.sh`
- `bash tests/secretary-integration.sh` → `PASS`.
- `bash tests/inform-never-block.sh` → still passes.
- `bash tests/router-auto-plan.sh` → still passes.
- **Manual A — secretary absent**: `SECRETARY_WORK_DIR` unset and no
  `~/.secretary-work-dir`; SessionStart emits no `[aims-secretary]` line.
- **Manual A — secretary present**: `SECRETARY_WORK_DIR=/tmp/ws-fake`
  pre-seeded; helper's block appears.
- **Manual B (registry, secretary detected, user says `yes`)**:
  pre-seed `~/.claude/commands/secretary.md` (any contents); run
  `/install-on .` on a fresh aims target; pick `yes` at Phase 3.5;
  confirm:
  ```sh
  jq -r '.projects[].project_root' ~/.config/the-secretary/aims-projects.json \
    | grep -Fxq "$(pwd)"
  ```
  (or `python3 -c "import json;d=json.load(open(...));print(any(p['project_root']=='...' for p in d['projects']))"`)
  AND that `===[aims: registered with secretary]===` appeared.
- **Manual B (registry, secretary detected, user says `no`)**: the
  registry file is unchanged (or, if it didn't exist, still does not).
- **Manual B (secretary not installed)**: `rm
  ~/.claude/commands/secretary.md` (or never installed); run
  `/install-on .`; confirm **no** registration question asked and no
  registry file created.
- **Manual B (idempotency)**: re-run `/install-on .` on a project
  already in the registry; AskUserQuestion offers update/skip; on
  update, the entry is replaced (not duplicated) and
  `===[aims: secretary registration updated]===` is emitted. Verify
  with `jq '.projects | length'` — count unchanged.
- **Manual B — inbox count**: append a fake entry to
  `docs/inbox/secretary-suggestions.md`; confirm
  `[aims-secretary] 1 unread suggestion …`.
- **Cross-repo — PR applied**: PR on `eliezeravihail/The_secretary`
  merged. Either:
  ```sh
  curl -sf https://raw.githubusercontent.com/eliezeravihail/The_secretary/main/.claude/commands/secretary.md \
    | grep -q '## aims-managed projects'
  ```
  Once merged, paste PR URL into ADR-0024.

## Close-out checklist

- **ADR**: WRITE — `0024-aims-secretary-integration.md`. Clear
  architectural commitment: env+dotfile (aims→secretary); explicit
  registry (secretary→aims); detection check pinned; schema v1 +
  forward-compat rule; ancestor match; user-approves invariant
  explicitly recorded.
- **Nodes**: UPDATE — `docs/memory/hooks/session-start.md` (reads
  external state via helper + surfaces inbox count). UPDATE —
  `docs/memory/installer/install-on.md` (now writes the secretary
  registry in optional Phase 3.5). CONSIDER NEW —
  `docs/memory/integration/secretary.md` if a triage command or
  removal flow lands later. v1: append to the two existing nodes.
- **CLAUDE.md**: UPDATE — add **"External integrations"** subsection
  naming The_secretary, the env+dotfile contract (Direction A), the
  registry path + schema v1 (Direction B), and the
  user-approves-before-aims-state-changes invariant.
- **Tests**: NEW — `tests/secretary-integration.sh` (jq-free; covers
  helper, session-start inbox count, AND registry-write shape).
  EXISTING `inform-never-block.sh` / `router-auto-plan.sh` continue
  to cover invariants this code touches indirectly.
- **TODO**: open a PR on `eliezeravihail/The_secretary` with the §B3
  content. The PR description must explicitly include the registry
  path (`~/.config/the-secretary/aims-projects.json`) and the v1
  schema (paste the example from §B2). Once merged, paste the PR URL
  into ADR-0024 and tick this item.

## Risks / unknowns

- **Cross-repo coordination tax.** Renaming the registry path or
  changing the schema requires synchronized patches across aims
  (install-on writer) and secretary (reader). Mitigation: name the
  path once in ADR-0024 and treat as a frozen contract; renames force
  a superseding ADR. The `schema_version` field is the breaking-change
  signal; readers MUST tolerate higher schema_versions by ignoring
  the file (and may warn).
- **Append-only inbox without a cursor → duplicate risk.** Same as
  v2. Mitigation: small, timestamped entries; revisit if it bites.
- **Registry abandonment.** If the user deletes an aims project from
  disk (or uninstalls aims from a registered project), the registry
  entry stays. secretary looks up the entry, finds the
  `project_root` nonexistent (or no longer aims-managed), and
  silently skips. **Acceptable and intentional in v1** — removal flow
  is deferred; stale entries cost nothing at read time.
- **Schema drift.** Adding fields under `schema_version: 1` is fine
  (readers ignore unknown keys). Renaming/removing fields bumps to
  `schema_version: 2` and is a coordinated change. Document the v1
  field set as frozen in ADR-0024.
- **Concurrent install-on sessions writing the same registry.** Rare
  but possible (two terminals). Mitigation: write through
  `<registry>.tmp` + atomic `mv` (POSIX-atomic). A concurrent write
  can still overwrite — install-on runs are interactive, so true
  concurrency is unlikely; the worst case is one entry "loses" and
  the user re-runs install-on on that project. Acceptable in v1.
- **secretary's work-state directory shape may evolve.** Same as v2 —
  small read surface keeps breakage small.
- **Hebrew content** in `todo.md` may truncate mid-codepoint. Same as
  v2 — acceptable.
- **Pre-existing divergence between `commands/install-on.md` and
  `templates/commands/install-on.md`.** Discovered during v3 Phase 1:
  the two files are NOT byte-identical right now (the global has
  summary-lang Phase content the template lacks). This violates the
  memory node's invariant and is **out of scope for this plan** —
  flagged here so it gets fixed separately. This plan's Phase 3.5
  patch must be applied identically to both copies regardless.
- **Two integration directions diverge in the future.** Same as v2.
- **Repo-name spelling.** `eliezeravihail/The_secretary` (capital T,
  underscore). Use that exact spelling in docs/ADRs at close-out.
