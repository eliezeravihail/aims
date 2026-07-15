# Plan: Memory-subsystem diet — delta consolidation, schema slim, README de-layering, shape-gated router, status hardening
Status: draft
Started: 2026-07-15

## תקציר מנהלים

תת-מערכת הזיכרון של aims צברה טקס שעולה יותר ממה שהוא מחזיר: שכתוב-מלא של node בכל קונסולידציה (המשימה שהמודל זייף עד שנדרש גלאי-שקרים, ADR-0027), סכמת 6 סעיפים שרובם פרפרזה נסחפת של ADRs, שכבת README-לכל-tag שמתיישנת כי היא לא מנוטרת, מסווג-כוונות של ~200 שורות regex שמזריק פסקה קבועה, ופרסינג `Status:` שביר שנשבר על קבצים עם יותר משורת Status אחת. התוכנית מדללת בחמישה מסלולים בלתי-תלויים: (A) קונסולידציה עוברת מ"שכתוב מלא" ל"הוספת שורת דלתא מתוארכת" עם קיפול (compaction) רק מעל סף — הוספה היא משימה שמודלים מבצעים אמינות; (B) סכמת node מצטמצמת ל-4 סעיפים שערכם ייחודי; (C) קובצי README של ה-tags נמחקים ובמקומם אינדקס מיוצר-מכנית ב-README העליון; (D) מסווג הכוונות מוחלף בשער-צורה של ~10 שורות; (E) פרסינג Status מוקשח ל-5 השורות הראשונות. נבחר delta-append על פני full-rewrite כי הוא תוקף את שורש הכשל של ADR-0027 במקום לשטר אותו. ליבת aims (plans, ADRs, inform-never-block, הזרקת-nodes) לא משתנה.

## Changes

Ordered so each track is independently verifiable. Every `templates/`
change is mirrored to `.claude/` by running `/install-on .` at the end
of each track (guarded by `tests/copies-identical.sh`).

---

### Track A — delta consolidation + 4-section schema

**New node body schema (ADR-0028, amends ADR-0008):**

```markdown
## Purpose
<one short paragraph: what this code does>

## Invariants & gotchas
- <what must not break when editing>
- open: <undecided design question, if any>

## Pointers
- ADR-NNNN — <why it matters here>
- <repo-relative file refs / external URLs>

## Deltas
- YYYY-MM-DD: <one line: what changed and why it matters> — <SHA|ADR|plan-slug>
```

Migration table (applied once to all 15 nodes, Phase 4):

| Old section          | Destination                                          |
|----------------------|------------------------------------------------------|
| `## Purpose`         | keep, trim to one paragraph                          |
| `## Design rationale`| fold load-bearing bullets into `## Pointers` (as "ADR-NNNN — why") or `## Invariants & gotchas`; drop restatements of ADR bodies |
| `## Known issues` fixed: | `## Deltas` line (date = commit date, keep SHA)  |
| `## Known issues` open:  | `## Invariants & gotchas` as `- open:` bullet    |
| `## Open questions`  | `## Invariants & gotchas` as `- open:` bullet        |
| `## Pointers`        | keep (incl. `- External: … review for impact` breadcrumbs) |

#### templates/memory/consolidate.sh

Two changes: (1) shrink the evidence payload — commit *summaries*, not
full patches; (2) emit the **delta prompt** by default, the full
**compaction prompt** only above thresholds.

```bash
# --- evidence gathering (replaces the two `head -c 4000` -p blocks) ---
if [ "$in_git" -eq 1 ] && [ -n "$LAST_TOUCHED" ]; then
  committed=$(git -C . log --since="$LAST_TOUCHED" --no-merges \
    --pretty=format:'%h %ad %s' --date=short --stat -- "$base" 2>/dev/null \
    | head -c 2000)
fi
uncommitted=""
if [ "$in_git" -eq 1 ]; then
  uncommitted=$( { git -C . diff HEAD --stat -- "$base"
                   git -C . diff HEAD -- "$base"; } 2>/dev/null | head -c 2000)
fi

# --- mode selection ---
DELTA_MAX="${AIMS_MEMORY_DELTA_MAX:-12}"
end=$(fm_end_line "$node")
body_lines=$(awk -v e="$end" 'NR>e' "$node" | wc -l | tr -d ' ')
n_deltas=$(awk '/^## Deltas/{d=1;next} /^## /{d=0} d && /^- /{n++} END{print n+0}' "$node")
MODE=delta
if [ "$n_deltas" -ge "$DELTA_MAX" ] || [ "$body_lines" -gt 150 ]; then
  MODE=compact
fi
```

Delta-mode ACTION text (replaces the six-section rewrite instructions):

```
ACTION FOR THIS NODE (mode: delta):
1. Append ONE line per meaningful change under `## Deltas` (newest last):
   `- <TODAY>: <what changed and why it matters> — <SHA|ADR|plan-slug>`
   Collapse many commits with one theme into one line. Skip noise
   (formatting, comment tweaks).
2. If a diff FALSIFIES a sentence in `## Purpose` or
   `## Invariants & gotchas`, fix that sentence in place (minimal edit).
   Do not otherwise rewrite sections.
3. Append the external-ref breadcrumbs under `## Pointers` as before.
4. Preserve frontmatter EXACTLY; do not touch dirty/last_touched/
   last_consolidated. Then run:
   bash .claude/memory/mark.sh "<node>" consolidated
```

Compact-mode ACTION text = the current full-rewrite rules, retargeted at
the 4-section schema, plus: "fold every `## Deltas` line into the three
sections above it (facts survive — move or merge, never delete), then
leave `## Deltas` empty."

`<TODAY>` is computed in bash (`date -u +%F`) and embedded in the prompt
so the model never guesses dates.

#### templates/memory/lint.sh

```bash
# ADR-0028 section checks: exactly four body sections in order.
EXPECTED='## Purpose|## Invariants & gotchas|## Pointers|## Deltas|'
```

- The fixed-SHA validity check re-targets `## Deltas` (any
  `[0-9a-f]{7,40}` token) instead of `## Known issues`.
- The absolute-path / same-repo-URL checks scan `## Pointers` +
  `## Deltas`.
- New informational check: deltas count ≥ `AIMS_MEMORY_DELTA_MAX`
  → "compaction due at next consolidation".

#### templates/memory/new-node.sh

Body scaffold in the heredoc becomes the four headings above (empty
sections, `## Deltas` last).

#### docs/adr/0028-delta-consolidation-and-four-section-schema.md (new)

Status `proposed`. Decision: consolidation appends dated delta lines +
minimal truth-fixes; full rewrite happens only at compaction thresholds.
Amends ADR-0008 (schema) and ADR-0009 (consolidation task shape);
records that this addresses the root cause of the ADR-0027 failure mode
(full-rewrite-under-constraints at Stop-time invites fake reports;
append is cheap to do honestly). Index row appended.

*(No change needed in `stop-consolidate.sh` for this track: its header
prompt, throttle, and ADR-0027 snapshot logic are mode-agnostic; the
per-node ACTION text lives in `consolidate.sh`.)*

---

### Track B — README de-layering

#### docs/memory/&lt;tag&gt;/README.md (×5 — delete)

Delete `discipline/ hooks/ installer/ memory/ testing/` READMEs (98
lines, unmonitored, provably stale — `hooks/README.md` still describes
pre-ADR-0020 blocking). Surviving facts move: the "memory-subsystem
hooks live under memory/…" routing note → top README; everything else
is either stale or duplicated by node Purposes.

#### templates/memory/readme-sync.sh (new, ~45 lines)

Regenerates the node index inside marker comments in
`docs/memory/README.md`:

```bash
#!/usr/bin/env bash
# Regenerate the "## Index" block of docs/memory/README.md from node
# frontmatter + first Purpose line. Deterministic; no LLM.
# Usage: readme-sync.sh [--check]   (--check: exit 1 on drift, change nothing)
set -u
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
. "$SCRIPT_DIR/_lib.sh"
README="$MEMORY_DIR/README.md"
gen() {
  while IFS= read -r leaf; do
    [ -z "$leaf" ] && continue
    node=$(fm_get "$leaf" node)
    purpose=$(awk '/^## Purpose/{p=1;next} /^## /{p=0} p&&NF{print;exit}' "$leaf")
    printf -- '- `%s` — %s\n' "${node:-$leaf}" "${purpose:-\(no purpose line\)}"
  done < <(list_leaves)
}
new=$(awk -v idx="$(gen)" '
  /<!-- BEGIN NODE INDEX -->/ {print; print idx; skip=1; next}
  /<!-- END NODE INDEX -->/   {skip=0}
  !skip {print}
' "$README")
if [ "${1:-}" = "--check" ]; then
  [ "$new" = "$(cat "$README")" ] || { echo "[aims-memory] README index drift — run readme-sync.sh" >&2; exit 1; }
  exit 0
fi
printf '%s\n' "$new" > "$README"
```

#### docs/memory/README.md

- `## Tags` prose slims to one line per tag (no leaf lists); the
  navigation section drops the per-tag-README step:
  `cat docs/memory/README.md` → leaf directly.
- New `## Index` section wrapped in
  `<!-- BEGIN NODE INDEX --> … <!-- END NODE INDEX -->`, populated by
  `readme-sync.sh`.
- Fix the (currently stale) hooks-tag description while here.

#### templates/memory/mark.sh

At the end of `consolidated` mode (after the `rm -f` lock line):

```bash
[ -x "$SCRIPT_DIR/readme-sync.sh" ] || true
bash "$SCRIPT_DIR/readme-sync.sh" 2>/dev/null || true
```

#### templates/memory/lint.sh (again)

```bash
# README index freshness (Track B): drift is an issue.
if [ -r "$SCRIPT_DIR/readme-sync.sh" ]; then
  bash "$SCRIPT_DIR/readme-sync.sh" --check 2>/dev/null || {
    printf '%s: node index out of sync (run readme-sync.sh)\n' "$MEMORY_DIR/README.md"
    issues=$((issues + 1))
  }
fi
```

#### templates/commands/install-on.md (+ two copies)

Memory-scripts row gains `readme-sync`:
`.claude/memory/{_lib,mark,new-node,find-dirty,lint,check-refs,consolidate,classify-inbox,doctor,readme-sync}.sh`

---

### Track C — prompt-submit: shape gate replaces intent classifier

#### templates/hooks/prompt-submit.sh

Delete the classifier (`lower=…`, `match()`, the seven intent branches,
the Hebrew-interrogatives case, the multilingual `ambiguous` fallback,
the `case "$intent"` router — lines ~181-251). Keep untouched: the
locale/char-counting block (still load-bearing for `${#prompt}`), the
suppression rules, and the entire memory injector. Replacement:

```bash
# ── Convention note — shape gate, not intent classes (ADR-0029) ──────────
# The note is factual and self-conditional ("for a NON-TRIVIAL change"),
# so over-firing is cheap; under-firing is backstopped by pre-write's
# state-aware note at the first source edit (ADR-0023). Gate:
#   long enough to be a task, not a pasted code block, not a question.
# Language-neutral by construction — no keyword lists (the old English
# regexes + Hebrew interrogative list are gone).
router_text=""
if [ "${#prompt}" -ge 30 ] && [ "${#prompt}" -le 4096 ] \
   && ! printf '%s' "$prompt" | grep -q '```' \
   && ! printf '%s' "$prompt" | grep -qE '\?[[:space:]]*$'; then
  router_text="[aims] Project convention: for a non-trivial change, plan before implementing — read-only discovery, then a \`Status: draft\` plan written to \`docs/plans/\`, then user approval, then implementation, then inline close-out (verify, ADR-if-warranted, mark completed, refresh memory). The full flow is documented in \`.claude/commands/plan.md\`. Planning is the *behavior*; the \`/plan\` slash command is an OPTIONAL shortcut that dispatches the planning pass to an Opus subagent — use it when the current model is not Opus and the task warrants careful planning. If you (the assistant) are not running on Opus and this prompt looks like a non-trivial change, ask the user ONCE via AskUserQuestion whether to use \`/plan\` for an Opus planner; otherwise just plan inline. (Informational; nothing is blocked.)"
fi
```

Stderr breadcrumb: `[aims-router] shape-gate hit — planning note injected.`
(drop `intent=%s`). Header comment block updated to match. Net: −~150
lines, −all language special-casing.

#### tests/router-auto-plan.sh

Rewrite the 6 cases for the gate semantics:

1. slash-prefixed → no injection
2. short prompt (<30 chars) → no injection
3. trailing-`?` question (any length) → no injection
4. short Hebrew comment (~22 chars / 42 bytes) → no injection
   *(preserves the char-vs-byte regression guard — case 6 today)*
5. long English task sentence → note injected
6. long Hebrew task sentence (no `?`) → note injected
7. prompt containing a ``` fence → no injection

#### docs/adr/0029-shape-gated-convention-note.md (new)

Status `proposed`. Decision: the per-prompt convention note fires on
prompt *shape* (length ∧ no fence ∧ not a question), not on regex
intent classes. Supersedes the intent-classification mechanism of
ADR-0015 (its draft-on-disk behavior stands). Rationale: the classifier
selected between injecting a *constant* paragraph or nothing; class
resolution added fragility (per-language keyword lists) with no
behavioral payoff. Index row appended.

#### README.md + CLAUDE.md

- README.md "Hooks" bullet for UserPromptSubmit: describe the shape
  gate; drop "Detects intent (bug, feature, …)".
- CLAUDE.md "Hooks" section: same one-line adjustment ("for an
  actionable prompt" → "for a task-shaped prompt").

---

### Track D — Status parsing hardening

#### templates/memory/_lib.sh

```bash
# Plan state lives in the file HEADER (first 5 lines). Body content —
# e.g. a code block quoting "Status: in-progress" — must never affect
# plan-state detection (real case: a completed plan carrying 4 Status
# lines confused `grep -l '^Status:'` callers).
plan_status() {
  head -n 5 "$1" 2>/dev/null | awk -F': *' '/^Status:/{print tolower($2); exit}' | tr -d '\r '
}
plans_with_status() {   # usage: plans_with_status <dir> <status>
  local d="$1" want="$2" f
  for f in "$d"/*.md; do
    [ -e "$f" ] || continue
    [ "$(plan_status "$f")" = "$want" ] && printf '%s\n' "$f"
  done
}
```

#### Hook call sites (4 files)

Each hook already locates `MEM_HELPERS` (or gains the standard 3-line
discovery block, as in `post-edit-marker.sh:22-24`) and sources
`_lib.sh`; a guarded fallback keeps jq-less/lib-less installs working:

```bash
command -v plans_with_status >/dev/null 2>&1 || plans_with_status() {
  grep -lE "^Status:[[:space:]]*$2" "$1"/*.md 2>/dev/null
}
```

Replacements:
- `session-start.sh:30,31,48,60` → `plans_with_status "$PLAN_DIR" in-progress` / `… draft`
- `prompt-submit.sh:78` → `[ -n "$(plans_with_status "$PLAN_DIR" in-progress)" ] && has_active_plan=1`
- `pre-write.sh:72` → same pattern
- `stop-consolidate.sh:97` → `IN_PROGRESS_PLAN=$(plans_with_status docs/plans in-progress | head -1)`

#### templates/hooks/post-edit-marker.sh

Add `docs/plans/*` to the skip-list. Plan files are workflow artifacts
— nodes reference them via `sessions:`, never `code:` — so routing
every freshly-written draft into `_inbox.md` is pure noise (observed
live: this very plan's draft landed in the inbox on write).

```bash
case "$rel" in
  .claude/*|.git/*|*/node_modules/*|*/dist/*|*/build/*|docs/memory/*|docs/plans/*) exit 0 ;;
esac
```

#### tests/router-auto-plan.sh (one added case)

Case 8: sandbox plan file with `Status: completed` on line 2 and a
decoy `Status: in-progress` inside a code block at line 20 → the
short-follow-up suppression must NOT trigger (no active plan).

*(Rejected alternative: moving completed plans to `docs/plans/archive/`
— breaks repo-relative pointers in ADRs and memory nodes. Header-scoped
parsing removes the correctness problem; growth is only a browsing
nuisance.)*

---

### Track E — retire the strict `.lock` protocol (gated on approval)

#### templates/hooks/stop-consolidate.sh

Delete the sidecar-lock filter block (lines ~130-188: `LOCK_TTL`,
`reap_stale_lock`, `try_claim`, `release_held_locks`, the trap, the
`CLAIMED` re-assignment). `DIRTY` proceeds unfiltered. The ADR-0027
snapshot logic stays (it is cheap and orthogonal).

#### templates/memory/mark.sh

Drop `rm -f "${node%.md}.lock"` (nothing creates `.lock` anymore).

#### templates/hooks/post-edit-marker.sh

Unchanged — the advisory `.marker` (stamp + "possible concurrent edit"
note) is the surviving, useful half of ADR-0024.

#### tests/consolidate.sh

Remove/adjust the lock-manipulation lines in the ADR-0027 cases
(`rm -f "$AIMS_MEMORY_DIR/x/foo.lock"` scaffolding becomes unnecessary).

#### docs/adr/0030-retire-strict-consolidation-lock.md (new)

Status `proposed`. Decision: the consolidation mutex is removed; the
advisory `.marker` remains the only cross-session signal. Supersedes
ADR-0024's strict half (and with it the 0018→0019→0024 lineage).
Rationale: three protocol iterations for a tool that in practice runs
single-session; worst uncoordinated case is a last-write-wins node
rewrite (both writes valid; with Track A's delta-append, collisions are
line-appends, more benign still). Index row appended.

---

## Open design questions

- **Track E go/no-go** — retire the strict lock entirely, or keep it
  dormant behind an env flag? Recommendation: retire (dead protocol
  code is its own staleness liability).
- **Delta line date** — consolidation-day (`date -u +%F`, monotonic
  append order; recommended) vs. commit date (more precise, but
  multi-commit deltas have no single date)?
- **`- open:` bullets under Invariants** — acceptable home for the old
  `## Open questions` content, or keep a fifth section? Recommendation:
  fold; a section that usually reads "None." earns no heading.
- **Question suppression edge** — a task phrased with a trailing `?`
  ("can you refactor X?") now gets no note. Accepted? Backstop remains
  pre-write's first-edit note (ADR-0023).

## Verification

- `bash -n templates/hooks/*.sh templates/memory/*.sh .claude/hooks/*.sh .claude/memory/*.sh`
- `bash tests/marker.sh && bash tests/consolidate.sh && bash tests/exit-plan-mode.sh && bash tests/router-auto-plan.sh && bash tests/inform-never-block.sh && bash tests/copies-identical.sh`
- `bash .claude/memory/lint.sh` → clean under the 4-section schema (all
  15 nodes migrated), README index in sync
- `bash .claude/memory/readme-sync.sh --check` → exit 0
- `bash .claude/memory/doctor.sh` → 15 nodes, 0 dirty, no inert
- Manual: `printf '{"prompt":"תתקן בבקשה את הבאג הארוך הזה במערכת"}' | bash .claude/hooks/prompt-submit.sh` → note injected; same with trailing `?` → silent
- Manual: `echo '{}' | AIMS_MEMORY_INTERVAL_SEC=0 bash .claude/hooks/stop-consolidate.sh` on a dirtied sandbox node → delta-mode prompt; with 13 pre-seeded deltas → compact-mode prompt

## Close-out checklist

- ADR: WRITE — 0028-delta-consolidation-and-four-section-schema; 0029-shape-gated-convention-note; 0030-retire-strict-consolidation-lock (Track E, if approved)
- Nodes: UPDATE — all 15 nodes (schema migration); content refresh for memory/helpers, memory/phase-a-marker, memory/phase-b-consolidation, hooks/prompt-submit, hooks/session-start, installer/install-on, installer/templates, testing/smoke-tests
- CLAUDE.md: UPDATE — "Hooks" section (consolidation = delta-append; router = shape gate)
- Tests: tests/router-auto-plan.sh rewritten (8 cases); tests/consolidate.sh adjusted (delta/compact modes, lock scaffolding removed); tests/copies-identical.sh unchanged and guarding
- TODO: docs/plans archive convention — rejected for now (link rot); revisit only if browsing pain is reported

## Risks / unknowns

- Migration of 15 nodes is LLM content-work; mitigated by the migration
  table + lint enforcing the new schema immediately after.
- Delta lines accrete noise if the model over-appends; mitigated by the
  `DELTA_MAX` compaction trigger + "collapse one theme into one line".
- Shape gate fires on long questions without `?` (rhetorical phrasing) —
  cosmetic; the note is self-conditional.
- Existing dirty-marker flow mid-migration: a node dirtied between
  schema change and its migration gets the delta prompt against an old
  body; the prompt's truth-fix rule covers it (worst case: one manual
  fix-up pass, caught by lint).
