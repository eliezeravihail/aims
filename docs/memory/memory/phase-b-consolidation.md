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
parents: []
children: []
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
last_touched: 2026-05-27T21:44:32Z
last_consolidated: 2026-05-27T21:44:32Z
---

## Purpose

Phase B of the two-phase design: the consolidation pass that rewrites
dirty node bodies. Wired to `Stop` with a bash throttle (default: 5
dirty nodes OR 30 min since last consolidation) so the hot path stays
cheap when there is nothing to do. SessionEnd runs the same
consolidation un-throttled as a safety net. `/done` forces it. The
hook never overwrites referenced source files — only node bodies and
breadcrumbs (non-duplication invariant).

## Design rationale

- The throttle is bash-only; the LLM is never asked "should we run?"
  Cost-control happens before any prompt is built.
- Consolidation is **in-band** (ADR-0009): the hook composes a prompt
  in bash and emits it as `additionalContext`; the active Claude Code
  session performs the Edits in its next turn and finishes each node
  with `bash .claude/memory/mark.sh <node> consolidated`. No external
  API key, no `curl`, no parallel curl path.
- Per-turn cap of 10 nodes (`stop-consolidate.sh:117`) keeps prompt
  size bounded; remaining nodes are re-queued on the next `Stop`.
- `consolidate.sh` emits **two** diff sections per source: committed
  history since `last_touched` (4 KB cap) and the current working
  tree + index diff (4 KB cap). The split lets a Stop-throttled
  consolidation fire mid-session — before any commit — and still
  give the model real signal about what just changed. Combined cap
  remains 8 KB per source.
- Transcript URLs are harvested in bash and offered to the model
  under "## Pointers > External" rather than synthesized inside the
  model — keeps the network surface in bash.

## Invariants & gotchas

- `stop-consolidate.sh` MUST NOT touch a node's
  `dirty/last_touched/last_consolidated` frontmatter; only `mark.sh
  consolidated` does, after the Edit succeeds.
- The state file `.claude/memory/.last-consolidated` is bumped the
  moment the prompt is queued (not after the Edit lands), so a slow
  model doesn't cause a re-nudge on the very next turn.
- The hook always exits 0; a stuck model leaves dirty markers
  visible in `doctor.sh` for self-healing on the next `Stop`.

## Known issues

- fixed: `Stop` hook required `ANTHROPIC_API_KEY` and silently
  skipped consolidation without it — replaced with the in-band
  injection mechanism (commit 0c0852f).

## Pointers

- ADR-0007 — two-phase design (partially superseded for this node).
- ADR-0008 — node body schema the prompt enforces.
- ADR-0009 — in-band consolidation mechanism.
- `templates/hooks/stop-consolidate.sh:1-148` — orchestrator.
- `templates/memory/consolidate.sh:1-100` — per-node prompt builder.

## Open questions

- Should the per-turn cap (10) be configurable per project, or is
  the conservative default sufficient given the 8 KB/node diff cap?
