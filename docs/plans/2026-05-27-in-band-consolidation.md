# Plan: in-band memory consolidation (no API key)
Status: in-progress
Started: 2026-05-27

## Context

ADR-0007 promises auto-maintenance via a `Stop` hook that calls Sonnet
to update node bodies. The call lives in `templates/memory/consolidate.sh:165`
as a `curl POST` to `api.anthropic.com` and requires `ANTHROPIC_API_KEY`
(`consolidate.sh:41-44`). Same pattern in
`templates/memory/classify-inbox.sh:35-40`. ADR-0007 itself flags the key
requirement as a ⚠️ consequence
(`docs/adr/0007-tree-based-memory-with-auto-maintenance.md:365-368`).

User decision: no API key, ever. The plugin runs **inside** Claude Code,
which already has the user's Claude account auth — but that auth is not
exposed to subprocess hooks (security boundary). However, hooks that
emit `additionalContext` (Stop, SessionStart, UserPromptSubmit) ARE a
working channel: the active in-session model reads the injection and
acts in the next turn. The user has confirmed this pattern works (their
own pre-push hook uses it to block-and-ask).

So: move every LLM call out of bash+curl and into hook-injected
instructions that the active Claude Code session executes in-band.

## Goal

Memory consolidation runs with zero external credentials: hooks build
the prompt; the active model executes it via Edit/Bash; bash helpers
do bookkeeping only.

## Options considered

- **A — Drop automatic consolidation; manual `/consolidate-memory` only.**
  Rejected: defeats ADR-0007's auto-maintenance promise.
- **B — Stop-hook injects "BEFORE responding, consolidate" into every
  prompt unconditionally.** Rejected: invasive on every turn.
- **C — Hook-injected instruction at threshold (chosen).** When the
  existing throttle trips, the Stop hook emits `additionalContext` with
  the full consolidation prompt (diffs already computed in bash). The
  model executes in the next turn. No new slash command needed; no
  marker file dance; no session-start coupling.
- **D — Keep curl, add a key.** Rejected by user.

## Decision

Option C. ADR-0009 records it and supersedes the relevant section of
ADR-0007.

## Steps

1. **Rewrite `templates/hooks/stop-consolidate.sh`.** Drop the
   `bash consolidate.sh per leaf` loop. New behaviour when threshold
   trips:
   - Compute the per-node diffs in bash (lift the logic currently in
     `consolidate.sh:60-74`).
   - Emit JSON `{hookSpecificOutput: {hookEventName: "Stop",
     additionalContext: "<prompt>"}}` containing: dirty-node list,
     each node's current body + diffs, transcript URLs, ADR-0008
     schema instructions (lifted from `consolidate.sh:91-156`), and a
     final step "after each node call
     `bash .claude/memory/mark.sh <node> consolidated`".
   - Also bumps `.last-consolidated` to avoid re-nudging next turn.
   - No `curl`. No `ANTHROPIC_API_KEY` reference. Inbox is handled the
     same way (separate or appended section).

2. **Replace `templates/memory/consolidate.sh`.** New role: emit the
   prompt-text-for-one-node to stdout, given a node path. Pure bash, no
   network. The Stop hook composes per-node sections from this helper
   so the prompt-building logic isn't duplicated. (Keeping the file is
   useful for the `/done` step and any future manual `/consolidate-memory`.)

3. **Replace `templates/memory/classify-inbox.sh`.** Same idea: emit
   prompt text for inbox classification; no API call. The Stop hook
   (or `/done`) is the consumer.

4. **Add `mark.sh` helper** if not already present. Sets
   `dirty: false`, bumps `last_touched` and `last_consolidated` for a
   given node path. (`fm_set` is already in `_lib.sh`.) Idempotent.

5. **Update `templates/memory/doctor.sh`.** Delete the
   `ANTHROPIC_API_KEY` line and the "(consolidation will skip)" tail.
   No replacement field needed — the dirty count + last-consolidated
   age already convey health.

6. **Update `templates/commands/done.md` step 7.** Instead of
   `AIMS_EXTRA_CONTEXT=... bash stop-consolidate.sh --force`: the step
   instructs the closing model to run consolidation in-band on nodes
   whose `code:` overlaps the plan's touched files, mining the plan +
   ADR text for invariants/rationale/fixed-bugs. Drop the
   "ANTHROPIC_API_KEY absent → propagation skipped" warning.

7. **Update `templates/commands/remember.md`.** Remove the "Don't open
   the Anthropic API" line (no longer relevant — there's no API to
   open).

8. **Write ADR-0009 — "Memory consolidation runs in-band via
   hook-injected instructions"** (`docs/adr/0009-in-band-memory-consolidation.md`).
   Status: accepted. Supersedes ADR-0007 §"Stop hook calls Sonnet"
   (lines 257-284) and ⚠️ consequence at line 365-368. Add a
   "Superseded in part by ADR-0009" banner to ADR-0007 (a header
   note, not body edits).

9. **Dogfood mirror** every `templates/...` change to `.claude/...`.

## Verification

- `bash -n templates/hooks/*.sh templates/memory/*.sh .claude/hooks/*.sh .claude/memory/*.sh` — passes.
- `grep -rn 'ANTHROPIC_API_KEY\|api\.anthropic\.com' templates/ .claude/` —
  empty (ADR markdown excluded).
- `bash .claude/memory/doctor.sh` — no API-key field; brief line still emitted.
- Smoke test: mark 5 nodes dirty in a fixture, pipe a stub Stop payload
  into `stop-consolidate.sh`, confirm stdout is valid JSON with
  `additionalContext` containing "## Purpose", "## Design rationale",
  the dirty node paths, and the mark.sh instruction. **No** network
  call (run under `unshare -n` or simply observe no curl in the script).
- `bash .claude/memory/lint.sh` — clean.
- End-to-end (manual after merge): edit a file under a node's `code:`,
  hit threshold, observe the next turn auto-runs the consolidation
  Edits before responding.

## Risks / unknowns

- **Nudge compliance.** The Stop-hook `additionalContext` is an
  instruction, not enforcement. If the model ignores it, dirty nodes
  remain dirty (visible in doctor) and next turn re-nudges. Acceptable.
- **Turn-cost visibility.** Today's curl cost was hidden; now it's
  an Edit-heavy turn the user sees. Mitigation: if dirty count is
  large (>10), include "do these N first, leave the rest for next
  turn" in the instruction.
- **Prompt size.** Diffs are already capped at 8 KB per node
  (`consolidate.sh:67`); we keep the cap. With 5 dirty nodes that's
  ~40 KB additionalContext — large but within Claude Code's context.
- **Old installs.** Projects that already installed via
  `/init-workflow` have the curl version of `consolidate.sh`. They'll
  see the deprecated path keep working (it just skips silently
  without the key) until they re-install. No active breakage.

## ADRs to record after implementation

- [x] ADR-0009 — drafted as part of step 8 (the decision IS this plan).
