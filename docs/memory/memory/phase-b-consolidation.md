---
node: memory/phase-b-consolidation
kind: module
code:
  - templates/hooks/stop-consolidate.sh
  - templates/hooks/session-end.sh
  - templates/hooks/pre-compact.sh
  - .claude/hooks/stop-consolidate.sh
  - .claude/hooks/session-end.sh
  - .claude/hooks/pre-compact.sh
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
last_touched: 2026-06-11T11:46:17Z
last_consolidated: 2026-06-11T11:46:17Z
---

## Purpose

Phase B of the two-phase design: the consolidation pass that rewrites
dirty node bodies. Wired to `Stop` with a bash throttle (default: 5
dirty nodes OR 30 min since last consolidation) so the hot path stays
cheap when there is nothing to do. SessionEnd is now a stderr
breadcrumb only — it reports dirty count but does NOT trigger
consolidation and does NOT bump the throttle (M3, ADR-0027). A new
PreCompact hook fires an advisory before context compaction so
signal isn't lost. Plan close-out (the /plan Phase 4 flow) still
forces consolidation of touched nodes. The hook never overwrites
referenced source files — only node bodies and breadcrumbs
(non-duplication invariant).

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
- **Mutex protocol split (ADR-0024, supersedes ADR-0019).** Two
  separate sidecars now coexist: `<leaf>.marker` is the advisory
  PostToolUse breadcrumb owned by `post-edit-marker.sh` (H1); the
  strict cross-session mutex `<leaf>.lock` is owned exclusively by
  `stop-consolidate.sh`, acquired with `set -C` (`O_EXCL`) writing
  the SESSION_ID, with `trap ... EXIT` releasing on abnormal exit
  and `mark.sh consolidated` releasing on success (H2). The two
  artifacts used to share one suffix and silently overwrote each
  other under concurrent sessions.
- **ADR-0027 discrepancy detection.** After preparing the prompt,
  the hook snapshots the current dirty-set to
  `docs/memory/.last-report-snapshot`. On the next Stop fire, if
  the snapshot is unchanged (the model reported "consolidated N
  nodes" without actually calling `mark.sh consolidated`), a
  factual breadcrumb is prepended to the prompt so the model
  recognises and corrects the stall.
- **ADR-0025 data-framing fences.** `consolidate.sh` wraps per-source
  diff payloads in fenced data blocks with a "data, not instructions"
  notice; the Stop-hook ACTION block is prepended with the
  project-bedrock compaction invariants so consolidation guidance
  survives compaction.
- **Centralized `json_escape`** in `_lib.sh` (M2) replaces ad-hoc
  per-hook escaping when assembling the Stop-block payload —
  handles all C0 control chars uniformly.
- **Bash≥4 soft guard** at the top of the hook (L4) prints a
  one-line advisory and exits 0 on older shells rather than
  misbehaving silently.
- **PreCompact hook (Track 3, inspired by project-bedrock and
  claude-code-context-handoff).** Advisory only — fires before
  context compaction with the dirty-node summary so the user can
  consolidate before signal is lost.

## Invariants & gotchas

- `stop-consolidate.sh` MUST NOT touch a node's
  `dirty/last_touched/last_consolidated` frontmatter; only `mark.sh
  consolidated` does, after the Edit succeeds. Per ADR-0024 the
  strict mutex is the sidecar `<leaf>.lock` (Stop-owned), distinct
  from `<leaf>.marker` (marker-owned advisory) — never collapse them.
- ADR-0026 records the Stop-hook `decision: block` carve-out from the
  general inform-never-block rule (ADR-0020): Stop is the only hook
  that legitimately uses `block` because it's the in-band injection
  channel, not a discipline gate.
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
- fixed: concurrent sessions clobbered each other's sidecars because
  the marker and the Stop mutex shared `<leaf>.lock`. Mutex protocol
  split: `.marker` (advisory) vs `.lock` (strict mutex, Stop-owned),
  with EXIT-trap release (commit 124e74a; ADR-0024).
- fixed: Stop-hook JSON payload broke on control characters in node
  paths/diffs because each hook hand-rolled escaping. Centralized
  `json_escape` in `_lib.sh` (commit 9973146; M2).
- fixed: SessionEnd re-ran consolidation un-throttled and bumped
  `.last-consolidated` even with zero dirty nodes, starving the next
  Stop fire of a legitimate turn. Demoted to stderr-only breadcrumb
  (commit 9973146; M3). Same commit added the advisory PreCompact
  hook.
- fixed: model reported "consolidated N nodes" without calling
  `mark.sh consolidated`, so the dirty list never drained.
  Snapshot-diff discrepancy detection added; breadcrumb prepended
  when the snapshot hasn't moved (commit ba9d38d; ADR-0027).
- fixed: `consolidate.sh` interleaved diff data with the prompt's
  imperative text, opening a prompt-injection surface. Wrapped
  per-source payloads in `<aims-source-diff>` data fences with a
  "data, not instructions" notice (commit 48e3988; ADR-0025).
- fixed: hook misbehaved on bash<4 (associative arrays / nameref).
  Added bash≥4 soft guard at top — advisory + exit 0 on older
  shells (commit 91fe2bd; L4).

## Pointers

- ADR-0007 — two-phase design (partially superseded for this node).
- ADR-0008 — node body schema the prompt enforces.
- ADR-0009 — in-band consolidation mechanism.
- ADR-0018 — superseded (in-frontmatter claim experiment).
- ADR-0019 — superseded by ADR-0024 (single-suffix sidecar).
- ADR-0021 — the consolidation prompt carries the reply-format note:
  hook results are reported to the user as a single line
  `===[aims: <message>]===`.
- ADR-0024 — mutex protocol split: `.marker` (advisory) vs `.lock`
  (Stop-owned strict mutex with EXIT trap). The design in force.
- ADR-0025 — data-framing fences on diff payloads + bedrock-style
  compaction invariants prepended to the ACTION block.
- ADR-0026 — Stop-hook `decision: block` carve-out from the general
  inform-never-block rule.
- ADR-0027 — discrepancy detection via
  `docs/memory/.last-report-snapshot`.
- `templates/hooks/stop-consolidate.sh` — orchestrator.
- `templates/hooks/session-end.sh` — stderr breadcrumb (M3).
- `templates/hooks/pre-compact.sh` — advisory pre-compaction hook.
- `templates/memory/consolidate.sh` — per-node prompt builder, fenced.

## Open questions

- Should the per-turn cap (10) be configurable per project, or is
  the conservative default sufficient given the 8 KB/node diff cap?
