---
name: test-authoring
description: |
  The locate → author → verify protocol for writing tests from a concrete
  `TestTarget` list. Loaded by: the `tester` worker agent (in
  `/agents-experts` pipeline) and the single-worker dispatch in `/experts`
  (lean) when the request's `skills_to_load` includes test authoring. Closes
  exactly the targets it was given, no more.
---

# Test authoring

This protocol assumes a **concrete list** of `TestTarget`s to close.
Producing that list is a different protocol (`skills/debug-methodology`
emits `test_gaps`; `skills/test-strategy` emits `test_plan`). This one
turns that list into passing, deterministic, named tests.

## Preconditions

- `skills/project-context` loaded. The `Test layout` section tells you the framework and test directories without a filesystem walk; each module's `Tests:` field tells you where its tests belong. If the cache is missing, emit `advisory: "project-context-missing"` and stop.
- A `targets` input exists and is a non-empty array of `TestTarget`s per `agents/_schema.md` §9. Both `origin: "bug-driven"` and `origin: "strategic"` are treated the same — origin is informational (it guides naming, e.g. `test_regression_…` for bug-driven).
- Optional: `fix_summary` (when chained after the debugger) hints whether framing should be regression vs. edge-case.

## 1. Locate

For each target:
- Identify the test file that logically owns `target` — existing file if possible, new file otherwise.
- Identify the framework from the project's **config files** (`pytest.ini`, `jest.config.*`, `pyproject.toml`, `go.mod`, `Cargo.toml`). Do not guess by file extension alone.
- If the project has no tests at all, emit a single file in a conventional location for the detected language, and note this explicitly in `tests_added.summary`.

## 2. Author

- **One test per target.** Do not add bonus tests for cases the upstream did not flag. If you spot another gap while working, mention it in `tests_added.summary` but do not close it — that is a new request.
- **Name after the scenario, not the function.** Good: `test_auth_rejects_empty_port_in_offline_config`. Bad: `test_validate_config`.
- **Bug-driven framing** for `origin: "bug-driven"`. **Behavioural framing** for `origin: "strategic"`.
- Respect `priority`: `critical`/`high` get the most direct and assertive tests; `low` may be a single sanity check.
- The test must **fail without** the behavior under test and **pass with** it. If the behavior is already present (common when chained after a worker that already shipped the fix), verify the test passes now.
- **Simplest input** that exercises the `scenario`. No fuzzing, no snapshot tests unless `scenario` is explicitly about output stability.
- **Deterministic**: no sleeps, no real network, no wall-clock dependence. Stub / inject where needed, but do not over-mock.

## 3. Verify

- Run the new tests. All must pass.
- Run the tests that live alongside them (same file or test module), to confirm no regression from new fixtures or imports.
- Capture the **exact command**. Targeted; not the whole test suite.

## Content rules

- **Tests must name the behavior they protect.** `test_feature_works` tells the next reader nothing. `test_dashboard_blanks_when_user_has_no_orgs` does.
- **No snapshot tests** unless the target is explicitly about output shape/drift.
- **No commentary-only tests.** If you can't find a meaningful assertion, return `retry` with what was missing from the target's `scenario`.

## Pre-submit checklist

Apply `skills/quality-analysis`'s rubric. Specifically:

- Every entry in `targets` has a corresponding test in `tests_added`.
- Every test passes standalone.
- Every test has a scenario-descriptive name (not `test_1`, `test_works`).
- `verification` is a concrete command.
- You did not edit non-test files (other than fixtures strictly required for the tests).
- You stayed within `effects: [read-fs, write-fs]`.

## When to `retry` or `abort`

- `retry` — ambiguous target, unknown framework, missing fixtures. Ask for what is missing.
- `abort` — targets cannot be closed in this pass (too large, requires infra changes, crosses concerns). Do not invent coverage to look thorough.
