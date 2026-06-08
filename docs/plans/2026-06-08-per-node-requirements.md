# Plan: Per-node requirements — explicit, edit-time-surfaced contract
Status: draft
Started: 2026-06-08

## תקציר מנהלים
כל צומת זיכרון יישא **דרישות מפורשות** — צ'קליסט של "MUST" שהקוד שהצומת מתעד
חייב להמשיך לקיים — כדי שבסשנים ארוכים תיקון של דבר אחד לא ישבור דרישה אחרת
בשקט. במקום סקציה שביעית, ממזגים את הכוונה לסקציה הקיימת ומשנים את שמה
`## Invariants & gotchas` → `## Requirements & invariants`, שמובילה כעת ברשימת
דרישות בדיקות (כל דרישה רשאית לצטט את הטסט/ADR שאוכף אותה) ואז מלכודות מימוש.
ה‑hook `post-edit-marker` יזריק את הדרישות **ברגע שעורכים את הקובץ** (factual,
לא מצווה — ADR-0020), ה‑`lint` יוודא שהסקציה אינה ריקה, ו‑`consolidate`/
`new-node` יעדכנו את הסכמה. המנגנון נוגע ב‑4 קבצי helper/hook (×2 עותקים) +
שכתוב קל של הסקציה ב‑15 הצמתים. בחרנו מיזוג על פני סקציה שביעית כדי לשמור על
שש סקציות וה‑lint התקין, ובחרנו אכיפה קלה (הצגה + בדיקת קיום) על פני הרצת
טסטים אוטומטית.

## Changes

### templates/memory/_lib.sh  +  .claude/memory/_lib.sh
Add a section-body extractor (used by the marker to surface requirements, and
reusable by lint). Append after `list_leaves`:
```bash
# Extract the body of a "## <heading>" section: lines between that heading and
# the next "## " (or EOF). Usage: fm_section <file> <heading-text-without-##>
fm_section() {
  local f="$1" heading="$2"
  [ -r "$f" ] || return
  awk -v h="## $heading" '
    $0 == h        { in_s=1; next }
    in_s && /^## / { in_s=0 }
    in_s           { print }
  ' "$f"
}
```

### templates/memory/lint.sh  +  .claude/memory/lint.sh
(1) Rename the enforced heading in `EXPECTED` (line 114). (2) Add a
content-presence check so the contract is never an empty heading.
```bash
  # ADR-0008/0021 section checks: exactly six body sections in order.
  EXPECTED='## Purpose|## Design rationale|## Requirements & invariants|## Known issues|## Pointers|## Open questions|'
  actual=$(grep -E '^## ' "$leaf" | tr '\n' '|')
  if [ "$actual" != "$EXPECTED" ]; then
    printf '%s: section headings/order wrong (got: %s)\n' "$leaf" "$actual"
    issues=$((issues + 1))
  fi

  # ADR-0021: the Requirements & invariants section must carry real content
  # (>=1 non-blank, non-placeholder line). An empty contract is exactly what
  # regressions slip through during long sessions.
  reqs=$(awk '
    $0=="## Requirements & invariants" { s=1; next }
    s && /^## /                        { s=0 }
    s && NF && $0 !~ /^[[:space:]]*\(.*\)[[:space:]]*$/ { print }
  ' "$leaf")
  if [ -z "$reqs" ]; then
    printf '%s: Requirements & invariants section is empty (no requirements stated)\n' "$leaf"
    issues=$((issues + 1))
  fi
```

### templates/memory/consolidate.sh  +  .claude/memory/consolidate.sh
Rewrite the schema hint for the renamed section (line 86) so consolidation
produces a checklist, not prose:
```
   ## Requirements & invariants — explicit checklist FIRST: one
                           "- MUST <specific, testable statement>" bullet per
                           requirement the code must keep satisfying; each may
                           cite the enforcing test/ADR (e.g. "— tests/foo.sh"
                           or "— ADR-NNNN"). Then any gotchas/traps. This is
                           the contract a future edit is checked against; be
                           specific, not vague.
```

### templates/memory/new-node.sh  +  .claude/memory/new-node.sh
Rename the scaffolded heading + checklist placeholder (line 90 region):
```
## Requirements & invariants

(Checklist FIRST: one "- MUST ..." bullet per requirement this code must
satisfy; cite the enforcing test/ADR where one exists. Then any gotchas.
This is the contract future edits are checked against.)
```

### templates/hooks/post-edit-marker.sh  +  .claude/hooks/post-edit-marker.sh
Surface each matched node's requirements right when its source is edited.
Declare an accumulator before the match loop, fill it inside, append to NOTE.
```bash
# before the `while IFS= read -r leaf` loop (near `notes=""`):
reqblock=""

# inside the loop, after `node=$(fm_get "$leaf" node); node="${node:-$leaf}"`:
  reqs=$(fm_section "$leaf" "Requirements & invariants" \
         | sed '/^[[:space:]]*$/d' | head -c 1200)
  [ -n "$reqs" ] && reqblock="${reqblock}"$'\n'"• ${rel} (node ${node}):"$'\n'"${reqs}"$'\n'

# after building NOTE (line ~112), before the JSON emit:
if [ -n "$reqblock" ]; then
  NOTE="${NOTE}"$'\n\n'"Requirements the edited file is expected to keep satisfying (factual — verify the change against them):${reqblock}"
fi
```

### templates/hooks/stop-consolidate.sh  +  .claude/hooks/stop-consolidate.sh
One-line rename in the EXTRA CONTEXT mining hint (line 211):
```
Mine for requirements/invariants (→ ## Requirements & invariants), design rationale
```

### docs/memory/**/*.md  — all 15 nodes (the bulk content work)
Mechanical+editorial transform applied to every leaf:
1. Rename `## Invariants & gotchas` → `## Requirements & invariants`
   (scripted: `sed -i 's/^## Invariants & gotchas$/## Requirements \& invariants/'`).
2. Reshape the body to **lead with `- MUST ...` requirement bullets**, then
   keep gotchas. Most existing bullets are already requirement-like; phrase
   them as explicit MUST and append the enforcing test/ADR pointer where one
   exists. Derive missing requirements from the node's `code:`, its ADRs, and
   CLAUDE.md.

Representative example — `docs/memory/hooks/prompt-submit.md`:
```markdown
## Requirements & invariants

- MUST always `exit 0` — UserPromptSubmit hooks are advisory only and cannot
  block a prompt. — tests/inform-never-block.sh
- MUST never create a `.planning-lock` and never emit an imperative note;
  injected text is factual context only. — ADR-0020, tests/router-auto-plan.sh
- MUST measure prompt length in characters, not bytes (force a UTF-8 LC_ALL
  when the inherited locale isn't UTF-8), so a short non-ASCII prompt does not
  trip the actionable fallback. — tests/router-auto-plan.sh (case 6)
- MUST keep lock/auto-engage and memory injection independent: a pure-question
  prompt that references a tracked file gets memory injection only. — ADR-0016
- Suppression order (any one short-circuits to exit 0): slash-prefix → active
  plan + short prompt → empty prompt.
- Gotcha: memory match derives a literal prefix from each `code:` glob (cut at
  the first `*`/`?`/`[`) and substring-tests the prompt; per-session de-dup at
  `.claude/memory/.injected-<session_id>`, total injection capped at 8 KB.
```
The other 14 nodes follow the same shape (lead with MUST bullets carrying
test/ADR pointers, then gotchas).

### docs/adr/0021-per-node-requirements.md  (new; created in close-out)
Refines ADR-0008: section #3 is renamed and redefined as an explicit
requirements checklist; `post-edit-marker` surfaces it at edit time (factual,
per ADR-0020); `lint` enforces non-empty content. Append an index row to
`docs/adr/README.md`. ADR-0008 stays accepted (refined, not superseded).

### tests/requirements.sh  (new)
jq-free smoke test:
- `fm_section` extracts the named section body (and only it).
- `lint.sh` flags a node whose `## Requirements & invariants` body is empty /
  placeholder-only, and is silent once a `- MUST ...` bullet is present.
- `post-edit-marker.sh`, given a payload editing a file tracked by a node with
  requirements, emits `additionalContext` containing the requirement text.

### CLAUDE.md  (Hooks section)
Extend the `PostToolUse` bullet: in addition to marking the leaf dirty, the
marker injects the node's requirements so they are visible at edit time.

## Open design questions
- Freshly scaffolded nodes (placeholder-only requirements) will be reported by
  the new lint check until filled. Proposed: accept it — lint is informational
  (exit 0) and the report is a useful "state the contract" nudge, not a block.
- `post-edit-marker` requirements injection is capped at 1200 bytes per matched
  node. If several nodes match one edit the note can still grow; proposed cap is
  per-node only (matches are rare and requirement sections are short). Revisit
  only if observed to bloat.
- Citing an enforcing test per requirement is **optional** (not all
  requirements have one); lint checks presence of content, not citations.

## Verification
- `bash -n templates/hooks/*.sh templates/memory/*.sh .claude/hooks/*.sh .claude/memory/*.sh`
- `diff -q` each changed pair under `templates/` vs `.claude/` → identical.
- `bash .claude/memory/lint.sh` → clean (all 15 nodes migrated, none empty).
- `bash tests/requirements.sh` → passes.
- `bash tests/router-auto-plan.sh && bash tests/marker.sh && bash tests/exit-plan-mode.sh` → pass.
  (`tests/consolidate.sh` + `tests/inform-never-block.sh` carry pre-existing,
  unrelated failures — confirm they are unchanged, not newly broken.)
- Manual: run `post-edit-marker.sh` with a payload editing a tracked source file
  and confirm the emitted `additionalContext` includes the requirements.

## Close-out checklist
- ADR: WRITE — 0021-per-node-requirements: per-node requirements checklist, surfaced at edit time
- Nodes: UPDATE — docs/memory/memory/helpers.md, docs/memory/memory/phase-a-marker.md, docs/memory/memory/phase-b-consolidation.md, docs/memory/testing/smoke-tests.md (their `code:` sources changed)
- CLAUDE.md: UPDATE — Hooks (post-edit-marker now surfaces requirements)
- Tests: tests/requirements.sh added
- TODO: NONE

## Risks / unknowns
- Migration atomicity: the `EXPECTED` rename in lint and the 15 node renames
  must land together, or lint transiently reports 15 ordering issues (no runtime
  break — lint is informational).
- `templates/` and `.claude/` copies must stay byte-identical for the 4
  mechanism files; a drift would mean the installed hook differs from the
  distributed one.
