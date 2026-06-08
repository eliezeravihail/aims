# Plan: Per-node requirements — user-sourced, captured in-session
Status: completed
Started: 2026-06-08

## תקציר מנהלים
דרישה היא **כוונת משתמש**, לא עובדת קוד — לכן היא נאספת ממך תוך כדי סשן ולא
מומצאת מקריאת הקוד. כל צומת מקבל אתחול אחיד בסקציה (הממוזגת)
`## Requirements & invariants`: *"לא ידועות דרישות מעבר ל‑CLAUDE.md; לפני עריכה
לאמת שוב מולו"*. הלכידה היא **קונבנציה התנהגותית** המעוגנת ב‑CLAUDE.md: כשאתה
מנסח אילוץ במהלך הדיון (למשל "אל תפר את הממשק", "הקובץ הזה בלתי תלוי בשני") או
כשעורכים קובץ, Claude **שואל אם לרשום זאת כדרישה** לצומת הרלוונטי — ורושם רק
אחרי אישורך. ה‑hook `post-edit-marker` מציג את הדרישות הרשומות **ברגע העריכה**
(factual, ADR-0020); הכלל המרכזי נגד רגרסיות: **אם שינוי מתנגש בדרישה רשומה —
לעצור ולשאול את המשתמש**. שינויי קוד: שם הסקציה מוחלף, `consolidate` מקבל
איסור מפורש להמציא דרישות, ו‑`lint` רק שומר על שם/סדר הכותרות (בלי אכיפת תוכן —
ריק הוא מצב תקין).

## Changes

### CLAUDE.md  — new convention (the heart of the feature)
Add a short "Requirements capture" subsection (and one Hooks bullet). This is
what makes Claude actually perform capture/verify/conflict-ask:
```markdown
## Requirements capture

Requirements are **user intent**, recorded only from the user — never
fabricated from code (that is mere observed behavior). They live per node in
`## Requirements & invariants`.

- **Capture on statement.** When you express a constraint during a session
  ("don't break the interface", "this file is independent of X"), or when a
  file is about to be edited, Claude asks whether to record it as a requirement
  on the relevant node, and records it verbatim only after you confirm.
- **Verify before editing.** A node seeded "no requirements beyond CLAUDE.md"
  means: re-verify against CLAUDE.md (and ask) before changing its code.
- **Conflict → ask.** If a change would conflict with a recorded requirement,
  or two requirements conflict, Claude stops and asks the user rather than
  silently choosing. This is the anti-regression guard for long sessions.
```

### docs/memory/**/*.md  — all 15 nodes (seed, no fabrication)
1. Rename `## Invariants & gotchas` → `## Requirements & invariants`
   (`sed -i 's/^## Invariants & gotchas$/## Requirements \& invariants/'`).
2. Prepend a uniform requirements seed line; keep existing bullets below as
   invariants/gotchas (those are legitimate observed facts, not fabricated
   requirements):
```markdown
## Requirements & invariants

- Requirements: none recorded beyond CLAUDE.md. Before editing, re-verify
  against CLAUDE.md and ask the user.

<existing invariant/gotcha bullets stay here, unchanged>
```

### templates/memory/_lib.sh  +  .claude/memory/_lib.sh
Section-body extractor used by the marker. Append after `list_leaves`:
```bash
# Body of a "## <heading>" section: lines between it and the next "## "/EOF.
# Usage: fm_section <file> <heading-text-without-##>
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

### templates/hooks/post-edit-marker.sh  +  .claude/hooks/post-edit-marker.sh
Surface each matched node's requirements at edit time. Add `reqblock=""` before
the match loop; inside, after `node=$(...)`:
```bash
  reqs=$(fm_section "$leaf" "Requirements & invariants" \
         | sed '/^[[:space:]]*$/d' | head -c 1200)
  [ -n "$reqs" ] && reqblock="${reqblock}"$'\n'"• ${rel} (node ${node}):"$'\n'"${reqs}"$'\n'
```
After NOTE is built, append (factual — names the conflict rule):
```bash
if [ -n "$reqblock" ]; then
  NOTE="${NOTE}"$'\n\n'"Recorded requirements for the edited file (verify the change against them; if it conflicts with one, ask the user; if you stated a new constraint, ask whether to record it):${reqblock}"
fi
```

### templates/memory/lint.sh  +  .claude/memory/lint.sh
Only rename the enforced heading (line 114). **No content-presence check** —
an empty/seeded requirements section is a valid state (requirements are
user-sourced and may be unknown):
```bash
  EXPECTED='## Purpose|## Design rationale|## Requirements & invariants|## Known issues|## Pointers|## Open questions|'
```

### templates/memory/consolidate.sh  +  .claude/memory/consolidate.sh
Rename heading (line 86) and forbid fabricating requirements:
```
   ## Requirements & invariants — KEEP user-recorded requirement bullets
                           verbatim; NEVER invent a requirement from a diff
                           (that is observed behavior, not user intent). You
                           may update invariants/gotchas (code facts) below the
                           requirements. New requirements come only from the
                           user (ask) or CLAUDE.md.
```

### templates/hooks/stop-consolidate.sh  +  .claude/hooks/stop-consolidate.sh
Rename the mining hint (line 211) and scope it to invariants only:
```
Mine for invariants/gotchas (→ ## Requirements & invariants, the non-requirement part), design rationale
```

### templates/memory/new-node.sh  +  .claude/memory/new-node.sh
Rename heading (line 90) + seed scaffold:
```
## Requirements & invariants

- Requirements: none recorded beyond CLAUDE.md. Before editing, re-verify
  against CLAUDE.md and ask the user.

(Invariants/gotchas — what must not break when editing. Concise.)
```

### docs/adr/0021-per-node-requirements.md  (new; created in close-out)
Refines ADR-0008: section #3 renamed to `## Requirements & invariants`;
requirements are user-sourced (captured on statement, confirmed, never
fabricated), seeded uniformly, surfaced at edit time (factual, ADR-0020), and
conflicts are escalated to the user. Append a row to `docs/adr/README.md`.

### tests/requirements.sh  (new)
jq-free smoke test for the mechanical parts (the NL-capture convention is
behavioral, not unit-testable):
- `fm_section` extracts only the named section body.
- `post-edit-marker.sh`, given a payload editing a tracked file, emits
  `additionalContext` containing the node's requirement text.
- `lint.sh` stays clean on a seeded node (renamed heading, seed line present).

## Open design questions
- Detecting a "stated constraint" in free chat is the model's judgment;
  something said in passing may be missed. Mitigation: also prompt at
  edit-time (post-edit-marker surfaces requirements + the ask-to-record note).
  Accept residual reliance on model judgment — there is no reliable bash parse
  of natural-language requirements.
- Conflict detection (change vs. recorded requirement) is also model judgment;
  the rule is "if you notice a conflict, ask." Not automatable.
- Once a node has ≥1 real recorded requirement, the uniform seed line should be
  dropped (it only states "none known"). Proposed: remove the seed line at the
  moment the first real requirement is recorded.

## Verification
- `bash -n templates/hooks/*.sh templates/memory/*.sh .claude/hooks/*.sh .claude/memory/*.sh`
- `diff -q` each changed `templates/` vs `.claude/` pair → identical.
- `bash .claude/memory/lint.sh` → clean (all 15 nodes: renamed heading + seed).
- `bash tests/requirements.sh` → passes.
- `bash tests/router-auto-plan.sh && bash tests/marker.sh && bash tests/exit-plan-mode.sh` → pass.
  (`tests/consolidate.sh`, `tests/inform-never-block.sh`: confirm only the
  pre-existing, unrelated failures remain — nothing newly broken.)
- Manual: run `post-edit-marker.sh` with a payload editing a tracked source
  file; confirm the emitted `additionalContext` includes the seeded requirement.

## Close-out checklist
- ADR: WRITE — 0021-per-node-requirements: user-sourced requirements captured in-session, seeded + surfaced at edit time, conflict→ask
- Nodes: UPDATE — docs/memory/memory/helpers.md, docs/memory/memory/phase-a-marker.md, docs/memory/memory/phase-b-consolidation.md, docs/memory/testing/smoke-tests.md (their `code:` sources changed)
- CLAUDE.md: UPDATE — new "Requirements capture" section + Hooks bullet (post-edit-marker surfaces requirements)
- Tests: tests/requirements.sh added
- TODO: NONE

## Risks / unknowns
- The capture/verify/conflict behavior depends on Claude reading the CLAUDE.md
  convention (it is always in context) — there is no hard enforcement; aims
  informs, never blocks (ADR-0020).
- Migration atomicity: the `EXPECTED` rename in lint and the 15 node renames
  must land together (lint is informational, so a transient mismatch only
  prints, never breaks).
- `templates/` and `.claude/` copies of the 4 mechanism files must stay
  byte-identical.

## Outcome
Implemented. Section #3 of the node schema is now `## Requirements &
invariants` across `lint.sh` (`EXPECTED`), `consolidate.sh`, `new-node.sh`,
`stop-consolidate.sh`, and all 15 nodes (each seeded "none recorded beyond
CLAUDE.md"). `_lib.sh` gained `fm_section`; `post-edit-marker.sh` surfaces a
node's requirements at edit time (factual, ADR-0020) and names the
verify/conflict/ask rules. The capture model lives in CLAUDE.md
("Requirements capture"): user-sourced only, recorded on confirmation, seed
dropped on first real requirement, conflict → ask. `consolidate.sh` is
forbidden from fabricating requirements; `lint.sh` enforces heading/order
but not content. ADR: docs/adr/0021-per-node-requirements.md (proposed,
refines ADR-0008). Open design questions resolved: requirement detection and
conflict detection are accepted as model judgment, mitigated by edit-time
surfacing; the seed line is dropped when the first real requirement is
recorded (CLAUDE.md convention).

## Closing checks
Verification (run from repo root):
- `bash -n` on all hooks/helpers/tests → OK.
- `templates/` vs `.claude/` parity for the 6 changed mechanism files → identical.
- `bash .claude/memory/lint.sh` → clean (15 nodes).
- `bash .claude/memory/doctor.sh` → 0 dirty, 0 inert, lint clean; 3 nodes
  >4 KB (ADR-0008 soft norm, informational — not addressed here).
- `tests/requirements.sh` (4 cases), `router-auto-plan.sh`, `marker.sh`,
  `exit-plan-mode.sh` → PASS.
- `tests/consolidate.sh`, `tests/inform-never-block.sh` → only their
  pre-existing, unrelated failures remain (unchanged by this plan).

Resolved checklist:
- ADR: WROTE — docs/adr/0021-per-node-requirements.md (proposed; refines ADR-0008) + README index row.
- Nodes: UPDATE — memory/helpers, memory/phase-a-marker, memory/phase-b-consolidation, testing/smoke-tests (consolidated); all 15 nodes renamed+seeded.
- CLAUDE.md: UPDATE — new "Requirements capture" section + PostToolUse Hooks bullet.
- Tests: tests/requirements.sh added.
- TODO: NONE (3 nodes >4 KB is a pre-existing soft-norm note, out of scope).
