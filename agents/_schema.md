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

The Router classifies every fresh request into one of four **scopes**. The
scope determines how heavy the orchestration is — we don't pay Planner +
Validator cost for a one-line edit, and we don't force decomposition on a
task that suffers from it.

| Scope      | When it applies                                                         | Executor behavior                                              |
|------------|--------------------------------------------------------------------------|----------------------------------------------------------------|
| `trivial`  | Obvious, bounded (one file / one function), matches one worker exactly. | Dispatch worker, **skip Validator**. Worker's envelope is final. |
| `simple`   | Single worker fits, but stakes are non-trivial (multi-file, side effects, ambiguous inputs). | Dispatch worker, run Validator **once** (terminal), then Router post-exec loop. |
| `holistic` | Self-contained feature/refactor; decomposition would hurt coherence (design choices are entangled). | Dispatch `_baseline` (Opus), end-to-end, **no Planner, no Validator**. |
| `complex`  | Multiple concerns need coordination (bug-fix + tests, multi-step cascades). | Dispatch Planner → walk Plan → Validator **per step with `validate: true`** + Router loop. |

`scope` is a property of the **request**, not of the agent. The same
worker may be invoked on a trivial request or a simple one. And the
`holistic` branch exists because pilot data showed that on feature builds
within single-context scope, a single Opus dispatch produced more correct
output than a decomposed pipeline — see `PILOT_FEATURE_REPORT.md`.

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

## 9. Tool discipline for infrastructure agents

Infrastructure agents (`_router`, `_planner`, `_validator`) have a **strict
minimal-tool rule**. This is not optional — empirical data from the medium-bug
pilot shows that without it, the Router drifts into the task's domain and
burns the tokens it was supposed to save.

Required conventions per infra role:

| Agent | Allowed tools | Forbidden behaviour |
|-------|---------------|---------------------|
| `_router`    | `[Read]` only (to read `agents/registry.md` and `.claude.md`) | No filesystem Grep/Glob, no Bash, no code analysis. Classification only. |
| `_planner`   | `[Read]` only (to read registry + project context) | No Bash, no Edit, no Write. |
| `_validator` | `[Read, Bash]` (Bash to run tests; that is its job) | No Edit, no Write. Never modify the artifact under review. |

Every infra-agent prompt **must** include a line stating what the agent is
forbidden from doing, not just what it should do. Prohibitions are more
effective than positive instructions for tier discipline.

**Observed**: in the cookiecutter-4 pilot, tightening `_router` from default
tools to `[Read]` plus the line *"do NOT read code, do NOT analyze the bug
yourself"* reduced tool calls from 2 to 0 and reclaimed ~1,800 tokens of
spurious analysis on a single dispatch.

## 10. Shared value types

Some value shapes flow between multiple agents. Keep them aligned so the
Planner can chain producers to consumers by schema match.

### TestTarget

Produced by `debugger` (field `test_gaps`) and `test_strategist` (field
`test_plan`). Consumed by `tester` (field `targets`).

```json
{
  "test_type": "unit" | "integration" | "e2e" | "property" | "regression",
  "target":    "<module / function / endpoint / UI flow>",
  "scenario":  "<specific input / state / timing to exercise>",
  "origin":    "bug-driven" | "strategic",
  "priority":  "critical" | "high" | "medium" | "low",     // optional, default "medium"
  "rationale": "<one-line justification>"                   // optional
}
```

- `origin: "bug-driven"` — the target is derived from a real failure the debugger observed.
- `origin: "strategic"` — the target comes from a coverage plan, not a specific bug.

The tester treats both origins the same; it only ever consumes a list of TestTargets.

