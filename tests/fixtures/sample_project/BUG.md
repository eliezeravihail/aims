# Bug report — src/calc.add

## Symptom
`add("3", 4)` raises `TypeError`. `add("3", "4")` returns `"34"` instead of `7`.

## Expected
Both calls should return `7`. Inputs that look numeric should be coerced.

## Test gap
`tests/test_calc.py` only covers `int + int` — no coverage for numeric strings.
