# Agent Registry

Authoritative list of **worker** agents available to `/project:experts`.
Infrastructure agents (`_router`, `_planner`, `_validator`) are not listed
here — they are always present; this registry is only for workers that
consumers plug in.

To register an agent: create `agents/<id>.md` conforming to the schema in
`agents/_schema.md`, then append one row to the table below.

| id       | file                | one-line capability                                                  |
|----------|---------------------|-----------------------------------------------------------------------|
| debugger | agents/debugger.md  | Reproduce, isolate, fix, and verify a bug. Terminal `verification` step. |

## Contract references
Every registered agent must conform to:
- `agents/_schema.md` — frontmatter, envelope, Plan, Verdict shapes
- `skills/quality-analysis/SKILL.md` — quality rubric (loaded by the agent itself as a pre-submit checklist, and by `_validator` as an evaluation rubric)

## How the registry is consumed
- `_router` reads it to pick a single agent in the simple-dispatch path.
- `_planner` reads it to constrain which agents may appear in a Plan.
- `/project:experts` reads it to resolve `agent` references inside a Plan before dispatch.

No other file should reach into the registry directly.
