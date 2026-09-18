"""Hidden oracle for task2-eval. Never shown to an arm.
Usage: python3 oracle.py <arm-dir-with-calc.py>
Checks existing behavior preserved AND the new exponentiation semantics
(tighter than * /, right-associative, parens override)."""
import sys, importlib, pathlib

arm = pathlib.Path(sys.argv[1]).resolve()
sys.path.insert(0, str(arm))
c = importlib.import_module("calc")

cases = [
    # preserved behavior
    ("2 + 3 * 4", 14), ("(2 + 3) * 4", 20), ("10 - 3 - 2", 5), ("7 / 2", 3), ("2 + 3", 5),
    # exponentiation
    ("2 ^ 3", 8),
    ("2 * 3 ^ 2", 18),        # ^ tighter than *
    ("2 ^ 3 * 2", 16),        # (2^3)*2
    ("2 ^ 2 ^ 3", 256),       # right-associative
    ("(2 ^ 2) ^ 3", 64),      # parens override
    ("2 + 3 ^ 2", 11),        # ^ tighter than +
    ("12 / 2 ^ 2", 3),        # ^ tighter than /
]
results = []
for expr, want in cases:
    try:
        got = c.evaluate(expr)
        results.append((expr, got == want, f"got {got}, want {want}"))
    except Exception as e:
        results.append((expr, False, f"exception: {e!r}"))

passed = sum(1 for _, ok, _ in results if ok)
print(f"ORACLE eval [{arm.name}]: {passed}/{len(results)} passed")
for expr, ok, detail in results:
    print(f"  [{'PASS' if ok else 'FAIL'}] {expr!r}" + (f"  -- {detail}" if not ok else ""))
sys.exit(0 if passed == len(results) else 1)
