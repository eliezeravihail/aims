---
description: "Lean mode — one worker on the right model, with methodology skills preloaded. Default for Claude Opus/Sonnet baselines. For weaker baselines (Copilot, smaller models) use /agents-experts instead."
allowed-tools: Read, Task, Bash
argument-hint: "<request>"
---

# /project:experts — lean mode

**Default command.** Single dispatch on the right model with methodology
skills loaded in its system context. No Planner, no per-step Validator
loop, no inter-agent envelope chaining. Cheapest mode that still produces
auditable artefacts.

Selection rule:
- Use **`/experts`** (this command) on strong baselines — Claude Opus /
  Sonnet.
- Use **`/agents-experts`** on weaker baselines — Copilot, smaller OSS
  models, constrained cloud contexts — where a single dispatch is
  unreliable and decomposition compensates.

Read once, then operate:
- `agents/_schema.md` — envelope, Plan, Verdict shapes.
- `agents/_router.md` — lean Router spec (emits `{model, skills_to_load, rationale}`).
- `agents/_validator.md` — optional terminal quality gate.
- `skills/project-context/SKILL.md` — the `.claude.md` cache procedure.
- `skills/quality-analysis/SKILL.md` — 7-dimension rubric.
- `skills/debug-methodology/`, `skills/test-authoring/`, `skills/test-strategy/`, `skills/feature-build/` — methodology playbooks the worker may load.

## State

```
state = {
  request: "<$ARGUMENTS>",
  decision: null | {action, model, skills_to_load, rationale},
  worker_envelope: null | <envelope>,
  verdict: null | <verdict>
}
```

## Step 0 — Project-context preflight

Same as `/agents-experts`: if `.claude.md` doesn't exist at the project
root, dispatch a single subagent to run the Bootstrap procedure in
`skills/project-context/SKILL.md`. Skip if present.

## Step 1 — Invoke `_router` (lean)

Dispatch `_router` as a subagent with:
```
inputs = { request: state.request }
```
Expect the envelope:
```json
{
  "ok": true,
  "outputs": {
    "decision": {
      "action": "dispatch-lean",
      "model": "...",
      "skills_to_load": ["...", ...],
      "rationale": "..."
    }
  }
}
```

If `action` is not `"dispatch-lean"` → protocol violation → `abort`.

## Step 2 — Dispatch the single worker

Compose the worker's system prompt from:
1. A thin role statement ("You are a Claude Code worker invoked in lean
   mode. Execute the user's request end-to-end following the methodology
   skills loaded below. Emit one JSON envelope per `agents/_schema.md` §2.")
2. The full text of each skill in `decision.skills_to_load`, concatenated.
3. The user's `request`.

Dispatch on the model specified in `decision.model`. Let it run
end-to-end in one context. Receive its envelope.

If the envelope is `ok: false` (`retry` or `abort`) → pass through to
the final report; stop.

## Step 3 — Optional terminal Validator

If the worker's `outputs` declare write effects (`created_files`,
`fix`, `tests_added`) AND the user has not opted out of validation:

Dispatch `_validator` as a subagent with:
```
inputs = {
  artifact: state.worker_envelope,
  agent_id: "lean-worker",
  step_goal: state.request,
  step_inputs: { request: state.request }
}
```

If `verdict.passed` is `false` → `abort` with reason; emit both the
verdict and the worker's envelope in the final report so the user can
see exactly what was rejected.

## Step 4 — Report

```
Mode:        lean
Model:       <decision.model>
Skills:      <decision.skills_to_load, comma-separated>
Outcome:     accept | abort
Verdict:     <pass/fail + score, if Validator ran>
Artefacts:   <created / updated paths, from outputs>
Rationale:   <decision.rationale>
```

## Rules the Executor itself must honor

- Never reason about the user's task. Delegate to `_router` and the worker.
- Never call tools directly. Always dispatch via `Task`.
- Never read a sub-agent's internal reasoning — only its envelope.
- Never skip the Validator when the worker claims write effects, unless
  the user explicitly opted out.
- Never modify a sub-agent's output before passing it downstream.
