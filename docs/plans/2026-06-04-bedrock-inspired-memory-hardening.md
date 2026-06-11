# Plan: Bedrock-inspired memory hardening
Status: superseded-by docs/plans/2026-06-11-aims-audit-fixes-master.md
Started: 2026-06-04
Superseded: 2026-06-11

## Supersession note (2026-06-11)

All three items from this plan were absorbed into the master audit-fixes
plan and shipped there:

- **Size cap (lint.sh)** → Track 5 of the master plan. Shipped in
  commit `91fe2bd` ("track 5: low-pri correctness + bash≥4 guard +
  leaf size cap"). Credit to project-bedrock
  (https://github.com/robotaitai/project-bedrock) preserved in
  `templates/memory/lint.sh`.

- **Compaction invariants (consolidate.sh)** → Track 2 of the master
  plan, alongside the ADR-0025 data-not-instructions framing. Shipped
  in commit `48e3988` ("track 2: security — data framing + bounded
  install-on deletion"). Credit to project-bedrock preserved in
  `templates/memory/consolidate.sh` ACTION section.

- **PreCompact hook (`templates/hooks/pre-compact.sh`)** → Track 3
  of the master plan. Shipped in commit `9973146` ("track 3:
  Stop/SessionEnd correctness + JSON escaping + PreCompact"). The
  implementation incorporates the SessionEnd lesson (M3 — never
  bump throttle without work) that this plan did not anticipate.
  Credit to both project-bedrock and claude-code-context-handoff
  (https://github.com/who96/claude-code-context-handoff) preserved
  in `templates/hooks/pre-compact.sh`.

The `Work/NOW.md` open question listed below remains intentionally
deferred — not folded into the master plan, available as a future
follow-up if needed.

---

## Original draft (preserved for reference; do not implement)

## תקציר מנהלים
מאמצים שלושה דפוסים מ-project-bedrock אל aims, כדי להפוך משמעת-זיכרון מ"שיקול דעת" ל"בדיקות חוזרות": (1) מגבלת גודל לעלי-זיכרון ב-`lint.sh` (אזהרה ~150 שורות, קריטי ~200) כדי לאלץ פיצול בזמן; (2) ניסוח מפורש של אינווריאנטות דחיסה ב-`consolidate.sh` ("כל עובדה בת-קיימא חייבת לשרוד דחיסה — להזיז או למזג, לעולם לא למחוק", ו"קבצי evidence/raw imports אינם נוגעים בדחיסה") כדי לקבע את הכוונה ברמת הפרומפט; (3) hook חדש `pre-compact.sh` שמפעיל את צינור הדחיסה הקיים לפני ש-Claude Code מסכם את ההקשר, תחת ADR-0020 — מודיע, לעולם לא חוסם. שלוש המשימות עצמאיות ונשלחות בנפרד בסדר: lint → invariant → PreCompact.

## Changes

### templates/memory/lint.sh (+ .claude/memory/lint.sh mirror)
Append a size-cap check inside the per-leaf loop, before the section-heading check. Counts non-frontmatter body lines so frontmatter bloat doesn't trigger the cap. Soft — reports an issue but exit stays 0 (ADR-0020 spirit; lint is already informational).
```bash
  # Size cap (bedrock-inspired): warn at AIMS_LEAF_WARN_LINES, critical at
  # AIMS_LEAF_CRIT_LINES. Counts body lines only (excludes YAML frontmatter)
  # so schema overhead doesn't trip the cap. Informational — never blocks.
  WARN_LINES="${AIMS_LEAF_WARN_LINES:-150}"
  CRIT_LINES="${AIMS_LEAF_CRIT_LINES:-200}"
  fm_end=$(fm_end_line "$leaf")
  total=$(wc -l <"$leaf" | tr -d ' ')
  body=$(( total - fm_end ))
  if [ "$body" -ge "$CRIT_LINES" ]; then
    printf '%s: CRITICAL size %d lines (>=%d) — split now\n' \
      "$leaf" "$body" "$CRIT_LINES"
    issues=$((issues + 1))
  elif [ "$body" -ge "$WARN_LINES" ]; then
    printf '%s: WARNING size %d lines (>=%d) — split at next opportunity\n' \
      "$leaf" "$body" "$WARN_LINES"
    issues=$((issues + 1))
  fi
```

### templates/memory/consolidate.sh (+ .claude/memory/consolidate.sh mirror)
Insert a new "INVARIANTS (hard, bedrock)" block at the top of the per-node ACTION text — before the existing six-section schema instructions — so it dominates the prompt frame.
```text
ACTION FOR THIS NODE:

INVARIANTS (hard, never violate):
   - Every durable fact must survive compaction — move or merge, never delete.
     If you remove text, the fact it encoded must land elsewhere in this node
     or in a related node, with a pointer back.
   - Evidence files and raw imports are never touched during compaction
     (aims has no Evidence/ today; this guards future drift).
   - Superseded decisions are marked (e.g. "Status: reversed" + SHA),
     not deleted.

1. Rewrite the body per the ADR-0008 schema (six sections, in order):
   ... (existing text unchanged) ...
```

### templates/hooks/pre-compact.sh (NEW, + .claude/hooks/pre-compact.sh mirror)
PreCompact fires just before Claude Code summarizes context. Delegates to the existing forced consolidation path (same as SessionEnd) so any dirty leaves are flushed while their source context still exists. Always exits 0 — best-effort, never blocks compaction (ADR-0020).
```bash
#!/usr/bin/env bash
# aims PreCompact hook — best-effort flush of dirty memory leaves before
# Claude Code summarizes context. Per ADR-0020: inform, never block.
# PreCompact must always succeed; consolidation failure is silent.

set -u

if [ -d ".claude/hooks" ]; then
  HOOKS_DIR=".claude/hooks"
elif [ -d "templates/hooks" ]; then
  HOOKS_DIR="templates/hooks"
else
  exit 0
fi

# Drain payload so the upstream pipe doesn't SIGPIPE us.
[ ! -t 0 ] && cat >/dev/null 2>&1 || true

# Delegate to the forced path (same as SessionEnd). It already:
#   - is a no-op when nothing is dirty
#   - emits a `decision: block` JSON only when work is queued
# For PreCompact we must NOT block compaction — discard stdout and always
# exit 0. The throttle state file is still bumped, which is desirable.
bash "$HOOKS_DIR/stop-consolidate.sh" --force >/dev/null 2>&1 || true

exit 0
```

### templates/settings.json.tmpl (+ .claude/settings.json mirror)
Add a PreCompact entry alongside the existing lifecycle hooks.
```json
    "PreCompact": [
      {
        "hooks": [
          { "type": "command", "command": "bash .claude/hooks/pre-compact.sh" }
        ]
      }
    ],
```

## Open design questions
- **Size cap severity in `doctor.sh`**: should `doctor.sh` exit non-zero on CRITICAL leaves (hard gate before release), or stay informational like `lint.sh`? Default in this draft: informational everywhere. Decide at implementation.
- **PreCompact scope**: run the FULL `stop-consolidate.sh --force` (drafted above), or a slimmer path that only marks/finds dirty without injecting the long in-band prompt? The full path is simpler and consistent; the slim path is faster but adds a code branch. Default: full path; revisit if PreCompact latency hurts.
- **`Work/NOW.md` "current focus" surface (DEFERRED, do not decide here)**: bedrock keeps a single short note of what's being worked on right now, distinct from in-progress plans and past ADRs. aims has a gap there — `docs/plans/*.md` with `Status: in-progress` is the closest proxy, but it's per-task, not per-session-focus. Adding a third surface risks drift (which surface owns what?). Flag as an open question; do not introduce in this plan.

## Verification
- `bash -n templates/hooks/pre-compact.sh .claude/hooks/pre-compact.sh templates/memory/lint.sh templates/memory/consolidate.sh`
- `bash .claude/memory/lint.sh` — runs clean on current tree (all leaves are <150 body lines; `helpers.md` is 130, closest); manually pad a fixture to >150 and >200 to confirm WARNING/CRITICAL emit.
- `bash .claude/memory/consolidate.sh docs/memory/memory/helpers.md | grep -F 'every durable fact must survive compaction'` — invariant text appears.
- `printf '{}' | bash .claude/hooks/pre-compact.sh; echo exit=$?` — exits 0 with no stdout when nothing is dirty.
- `bash tests/inform-never-block.sh` — still passes (pre-compact contains no `exit 2`).

## Close-out checklist
- ADR: WRITE — `0024-precompact-best-effort-never-blocks.md` (new lifecycle hook + new invariant: PreCompact is best-effort and must not block compaction even on consolidation failure). The size-cap and invariant-text changes fold into existing ADR-0007/0008/0009 (no new ADR for those — they refine, not redirect).
- Nodes: UPDATE — `docs/memory/memory/phase-b-consolidation.md` (add `templates/hooks/pre-compact.sh` + `.claude/hooks/pre-compact.sh` to `code:`, document invariants block); `docs/memory/memory/helpers.md` (note new size-cap behavior in `lint.sh`, env vars `AIMS_LEAF_WARN_LINES`/`AIMS_LEAF_CRIT_LINES`).
- CLAUDE.md: UPDATE — `## Hooks` section, add PreCompact bullet alongside UserPromptSubmit / PreToolUse / PostToolUse.
- Tests: EXISTING cover it (`tests/inform-never-block.sh` already greps for blocking exits across `templates/hooks/`); add a fixture-based assertion in a follow-up if the size-cap regresses.
- TODO: `Work/NOW.md` decision deferred; revisit whether `doctor.sh` should hard-fail on CRITICAL leaves.

## Risks / unknowns
- PreCompact payload shape from Claude Code is undocumented in-repo; the hook ignores stdin defensively, which is safe but means we collect no compaction metadata.
- Throttle state bump inside PreCompact may suppress the next Stop-hook consolidation by up to `AIMS_MEMORY_INTERVAL_SEC` (default 1800s). Acceptable — PreCompact already did the work.
