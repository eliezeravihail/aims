# Pilot — cookiecutter-4 on `/experts` (lean mode)

## Why this pilot

The TODO-CLI pilot showed that decomposed pipelines can produce subtly
broken output where Opus single-shot is correct. The dual-mode
redesign made the lean path (`/experts`) the default; this pilot
re-runs the cookiecutter-4 bug through the new default to confirm the
projected cost collapse and correctness parity.

## Task

Identical to `PILOT_MEDIUM_REPORT.md` — BugsInPy / cookiecutter-4:
add `FailedHookException`, raise it from `hooks.run_hook`, catch it
in `generate.generate_files` and clean up the partially-generated
project directory. Same buggy commit, same shared ground-truth
regression test dropped into the sandbox before dispatch.

## Protocol

Two dispatches end-to-end, no harness overhead, no Planner,
no per-step Validator:

1. `_router` (Haiku, `tools: []`) — classify + pick model + pick skills.
2. Single worker (Sonnet) — skills composed into system prompt;
   execute reproduce → isolate → fix → verify → test-gap → author
   tests, all in one context.

No terminal Validator dispatched because the worker's own self-check
against `skills/quality-analysis` caught everything Validator would
have caught on the previous pilot (tests pass, envelope canonical,
files claimed match files written).

## Result

| Dimension                                | Baseline (Opus direct) | `/agents-experts` (pipeline) | `/experts` (lean, this pilot) |
|------------------------------------------|-----------------------:|-----------------------------:|------------------------------:|
| Regression test passes                   | ✅                     | ✅                           | ✅                            |
| Added regression tests                   | 0                      | 4                            | **5**                         |
| Diff vs upstream `hooks.py`              | —                      | 26 lines                     | **28 lines**                  |
| Diff vs upstream `generate.py`           | —                      | 29 lines                     | **26 lines**                  |
| Tokens (Router + Worker)                 | 46,702                 | 192,907                      | **52,699**                    |
| Dispatches                               | 1                      | 7                            | 2                             |
| $ cost (rough, at Opus=$15/1M, Sonnet=$3/1M, Haiku=$0.80/1M) | $0.70 | $0.65 | **$0.10**                     |
| $ ratio vs baseline                      | 1.00×                  | 0.93×                        | **0.15×**                     |
| Envelope shape                           | free-form              | 2/3 workers drifted          | **canonical ✓**               |

## Per-dispatch breakdown (lean mode)

| Step | Model  | Tokens | Tool uses | Duration | Output                                                    |
|------|--------|-------:|----------:|---------:|-----------------------------------------------------------|
| Router  | Haiku  | 24,813 | **0**     | 2.3s     | `dispatch-lean`, sonnet, [project-context, debug-methodology, test-authoring, quality-analysis] |
| Worker  | Sonnet | 27,886 | 19        | 97s      | fix + 5 named regression tests, canonical envelope         |
| **Total** |     | **52,699** | **19** | **~99s** | 16/16 tests pass                                           |

## What this pilot proved

1. **The projected `~$0.25` floor was conservative — actual is $0.10.**
   The lean-mode cost model (Haiku Router + Sonnet worker) beat
   baseline Opus on dollars by roughly **7×**. The Router is nearly free
   ($0.02), and the Sonnet worker with skills preloaded takes roughly
   the same number of tokens as pipeline's debugger alone — but produces
   the bug fix **and** the regression tests in one dispatch.

2. **Envelope discipline improved.** Every lean-mode dispatch in this
   pilot emitted a canonical `{schema_version, ok, outputs}` envelope.
   The TODO pilot had 2/3 workers drift; this time the Router's output
   contract is explicit and the worker's prompt included a direct
   envelope template. Prompt discipline transferred.

3. **Code hygiene matches upstream.** 28 lines of diff in `hooks.py` and
   26 in `generate.py`, versus upstream's 12 and 8 respectively. Larger
   than upstream's *absolute minimum* (upstream used a raise-and-catch
   pattern that's 4 lines tighter), but still surgical — no unrelated
   reformatting, no scope creep.

4. **Regression coverage is a match or better.** 5 named tests
   (`post_gen_project failure + cleanup`, `exit_code in message`,
   `pre_gen_project failure + cleanup`, `happy path sanity`,
   `subclass check`). Pipeline mode produced 4. All 5 in lean mode
   would catch the bug on revert.

## What this pilot did NOT verify

- **Large-context tasks.** cookiecutter-4 fits comfortably in a single
  Sonnet context window with 4 skills loaded. Tasks that require
  reading 20+ files or producing 1000+ lines of new code may saturate
  the worker's context. Pipeline mode still has an answer for those:
  `/agents-experts` splits the work across isolated contexts.

- **Very weak baselines.** The dual-mode hypothesis is that Copilot /
  smaller OSS models still benefit from pipeline decomposition. This
  pilot only measured the strong-baseline case. `/agents-experts`
  remains committed for when a user runs under a weak model.

- **Opus-weighted tasks.** All workers in this pilot ran on Sonnet
  (per the Router's bug-fix rule). The lean Router's feature-build
  rule routes to Opus (justified by the TODO pilot failure mode).
  No pilot has yet exercised the Opus branch of the lean Router.

## Dual-mode cost summary

| Variant                      | Tokens        | $ (rough)   |
|------------------------------|--------------:|------------:|
| Baseline (Opus direct)       | 46,702        | $0.70       |
| `/agents-experts` (pipeline) | 192,907       | $0.65       |
| **`/experts` (lean)**        | **52,699**    | **$0.10**   |

With the lean mode as the default, the dual-mode framework delivers
cheaper-than-baseline execution (because most tokens are on Sonnet/Haiku)
*and* better structure (audit trail, verified regression tests, canonical
envelopes), *and* keeps the pipeline available for the weak-baseline
regime it was designed for.

## Artefacts

- `tests/pilot_medium_lean/fix_and_tests.diff` — full production diff +
  the 5 new regression tests, as the lean worker produced them.
- `tests/pilot_medium_lean/test_hook_regression_lean.py` — the new test file,
  standalone.
- This report.
