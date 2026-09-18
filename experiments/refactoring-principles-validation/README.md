# Validation — does `refactoring-principles.md` lead to a correct adaptation?

The design pilot (`../principles-polish-vs-openspec/`) tested `design-principles.md` on **first-time
design**. This tests the new [`refactoring-principles.md`](../../skills/aims-guide/references/refactoring-principles.md)
on its own task: **adapting existing code to a new requirement**. Unlike the design pilots, this one runs on
**real code with a runnable oracle**, so the correctness reading is not a judge's opinion — it is a test
result.

## Setup

- **`base/`** — a small, working stage-1 module (`pricing.py` + `test_pricing.py`): market 1, a single order
  total (subtotal minus an order-level discount). Deliberately lean — the discount is computed once at the
  order total, with **no per-line allocation** (correct YAGNI at stage 1). This is the "existing code".
- **`change-card.md`** — the new requirement: a **second market** needs per-line reporting with tax on the
  **discounted** line amount, line finals summing exactly to the order total (an **allocation** nobody stated
  at stage 1), market 1 unchanged.
- **`hidden/oracle_test.py`** — never shown to an arm. Runs each arm's `pricing.py` against a battery: market-1
  preserved, `Σ line_finals == order_final`, largest-remainder allocation, and per-line tax on the
  **discounted** amount (the S4 trap — computing tax on the *undiscounted* line is the failure that put aims
  last in `../judging-rubric/regrade-results.md`).

## Arms (identical starting code, identical change)

| | **aims-refactor** | **plain** |
|---|---|---|
| Method | follows the shipped `/aims-refactor` + `refactoring-principles.md` as-is | no method — "adapt it, make it work well" |

Isolating the **method's** effect on the adaptation: same base code, same requirement, one variable.

## Reading

The primary reading is **rubric-free and runnable**: `python3 hidden/oracle_test.py arms/<arm>/` — how many
checks pass, and specifically whether the S4 (allocation / tax-on-discounted) is shipped correct. Secondary:
did the arm preserve market 1 (existing tests pass unchanged), keep the allocation to one owner, and separate
a refactor step from the change. `results.md` records both.
