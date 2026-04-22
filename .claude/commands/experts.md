---
description: "Expert router — parse a request and invoke the right agent(s) in single, cascade, or loop mode"
allowed-tools: Read, Write, Bash
argument-hint: "<request>"
---

# /project:experts

Behavior router. Parses `$ARGUMENTS`, picks a mode, loads the agent files from
`agents/router.md`, and executes them. The router does not carry domain logic —
it only orchestrates.

## Usage
```
/project:experts find a book on reinforcement learning
/project:experts encode sutton_barto_rl
/project:experts build the library for graph neural networks
/project:experts refresh stale books in NLP
```

## Step 1 — Load registry
Read `agents/router.md`. This is the authoritative list of available agents and their files.

## Step 2 — Parse intent
Classify `$ARGUMENTS` into exactly one intent by matching in order (first match wins):

| Intent   | Trigger phrases (case-insensitive)                                     |
|----------|-------------------------------------------------------------------------|
| BUILD    | "build", "grow the library", "find and encode", "full pipeline"        |
| REFRESH  | "refresh", "update stale", "audit and update"                          |
| ENCODE   | "encode", "add book", or an explicit `lowercase_underscored` token     |
| FIND     | "find", "recommend", "which book", "best book"                         |
| default  | (no match) → FIND                                                       |

## Step 3 — Choose mode & pipeline

| Intent   | Mode     | Pipeline                                   | Max loops |
|----------|----------|--------------------------------------------|-----------|
| FIND     | SINGLE   | book_finder                                | 1         |
| ENCODE   | LOOP     | book_encoder                               | 3         |
| BUILD    | CASCADE  | book_finder → book_encoder                 | 3 on encoder |
| REFRESH  | CASCADE  | book_finder (per stale slug) → book_encoder | 3 on encoder |

## Step 4 — Load the agent files
For every agent id in the pipeline, read `agents/<id>.md`. Respect:
- `model` in frontmatter — invoke with this exact model
- `tools` in frontmatter — use only these tools
- `inputs` / `outputs` — the contract the router binds against

## Step 5 — Execute

### SINGLE
1. Bind inputs from `$ARGUMENTS` to the agent's `inputs` list.
2. Invoke the agent.
3. Emit its output verbatim.

### LOOP (max 3)
1. Bind inputs. Initial `retry_hint = null`.
2. Invoke the agent.
3. If the output is a single line starting with `STATUS: RETRY <reason>` AND attempt < max:
   - Set `retry_hint = <reason>`, increment attempt, go to step 2.
4. Stop when the agent returns its normal output contract OR attempt == max.
5. Emit final status and collected retry reasons.

### CASCADE
Maintain a `state` dict keyed by output field names.
1. Run stage 1. On `STATUS: RETRY`: one retry, then abort.
2. Write the stage-1 output fields into `state`.
3. Run stage 2 inside the LOOP mode above, binding its `inputs` from `state`.
4. Emit a per-stage report.

### REFRESH (specialisation of CASCADE)
Resolve the list of targets the router should iterate over from project conventions (staleness and filter parsing belong to the skills/playbook, not to the router). For each target, run the CASCADE above.

## Step 6 — Report
```
Mode: <SINGLE|LOOP|CASCADE|REFRESH>
Agents: <list>
Steps: <per-step pass/fail + loop count>
Artifacts: <created / updated paths, if any>
Retries: <reasons, if any>
```

## Input binding
- FIND: text after the trigger phrase → `domain`.
- ENCODE: first `lowercase_underscored` token → `slug`; remaining fields come from the project's queue/config (not embedded here).
- BUILD: text after the trigger phrase → `domain`.
- REFRESH: optional category filter after the trigger phrase.
