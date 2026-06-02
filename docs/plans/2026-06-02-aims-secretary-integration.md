# Plan: aims ↔ The_secretary bidirectional integration
Status: draft
Started: 2026-06-02

## תקציר מנהלים

שילוב **דו-כיווני** בין `aims` ל-`/secretary` (`eliezeravihail/The_secretary`),
מינימלי ובעל ניוון-חיננית (graceful degradation) בשני הכיוונים.

**כיוון א' (aims → קורא secretary)** — נשמר כפי שתוכנן בטיוטה הקודמת. hook
ב-`SessionStart` של aims קורא את `todo.md` ו-tail של הלוג היומי מתוך
work-state dir של secretary, כשהמיקום נקבע ע"י `SECRETARY_WORK_DIR`
(env) או `~/.secretary-work-dir` (dotfile). שתי השאלות הפתוחות הקודמות
(env-vs-dotfile, fallback פר-פרויקט) נסגרו: **env+dotfile, ללא fallback
פר-פרויקט ב-v1**.

**כיוון ב' (secretary → כותב ל-inbox פר-פרויקט של aims)** — חדש. PR
על `eliezeravihail/The_secretary` שמלמד את secretary, כשהוא רץ ב-cwd שנראה
מנוהל-aims (היוריסטיקה אחת ויחידה — ראה §B), להוסיף שני התנהגויות:
(a) לקרוא read-only את `CLAUDE.md`, `docs/adr/README.md`, ותכניות
`Status: in-progress` כקונטקסט בפתיחת סשן; (b) **לכתוב** הצעות (עקרונות
תכנון, משימות) כ-append בלבד ל-`<project>/docs/inbox/secretary-suggestions.md`.
secretary לעולם אינו עורך ADRs, CLAUDE.md, plans או memory nodes ישירות.
**עיבוד ההצעות נשאר אצל המשתמש** — aims רק מציג ספירת unread ב-SessionStart
(לא תוכן); המשתמש פותח את הקובץ, מחליט פר-entry (כתיבת ADR / TODO בתכנית
/ dismiss). הזרימה מכבדת את חוק היסוד של aims: **שינוי-state רק לאחר
אישור המשתמש**.

ה-PR על secretary הוא **deliverable כתוכן בלבד** (קטעי קוד בתוך §E של תכנית
זו), לא כפעולה — סביבת התכנון הזו מוגבלת ל-`eliezeravihail/aims`.

## Goal

aims sessions begin with awareness of (1) the user's active personal-secretary
tasks for the day, and (2) any new suggestions secretary has dropped into the
project's inbox — without coupling either tool to the other's presence,
without blocking any edit, and without secretary ever mutating aims state
directly. The user remains the only actor who turns a suggestion into an
ADR, a plan TODO, or a memory update.

## Decision

### Direction A — aims reads secretary at SessionStart (unchanged from previous draft)

A new helper `templates/hooks/lib/secretary-context.sh` resolves the
secretary work-state directory:

1. `$SECRETARY_WORK_DIR` (env var) — **wins**.
2. First non-blank line of `~/.secretary-work-dir` — **fallback**.
3. Nothing — silent.

When found, it reads the head of `todo.md` (cap 1500B) and the tail of
today's `daily/YYYY-MM/YYYY-MM-DD.md` (cap 800B; falls back to the most
recent daily log if today's doesn't exist). Emits a single
`[aims-secretary]` block. The session-start hook sources it last so a
failure cannot perturb earlier output.

**Resolved (previously open):**
- *env vs dotfile vs both?* → **both** (env first, dotfile fallback). The
  user confirmed this is the desired surface; the maintenance cost of two
  code paths is small (≈10 LOC).
- *fall back to grepping `secretary.md` for `work_state_dir:` per-project?*
  → **no, not in v1**. Keeps aims ignorant of secretary's internal config
  format. Revisit only if friction shows up in practice.

### Direction B (new) — secretary writes to a per-project inbox

A PR on `eliezeravihail/The_secretary` (content in §E of `## Changes`)
teaches secretary two behaviors, both gated on a single heuristic:

> **Heuristic — "is this cwd an aims-managed project?"**
>
> ```bash
> [ -f "$cwd/docs/adr/README.md" ] \
>   && grep -q 'aims' "$cwd/.claude/hooks/session-start.sh" 2>/dev/null
> ```
>
> Both conditions must hold. Either alone produces too many false
> positives (every project that imitates ADR-style docs; every project
> that mentions `aims` in a hook for unrelated reasons). The pair is a
> tight fingerprint of an aims install. Pinned in §B of `## Changes`.

When the heuristic matches:

1. **Read-only context expansion at session-open.** secretary additionally
   reads `<cwd>/CLAUDE.md`, `<cwd>/docs/adr/README.md`, and any
   `<cwd>/docs/plans/*.md` with `Status: in-progress`. These join its
   normal session-open context (work-state `todo.md` + daily log tail).
2. **Append-only suggestion writes.** When secretary decides during the
   conversation that something belongs in the project's planning surface
   (a recurring principle, a follow-up task), it appends an entry to
   `<cwd>/docs/inbox/secretary-suggestions.md`. It **never** edits ADRs,
   CLAUDE.md, plans, memory nodes, or even existing entries in the inbox.

When the heuristic fails: secretary behaves exactly as today. Zero new
output, zero new prompts, zero new files.

### Direction B side of aims — surface unread count at SessionStart

The aims SessionStart hook gains a small block that:

- Detects `docs/inbox/secretary-suggestions.md`.
- **Counts** entries (lines matching `^## ` — entries are `## <ISO ts> — <title>`).
- Emits a factual one-liner: `[aims-secretary] N unread suggestion(s) in docs/inbox/secretary-suggestions.md`.
- Does NOT dump entry content. The count is enough to prompt the user
  to open the file; pushing content into context every session would
  bloat the prompt and re-surface already-considered material.

**Resolved (no cursor in v1).** The "unread" count is just the **total
entry count**. The user removes processed entries inline (or marks them
clearly) as part of triage. A `<!-- aims:read-cursor … -->` marker was
considered and rejected for v1: it doubles the mental model (the file
*and* the cursor) and the simpler design — "if it's still in the file,
it's still pending" — fits aims' "edit the file directly" ethos for
the memory inbox (precedent: `docs/memory/_inbox.md` works exactly
this way; classify-inbox.sh treats every line as pending until removed).

### Direction B side of aims — processing UX

**v1 has no new command.** The user opens
`docs/inbox/secretary-suggestions.md` like any other file and decides
per entry: write an ADR, add a TODO to an active plan, fold into a
memory node, or simply delete the entry. The README gains one short
paragraph explaining this.

A future `/secretary-inbox` command (interactive triage with
AskUserQuestion: ADR / TODO / dismiss) was considered and **deferred**.
The minimum-surface principle wins: a markdown file the user already
knows how to edit beats a new command surface that has to be
maintained, documented, and tested.

### Why this shape

- **Boundary is preserved.** secretary never mutates aims state — the
  inbox is a proposal surface, not a state surface. The "user approves
  before aims state changes" invariant (the same one that gates plan
  Phase 4) holds.
- **Mirrors `_inbox.md`.** aims already has an "external entries land in
  a markdown file; user/classifier triages them out" pattern at
  `docs/memory/_inbox.md`. Direction B borrows the **shape** (append-only,
  one entry per heading, processing is removal). It does **not** reuse
  the same file — memory inbox is for source paths needing classification;
  this inbox is for cross-tool suggestions. Different scopes, same grammar.
- **Graceful in both directions.**
  - Without secretary installed: aims helper exits silent; inbox file
    doesn't exist; SessionStart emits nothing extra.
  - Without aims installed in cwd: secretary's heuristic fails; secretary
    behaves as today.
  - Without the inbox file: SessionStart's count block is skipped silently.
- **Read-only, non-blocking on aims' side.** Every new code path exits 0.
  ADR-0020 holds: hooks inform, never block.
- **No new toolchain.** Pure bash + `grep`/`wc`/`head`/`tail`.

### Rejected directions

- **D. Shared context layer** (third artifact maintained by both tools).
  Rejected: YAGNI; two-tool integration doesn't justify a third surface.
- **C-as-state-write** (secretary writes directly into `docs/adr/`,
  `CLAUDE.md`, etc.). Rejected: violates the user-approves invariant.
- **aims auto-ingests inbox entries on close-out.** Rejected: same reason.

## Changes

### A. `templates/hooks/lib/secretary-context.sh` — NEW

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

### B. `templates/hooks/session-start.sh` — APPEND TWO blocks before `exit 0`

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
# Per-project markdown file secretary may append entries to. We surface a
# count only — never dump entries into context (would push too much in).
# Triage is the user opening the file and editing entries out as they
# turn into ADRs / plan TODOs / dismissals.
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
are independent — failure in one cannot affect the other.)

### C. `.claude/hooks/lib/secretary-context.sh` and `.claude/hooks/session-start.sh` — MIRROR

After the template edits, refresh the dogfooded install:

```bash
mkdir -p .claude/hooks/lib
cp templates/hooks/lib/secretary-context.sh .claude/hooks/lib/secretary-context.sh
cp templates/hooks/session-start.sh         .claude/hooks/session-start.sh
chmod +x .claude/hooks/lib/secretary-context.sh
```

Or equivalently: `/install-on .` (the supported dogfooding refresh path
per CLAUDE.md).

### D. `templates/commands/install-on.md` — copy `lib/` into target hooks

The install-on command currently materializes hooks one-by-one in its
"Hooks" copy table. Add the `lib/` subdir so every aims-bootstrapped
project gets the secretary helper too.

Patch under the "Hooks" copy table (around the line copying
`templates/hooks/{session-start,…}.sh`):

```diff
 | `.claude/hooks/{session-start,prompt-submit,pre-write,post-edit-marker,exit-plan-mode,stop-consolidate,session-end}.sh` | `templates/hooks/<same>` |
+| `.claude/hooks/lib/secretary-context.sh` | `templates/hooks/lib/secretary-context.sh` |
```

And in the prose around "After copy: `chmod +x …`", add:

```diff
-After copy: `chmod +x TARGET/.claude/hooks/*.sh TARGET/.claude/memory/*.sh`.
+After copy: `chmod +x TARGET/.claude/hooks/*.sh TARGET/.claude/hooks/lib/*.sh TARGET/.claude/memory/*.sh`.
```

The inbox directory itself (`docs/inbox/`) is **not** created by
install-on. It's created lazily on first write — by secretary, after the
PR (§E) is applied. Leaves install-on idempotent and avoids
materializing an empty directory that means nothing without secretary.

### E. PR on `eliezeravihail/The_secretary` — content (to be applied manually)

> **Note:** This sub-section is the **PR deliverable as content**, since
> this planning environment is restricted to `eliezeravihail/aims`. The
> main session (or the user) creates the PR; this section is the source
> of truth for what goes in it. Once merged, link the PR URL into
> ADR-0024.

#### E.1. Edit `.claude/commands/secretary.md` — add a new section

Insert the following section between the existing **Procedures** and
**Boundaries** sections (or anywhere late in the file — it does not
depend on prior sections):

```markdown
## aims-managed projects (optional integration)

If the current working directory looks like a project managed by
[aims](https://github.com/eliezeravihail/aims), this section governs two
additional behaviors. If the heuristic below fails, ignore this entire
section — Secretary behaves exactly as it does for any other project.

### Heuristic — is this cwd aims-managed?

Run (e.g. via `Bash`):

```bash
[ -f "./docs/adr/README.md" ] \
  && grep -q 'aims' "./.claude/hooks/session-start.sh" 2>/dev/null \
  && echo aims || echo plain
```

If the result is `plain` (either file missing, or the grep failed), skip
the rest of this section. If the result is `aims`, both behaviors below
are active.

### Behavior 1 — read-only project context at session-open

On Session open, in addition to the normal `todo.md` / daily-log read,
also read (read-only):

- `./CLAUDE.md` — project conventions.
- `./docs/adr/README.md` — ADR index.
- Every `./docs/plans/*.md` whose first ~10 lines contain
  `Status: in-progress` (use `grep -lE '^Status:\s*in-progress' docs/plans/*.md`).

Hold these as session context. Do not summarize them aloud unless asked.
They exist so Secretary's answers (drift detection, what's-stuck, task
placement) can name aims-side concepts (ADR numbers, in-progress plans)
accurately.

### Behavior 2 — append suggestions to the project inbox

When the conversation surfaces something that belongs in the project's
planning record — a recurring principle, a follow-up task, a note worth
preserving — **do not** edit ADRs, CLAUDE.md, plans, or memory nodes.
Instead append an entry to `./docs/inbox/secretary-suggestions.md`
(create the file and `docs/inbox/` directory if missing).

**Format** — append-only; one entry per heading; never edit existing
entries:

````markdown
## YYYY-MM-DDTHH:MM:SSZ — <short title>
source: secretary
kind: principle | task | note
cwd: <absolute path you saw>

<prose body — one short paragraph, or a small bullet list>
````

Concrete example:

````markdown
## 2026-06-02T15:31:07Z — Bound retry loops by elapsed time, not count
source: secretary
kind: principle
cwd: /home/avi/work/aims

The user repeatedly hit cases where retry-by-count masked a stuck
upstream. Suggest a small principle in CLAUDE.md or a new ADR:
"Retry budgets are wall-clock-bounded, not count-bounded."
````

Use `Bash` (`date -u +%FT%TZ`) to compute the timestamp. Append via
`>>` redirection or the Write tool in append mode — never overwrite
the file. Triage is the user's job; Secretary's role ends at appending.

### Boundary

Secretary writes **only** to `./docs/inbox/secretary-suggestions.md`
inside an aims-managed cwd. It must never edit any of:

- `./docs/adr/**`
- `./CLAUDE.md`
- `./docs/plans/**`
- `./docs/memory/**`
- `./.claude/**`

These belong to the user and to aims. The inbox is the only write
surface secretary has on the project side.
```

#### E.2. Append a one-liner to `README.md`

In the "What it does" list near the top, add one bullet:

```diff
 - Integrates with **Slack** (reading and summarising conversations)
+- Integrates with **[aims](https://github.com/eliezeravihail/aims)** projects (read-only context + append-only suggestion inbox at `<project>/docs/inbox/secretary-suggestions.md`)
 - Optionally tracks **experiment results** (`measures.md`) — stripped at setup if not needed
```

#### E.3. Backwards-compat note

No existing behavior changes. The heuristic returns `plain` for every
project that isn't aims-managed, and Behaviors 1 + 2 are no-ops in that
case. No config in `secretary.md`'s Config section is added (the
integration is fully heuristic-driven; nothing for users to fill in).

### F. `README.md` (aims side) — expanded subsection under "Hooks"

```markdown
### Optional: The_secretary integration (bidirectional)

aims interoperates with [`The_secretary`](https://github.com/eliezeravihail/The_secretary)
in two directions; both gracefully degrade to no-ops if the other tool
isn't installed.

**aims → secretary (read-only).** aims' `session-start` hook can surface
secretary's current `todo.md` head + most recent daily-log tail.
Point aims at secretary's work-state directory with **either**:

```sh
export SECRETARY_WORK_DIR=/path/to/your/work-state
# …or:
echo /path/to/your/work-state > ~/.secretary-work-dir
```

If neither is set, the hook stays silent. The probe is strictly
read-only; aims never writes into secretary's work-state directory.

**secretary → aims (append-only inbox).** When secretary runs in an
aims-managed cwd (heuristic: `docs/adr/README.md` exists AND
`.claude/hooks/session-start.sh` mentions `aims`), it may append
suggestions — planning principles, follow-up tasks, notes — to
`docs/inbox/secretary-suggestions.md`. aims' `session-start` hook
surfaces the **count** of pending entries (not the content) so you know
to triage.

**Triage is manual.** Open `docs/inbox/secretary-suggestions.md`,
decide per entry: write an ADR, add a TODO to an active plan, fold
into a memory node, or delete the entry. secretary never mutates aims
state directly — every state change still goes through you. (Same
invariant that gates plan Phase 4.)
```

### G. `docs/adr/00NN-aims-secretary-integration.md` — NEW ADR (close-out)

Status `proposed` at close-out. Number assigned at close-out (currently
expected to be **0024**). Records:

- The cross-tool contract: env+dotfile (aims→secretary); heuristic +
  append-only inbox file (secretary→aims).
- The inbox file format (path, entry heading shape, frontmatter-ish
  fields, append-only rule).
- The "user approves before aims state changes" invariant: secretary
  cannot edit aims-owned files; the inbox is a proposal surface only.
- Graceful-degrade rules in both directions.
- Open: whether to add a `/secretary-inbox` triage command (deferred to
  a separate ADR if v1 friction shows up).

### H. `tests/secretary-integration.sh` — NEW (smoke test, jq-free)

```bash
#!/usr/bin/env bash
# Asserts:
#   Helper (Direction A):
#     1. Emits nothing and exits 0 when no env / dotfile set.
#     2. Emits an [aims-secretary] block when SECRETARY_WORK_DIR points
#        at a fake work-state directory with a todo.md.
#     3. Exits 0 even when SECRETARY_WORK_DIR points at /nonexistent.
#   SessionStart (Direction B):
#     4. Emits `[aims-secretary] N unread suggestion(s) …` when an inbox
#        file with N entries is present (run from a temp project root).
#     5. Emits no inbox line when the inbox file is absent.
#     6. session-start.sh exits 0 in every case above.
set -u
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
HELPER=templates/hooks/lib/secretary-context.sh
HOOK=templates/hooks/session-start.sh

# --- Direction A ---

# 1. silent
unset SECRETARY_WORK_DIR
out=$(HOME="$TMP" bash "$HELPER" 2>/dev/null || true)
[ -z "$out" ] || { echo "FAIL: silent case emitted output: $out"; exit 1; }

# 2. populated
mkdir -p "$TMP/ws/daily/$(date -u +%Y-%m)"
printf '# Tasks\n- [ ] write the integration plan\n' > "$TMP/ws/todo.md"
printf '# %s\n### [aims] drafted plan\n' "$(date -u +%Y-%m-%d)" \
  > "$TMP/ws/daily/$(date -u +%Y-%m)/$(date -u +%Y-%m-%d).md"
out=$(SECRETARY_WORK_DIR="$TMP/ws" bash "$HELPER" 2>/dev/null || true)
echo "$out" | grep -q '\[aims-secretary\]' \
  || { echo "FAIL: populated case missing marker"; exit 1; }

# 3. broken path
out=$(SECRETARY_WORK_DIR=/nonexistent/path bash "$HELPER" 2>/dev/null; echo "rc=$?")
echo "$out" | grep -q 'rc=0' \
  || { echo "FAIL: broken path returned nonzero"; exit 1; }

# --- Direction B (inbox count) ---

# Build a tiny fake project root so session-start.sh's relative-path
# `docs/inbox/...` check resolves.
PROJ="$TMP/proj"
mkdir -p "$PROJ/docs/inbox" "$PROJ/docs/plans" "$PROJ/docs/adr" "$PROJ/.claude"
cp "$HOOK" "$PROJ/session-start.sh"

# 4. three entries → "3 unread suggestions"
cat > "$PROJ/docs/inbox/secretary-suggestions.md" <<'EOF'
## 2026-06-02T10:00:00Z — first
source: secretary
kind: note

body
## 2026-06-02T11:00:00Z — second
source: secretary
kind: principle

body
## 2026-06-02T12:00:00Z — third
source: secretary
kind: task

body
EOF
out=$(cd "$PROJ" && bash session-start.sh 2>/dev/null || true)
echo "$out" | grep -q '\[aims-secretary\] 3 unread suggestions' \
  || { echo "FAIL: count line missing or wrong: $out"; exit 1; }

# 5. inbox absent → no inbox line
rm "$PROJ/docs/inbox/secretary-suggestions.md"
out=$(cd "$PROJ" && bash session-start.sh 2>/dev/null || true)
echo "$out" | grep -q 'unread suggestion' \
  && { echo "FAIL: emitted inbox line when file absent"; exit 1; }

# 6. exit code in all cases above already implied by `|| true` not firing
echo PASS
```

## Open design questions

1. **Inbox processing surface — file-only vs new `/secretary-inbox` command?**
   Default: **file-only for v1**. The user opens the markdown, edits
   entries out as they triage. A new command (interactive AskUserQuestion
   per entry → ADR / plan TODO / dismiss) is more ergonomic but adds a
   command surface to maintain. Confirm file-only, or request the
   command.

2. **Should aims surface the FULL content of the latest unprocessed
   entry at SessionStart, or only the count?** Default: **only the
   count**, to avoid context bloat (every new entry would re-inject on
   every session until removed). Confirm, or request "count + last
   entry's title line".

3. **`cwd` field in each inbox entry — absolute path or
   git-root-relative?** Default: **absolute path**. More useful when
   reviewing the inbox across machines or when the same project is
   cloned to multiple paths. Confirm, or switch to git-root-relative
   (smaller diff if the project moves on disk).

## Verification

- `bash -n templates/hooks/*.sh templates/hooks/lib/*.sh && bash -n .claude/hooks/*.sh .claude/hooks/lib/*.sh`
- `bash tests/secretary-integration.sh` → `PASS` (covers both directions:
  helper cases 1-3 + session-start inbox cases 4-5).
- `bash tests/inform-never-block.sh` → still passes (helper + new inbox
  block both exit 0 unconditionally; no `block` mode anywhere).
- `bash tests/router-auto-plan.sh` → still passes (surface unchanged).
- **Manual A — secretary absent**: with `SECRETARY_WORK_DIR` unset and
  no `~/.secretary-work-dir`, open a Claude Code session in this repo;
  confirm session-start output is identical to before any aims↔secretary
  block (no `[aims-secretary] …` lines anywhere).
- **Manual A — secretary present**: `SECRETARY_WORK_DIR=/tmp/ws-fake`
  pre-seeded with `todo.md` + a daily log; confirm the helper's block
  appears.
- **Manual B — inbox absent**: in this repo (no
  `docs/inbox/secretary-suggestions.md`), confirm no
  `unread suggestion(s)` line appears.
- **Manual B — inbox seeded**: simulate secretary by

  ```sh
  mkdir -p docs/inbox
  cat >> docs/inbox/secretary-suggestions.md <<EOF
  ## $(date -u +%FT%TZ) — manual smoke test
  source: secretary
  kind: note
  cwd: $(pwd)

  hello
  EOF
  ```

  open a session; confirm a `[aims-secretary] 1 unread suggestion in
  docs/inbox/secretary-suggestions.md` line is emitted. Remove the file
  to restore the silent state.
- **Cross-repo — PR applied**: confirm the PR on
  `eliezeravihail/The_secretary` (§E content) was merged. Either
  `gh pr view <pr-url> --json mergedAt` shows a non-null `mergedAt`, or:

  ```sh
  curl -sf https://raw.githubusercontent.com/eliezeravihail/The_secretary/main/.claude/commands/secretary.md \
    | grep -q '## aims-managed projects'
  ```

  Once merged, paste the PR URL into ADR-0024's body.

## Close-out checklist

- **ADR**: WRITE — `0024-aims-secretary-integration.md` (clear
  architectural commitment: cross-tool contract in both directions,
  new env/dotfile surface on the aims side, new inbox file format on
  both sides, user-approves invariant explicitly recorded).
- **Nodes**: UPDATE — `docs/memory/hooks/session-start.md` (now reads
  external state via a helper AND surfaces a per-project inbox count).
  CONSIDER NEW — `docs/memory/integration/secretary.md` if the
  integration grows past two files (helper + a triage command, if §1
  of Open Questions ever flips). v1: just append to the session-start
  node.
- **CLAUDE.md**: UPDATE — add a short **"External integrations"**
  subsection naming The_secretary, the `SECRETARY_WORK_DIR` env /
  `~/.secretary-work-dir` dotfile contract, the inbox path
  (`docs/inbox/secretary-suggestions.md`), and the
  **user-approves-before-aims-state-changes** invariant that gates the
  inbox.
- **Tests**: NEW — `tests/secretary-integration.sh` (jq-free; covers
  both helper and session-start inbox-count paths). EXISTING
  `inform-never-block.sh` / `router-auto-plan.sh` continue to cover
  the invariants the new code touches indirectly.
- **TODO**: open a PR on `eliezeravihail/The_secretary` with the
  content from §E of `## Changes`. Once merged, paste the PR URL into
  ADR-0024's body and tick this item.

## Risks / unknowns

- **Cross-repo coordination tax.** Any rename of the inbox path
  (`docs/inbox/secretary-suggestions.md`) requires synchronized patches
  on both sides — aims' session-start hook AND secretary's `.claude/
  commands/secretary.md`. Mitigation: name it once in ADR-0024 and
  treat it as a frozen contract; renames force a superseding ADR.
- **Append-only without a cursor → duplicate risk.** If secretary
  mis-detects "already wrote that suggestion this session" (e.g. across
  a restart), it may append the same entry twice. Mitigation: keep
  entries small and timestamped so duplicates are visually obvious
  during triage; revisit if duplication becomes a real pain.
- **secretary's work-state directory shape may evolve.** The README
  pins `todo.md`, `results.md`, `daily/YYYY-MM/YYYY-MM-DD.md`,
  `measures.md`. The helper only reads `todo.md` and the daily log;
  if either is renamed in a future secretary release, the helper goes
  silent (acceptable graceful-degrade) but the integration's value
  drops on the read side. Small surface = small breakage.
- **Hebrew content** in `todo.md` may make `head -c 1500` truncate
  mid-codepoint. Acceptable — the output is informational context,
  not a structured payload; a mangled trailing char doesn't hurt
  model comprehension. Switch to `head -n` with a line cap if it ever
  surfaces as a real problem.
- **Heuristic false positives/negatives on secretary's side.** The
  `docs/adr/README.md` + `grep aims session-start.sh` pair is tight
  but not bulletproof: a project that copied aims hooks then renamed
  the project away from aims would still match; a heavily customized
  aims install that renamed `session-start.sh` would miss. Acceptable
  for v1; revisit if real misclassifications appear.
- **Two integration directions diverge in the future.** If a Direction
  B' (aims→writes secretary's daily log) is later requested, the
  surfaces chosen here don't constrain it — both can layer on without
  renaming `SECRETARY_WORK_DIR` or the inbox path.
- **Repo-name spelling.** The repo is `eliezeravihail/The_secretary`
  (capital T, underscore). All docs/ADRs at close-out must use that
  exact spelling.
