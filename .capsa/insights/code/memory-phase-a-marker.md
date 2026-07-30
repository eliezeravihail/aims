---
kind: code
title: "Phase A of the two-phase maintenance design: a PostToolUse hook on"
created: 2026-07-15
updated: 2026-07-29
code_globs: ["templates/hooks/post-edit-marker.sh", ".claude/hooks/post-edit-marker.sh", "templates/memory/mark.sh"]
tags: [memory]
---

## Purpose

Phase A of the two-phase maintenance design: a PostToolUse hook on
Edit/Write/MultiEdit/NotebookEdit that names every insight whose
`code_globs` covers the edited file (via `mark.sh` + `list_insights`),
refreshes an advisory marker kept OUTSIDE the capsule (Capsa §1.5), and
injects a factual note. Staleness itself is COMPUTED (Capsa §1.4), not
flagged — the marker is only a cache. Unmatched paths go to the
out-of-capsule inbox. Dumb on purpose — judgment is deferred to Phase B
(ADR-0007/0009). Never blocks, always exits 0.

## Invariants & gotchas

- Never blocks, never exits non-zero — a broken marker must not block
  the user's edit.
- Skip-list: `.capsa/*` (the capsule is data, not tracked code),
  `.claude/*`, `.git/*`, and vendored dirs (`node_modules`/`dist`/
  `build`). Decision records live in `.capsa/decisions/` and belong in
  insight `## Pointers` prose, not `code_globs`.
- The advisory marker (session-id + mtime, kept under `.claude/`,
  §1.5) is the ONLY sidecar since ADR-0030 retired the strict `.lock`.
  Same session refreshes silently; another session's marker younger
  than `AIMS_NODE_LOCK_STALE_SEC` (3600s) → "possible concurrent edit"
  note (ask the user before updating); older → taken over.
- Marker writes are symlink-guarded + O_EXCL (M4) — a planted symlink
  cannot redirect the write.
- `path_matches` (in `_lib.sh`) is the single matching implementation;
  don't reimplement. Output JSON goes through `json_escape`.

## Pointers

- ADR-0007 — Phase A specification.
- ADR-0024 — introduced the `.marker`/`.lock` split (the `.lock` half
  now retired by ADR-0030).
- ADR-0030 — advisory markers are the only cross-session signal.
- tests/marker.sh — smoke cases incl. glob matching (ADR-0014).

## Deltas

- 2026-06-11: mutex split — advisory `.marker` vs strict `.lock`;
  symlink-guarded marker write (M4) — 124e74a, ADR-0024.
- 2026-06-11: `docs/adr/` became a tracked surface (D2) — e409d6e.
- 2026-07-15: `docs/plans/*` added to the skip-list (drafts no longer
  leak into `_inbox.md`); `mark.sh consolidated` now triggers
  `readme-sync.sh` and no longer removes `.lock` sidecars — ADR-0030,
  plan 0017.
- 2026-07-29: retargeted to Capsa — names insights by `code_globs`,
  staleness computed not flagged, markers + inbox moved OUTSIDE the
  capsule (§1.5), skip-list now `.capsa/*`+`.claude/*` — f62ef11
  (decision 0031).
