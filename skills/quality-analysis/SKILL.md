---
name: quality-analysis
description: Shared rubric for software output quality and reliability. Loaded by producing agents (as a pre-submit checklist) and by the _validator agent (as an evaluation rubric). Use whenever an agent is about to emit a result, or is asked to judge one.
---

# Quality & Reliability Rubric

This skill is a **shared contract**, not a preference. The agent that
produces an artifact and the agent that validates it both load this file
and therefore agree on what "good" looks like. That alignment is the
whole point — without it, the Validator's verdicts are opinion.

## When to load
- You are an agent about to return an `outputs` envelope — use the rubric as a self-check before emitting.
- You are `_validator` — use the rubric to score an artifact and emit a Verdict.

## The seven dimensions

Score each independently 0..1. The overall `score` is the geometric mean
(any zero kills the result — reliability is not a sum).

| # | Dimension              | Pass means                                                                 | Red flags                                                           |
|---|------------------------|-----------------------------------------------------------------------------|---------------------------------------------------------------------|
| 1 | **Correctness**        | Output actually solves the stated task, on the stated inputs.               | Solves an adjacent task; works on easy inputs only.                 |
| 2 | **Contract fidelity**  | Output matches the declared `outputs` schema exactly — names, types, shape. | Missing ports; extra prose wrapping the JSON envelope; wrong types. |
| 3 | **Groundedness**       | Every factual claim traces to a source, tool result, or input.              | Invented citations, fabricated APIs, made-up file paths.            |
| 4 | **Completeness**       | No declared output port is left empty or placeholder-filled.                | `"..."`, `"TODO"`, silently dropped fields.                         |
| 5 | **Internal consistency** | Parts of the output do not contradict each other.                         | Summary says X, detail says ¬X. Step 3 depends on step 1's output not produced. |
| 6 | **Safety / side-effect discipline** | The agent stayed within its declared `effects`.                 | `effects: [read-fs]` agent that wrote files or made web calls.      |
| 7 | **Cost discipline**    | No obviously wasted work (duplicate tool calls, re-fetching the same page). | Symptom of a confused agent; often correlates with low Correctness. |

## Red flags — automatic fail (score 0, `suggested_action: retry` or `re-route`)

- Envelope is not valid JSON, or is wrapped in extra prose.
- `outputs` contains a port not declared in the agent's frontmatter.
- Claimed file paths do not exist (for `write-fs` effects).
- Claimed URLs are placeholder-shaped (`example.com`, `...`) or syntactically invalid.
- Output contains training-data patterns that don't match the actual task (e.g. code for the wrong language).

## Suggested-action rule of thumb

Choose `suggested_action` using the issues you found:

| Worst issue severity | Dimension(s) failing                    | Suggested action |
|----------------------|------------------------------------------|------------------|
| low / medium         | Contract fidelity, Completeness          | `retry` — the agent can fix it with a hint. |
| high                 | Groundedness, Internal consistency       | `re-route` — different agent, same goal; this one is confused. |
| critical             | Correctness (wrong task solved)          | `replan` — the Plan itself was wrong. |
| any                  | Safety / side-effects violated           | `abort` — do not retry; escalate to the user. |
| none (all pass)      | —                                        | `accept`. |

## Verdict shape (return this from `_validator`)

Defined in `agents/_schema.md` §4. Reproduced here for convenience:

```json
{
  "passed": <bool>,
  "score": <float 0..1>,
  "issues": [
    { "severity": "...", "location": "...", "reason": "...", "suggestion": "..." }
  ],
  "suggested_action": "accept" | "retry" | "re-route" | "replan"
}
```

## Pre-submit checklist (for producing agents)

Before emitting your envelope, walk this list:

1. Is my output valid JSON, with exactly one of `outputs` / `retry` / `abort`?
2. Do my `outputs` keys match my declared `outputs` ports, nothing more, nothing less?
3. Did every factual claim come from a tool result or input — not from guess?
4. Did I stay inside my declared `effects`?
5. Are all declared ports populated (no `TODO`, no `...`)?

If any answer is no, either fix the output or return a `retry` envelope with a precise hint. Do not ship a failing result hoping the Validator will catch it — the Validator's job is to enforce the rubric, not to be your QA.
