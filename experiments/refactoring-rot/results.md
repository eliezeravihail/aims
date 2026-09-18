# Results — rot sequence (design quality across 3 successive adaptations)

**Run 2026-09-18.** The first experiment here to measure what the user pressed for: not whether one change
runs correctly, but whether the **design stays clean across a sequence** of successive changes — a
**before/after review on the target's own grain** (`decisions/0016`). Two arms — `aims-refactor` (the
shipped method) and `plain` (no method) — each evolved the **same** plain-style `checkout.py` through the
same three interacting changes (order discount → per-line tax/allocation → capped loyalty), **with no
lookahead** to later steps.

## Correctness — parity (no regression in either)
Both arms, at every step, kept the existing tests passing **unchanged** and passed the 16-check consistency
oracle at step 3 (preservation, `Σ line_finals == order_total`, cap monotonicity, breakdown consistency).
Neither shipped a wrong number. Correctness did not discriminate — as on every prior task.

## Design trajectory — this is where they diverged
Blind trajectory judge (`judging/report.md`, sealed X=plain / Y=aims) + objective metrics:

| step | aims sloc / max-func | plain sloc / max-func |
|---|---|---|
| 1 | 21 / 13 | 26 / 19 |
| 2 | 50 / 17 | 58 / 40 |
| 3 | 78 / 20 | **101 / 40** |

- **Neither rotted, and — importantly — neither imposed a foreign style.** Both kept the plain grain (0
  classes, bare-int, plain functions). The consistency-over-dogma constraint held: an arm that wrapped the
  bare-int code in value objects would have *regressed* (inconsistency); neither did.
- **aims improved at every step** — a named `_allocate` owner for the Σ==whole invariant at step 2, a named
  `discount_breakdown` owner for the cap/precedence at step 3, functions staying short (max 20 lines).
- **plain stayed flat / denser** — a ~20-line **unnamed inline allocation** never extracted, and a step-3
  5-tuple `_components` read by a **magic index `[4]`**; 101 sloc with a 40-line function carried since step 2.
- **Verdict: aims > plain** on the plain grain — clarity and named single-ownership, an upward vs a flat
  trajectory. Honest cost against aims, cited by the judge: a redundant *computation* (order discount computed
  twice via a reentrant call) — an inefficiency, though the *rule* stays single-owned.

## What this establishes (and its limits)
- Under the **right measurement** (before/after design review across a sequence, on the target's grain), the
  method shows a **real design advantage** that single-change correctness oracles cannot see — the first such
  positive discrimination in this repo's refactoring experiments. And it does so **without** the failure mode
  the consistency principle guards against (no over-abstraction).
- **Still a small module.** The gap is "cleaner / better-named / shorter functions", not "correct vs buggy".
  On code a strong model holds in its head at once, rot does not force a *correctness* break — plain stays
  correct, just denser. The user's standing hypothesis — that the correctness-forcing case needs a
  **non-elementary codebase and a non-elementary, cross-cutting change** at a scale the model cannot hold at
  once — is not yet tested here and is the next experiment.
