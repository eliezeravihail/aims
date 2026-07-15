# ADR-0028: Consolidation appends dated deltas; nodes carry four sections
Status: proposed
Date: 2026-07-15
Supersedes: — (amends ADR-0008 and ADR-0009)
Superseded by: —

## Context

Under ADR-0008/0009 every consolidation was a **full body rewrite**
against a six-section schema (Purpose, Design rationale, Invariants &
gotchas, Known issues, Pointers, Open questions), executed in-band at
Stop-time. Two structural costs accumulated:

1. **The task shape invited false reports.** Rewrite-under-constraints
   at the end of a turn is exactly the work the model skipped while
   claiming otherwise — the failure mode that forced ADR-0027's
   discrepancy detector. The detector treats the symptom; the task
   shape is the cause.
2. **Two of six sections were drifting paraphrase.** "Design rationale"
   and much of "Known issues" restated ADR and commit-message content;
   each rewrite re-summarized them, drifting further from the sources
   they mirror. The 2026-07-15 review found a node
   (`hooks/pre-write.md`) whose body described blocking behavior that
   ADR-0020 had removed weeks earlier.

The evidence payload was also oversized: full `git log -p` patches
(4 KB × 2 per source) where a delta line needs only what changed and
why.

## Decision

We will make **delta-append the default consolidation action** and slim
the node schema to four sections:

```
## Purpose               one short paragraph
## Invariants & gotchas  what must not break; `- open: …` for undecided questions
## Pointers              ADRs / plans / commits / external, each with why-it-matters
## Deltas                appended, newest last:
                         - <commit-date>: <what changed and why> — <SHA|ADR|plan-slug>
```

Per consolidation the model (a) appends one dated delta line per
meaningful change — dated by the **commit date** from the evidence,
today's date only for uncommitted work — and (b) fixes in place any
sentence in Purpose/Invariants that the change falsified. A **full
rewrite runs only at compaction thresholds**: deltas ≥
`AIMS_MEMORY_DELTA_MAX` (default 12) or body > 150 lines, at which
point delta lines fold into the three sections above them. Evidence
shrinks to commit summaries (`git log --pretty='%h %ad %s' --stat`,
2 KB cap) instead of full patches.

Old-schema content maps as: Design rationale → Pointers ("ADR-NNNN —
why") or Invariants; Known issues `fixed:` → Deltas; Known issues
`open:` and Open questions → `- open:` bullets under Invariants.

## Consequences

- ✅ The routine consolidation task becomes append + spot-fix — cheap
  to do honestly, hard to fake accidentally; the ADR-0027 detector
  becomes a backstop instead of a load-bearing wall.
- ✅ Stop-hook prompt size drops by roughly an order of magnitude
  (summaries not patches; no full-body rewrite instructions).
- ✅ Less to rot: sections that mirrored ADRs no longer exist to drift.
- ⚠️ Delta lines accrete noise between compactions; accepted — the
  threshold bounds it and lint warns when compaction is due.
- ⚠️ A one-time migration of all existing nodes is required; lint
  enforces the new schema immediately, so stragglers are visible.
- 🔒 Rules out returning to unconditional full rewrites, and rules out
  per-node freeform section sets (lint pins the four headings).

## Alternatives considered

- **Keep six sections, rewrite less often**: rejected — frequency was
  not the problem; the rewrite task shape and duplicated sections were.
- **Deltas as a separate sidecar file per node**: rejected — splits the
  injectable context in two; the body IS the interface (ADR-0008).
- **Commit-message mining instead of model-written deltas**: rejected —
  loses the "why it matters here" judgment that makes a delta worth
  reading.

## Verification

- `templates/memory/consolidate.sh` — `MODE=delta|compact` selection
  block and the two ACTION texts.
- `templates/memory/lint.sh` — `EXPECTED='## Purpose|## Invariants &
  gotchas|## Pointers|## Deltas|'` plus the compaction-due warning.
- `bash tests/consolidate.sh` — covers both modes.
