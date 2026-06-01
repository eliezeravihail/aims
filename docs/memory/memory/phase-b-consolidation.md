---
node: memory/phase-b-consolidation
kind: module
code:
  - templates/hooks/stop-consolidate.sh
  - templates/hooks/session-end.sh
  - .claude/hooks/stop-consolidate.sh
  - .claude/hooks/session-end.sh
  - templates/memory/consolidate.sh
  - templates/memory/classify-inbox.sh
  - templates/memory/check-refs.sh
commits: []
sessions:
  - docs/plans/memory-tree-system.md
related:
  - memory/phase-a-marker
  - memory/helpers
  - discipline/done
claude_md_refs:
  - "Hooks"
external_refs:
  - { path: docs/adr/0007-tree-based-memory-with-auto-maintenance.md, kind: adr, why: Phase B specification — the throttled LLM consolidation pass }
  - { path: tests/consolidate.sh, kind: test, why: end-to-end test against a Python mock Anthropic endpoint }
owners:
  - ema
dirty: false
last_touched: 2026-05-25T11:46:53Z
last_consolidated: 2026-05-25T11:46:53Z
---

## Purpose

Phase B of the two-phase design: the LLM consolidation pass. Wired to `Stop` with a bash throttle (default: 5 dirty leaves OR 30 min since last consolidation) so the hot path stays at ~18ms when there's nothing to do. SessionEnd runs the same consolidation un-throttled as a safety net. /done forces it. consolidate.sh asks the model to update the leaf body from git diffs of referenced sources and to append breadcrumbs for changed external_refs / claude_md_refs — never overwrites the referenced files themselves (non-duplication invariant).

## Logical rules & invariants

- Never blocks. Always exits 0.
- Throttle: run only when `N_DIRTY >= DIRTY_MAX` (default 5) OR `ELAPSED >= INTERVAL_SEC` (default 1800s). `--force` bypasses both.
- If `ANTHROPIC_API_KEY` is absent, leaves stay dirty and the hook exits 0 silently.
- The non-duplication invariant: consolidation updates leaf bodies only — it never writes to CLAUDE.md, ADRs, plans, or other external files.
- `classify-inbox.sh` output is informational at Stop time; auto-applying confident classifications happens only inside `/done`.

## Editing considerations

- The state file (`.claude/memory/.last-consolidated`) stores a plain Unix timestamp (seconds since epoch). The format must not change — both `stop-consolidate.sh` and `check-refs.sh` read it.
- `--force` / `-f` is the `/done` code path. Do not add throttle checks inside the `FORCE=1` branch.
- Overrides via `throttle.conf` (a sourced shell snippet) take effect on the two `AIMS_MEMORY_*` variables. Document any new tunables there.

## Deliberations & history

## Open questions
