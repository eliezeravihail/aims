---
name: test-strategy
description: |
  Design coverage for upcoming code (mode: design) OR assess coverage of an
  existing module (mode: assess). Emits a prioritised list of `TestTarget`s
  with `origin: "strategic"` for the tester (or single worker) to close.
  Read-only: does not write tests, does not prescribe framework or syntax.
  Loaded by: the `test_strategist` worker in `/agents-experts`, and the
  single worker in `/experts` when strategic coverage work is needed.
---

# Test strategy

Decide **what should be tested and why**. Framework, syntax, and specific
assertions are the `test-authoring` protocol's concern.

Two modes:

| `mode`   | Trigger                                                             | Output                         |
|----------|---------------------------------------------------------------------|--------------------------------|
| `design` | A Plan will produce new code; define the test plan up front.        | `test_plan`                    |
| `assess` | Stand-alone evaluation of an existing project's coverage.           | `test_plan` + `coverage_report` |

## Preconditions

- `skills/project-context` loaded. Module graph and `Test layout` are the foundation for risk mapping — you cannot identify a risk surface for a module you have not located.
- In `assess` mode: use the cache's `Sources consulted` footer to calibrate confidence in your report.
- If the cache is missing, emit `advisory: "project-context-missing"` and stop — you are read-only and cannot bootstrap it.

## Mode: `design`

1. Read `task_description` (required) and `plan_context` (optional — other steps of the Plan that will produce code). Form a mental model of what will exist when the Plan finishes.
2. Identify the **risk surface**: inputs, external boundaries (APIs, files, time), state transitions, invariants. Tests exist primarily to guard risk surfaces.
3. For each risk, emit one `TestTarget` (shape in `agents/_schema.md` §9):
   - `test_type` at the smallest level that genuinely exercises the risk (prefer unit; escalate only when the risk is cross-boundary).
   - `target` — the module/function/endpoint where the test belongs.
   - `scenario` — concrete input/state, not "happy path".
   - `origin: "strategic"`.
   - `priority` calibrated to the risk (data-loss bug = critical; cosmetic rendering = low).
   - `rationale` — one sentence.
4. Sort `test_plan` by `priority` descending, then by `test_type` (unit before integration before e2e).
5. Do not write tests. Do not prescribe framework — `test-authoring` picks that from the project's config.

## Mode: `assess`

1. Read the codebase under `codebase_hint`. Inventory the existing tests (location, count, framework).
2. Classify each module / function by coverage:
   - `covered` — exercised by at least one meaningful test.
   - `shallow` — exercised but with weak assertions (e.g. only `assert result is not None`, snapshot-only).
   - `uncovered` — no test touches this path.
3. Identify risk-bearing paths that are `shallow` or `uncovered`. Prioritise by cost-of-defect × probability-of-defect.
4. Emit:
   - `test_plan` — `TestTarget[]` for gaps you would recommend closing, highest-impact first.
   - `coverage_report`:
     ```json
     {
       "total_modules": <int>,
       "covered":       <int>,
       "shallow":       <int>,
       "uncovered":     <int>,
       "framework":     "<pytest|vitest|jest|go test|...>",
       "top_risks": [
         { "target": "<...>", "severity": "critical|high|medium|low", "reason": "<...>" }
       ]
     }
     ```
5. Do NOT produce a "100% coverage" plan. Coverage is a proxy, not the goal; **risk coverage** is the goal.

## Content rules

- **Every TestTarget must be justified by risk**, not by aesthetics. No "should have a test for X because it's public". Every entry has a concrete failure mode it prevents.
- **No implementation details.** You describe scenarios (`"rejects empty port when mode=offline"`), not test code (`"assertRaises(ValueError)"`).
- **Do not expand scope.** Stay within `scope_boundaries` and the `task_description`. Uncovered risks outside the scope go in `coverage_report.top_risks` with a note — not in `test_plan`.
- **Honesty in `assess`.** If coverage is good, say so — an empty `test_plan` with a short positive note in `coverage_report` is a legitimate output. Do not invent gaps.

## Pre-submit checklist

Apply `skills/quality-analysis`'s rubric. Specifically:

- Every TestTarget has all required fields per `_schema.md` §9.
- Every `scenario` is concrete (names inputs/states, not just "edge cases").
- In `design` mode: the plan is scoped to `task_description`, not the whole project.
- In `assess` mode: `coverage_report` numbers come from the actual file inventory you ran, not estimates.
- You did not call any non-read tool. No Edit, no Write.
- You did not write any test code.

## When to `retry` or `abort`

- `retry` — missing `task_description` in `design` or missing `codebase_hint` in `assess`.
- `abort` — the input is contradictory (e.g., scope_boundaries excludes everything that could plausibly be tested).
