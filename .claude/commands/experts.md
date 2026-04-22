---
description: "Tiered agent router — Router (Haiku) triages, Planner (Opus) decomposes, Validator (Sonnet) gates, workers execute. Each in its own context."
allowed-tools: Read, Task, Bash
argument-hint: "<request>"
---

# /project:experts

Orchestrator for the tiered agent routing system. This command itself is the
**Executor** — thin, deterministic bookkeeping over a state machine. It never
reasons about the task; it delegates every decision and every piece of work to
a sub-agent with its own isolated context.

Read once, then operate:
- `agents/_schema.md` — envelope, Plan, Verdict shapes.
- `agents/registry.md` — registered worker agents.
- `agents/_router.md`, `agents/_planner.md`, `agents/_validator.md` — infra agents.

## State the Executor maintains

```
state = {
  request: "<$ARGUMENTS>",
  plan: null | Plan,
  step_results: { "<step.id>": <worker envelope> },
  verdicts:     { "<step.id>": <Verdict> },
  caps_used: { retries_per_step: {<step.id>: int}, reroutes: int, replans: int }
}
```

All counters start at 0. Caps come from `plan.caps` (defaults in `_schema.md` §6).

## The state machine

```
              ┌───────────────────────────┐
              │ 1. Router (pre-exec)      │
              │    → scope + action       │
              └────┬──────────┬──────────┬┘
    dispatch-trivial│ dispatch-simple │  │ dispatch-planner
                   ▼          ▼          ▼
         ┌─────────────┐ ┌─────────────┐ ┌──────────────────┐
         │ 2a. worker  │ │ 2a. worker  │ │ 2b. Planner→Plan │
         │ (no valid-  │ │             │ │                  │
         │  ator)      │ │             │ └────────┬─────────┘
         └──────┬──────┘ └──────┬──────┘          ▼
                │               │       ┌────────────────────┐
                │               │       │ 3. Walk Plan step- │
                │               │       │    by-step         │
                │               │       └────────┬───────────┘
                │               │                │
                │               └────────┬───────┘
                │                        ▼
                │            ┌──────────────────────────┐
                │            │ 4. Validator (step has   │
                │            │    validate: true)       │
                │            └────────────┬─────────────┘
                │                         ▼
                │            ┌──────────────────────────┐
                │            │ 5. Router (post-exec):   │
                │            │    Verdict + state →     │
                │            │    accept/retry/re-route/│
                │            │    replan/abort          │
                │            └────────────┬─────────────┘
                │                         │
                ▼             ┌───────────┼─────────┬────────┐
             accept           ▼           ▼         ▼        ▼
           (trivial         accept      retry    re-route  replan  abort
            path end)      (done)     (back 2a) (back 2a)(back 2b)(fail)
```

## Steps the Executor performs

### Step 1 — Invoke `_router` (pre-exec mode)
Dispatch `_router` as a subagent with:
```
inputs = { request: state.request }
```
Read its `decision.action` and `decision.scope`:
- `dispatch-trivial` → go to Step 2a (trivial path, no Validator).
- `dispatch-simple`  → go to Step 2a (simple path, Validator terminal).
- `dispatch-planner` → go to Step 2b (complex path).
- Anything else at this stage is a protocol violation → `abort`.

### Step 2a — Run a single worker
Dispatch `decision.target_agent` as a subagent with inputs derived from the request. Record the envelope in `state.step_results["s1"]`.

Branch on scope:
- `scope == "trivial"` → **skip Step 4 and Step 5**. The worker's envelope is the final outcome. Emit the report and stop.
- `scope == "simple"`  → go to Step 4 (Validator runs once, then post-exec Router loop).

### Step 2b — Invoke `_planner`
Dispatch `_planner` as a subagent with:
```
inputs = { request: state.request, last_verdict: ..., last_plan: ... }  // last_* populated on replan
```
Store the returned Plan in `state.plan`. Go to Step 3.

### Step 3 — Walk the Plan
For each step in `state.plan.steps` (respecting `depends_on`):
1. Resolve `inputs` — substitute every `${sN.outputs.<port>}` with the actual value from `state.step_results[sN].outputs[<port>]`.
2. Dispatch `step.agent` as a subagent with the resolved inputs.
3. Store the returned envelope in `state.step_results[step.id]`.
4. If the envelope's `ok` is `false` with a `retry` signal: increment `caps_used.retries_per_step[step.id]`; if under the cap, re-dispatch with `retry_hint`; else escalate to Step 5 with a synthetic Verdict (`passed: false, suggested_action: re-route`).
5. If the envelope's `ok` is `false` with an `abort`: go to Step 5 with a synthetic Verdict (`suggested_action: abort`).
6. If the step's `validate: true`, go to Step 4 for this step. Otherwise continue.

### Step 4 — Invoke `_validator`
Dispatch `_validator` as a subagent with:
```
inputs = {
  artifact:    state.step_results[step.id],
  agent_id:    step.agent,
  step_goal:   state.plan.goal + " — step: " + step.id,
  step_inputs: <resolved inputs from Step 3>
}
```
Store the returned Verdict in `state.verdicts[step.id]`. Go to Step 5.

### Step 5 — Invoke `_router` (post-exec mode)
Dispatch `_router` as a subagent with:
```
inputs = {
  verdict: state.verdicts[step.id],
  state:   { caps_used, current_step: step.id }
}
```
Act on the returned `decision.action`:
- `accept` → mark the step done; continue walking the Plan at Step 3 (next step), or finish if no steps remain.
- `retry` → increment `caps_used.retries_per_step[step.id]`, re-dispatch step.agent with a `retry_hint` composed from the Verdict's top issue. Then Step 4 again.
- `re-route` → increment `caps_used.reroutes`. Pick a different agent (the Router's `target_agent`, if provided; otherwise consult `agents/registry.md` for a sibling capability). Dispatch with the same inputs. Then Step 4 again.
- `replan` → increment `caps_used.replans`. Go to Step 2b with `last_verdict` and `last_plan` set.
- `abort` → stop with a structured failure report.

## Final report
Whether success or abort, emit exactly this block (plus structured outputs for success):

```
Plan:          <plan_id or "direct">
Steps run:     <list of step ids>
Caps used:     retries=<..>, reroutes=<..>, replans=<..>
Outcome:       accept | abort
Artifacts:     <created / updated paths, if any>
Verdicts:      <per-step score, if any>
```

## Rules the Executor itself must honor
- Never reason about the user's task. Delegate every decision (Router) and every decomposition (Planner).
- Never call a worker's tools directly. Always dispatch via `Task`.
- Never read a sub-agent's internal reasoning — only its envelope.
- Never exceed a cap silently. Always emit a report on `abort`.
- Never modify a sub-agent's output before passing it downstream. Bind only through the envelope's declared ports.
