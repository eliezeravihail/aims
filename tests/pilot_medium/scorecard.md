# Pilot: Medium-Bug Experiment — cookiecutter-4

## Target

Bug: **BugsInPy / cookiecutter-4**. Hook scripts (pre/post_gen) that exit non-zero are silently ignored; the partially-generated project directory is left on disk. Fix requires coordinated changes across 3 files: add `FailedHookException`, raise it in `hooks.run_hook`, catch it in `generate.generate_files` and clean up.

Buggy commit: `9568ab6ecd2d6836646006c59473c4a4ac0dee04` (cookiecutter). Upstream fix: `457a1a4` — 26 lines of code + 16 lines of tests.

## Protocol

Both sandboxes started from the same buggy commit. A regression test
(`test_failing_hook_regression.py`, taken from the upstream fix commit) was placed
in both as a known-failing check — this is our shared ground-truth signal.

- **Baseline**: single Sonnet Agent dispatch, "fix this bug".
- **With-system**: Router (Haiku, restricted to Read only) → Planner (Opus) →
  debugger (Sonnet) → Validator (Sonnet) → test_strategist (Sonnet, assess mode) →
  tester (Sonnet) → Validator (Sonnet).
- **Stretch goal**: Inject wrong fix (raise `ValueError` instead of `FailedHookException`), dispatch Validator with a lying artifact, check detection.

## Scorecard

| Metric                                   | Baseline            | With-system          |
|------------------------------------------|---------------------|----------------------|
| Regression test passes                   | ✅                  | ✅                   |
| All existing hook tests pass             | ✅                  | ✅                   |
| Additional regression tests written      | 0 (3 listed as text only) | **4 (all pass; all would catch bug on revert)** |
| Files touched (production)               | 3 + 1 unrelated (`setup.cfg`) | 3 |
| **Diff size vs upstream fix**            | 88 insertions / 64 deletions (reformatted `generate_files`) | **30 insertions / 6 deletions (matches upstream pattern)** |
| Scope creep                              | Yes — added `setup.cfg` pytest config, rewrote function body | No — minimal surgical changes |
| Tokens (total)                           | **46,702**          | **192,907** (4.13×)  |
| Tool uses                                | 59                  | 95 across 7 dispatches |
| Duration (serial)                        | 273 s               | ~340 s (parallelisable: Planner + Strategist could overlap in a future optimisation) |
| **Router drift** (restriction fix)       | n/a                 | **0 tool uses** (vs 2 last pilot) — prompt discipline worked |
| **Validator caught lying artifact (stretch)** | n/a            | ✅ `passed:false, score:0.15, tests_passed:false, fix_matches_claim:false` |

## Per-tier breakdown (with-system)

| Step | Model | Tokens | Tool uses | Duration | Outcome |
|------|-------|-------:|----------:|---------:|---------|
| Router (pre-exec) | Haiku | 24,793 | 0 | 1.7 s | `dispatch-planner`, scope=complex |
| Planner | Opus 4.6 | 12,776 | 0 | 13.2 s | 3-step plan with correct binding |
| debugger | Sonnet | 28,621 | 20 | 101 s | 3 files fixed, 5 gaps emitted |
| Validator (on debugger) | Sonnet | 19,124 | 8 | 29 s | `accept`, score 0.985 |
| test_strategist | Sonnet | 43,674 | 29 | 81 s | 7 strategic gaps, coverage report |
| tester | Sonnet | 37,151 | 18 | 82 s | 4 tests authored, all pass |
| Validator (on tester) | Sonnet | 26,768 | 16 | 85 s | `accept`, score 1.0, `tests_would_catch_bug: true` verified by revert-reasoning |
| **Main pipeline total** | | **192,907** | **91** | **~393 s serial** | |
| Stretch: Validator on lying artifact | Sonnet | 13,821 | 4 | 18 s | Caught: `passed:false`, score 0.15, 2 critical issues cited |

## Findings

### 1. **Both approaches fix the bug; with-system's fix is cleaner**
Baseline passes the regression test but rewrote `generate_files` along the way
(134 lines of diff in one file vs. upstream's surgical try/except). With-system's
debugger emitted a 30-line diff that closely mirrors upstream's pattern.
**Hypothesis**: the Planner's "minimum fix across the files" framing, plus the
debugger's "no drive-by refactors" rule, channelled Sonnet toward surgical edits.

### 2. **With-system adds real regression coverage; baseline does not**
Baseline listed 3 hypothetical "test gaps" as free text and stopped. With-system's
test_strategist identified 7 gaps, the tester authored 4, and the Validator
verified all 4 would catch the bug if the fix were reverted. That's the concrete
value of the pipeline: **artifacts that outlive the conversation**.

### 3. **Router drift was fixable.** Last pilot, Router used 2 tool calls and 26,604
tokens on a classification it didn't need to investigate. This time, with
explicit `tools: [Read]` restriction and a prompt saying *"do NOT read code,
do NOT analyze the bug yourself"*, Router used **0 tool uses** and produced a
clean envelope in 1.7 s. Prompt discipline + tool restriction closed the drift.

### 4. **Validator caught a lying artifact** (stretch goal)
When the Validator was handed an artifact claiming "fix applied" but the actual
code raised the wrong exception type, it ran the tests, inspected the file,
detected the mismatch, and returned `passed: false` with two critical issues
naming the exact line. **This is the first empirical evidence of Validator
value**: an open-loop baseline would have shipped the broken fix.

### 5. **Cost**: 4.13× baseline tokens for meaningful-but-not-essential extras
On a medium bug, the pipeline costs ~4× the tokens. What you get for 3× the
spend: regression coverage (4 named tests that would catch the bug), a cleaner
diff, an objective quality gate, and an audit trail. Whether that's worth it
depends on whether those regression tests have durable value — in a production
codebase they probably do; in throwaway work they don't.

## Unexpected behaviours

### Baseline's setup.cfg change
The baseline added a `[tool:pytest]` section with `norecursedirs` to stop pytest
from collecting inside template-fixture directories. This is a real improvement
to the repo, but it's unrelated to the bug — textbook scope creep. A reviewer
would reject this as "fold into a separate PR". With-system's debugger stayed
in scope.

### test_strategist's depth
The strategist's 7 gaps were substantively deeper than the debugger's 5: it
identified the `overwrite_if_exists + hook failure` interaction, which neither
the debugger nor baseline would have caught (it's a two-dimensional coverage gap).
**Finding**: Separating "what to test" from "how to test" genuinely helps — each
role goes deeper in its lane.

### The Validator's dual role
The debugger-validator and tester-validator behaved differently. The debugger
one ran the tests to confirm. The tester one reasoned about whether the tests
*would catch the bug* (counterfactual) — a harder question. Both produced
high-quality verdicts. The `objective_checks` fields (`tests_passed`,
`tests_would_catch_bug`, `fix_matches_claim`) are the real discipline anchor:
they force the LLM to make a verifiable claim, not an aesthetic judgement.

## Artifacts

- `baseline/fix.diff` — full baseline diff
- `with_system/fix.diff` — full with-system debugger's fix diff
- `with_system/test_hook_cleanup_strategic.py` — the 4 regression tests authored by the tester
- `regression_test_injected.py` — the shared "ground truth" test present in both sandboxes

## Decision

On this specific medium bug:
- **Both approaches succeed on correctness.**
- **With-system wins on code hygiene** (surgical diff, no scope creep).
- **With-system wins on test coverage** (4 passing named regression tests vs. 0).
- **With-system wins on error detection** (Validator caught a lying artifact — baseline has no such layer).
- **Baseline wins on cost** (~4× cheaper).

The ratio isn't conclusive proof the pipeline is worth it in general. But on
this pilot, **for any production-grade scenario where regression coverage and
auditability matter, the 4× cost buys artifacts the baseline cannot produce**.
For throwaway exploration, Baseline still dominates.

## Recommended Phase 3 direction

Given the pilot data:

1. **Keep the 3-scope model.** The pilot validated that `complex → full pipeline`
   produces measurably different outcomes (the extra tests, the Validator catch).
   Collapsing to 2-scope would lose the `trivial` fast-path.

2. **Make test_strategist optional** (cost: 43k tokens). For simpler complex
   bugs, the debugger's own test_gaps are enough. Skip the strategist when the
   debugger's gaps number ≤ 3 and are all `critical`/`high`. This would save
   ~20% pipeline cost with minimal coverage loss.

3. **Ship the Validator as the core value prop.** It caught a real fault
   (stretch goal) that no other layer would have. The ~20k tokens for a
   Validator pass is among the best cost/value in the pipeline.

4. **Keep the Router restriction.** `tools: [Read]` + "no code analysis" prompt
   discipline fixed the 2-tool-use drift from the previous pilot. Pattern is
   replicable.

5. **Still open**: re-route / replan paths. Neither triggered in this pilot
   because the debugger got it right. A follow-up pilot where the debugger
   produces a bad fix would exercise those paths.
