# Pilot Report — Medium-Bug Experiment

## Context

Following the LCS pilot (single-line DP bug, baseline won 5.3× on cost),
this second pilot targets a **medium-sized cross-module bug** — the scenario
where the tiered routing architecture is supposed to shine. We picked
**cookiecutter-4 from BugsInPy**: adding `FailedHookException`, raising it
from `hooks.py`, and catching + cleaning up in `generate.py`. Three files,
coordinated change, real maintainer fix we can compare against.

## One-screen result

| Dimension | Baseline (single Sonnet) | With-system pipeline |
|-----------|-------------------------:|---------------------:|
| Bug fixed | ✅                       | ✅                   |
| Regression tests added | 0 (3 listed as text) | **4 authored, all verify-catch the bug** |
| Production diff size | 88 ins / 64 del + `setup.cfg` scope creep | **30 ins / 6 del, stays surgical** |
| Similarity to upstream fix | 134-line diff on `generate.py` | 29-line diff on `generate.py` |
| Tokens | 46,702 | 192,907 (**4.13×**) |
| Duration (serial) | 273 s | ~393 s |
| Validator caught a lying artifact (stretch) | n/a | ✅ **objective detection worked** |

Full numbers and per-tier breakdown: [`tests/pilot_medium/scorecard.md`](tests/pilot_medium/scorecard.md).

## What was proved

1. **The Validator tier is not theatre.** In the stretch experiment, we
   handed a Validator an artifact that claimed a correct fix while the
   actual code raised `ValueError` instead of `FailedHookException`. The
   Validator ran the tests, read the source, and produced
   `passed: false, score: 0.15, fix_matches_claim: false` with two
   critical issues citing the exact line. Baseline has no such layer;
   a broken fix would ship.

2. **Router drift is fixable.** Last pilot, Haiku Router spent 26k tokens
   and 2 tool calls analyzing code before triaging — violating its own
   contract. This pilot, with `tools: [Read]` restriction and an explicit
   "do not analyze the bug yourself" line in the prompt, Router used
   **zero tool calls** and returned a clean envelope in 1.7 s. Prompt
   discipline is cheap to add and effective.

3. **Separation of concerns actually produces different artifacts.** The
   debugger emitted 5 test gaps (bug-driven). The test_strategist ran
   assessment and emitted 7 gaps (strategic) including the
   `overwrite_if_exists + hook failure` interaction that the debugger
   missed. These are different angles; having both roles is not redundant.

## What remains uncertain

1. **The cost ratio (4.13×) is real.** For a one-off bug, it's not
   obviously worth it. For a production codebase where the regression
   tests will guard future refactors, it is. The question becomes
   organisational, not technical.

2. **Re-route / replan paths were not exercised.** The debugger got the
   fix right on the first pass, so the recovery paths in the state machine
   haven't been validated on a real bug. A follow-up experiment where the
   debugger deliberately produces an imperfect fix would cover this.

3. **test_strategist is expensive.** 43k tokens is ~20% of the pipeline.
   It produced real value (the `overwrite_if_exists` gap) but may not be
   justified on every run. A heuristic to skip it when the debugger's
   gaps are already comprehensive would reduce cost with low coverage risk.

## Architectural conclusions

Moving into Phase 3, my recommendations are:

1. **Keep the 3-scope model**. The pilot shows `complex → full pipeline`
   produces measurably different outcomes. Collapsing to 2 would lose the
   trivial fast-path without clear gain.

2. **Promote the Validator** in the docs as the core value proposition.
   It is the tier that most directly catches LLM errors the baseline
   would ship. Every other tier can be argued with — this one has
   empirical support.

3. **Harden the Router-restriction pattern** into the agent specification
   template: `tools` field should default-minimal, and every infra-agent
   prompt should explicitly forbid domain work. Document this as a
   convention in `agents/_schema.md`.

4. **Make test_strategist opt-in** for simpler complex tasks. Add a
   Planner heuristic: skip the strategist step when the debugger's
   own gaps are ≥ 3 high/critical and cover the same module surface.

5. **Run a pilot with deliberate debugger failure**. Force a retry → replan
   loop. That's the only remaining major path that hasn't been exercised
   on real data.

## Files in this commit

- `PILOT_MEDIUM_REPORT.md` — this file
- `tests/pilot_medium/scorecard.md` — detailed scorecard
- `tests/pilot_medium/baseline/fix.diff` — baseline's production diff
- `tests/pilot_medium/with_system/fix.diff` — with-system debugger's production diff
- `tests/pilot_medium/with_system/test_hook_cleanup_strategic.py` — the 4 regression tests authored by the tester
- `tests/pilot_medium/regression_test_injected.py` — shared ground-truth regression test present in both sandboxes
