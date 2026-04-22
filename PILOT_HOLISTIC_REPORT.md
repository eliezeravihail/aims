# Pilot — `holistic` scope re-run (contacts CLI)

## Why this pilot exists

The TODO-CLI pilot (`PILOT_FEATURE_REPORT.md`) showed that on a bounded
feature build, the decomposed pipeline produced a **subtly broken**
implementation (id-reuse after full drain) while a single Opus dispatch
produced a correct one. The architectural response was the `holistic`
scope and the `dispatch-baseline` action — an escape hatch that routes
a feature build to a single Opus dispatch with no decomposition.

This pilot tests the prediction: given a similar bounded-feature build,
the Router now classifies as `holistic`, the Executor dispatches
`_baseline` only, the pipeline produces a correct implementation, and
the cost ratio drops from 6.8× toward ~1× plus Router overhead.

## Task

A terminal contacts-manager CLI in Python. Same profile as TODO —
bounded, plain-text persistence, CRUD + search, one English sentence
description. Same pilot shape; different surface, to avoid overfitting.

## Result

| Dimension | Baseline (Opus × 1) | With-system (Router → `_baseline`) |
|-----------|--------------------:|-----------------------------------:|
| Drain-then-add id | **3** (monotonic ✓) | **3** (monotonic ✓) |
| Tests / assertions | 15 unittest cases | 42-assertion verify.sh |
| LOC production | 341 | 356 |
| Tokens — Router | n/a | **26,539** |
| Tokens — Worker | 23,191 | **25,124** |
| Tokens — total | **23,191** | **51,663** |
| Cost ratio | 1.00× | **2.23×** |
| Dispatches | 1 | 2 |
| Router routed to | n/a | **`dispatch-baseline` / `holistic` ✓** |
| Envelope-shape conformance | n/a (free-form) | **canonical ✓** (no drift) |
| Tool-use discipline — Router | n/a | 2 Read-only (no drift) |

## Hypotheses from `FRAMEWORK_EVAL_PLAN.md` — grades

**H1 (Router scope classification):** ✅ PASS. Router classified
`holistic` + `dispatch-baseline` on first try, rationale: "Self-contained
CLI app: single-feature implementation, no test/audit/split concerns.
One agent suffices." Matched expected classification.

**H2 (Router tool discipline):** ✅ PASS, qualified. 2 Read-only tool
calls (presumably `agents/registry.md` + `.claude.md`). No Bash, no
Grep, no Edit, no attempt to read the user's codebase. Still not zero —
but strictly within the `tools: [Read]` allowlist. Previous pilots had
drift; this one does not.

**H3 (Envelope shape compliance):** ✅ PASS. Both dispatched agents
(`_router` and `_baseline`) emitted canonical `{schema_version, ok,
outputs}` shape. The implementer/tester drift observed in the TODO
pilot did not recur here — likely because the `_baseline` spec
explicitly states the envelope shape in the agent body's output contract.

**H4 (Validator correctness):** n/a. The `holistic` path skips the
Validator by design; this hypothesis doesn't apply.

**H5 (Holistic vs Complex routing):** ✅ PASS. On a task the previous
design would have routed to `complex` → full 7-tier pipeline (and lost
on correctness), the new `holistic` rule routed to `_baseline` directly
and matched baseline quality.

**H6 (Cost ratio trend):** ✅ PASS. Pipeline/baseline ratio dropped from
6.8× (TODO) to **2.23×** here. The saving is the cost of Planner (−13k)
+ test_strategist (−44k) + implementer Sonnet pass (−32k) + 2 Validator
passes (−60k) + tester (−37k) — all skipped in the holistic path.

## Evidence the prediction held

1. **Same invariant, opposite outcome from TODO pilot.**
   On the TODO pilot, the decomposed pipeline produced `id=1` after
   full drain (bug). This time, with the holistic path, the pipeline
   produced `id=3` — matching baseline's correct behaviour.

2. **Cost collapse of ~3×.**
   192,907 tokens (TODO, complex path) → 51,663 tokens (this pilot,
   holistic path) for a task of comparable complexity. The Router's
   new classification turned a 6.8× overhead into a 2.23× overhead.

3. **Router stayed in lane.**
   Zero drift into the task's domain. The `tools: [Read]` restriction
   and the "do not analyse the request" line in the prompt held under
   a second test case. Consistent with the cookiecutter pilot (where
   these guards were first introduced) and unlike the TODO pilot
   (where they had regressed).

## What this doesn't prove

- **Router accuracy on harder classifications.** This task was
  textbook-holistic (one-sentence description, no "with tests", no
  "and also"). A more ambiguous request might still misroute. Next
  pilot should stress classification boundaries.

- **`_baseline` quality on larger features.** The contacts CLI fits
  comfortably in one Opus dispatch. Bigger features may push against
  context limits, at which point `complex` would be the right choice
  even if the task "feels" holistic. No data on that yet.

- **The 2.23× cost is still real.** It buys correct scope routing —
  a decision the user would otherwise have to make themselves. Whether
  that's worth ~27k tokens per dispatch depends on how often users can
  classify correctly without help.

## Residual risks

- Router drift could return on a larger/more ambiguous request. H2 held
  here but has failed before.
- Envelope shape held here but failed on 2/3 workers in the TODO pilot.
  One datapoint of non-drift is encouraging, not conclusive.
- The cost-ratio improvement is entirely due to skipping the pipeline.
  If the Router ever misroutes a holistic task as complex, the
  improvement evaporates; conversely if it misroutes a truly complex
  task as holistic, correctness drops to a single-dispatch ceiling.

## Files

- `tests/pilot_holistic/baseline/` — contacts.py (341 LOC) + test_contacts.py (220 LOC, 15 tests)
- `tests/pilot_holistic/with_system/` — contacts.py (356 LOC) + verify.sh (42 assertions)
- This report

## One-line verdict

**The `holistic` / `dispatch-baseline` escape hatch works as designed.**
On a bounded feature build, the Router now correctly routes to a single
Opus dispatch, the pipeline produces a correct implementation (including
the monotonic-id invariant the TODO pipeline failed on), and the cost
ratio drops from 6.8× to 2.23×.
