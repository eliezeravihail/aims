# ADR-0009: Memory consolidation runs in-band via hook-injected instructions
Status: accepted
Date: 2026-05-27
Supersedes: parts of ADR-0007 (the `Stop → curl Sonnet` mechanism and
            the ⚠️ ANTHROPIC_API_KEY consequence)
Superseded by: —

## Context

ADR-0007's automatic-maintenance mechanism is a `Stop` hook that, when
the dirty-leaf throttle trips, calls `consolidate.sh` per leaf. Each
call is a `curl POST` to `api.anthropic.com`
(`templates/memory/consolidate.sh:165`) gated on `ANTHROPIC_API_KEY`
(`consolidate.sh:41-44`). Same shape for `classify-inbox.sh:35-40`.
ADR-0007 itself flagged this as ⚠️ at lines 365-368: without the key,
dirty markers accumulate silently.

The plugin runs **inside** Claude Code, which already has the user's
Claude account auth — but that auth is not exposed to subprocess
hooks (Claude Code security boundary). So bash hooks cannot reuse it.

Claude Code hooks that emit `additionalContext` (`SessionStart`,
`UserPromptSubmit`, `Stop`) ARE a working channel: the injected text
appears in the active model's context on the next turn, and the model
acts on it via its existing Edit/Bash/etc. tools. The aims router
already uses this pattern (ADR-0004); the user's own pre-push hook
uses it to block-and-ask. The pattern is proven.

There is no business case for requiring an external API key when the
session already has model access.

## Decision

We will move every LLM call out of bash+curl and into hook-injected
instructions executed in-band by the active Claude Code session. The
`Stop` hook becomes a prompt builder: when the existing throttle
trips it computes per-node diffs in bash, packages them with the
ADR-0008 schema rules, and emits the result as
`additionalContext`. The model performs the consolidation Edits in
its next turn and calls a `mark.sh` helper to flip `dirty: false`.
Inbox classification follows the same pattern.

Boundary: this ADR governs **how** consolidation runs. The schema
(ADR-0008), the marker mechanism (Phase A of ADR-0007), the throttle
thresholds, and the tree layout are unchanged.

## Consequences

- ✅ Zero external credentials. The plugin works for any user with a
  Claude Code session.
- ✅ One less surface for a missing-env-var class of bugs; doctor
  reports become simpler.
- ✅ The consolidation prompt is visible in the model's context, so
  the user can see exactly what was asked and override it.
- ⚠️ Consolidation now consumes a visible turn instead of running
  invisibly in a background `curl`. Acceptable: the user already
  watches Stop-hook output; surfacing a real action is a feature, not
  a bug.
- ⚠️ The injection is an instruction, not enforcement. If the model
  ignores it, dirty markers persist (visible in doctor) and the next
  `Stop` re-nudges. We treat this as self-healing, not as a
  reliability gap.
- ⚠️ Prompt size grows with the number of dirty nodes. Mitigation:
  per-node diff cap stays at 8 KB (`consolidate.sh:67`); the prompt
  can ask the model to handle the first N nodes and defer the rest
  if the list is long.
- 🔒 We will not ship a parallel curl-based path. There is one
  consolidation mechanism, and it is in-band. (Manual users who want
  curl can still pipe the helper's stdout into their own client; the
  plugin doesn't endorse it.)

## Alternatives considered

- **A — Drop automatic consolidation; manual `/consolidate-memory`
  only.** Rejected: kills ADR-0007's auto-maintenance promise.
- **B — Inject "before responding, consolidate" on every
  UserPromptSubmit.** Rejected: invasive on every turn; can't reuse
  the existing dirty-threshold gate cleanly.
- **C — Keep curl, require an API key.** Rejected by the user; also
  fundamentally redundant given the active session already has model
  access.
- **D — Marker file + SessionStart nudge to invoke a slash command.**
  Rejected as over-engineered: the `Stop` hook can inject the actual
  work, no detour through a marker file and a slash command is
  needed.

## Verification

- `grep -rn 'ANTHROPIC_API_KEY\|api\.anthropic\.com' templates/ .claude/`
  returns only this ADR and ADR-0007 (historical).
- `templates/hooks/stop-consolidate.sh` contains no `curl` invocation;
  its stdout (when the throttle trips) is a single JSON object with
  `hookSpecificOutput.additionalContext` carrying the consolidation
  prompt.
- `bash .claude/memory/doctor.sh` has no `ANTHROPIC_API_KEY` field.
- ADR-0007 carries a top-of-file note pointing here for the
  superseded mechanism.
