# Change request — add exponentiation to the evaluator

You are handed an existing, working arithmetic evaluator (`calc.py` + `test_calc.py`).

Add an **exponentiation** operator `^`:

- `2 ^ 3` evaluates to `8`.
- Exponentiation **binds tighter than** `*` and `/` (so `2 * 3 ^ 2` is `2 * (3 ^ 2)` = `18`).
- Exponentiation is **right-associative** (so `2 ^ 2 ^ 3` is `2 ^ (2 ^ 3)` = `256`).
- Parentheses still override (so `(2 ^ 2) ^ 3` = `64`).

Everything the evaluator does today must keep working **exactly** — the existing `test_calc.py` must pass
**unchanged**. Numbers stay non-negative integers.

Deliver the adapted `calc.py` (and any tests you add). Do not edit `test_calc.py`.
