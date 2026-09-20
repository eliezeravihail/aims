# Task: a layered access-control evaluator

Build a Python module `access.py`. No external dependencies.

## Model

A rule is a pair `(scope, effect)`:
- `scope` is a `/`-segmented path prefix, e.g. `"a/b"`. The empty string `""` is the **root** scope and
  matches every path. A scope matches a path when it equals the path or is a segment-boundary prefix of it
  (`"a/b"` matches `"a/b"` and `"a/b/c"`, but **not** `"a/bc"`).
- `effect` is either `"ALLOW"` or `"DENY"`.

## API (contractual)

- `AccessControl(rules)` — `rules` is a list of `(scope, effect)` pairs.
- `evaluate(path: str) -> str` — return `"ALLOW"` or `"DENY"` for `path`, by these rules:
  1. Consider only rules whose scope **matches** `path`.
  2. Among those, the **most specific** rule decides — most specific = the **longest** matching scope (by
     number of path segments; the root `""` is the least specific).
  3. If **several** rules tie at that most-specific scope, **`DENY` wins**.
  4. If **no** rule matches, the result is **`DENY`** (default deny).

## Examples
- `[("a", "ALLOW")]`, path `"a/b/c"` → `"ALLOW"`.
- `[("a", "DENY")]`, path `"a/b/c"` → `"DENY"`.
- `[("a", "ALLOW"), ("a/b", "DENY")]`, path `"a/b/c"` → `"DENY"` (the more specific `a/b` DENY decides).
- `[]`, path `"a"` → `"DENY"`.

Keep it clean and correct.
