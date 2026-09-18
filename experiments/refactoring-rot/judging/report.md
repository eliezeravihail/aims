# Blind design-trajectory review — order-pricing module (base -> 3 successive changes)

Sealed mapping (revealed after scoring): **X = plain, Y = aims-refactor**. Judged blind, on the module's own
PLAIN grain (bare int cents, plain functions, tuples). The question was regression/flat/improvement across
the sequence, not single-step correctness.

## Result
- **Neither rotted; neither imposed a foreign style.** Both kept the plain grain — no classes/value objects.
  So the consistency-over-dogma constraint held for both arms (an over-abstracting arm would have been a
  regression; neither was).
- **Y (aims) improved at every step.** Step 2: extracted a named `_allocate(total, weights)` — the single
  owner of the Σ==order_total conservation invariant — so `line_charges` is 3 lines. Step 3: `discount_breakdown`
  is the single named owner of the cap/precedence rule; `order_total` reads the granted amount from it; every
  function stays short. Named single-ownership per rule.
- **X (plain) stayed flat / denser.** Its step-2 largest-remainder allocation is a ~20-line **unnamed inline
  block** inside `line_charges` that was never extracted; step 3 centralizes the cap correctly but into a
  multi-job `_components` returning a 5-tuple consumed by a **magic index `[4]`**.
- **Verdict: aims > plain**, on clarity/altitude and named single-ownership — not correctness (both pass the
  16-check consistency oracle + all existing tests unchanged) and not grain-fit (both respected the plain
  style). Honest cost against aims: a minor redundant *computation* (the order discount is computed twice via
  a reentrant `order_total` call) — a real inefficiency, though the *rule* is still single-owned.

## Objective metric trajectory (rubric-free corroboration)
| step | aims sloc / max-func | plain sloc / max-func |
|---|---|---|
| base | 11 / 3 | 11 / 3 |
| 1 | 21 / 13 | 26 / 19 |
| 2 | 50 / 17 | 58 / 40 |
| 3 | 78 / 20 | 101 / 40 |

Plain grows larger and keeps a 40-line function from step 2 onward; aims stays smaller with a 20-line max —
the same divergence the blind judge read qualitatively.
