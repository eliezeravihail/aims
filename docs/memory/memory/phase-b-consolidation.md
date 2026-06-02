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
last_touched: 2026-06-02T15:43:39Z
last_consolidated: 2026-06-02T15:43:39Z
---

## Purpose

Phase B of the two-phase design: the consolidation pass that rewrites
dirty node bodies. Wired to `Stop` with a bash throttle (default: 5
dirty nodes OR 30 min since last consolidation) so the hot path stays
cheap when there is nothing to do. SessionEnd runs the same
consolidation un-throttled as a safety net. Plan close-out (the /plan
Phase 4 flow) also forces consolidation of touched nodes. The hook
never overwrites referenced source files — only node bodies and
breadcrumbs (non-duplication invariant).

## Design rationale

- The throttle is bash-only; the LLM is never asked "should we run?"
  Cost-control happens before any prompt is built.
- Consolidation is **in-band** (ADR-0009): the hook composes a prompt
  in bash and injects it via the Stop-hook `decision: block` + `reason`
  contract; blocking keeps the turn going so the active Claude Code
  session performs the Edits and finishes each node with
  `bash .claude/memory/mark.sh <node> consolidated`. No external API
  key, no `curl`, no parallel curl path. (`hookSpecificOutput.
  additionalContext` is NOT a valid Stop field — using it makes the
  harness reject the output and silently drops the nudge.)
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
- **Multi-session safety via sidecar lockfiles (ADR-0019, supersedes
  ADR-0018):** after the throttle trips, the hook attempts to create
  `<leaf>.lock` next to each dirty node using `set -C` (`O_EXCL`) with
  the SESSION_ID as the body. Nodes whose sidecar already exists and is
  fresh (mtime within `AIMS_LOCK_TTL_SEC`, default 600s) are skipped —
  another session owns them. A `trap ... EXIT` releases any locks we
  hold if the hook dies before `mark.sh consolidated` removes them on
  success. Mutex visibility is git-style: `ls docs/memory/<tag>/` shows
  who is editing what. The frontmatter is no longer touched for mutex
  purposes; the ADR-0018 `consolidating_by` field is gone.

## Invariants & gotchas

- `stop-consolidate.sh` MUST NOT touch a node's
  `dirty/last_touched/last_consolidated` frontmatter; only `mark.sh
  consolidated` does, after the Edit succeeds. Per ADR-0019 the mutex
  is a sidecar `<leaf>.lock` file, not a frontmatter field — so this
  invariant holds without exception now.
- The state file `.claude/memory/.last-consolidated` is bumped the
  moment the prompt is queued (not after the Edit lands), so a slow
  model doesn't cause a re-nudge on the very next turn.
- The hook emits `decision: block` ONLY when the throttle trips (to
  inject the prompt); otherwise it exits 0 with no output. A stuck
  model leaves dirty markers visible in `doctor.sh` for self-healing
  on the next `Stop`.

## Known issues

- fixed: `Stop` hook required `ANTHROPIC_API_KEY` and silently
  skipped consolidation without it — replaced with the in-band
  injection mechanism (commit 0c0852f).
- fixed: in-band injection used `hookSpecificOutput.additionalContext`,
  which Claude Code v2.1.153 rejects for the Stop event — the nudge
  silently failed validation. Switched to `{"decision":"block",
  "reason":...}` (commit f44f19c).

## Pointers

- ADR-0007 — two-phase design (partially superseded for this node).
- ADR-0008 — node body schema the prompt enforces.
- ADR-0009 — in-band consolidation mechanism.
- ADR-0018 — superseded (in-frontmatter claim experiment).
- ADR-0019 — sidecar `<leaf>.lock` mutex + EXIT trap; the design in
  force.
- ADR-0021 — the consolidation prompt carries the reply-format note:
  hook results are reported to the user as a single line
  `===[aims: <message>]===`.
- `templates/hooks/stop-consolidate.sh:1-148` — orchestrator.
- `templates/memory/consolidate.sh:1-100` — per-node prompt builder.

## Open questions

- Should the per-turn cap (10) be configurable per project, or is
  the conservative default sufficient given the 8 KB/node diff cap?
