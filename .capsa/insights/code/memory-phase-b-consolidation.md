---
kind: code
title: "Phase B: the throttled Stop-hook pass that keeps node bodies current."
created: 2026-07-15
updated: null
code_globs: ["templates/hooks/stop-consolidate.sh", "templates/hooks/session-end.sh", "templates/hooks/pre-compact.sh", ".claude/hooks/stop-consolidate.sh", ".claude/hooks/session-end.sh", ".claude/hooks/pre-compact.sh", "templates/memory/consolidate.sh", "templates/memory/classify-inbox.sh", "templates/memory/check-refs.sh", "docs/adr/0028-delta-consolidation-and-four-section-schema.md", "docs/adr/0030-retire-strict-consolidation-lock.md"]
tags: [memory]
---

## Purpose

Phase B: the throttled Stop-hook pass that keeps node bodies current.
Bash-only throttle (5 dirty nodes OR 30 min); when tripped, the hook
assembles per-node prompts from `consolidate.sh` and injects them via
the Stop-hook `decision: block` + `reason` contract (ADR-0009/0026) so
the active session Edits in-band and finishes each node with `mark.sh
<node> consolidated`. Per ADR-0028 the default per-node action is
**delta-append** (one dated line + minimal truth-fixes); **compact**
(full 4-section rewrite folding deltas) only past thresholds
(`AIMS_MEMORY_DELTA_MAX`=12 deltas or >150 body lines). SessionEnd is
a stderr breadcrumb only; PreCompact fires an advisory before context
compaction.

## Invariants & gotchas

- The hook MUST NOT touch node frontmatter; only `mark.sh consolidated`
  does.
- Stop is the only hook that may emit `decision: block` — it is the
  in-band continuation channel, not a refusal (ADR-0026).
  `hookSpecificOutput.additionalContext` is invalid for Stop and gets
  silently rejected by the harness.
- The throttle state file is bumped when the prompt is QUEUED (not
  after Edits land) to avoid re-nudge on the very next turn; SessionEnd
  must never bump it (M3).
- **No consolidation mutex** (ADR-0030): dirty nodes are handed to the
  model unfiltered; the worst concurrent case is a last-write-wins
  delta append. The advisory `.marker` remains the cross-session
  signal.
- ADR-0027 discrepancy detection: a state snapshot
  (`docs/memory/.last-report-snapshot`, gitignored) is written on
  every emit; an unchanged snapshot on the next fire prepends a
  factual "previous report did not match measured state" breadcrumb.
  Drain-claim reply words are reserved for actually-drained state.
- Evidence per source is commit summaries (`git log --pretty='%h %ad
  %s' --stat`, 2 KB cap) + uncommitted stat/patch (2 KB cap); delta
  dates come from the `%ad` field (today only for uncommitted-only
  changes). Payloads are fenced as data (ADR-0025).
- Per-turn cap of 10 nodes; the rest re-queue on the next Stop.
  bash ≥ 4 required (soft guard, exits 0 on 3.2).
- open: should the per-turn cap (10) be configurable per project?

## Pointers

- ADR-0009 — in-band mechanism; ADR-0026 — the `decision: block`
  carve-out; ADR-0021 — the `===[aims: <msg>]===` reply format.
- ADR-0028 — delta/compact modes (the prompt shapes live in
  `consolidate.sh`).
- ADR-0030 — strict-lock retirement (supersedes ADR-0024's strict
  half; 0018→0019→0024 lineage closed).
- ADR-0025 / ADR-0027 — data fences; discrepancy snapshot.
- templates/hooks/stop-consolidate.sh — orchestrator;
  templates/memory/consolidate.sh — per-node prompt builder.

## Deltas

- 2026-05-27: API-key/curl consolidation replaced by in-band Stop
  injection — ADR-0009.
- 2026-06-02: injection switched from `additionalContext` (rejected on
  Stop) to `decision: block` + `reason` — ADR-0026 records the
  carve-out.
- 2026-06-11: mutex split `.marker`/`.lock` (124e74a, ADR-0024);
  centralized `json_escape` + SessionEnd demoted to breadcrumb +
  PreCompact added (9973146); data fences on diff payloads (48e3988,
  ADR-0025); discrepancy snapshot (ba9d38d, ADR-0027); bash≥4 guard
  (91fe2bd).
- 2026-07-15: delta-append became the default consolidation action
  with threshold-gated compaction; evidence shrunk to commit summaries
  (2 KB caps) — ADR-0028.
- 2026-07-15: strict `.lock` claim/reap/trap machinery removed from the
  Stop hook — ADR-0030,
  docs/plans/2026-07-15-memory-subsystem-diet.md.
