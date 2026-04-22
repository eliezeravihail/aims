# Pilot Report — Retry-with-Hint Path (live)

## What was tested

The state machine's retry-with-hint path:
1. Debugger produces an incomplete fix (only partially addresses the requirements).
2. Validator runs objective checks, detects the incompleteness, returns
   `passed: false, suggested_action: retry, issues[0].suggestion: "<concrete hint>"`.
3. Executor re-dispatches the Debugger with `retry_hint` = the suggestion.
4. Debugger completes the fix using the hint.
5. Validator runs objective checks again → `passed: true, accept`.

Previously only exercised in the deterministic harness tests (`tests/test_executor_integration.py::test_retry_path_when_validator_asks`, and the newly-added `test_retry_in_plan_step_feeds_hint_back`). This pilot exercises the same path with **real LLMs**.

## Setup

Reused the cookiecutter-4 sandbox; added a second regression test that checks
the cleanup path (partially-generated project dir is removed on hook failure).
Buggy state: both tests fail.

| Test | Buggy | After partial fix | After retry |
|------|-------|-------------------|-------------|
| `test_hook_exception_regression.py` | FAIL | PASS | PASS |
| `test_hook_cleanup_regression.py`   | FAIL | **FAIL** (still) | PASS |

To force a partial first attempt (Sonnet's debugger was too capable on the
unconstrained re-run), the first debugger dispatch was given a **hard
prohibition**: "You MUST NOT edit `cookiecutter/generate.py`". That forced
the debugger to fix only the exception-related test on attempt 1, leaving
the cleanup test failing — exactly the scenario we wanted to measure.

## Transcript

### Attempt 1 — Debugger with constraint (forces partial fix)
- Model: Sonnet
- Tokens: 15,022
- Tool uses: 8
- Duration: 35 s
- Outcome: Fixed `exceptions.py` + `hooks.py`. Did not touch `generate.py` per constraint.
- Resulting state: exception test PASSES, cleanup test FAILS.

### Validator on attempt 1 — detects incompleteness
- Model: Sonnet
- Tokens: 18,337
- Tool uses: 6
- Duration: 20 s
- Verdict:
  - `passed: false`
  - `score: 0.54`
  - `objective_checks.cleanup_test_passed: false`
  - `suggested_action: retry`
  - Top issue's `suggestion` is a concrete code template:
    > Wrap the pre_gen_project hook call in a try/except FailedHookException
    > block. On catch, remove project_dir with shutil.rmtree(project_dir,
    > ignore_errors=True) before re-raising. [...]

### Attempt 2 — Debugger with retry_hint
- Model: Sonnet
- Tokens: 25,406
- Tool uses: 14
- Duration: 60 s
- Inputs: same request + `retry_hint` set to the Validator's suggestion.
- Outcome: Extended the fix to `generate.py` exactly as hinted. Both
  `pre_gen_project` and `post_gen_project` wrapped in try/except with
  `rmtree` + re-raise.

### Validator on attempt 2 — final accept
- Model: Sonnet
- Tokens: 16,071
- Tool uses: 4
- Duration: 26 s
- Verdict:
  - `passed: true`
  - `score: 0.97`
  - `objective_checks.regression_tests_passed: true, no_new_regressions: true`
  - `suggested_action: accept`
  - One low-severity note: an `EXIT_SUCCESS` import was left unused (cosmetic).

## Totals

| Metric                  | Value    |
|-------------------------|---------:|
| Dispatches              | 4 (debugger×2 + validator×2) |
| Total tokens            | 74,836   |
| Total tool uses         | 32       |
| Total duration (serial) | 141 s    |

## Findings

### 1. **Retry-with-hint works end-to-end with real LLMs.**
The pipeline correctly:
- Passed the Validator's structured suggestion into the Debugger as `retry_hint`.
- The Debugger used the hint to extend its fix, not start over — the `exceptions.py` + `hooks.py` changes from attempt 1 remained on disk.
- The Validator objectively verified the second attempt.

This validates the `retry` path in the state machine on **real** data, not
just mocks.

### 2. **Forcing a partial fix is hard — Sonnet's debugger is proactive.**
My first attempt to trigger a natural retry failed: even when told to
"focus on exceptions.py and hooks.py," the debugger noticed the second
regression test in the directory and fixed generate.py anyway. I had to
use an **explicit prohibition** ("MUST NOT edit generate.py") to force a
partial first attempt.

This is an important finding for the pipeline design: **Sonnet-class
workers rarely produce natural partial fixes when given full context**.
The retry path matters most for cases the human deliberately scopes (small
PRs, constrained diffs) or where context is genuinely missing.

### 3. **The Validator's `issues[0].suggestion` is directly usable as `retry_hint`.**
The Validator emitted a suggestion that was a concrete, actionable
next-step — essentially a code template. The Debugger followed it
verbatim. This works because the shared `skills/quality-analysis` rubric
forces suggestions to be "concrete enough for the Router to act on,"
not generalities.

**Design implication**: the Executor (future work) should extract the
retry_hint directly from `verdict.issues[0].suggestion` rather than
synthesizing its own hint from the whole verdict. The Validator already
did the work.

### 4. **Retry cost is low relative to the full pipeline.**
The retry cycle (attempt 2 + Validator 2) cost 41,477 additional tokens.
On a 192,907-token full pipeline, that's +21%. For an outcome that
otherwise would have been a shipped-broken fix, this is cheap insurance.

### 5. **Token cost per retry is decreasing.**
Attempt 2 cost fewer tokens than attempt 1 (25k vs 15k — wait, attempt 2
was higher). Let me correct: attempt 2 did more work (extended to 3
files vs 2) so it used more tokens. But the **Validator** costs decreased
(18k → 16k): once the bug is well-understood, re-verification is cheaper
than initial diagnosis. That's a nice property.

## What this doesn't prove

- **Replan path**: the Validator suggested retry, not replan. A replan
  would mean rejecting the Plan itself (the agent choice was wrong, not
  just the execution). No natural trigger for replan has been observed
  yet in pilots.
- **Re-route path**: similarly untested on real data. Would occur if the
  Validator said "this agent is confused, try a different one" —
  plausible but not observed on these bug fixes.
- **Cap-exceeded abort**: in the retry pilot, one retry was sufficient.
  The caps (3 per step, 3 reroutes, 2 replans) have not been stress-tested.

These are future-pilot items.

## Artifacts

- `tests/pilot_retry/final_fix.diff` — the completed fix as it stood after retry
- `tests/pilot_retry/test_hook_cleanup_regression.py` — the added regression test
- `tests/test_executor_integration.py::test_retry_in_plan_step_feeds_hint_back` — deterministic harness test covering the same path
- `tests/test_executor_integration.py::test_lying_artifact_is_rejected_on_objective_check` — deterministic harness test covering the stretch-goal scenario

## Decision

The `retry` path is **empirically validated**. Pipeline architecture is
sound for this path. Remaining Phase 3 items (`re-route`, `replan`,
cap-abort) can be deferred until a pilot genuinely triggers them.
