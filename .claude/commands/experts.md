---
description: "Expert router — parse a request and invoke the right agent(s) in single, cascade, or loop mode"
allowed-tools: Read, Write, Bash
argument-hint: "<request>"
---

# /project:experts

Generic behavior router. Parses `$ARGUMENTS`, resolves which agent(s) to run,
and executes them in SINGLE, LOOP, or CASCADE mode. The router is domain-neutral —
it knows nothing about what any specific agent does; it only orchestrates.

## Step 1 — Load registry
Read `agents/router.md`. This is the authoritative list of agents available in
this project, one row per agent with `id`, `file`, and a one-line capability.

## Step 2 — Resolve target agent(s)
Match `$ARGUMENTS` to agents by scoring its tokens against each registry row's
capability string. Two resolution outcomes:

- **Single agent matches** → SINGLE or LOOP mode (see Step 3).
- **Multiple agents form a pipeline** (stage N's `outputs` schema is a superset
  of stage N+1's `inputs` schema) → CASCADE mode.

If `$ARGUMENTS` does not match any agent, emit the registry and stop.

## Step 3 — Choose mode

| Condition                                                           | Mode    | Max loops |
|---------------------------------------------------------------------|---------|-----------|
| Single agent, request is idempotent / read-only                     | SINGLE  | 1         |
| Single agent, request produces artifacts and the agent declares a quality gate | LOOP    | 3         |
| Pipeline of two or more agents, schemas chain                       | CASCADE | 3 on the last stage with a quality gate |

Any agent may be promoted from SINGLE to LOOP if its output begins with
`STATUS: RETRY <reason>` — that is the universal retry signal.

## Step 4 — Load agent files
For every agent in the pipeline, read `agents/<id>.md`. Respect:
- `model` in frontmatter — invoke with this exact model
- `tools` in frontmatter — use only these tools
- `inputs` / `outputs` — the contract the router binds against

## Step 5 — Execute

### SINGLE
1. Bind inputs from `$ARGUMENTS` to the agent's declared `inputs`.
2. Invoke the agent.
3. Emit its output verbatim.

### LOOP (max 3)
1. Bind inputs. Initial `retry_hint = null`.
2. Invoke the agent.
3. If the output is a single line starting with `STATUS: RETRY <reason>` AND attempt < max:
   - Set `retry_hint = <reason>`, increment attempt, go to step 2.
4. Stop when the agent returns its normal output contract OR attempt == max.
5. Emit the final output plus any collected retry reasons.

### CASCADE
Maintain a `state` dict keyed by field names.
1. Bind stage 1's `inputs` from `$ARGUMENTS`. Run stage 1.
2. On `STATUS: RETRY` at stage 1: one retry, then abort the cascade.
3. Merge stage 1's `outputs` into `state`.
4. For each subsequent stage: bind `inputs` from `state`, run it in LOOP mode,
   merge its `outputs` into `state`.
5. Emit a per-stage report.

## Step 6 — Report
```
Mode: <SINGLE|LOOP|CASCADE>
Agents: <list>
Steps: <per-stage pass/fail + loop count>
Artifacts: <paths or structured outputs, if any>
Retries: <reasons, if any>
```
