# Pilot Report — Feature Build (Terminal TODO CLI)

## Target

Greenfield Python CLI, plain-text persistence, 5 operations (add / list /
complete / remove / persist across runs), standard edge cases. Both
implementations built from the same spec into isolated sandboxes.

## Protocol

- **Baseline**: single **Opus** dispatch. "Plan and build this."
- **With-system**: tiered pipeline that required adding a new worker:
  Router (Haiku) → Planner (Opus) → test_strategist (Sonnet, design mode)
  → implementer (Sonnet) → Validator (Sonnet) → tester (Sonnet) →
  Validator (Sonnet).

The `implementer` agent did not exist when this pilot began. Running the
Router on an empty-of-implementer registry would have left the Planner
unable to build a feature. **The first finding of this pilot was exposed
before dispatch #1**: the registry had no worker for greenfield code.
Adding `agents/implementer.md` (Sonnet, symmetric with `tester`) was the
price of running the pipeline at all.

## One-screen result

| Metric                                        | Baseline (Opus × 1) | With-system (7-tier)    |
|-----------------------------------------------|--------------------:|------------------------:|
| Tests pass end-to-end                         | ✅ 13/13             | ✅ 93/93                |
| Monotonic ids across full drain (add A, add B, remove both, add C → id=?) | ✅ id=3 (correct)  | ❌ **id=1 (reuses)** |
| LOC produced (production)                     | 303                 | 416 (5-module package)  |
| LOC tests                                     | 155                 | 840 across 5 files      |
| Tokens (total)                                | **26,841**          | **182,574** (**6.8×**)  |
| Duration (serial)                             | 125 s               | ~660 s (5.3×)           |
| Tool uses                                     | 11                  | 117                     |
| Envelope-shape conformance from workers       | n/a                 | **2/3 violated** (implementer used `{status,port}`, tester used `{agent,status}`) |
| Validator caught implementer's monotonicity bug | n/a               | ✅ (1st Validator pass, score 0.94) |
| Strategist+tester caught implementer's monotonicity bug | n/a          | ❌ (target list didn't enumerate drain-then-add) |

Full per-tier breakdown: `tests/pilot_feature/scorecard.md`.

## The headline finding

**Baseline produced a more correct implementation on the monotonicity
invariant than the with-system pipeline did.**

On the drain-then-add sequence:

| Sequence | Baseline result | With-system result |
|----------|-----------------|--------------------|
| `add a, add b, remove 1, remove 2, add c` | `[ ] 3  c` | `[ ] 1  c` |

Opus (single dispatch) chose to persist a `# next_id=<n>` header in the
task file, so the next id is always strictly greater than any id ever
assigned — surviving full drains and process restarts. The with-system
implementer (Sonnet) used `max(existing_ids) + 1` with a default of 1 on
empty — mathematically fine until the list is empty, at which point ids
are reused.

Why did the pipeline not catch this?
- `test_strategist`'s 29 TestTargets covered: monotonicity within a
  session (`add successive → strictly increasing`), but **not** the
  specific post-drain path.
- `tester` wrote 93 tests. All 27 targets (I dropped 2 from strategist's
  29 to keep prompt size bounded) were faithfully covered — but the
  invariant was never a target.
- `_validator` (after the implementer step) **did** catch the bug,
  flagged it as `high` severity with a precise `retry_hint`. But
  `verdict.passed = true` (score 0.94 ≥ threshold), so the Router's
  decision table says `accept`, not `retry`. The bug proceeded.

This is an honest architectural failure: **the pipeline's coverage is
only as good as its strategist's enumeration**. A strategist that misses
a risk surface produces blind spots no downstream worker can fix.

## What the pipeline did produce that baseline did not

### 1. Modular package layout
Baseline: 1 monolithic `todo.py` (303 lines). With-system: 5-module
`todo/` package (storage, tasks, cli, __main__, __init__). Easier to
review, modify, and test in isolation.

### 2. 7× test coverage
Baseline: 13 unittest cases. With-system: 93 pytest cases across 5 files
with clear class-per-target organization. Most of the extras are real
scenarios (unicode, property-based round-trip, subprocess-level e2e).

### 3. Explicit test plan as an artifact
The strategist's 29 TestTargets are a **plan of record** — you can read
them before reading any test code to know what's covered and why. That's
a governance property the baseline can't offer.

### 4. Objective Validator pass on the implementer
The Validator's verdict on the implementer explicitly listed:
- envelope shape violation (high)
- monotonicity bug (medium)
- `--5` edge case in id parsing (low)
- hardcoded default path (low)

Whether the Router chose to act on these is a separate decision. The
artifacts exist and are auditable.

## Envelope-shape violations in back-to-back workers (new finding)

Both Sonnet workers emitted non-conforming outer envelopes:
- implementer: `{"status": "success", "port": "done", "outputs": {...}}`
- tester: `{"agent": "tester", "status": "done", "outputs": {...}}`

Neither is the canonical `{"schema_version":1, "ok":true, "outputs":{...}}`
the schema requires. The harness's strict validator would reject both.

**Hypothesis**: Sonnet reads the full agent body spec, sees the output
contract, and paraphrases it rather than copying. Fixing this requires
either:
- A one-shot envelope example in every worker's prompt.
- A post-processor in the Executor that normalizes common shape drifts
  (`status→ok`, `port/agent→discarded`) before passing to the schema
  validator.

Recommendation: add a **one-shot envelope example** at the end of every
worker's body. That's ~3 lines per agent and removes ambiguity.

## Per-tier breakdown

| Step | Model | Tokens | Tool uses | Duration | Findings |
|------|-------|-------:|----------:|---------:|----------|
| Router (pre-exec) | Haiku | 26,766 | 3 | 10.9 s | Drift returned: analyzed request in prose before JSON despite tool restriction. Still produced valid envelope. |
| Planner | Opus | 13,135 | 0 | 18.6 s | Clean 3-step plan with correct `${...}` binding. |
| test_strategist (design) | Sonnet | 11,346 | 0 | 39.2 s | 29 TestTargets. Coverage blind spot: no drain-then-add target. |
| implementer | Sonnet | 31,627 | 43 | 219 s | 5-module package. Envelope shape wrong. Monotonicity bug in `_next_id()`. |
| Validator (impl) | Sonnet | 22,906 | 24 | 105 s | Caught monotonicity bug, envelope violation, and 2 minor issues. `passed: true` → pipeline proceeded. |
| tester | Sonnet | 43,388 | 24 | 160 s | 93 tests authored, all pass. Closed 27/27 handed-in targets. Envelope shape wrong. |
| Validator (test) | Sonnet | 33,406 | 26 | 110 s | Flagged missing drain-then-add coverage; 2 vacuous tests; `passed: false`, score 0.77, suggested retry. |
| **Total** | | **182,574** | **120** | **~660 s** | |

## What this pilot proved

1. **For a bounded feature, Opus single-shot can beat a decomposed
   pipeline on correctness.** The cost differential (6.8×) buys more
   tests and better structure, but does *not* buy better correctness on
   invariants the strategist fails to enumerate.

2. **Registry completeness is a prerequisite.** A routing architecture
   that can't build greenfield features is missing a worker class. The
   `tester`/`test_strategist` pair implied the symmetric need for an
   `implementer`; only the feature pilot exposed it.

3. **The Validator finds real bugs, but `passed: true + suggested_action:
   retry` is a decision-table ambiguity.** The current rule says
   `passed: true → accept`. On this pilot that meant a known bug shipped
   to the tester stage. Either the rule needs to tighten (any non-accept
   suggestion triggers retry) or the Validator needs to be stricter about
   `passed: true`.

4. **Envelope-shape drift is consistent enough to need a fix.** Two out
   of three Sonnet workers produced malformed outer envelopes. Add a
   one-shot example per agent body, or a tolerant normalizer in the
   Executor.

5. **The strategist is the coverage bottleneck.** Missing an invariant at
   plan time means the tester won't close it. Feature pilots should
   iterate strategist→Validator loops, not just tester→Validator.

## Recommendations (in order)

1. **Tighten the Router decision table**: `verdict.passed == true AND
   verdict.suggested_action != "accept"` → `retry`, not `accept`. This
   single change would have caught the monotonicity bug on this pilot.

2. **Add a one-shot envelope example** to every worker body. Non-trivial
   for retroactive consistency; ~3 lines per agent.

3. **Strengthen `_planner.md` to enumerate invariants**, not just data
   and control flow. Current feature-build pattern is
   `strategist → implementer → tester`. Add: the strategist must
   explicitly enumerate at least one test target per user-visible
   invariant mentioned in the feature description.

4. **Pilot Opus as the implementer** — once — on the same task, to
   isolate whether the monotonicity miss is a Sonnet limitation or a
   decomposition limitation. If Opus+decomposition still misses it, the
   strategist is at fault. If it doesn't, the worker model is.

5. **Don't claim feature-build capability in docs until the above land.**
   On this pilot the pipeline produced a **subtly broken** implementation
   where the single-Opus baseline produced a correct one.

## Artifacts

- `tests/pilot_feature/baseline/todo.py` + `test_todo.py`
- `tests/pilot_feature/with_system/todo/` (5-module package)
- `tests/pilot_feature/with_system/tests/` (5 test files, 93 tests)
- This report.
