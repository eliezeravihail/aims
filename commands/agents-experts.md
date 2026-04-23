---
description: "Decomposed pipeline mode — Router (Haiku) triages, Planner (Opus) decomposes, Validator (Sonnet) gates, workers execute in isolated contexts. Use for weaker baselines (Copilot, smaller models). For Claude Opus/Sonnet use /experts (lean) instead."
allowed-tools: Read, Task, Bash
argument-hint: "<request>"
---

# /project:agents-experts

Orchestrator for the **decomposed pipeline** mode. This command is the
**Executor** — thin, deterministic bookkeeping over a state machine. It never
reasons about the task; it delegates every decision and every piece of work to
a sub-agent with its own isolated context.

Use this command when your baseline model is weak or unreliable at
single-dispatch (Copilot, smaller OSS models). For strong baselines
(Claude Opus/Sonnet) prefer `/experts`, which runs a single lean worker
with methodology skills loaded — measurably better per-dispatch dollars
on the empirical pilots.

Read once, then operate:
- `agents/_schema.md` — envelope, Plan, Verdict shapes.
- `agents/registry.md` — registered worker agents.
- `agents/_router_pipeline.md`, `agents/_planner.md`, `agents/_validator.md` — infra agents used in pipeline mode.
- `skills/project-context/SKILL.md` — how to read or build `.claude.md`, the shared project-structure cache.

## Step 0 — Project-context preflight (before anything else)

The shared `.claude.md` at the project root is how isolated subagents avoid
re-discovering the codebase. Preflight:

1. Check whether `.claude.md` exists at the project root.
2. **If missing** — dispatch a single subagent to run the **Bootstrap** procedure in `skills/project-context/SKILL.md`. This subagent's only job is to build `.claude.md`. It is dispatched on **Sonnet** (structure extraction needs reasoning but not top-tier planning). When it returns, continue to Step 1.
3. **If present but stale** (a worker later emits `advisory: "project-context-stale"`) — schedule a **Refresh** invocation of the skill as the next pipeline step before continuing the user's request.
4. **If present and fresh** — proceed directly to Step 1.

In all cases, pass `project_context_path: ".claude.md"` in the initial
inputs to `_router_pipeline` and `_planner`, so downstream dispatch can assume the
cache exists.

User can force initialization or refresh explicitly:
```
/project:experts init project context
/project:experts refresh project context
```
Both short-circuit into a single Bootstrap/Refresh run and emit a one-line status.

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

### Step 1 — Invoke `_router_pipeline` (pre-exec mode)
Dispatch `_router_pipeline` as a subagent with:
```
inputs = { request: state.request }
```
Read its `decision.action` and `decision.scope`:
- `dispatch-trivial`  → go to Step 2a (trivial path, no Validator).
- `dispatch-simple`   → go to Step 2a (simple path, Validator terminal).
- `dispatch-baseline` → go to Step 2c (holistic path, single Opus dispatch, no Validator).
- `dispatch-planner`  → go to Step 2b (complex path).
- Anything else at this stage is a protocol violation → `abort`.

### Step 2a — Run a single worker
Dispatch `decision.target_agent` as a subagent with inputs derived from the request. Record the envelope in `state.step_results["s1"]`.

Branch on scope:
- `scope == "trivial"` → **skip Step 4 and Step 5**. The worker's envelope is the final outcome. Emit the report and stop.
- `scope == "simple"`  → go to Step 4 (Validator runs once, then post-exec Router loop).

### Step 2c — Holistic dispatch to `_baseline`
Dispatch `_baseline` as a subagent with `inputs = { request: state.request }`.
Record the envelope in `state.step_results["s1"]`.

**Skip Step 4 and Step 5 entirely.** The holistic path exists to avoid
decomposition overhead when pilot data shows decomposition hurts quality.
A Validator pass would partially undo that saving (and can't meaningfully
evaluate a cohesive build without decomposing the rubric). The user can
re-dispatch with `dispatch-planner` if they want a quality-gated run.

Emit the report and stop.

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

### Step 5 — Invoke `_router_pipeline` (post-exec mode)
Dispatch `_router_pipeline` as a subagent with:
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
