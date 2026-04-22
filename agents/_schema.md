# Agent-routing contracts

Canonical schemas the entire routing system depends on. Every agent file and the
`/project:experts` command binds against these shapes. If a shape changes here,
every consumer must be updated.

## 1. Agent frontmatter

Every `agents/<id>.md` (worker or infrastructure) starts with YAML frontmatter:

```yaml
---
name: <id>                       # must match the filename stem
model: <exact model id>          # e.g. claude-haiku-4-5-20251001
tools: [<tool>, ...]             # whitelist the agent may use
capabilities: [<tag>, ...]       # discrete tags; used by Router & Planner
inputs:                          # named ports the caller binds into
  - <name>: <type>               # type is a descriptive hint, not enforced
outputs:                         # named ports the caller reads back
  - <name>: <type>
effects: [read-fs | write-fs | web | external-api]   # declared side-effects
idempotent: <bool>               # safe to re-run with same inputs?
strategy:                        # default run policy (caller may override)
  max_retries: <int>
  on_failure: abort | retry | escalate
---
```

Infrastructure agents (`_router.md`, `_planner.md`, `_validator.md`) follow the
same shape — they are agents that happen to orchestrate other agents.

## 2. Result envelope (worker → caller)

Every agent call returns exactly one JSON envelope as its final output.
The caller reads only the envelope — not the agent's internal reasoning.

```json
{ "ok": true,  "outputs": { "<port>": <value>, ... } }
```

```json
{ "ok": false, "retry": { "reason": "<short>", "hint": "<what to change>" } }
```

```json
{ "ok": false, "abort": { "reason": "<short>" } }
```

Rules:
- Exactly one of `outputs` / `retry` / `abort` is present.
- `outputs` keys must match the agent's declared `outputs` ports.
- `retry` means "the agent wants another attempt with the given hint".
- `abort` means "a retry won't help — escalate or fail".

## 3. Plan (Planner → Executor)

A Plan is an ordered list of steps. Each step invokes one agent. Linear by
default; a step may declare `depends_on` for non-adjacent dependencies.

```json
{
  "plan_id": "<short id>",
  "goal": "<one-line restatement of the user's request>",
  "steps": [
    {
      "id": "s1",
      "agent": "<agent id from registry>",
      "inputs": { "<port>": "<literal OR ${sN.outputs.<port>}>" },
      "validate": true,
      "depends_on": []
    }
  ],
  "caps": { "retries_per_step": 3, "reroutes": 3, "replans": 2 }
}
```

Binding syntax: `${sN.outputs.<port>}` resolves to step `sN`'s output port at
execution time. Literals are passed through.

`validate: true` means "after this step, invoke `_validator` on the outputs".

## 4. Verdict (Validator → Router)

```json
{
  "passed": <bool>,
  "score": <float 0..1>,
  "issues": [
    {
      "severity": "critical" | "high" | "medium" | "low",
      "location": "<port | path | step-id>",
      "reason": "<what's wrong>",
      "suggestion": "<what to change>"
    }
  ],
  "suggested_action": "accept" | "retry" | "re-route" | "replan"
}
```

`suggested_action` is a recommendation; the Router decides.

## 5. Task scope (Router's pre-exec classification)

The Router classifies every fresh request into one of three **scopes**. The
scope determines how heavy the orchestration is — we don't pay Planner +
Validator cost for a one-line edit.

| Scope     | When it applies                                                         | Executor behavior                                              |
|-----------|--------------------------------------------------------------------------|----------------------------------------------------------------|
| `trivial` | Obvious, bounded (one file / one function), matches one worker exactly. | Dispatch worker, **skip Validator**. Worker's envelope is final. |
| `simple`  | Single worker fits, but stakes are non-trivial (multi-file, side effects, ambiguous inputs). | Dispatch worker, run Validator **once** (terminal), then Router post-exec loop. |
| `complex` | Multiple agents needed, or decomposition required.                      | Dispatch Planner → walk Plan → Validator **per step with `validate: true`** + Router loop. |

`scope` is a property of the **request**, not of the agent. The same worker
may be invoked on a trivial request or a simple one.

## 6. Failure taxonomy

| Signal      | Who raises it        | What the Router does                                  |
|-------------|----------------------|-------------------------------------------------------|
| `retry`     | Worker (in envelope) | Re-invoke same agent, same inputs, plus `retry_hint`. |
| `re-route`  | Validator verdict    | Invoke a different agent with the same goal.          |
| `replan`    | Validator verdict    | Hand the verdict back to `_planner` for a new Plan.   |
| `abort`     | Worker or Router     | Stop with a structured failure report.                |

## 7. Loop caps (defaults)

| Cap                  | Default | Scope                         |
|----------------------|---------|-------------------------------|
| `retries_per_step`   | 3       | per worker step in a Plan     |
| `reroutes`           | 3       | per user request              |
| `replans`            | 2       | per user request              |

Exceeding any cap → `abort`.

## 8. Context isolation

Each agent call is a separate Claude Code subagent invocation. Only the
envelope crosses the context boundary — not the agent's tool calls, internal
reasoning, or intermediate artifacts. This is the core cost-control mechanism.
