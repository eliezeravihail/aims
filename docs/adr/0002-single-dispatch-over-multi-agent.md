# ADR-0002: Single-dispatch over multi-agent orchestration
Status: accepted
Date: 2026-05-06
Supersedes: ADR equivalent of prior `expert-system` dual-mode design (informal)
Superseded by: —

## Context

The previous incarnation of this repository (`expert-system`, dual-mode
`/experts` and `/agents-experts`) implemented a multi-agent pipeline:
Router → Planner → Workers → Validator, with a Python harness, JSON
envelopes, and per-step state. That design assumed a weak baseline model.

Two pieces of evidence pushed against keeping it:

- The 2025–2026 multi-agent literature (Cemri et al., Google Research's
  "science of scaling agent systems", Bouchard's "multi-agent is becoming
  the new overengineering") consistently reports that on strong baselines
  (Opus / Sonnet) the marginal accuracy gain over single dispatch drops
  from ~10% to ~3%, while token cost grows 4–220×.
- Anthropic's own guidance: subagents are worth the overhead only at
  ≥10 files explored or ≥3 independent units of work; otherwise they
  fragment the model's mental picture.

The user's baseline is Opus / Sonnet. The pipeline was paying for a
problem they don't have.

## Decision

The plugin uses **single-dispatch with discipline**: one Claude session,
one model selection per task, no router, no validator, no orchestrator.

Reliability comes from three sources, in order of leverage:

1. **Plan-mode discipline** — `/plan` enforces read-only exploration and
   ends with `ExitPlanMode` for explicit user approval. The plan is then
   persisted to `docs/plans/` so it survives context compaction.
2. **Decision artifacts** — `/adr` writes append-only records reviewable
   in PRs. Decisions cannot quietly disappear into chat history.
3. **Hooks as guardrails** — deterministic shell scripts that block edits
   while a planning lock exists, and (optionally) require an in-progress
   plan when editing under `src/`. Not LLM-judged; not bypassable by accident.

Models are pinned per slash command via frontmatter: Opus for `/plan`,
`/adr`, `/done`; Haiku for `/grunt`. Implementation runs on the user's
session model (Sonnet recommended).

## Consequences

- ✅ One execution path. No orchestration bugs, no envelope schemas,
  no inter-agent context loss.
- ✅ Cheaper per task — fewer LLM calls, no token amplification.
- ✅ Easier to reason about and debug. The plugin is markdown + bash.
- ⚠️ Loses the structured re-route / replan failure handling that the
  pipeline had. We bet that on a strong baseline this isn't worth the
  complexity; tests + verification commands fill the gap.
- ⚠️ Weak-baseline users (Copilot, smaller OSS) will not benefit as much.
  The plugin is explicitly not for them.
- 🔒 Closes the door on building a worker registry, a Python harness, or
  an envelope schema in this repo. If those become necessary again, fork.

## Alternatives considered

- **Keep the dual-mode design** — rejected: pays for orchestration the
  baseline doesn't need, and the code surface (`harness/`, `agents/`,
  `schemas/`) was an order of magnitude larger than the value.
- **Lean mode only, drop pipeline mode** — rejected as a half-step:
  still ships the harness and registry, still implies a multi-agent
  mindset. Cleaner to commit fully to single-dispatch.
- **Skills-only plugin (no commands)** — rejected: skills don't enforce
  process; commands with frontmatter pin model and behavior at the
  invocation boundary, where it matters.

## Verification

- No `agents/`, `harness/`, or `schemas/` directories in the repo
  (`find . -type d -name 'agents' -o -name 'harness' -o -name 'schemas'`
  returns nothing).
- `commands/` contains exactly five command files corresponding to the
  ais surface.
- `README.md` "Design principles" section (point 1) cites this trade-off.
