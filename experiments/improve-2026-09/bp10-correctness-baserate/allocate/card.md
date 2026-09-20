# Task: split an amount into parts

Build a Python module `split.py` with one function. No external dependencies.

- `split(n: int, k: int) -> list[int]` — divide the integer amount `n` into `k` parts that are **as even as
  possible**, and whose **sum is exactly `n`**. Return the `k` parts as a list. If `k < 1`, raise `ValueError`.

## Examples
- `split(10, 5)` → `[2, 2, 2, 2, 2]`.
- `split(42, 1)` → `[42]`.

Keep it clean and correct.
