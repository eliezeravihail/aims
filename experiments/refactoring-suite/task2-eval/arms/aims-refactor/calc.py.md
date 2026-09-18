---
title: calc.py
date: 2026-09-18
hash: "sha256:7a31df875a25809d51eb943526e5a6312db2023a38f533d262fc302024e9b972"
---

# calc.py

## Insights

- The precedence/associativity of the evaluator is not data; it is encoded in the **shape of the
  recursive-descent method chain**. Precedence = who delegates to whom (`expr` → `term` → `power` →
  `factor`); associativity = whether a rung loops (left) or recurses into itself (right). To read or
  change a binding rule, read the corresponding method, not a table.
- `power()` is a transparent pass-through to `factor()` whenever no `^` follows, which is what makes the
  `^` adaptation preserve every `^`-free expression bit-for-bit.

## Decisions

- 2026-09-18 — **`^` (exponentiation) is owned by the `power()` rung, inserted between `term` and
  `factor`.** Its precedence (tighter than `*`/`/`, looser than atoms/parens) is owned by its position in
  the delegation chain: `term` delegates to `power`, `power` delegates to `factor`. Its
  right-associativity is owned by `power()` recursing into `power()` for the exponent (not into `factor`),
  so the tail binds as one exponent (`2 ^ 2 ^ 3 == 2 ^ (2 ^ 3)`). Parentheses override via `factor`'s
  existing `'(' expr ')'` case — no special-casing. Tokenizer change is limited to admitting `^` as an
  operator token; no other rung was reopened, so `+ - * /` and parentheses behave exactly as before.
  Result stays a non-negative integer (`int ** non-negative int` is `int`).

## Discussions

- Considered writing `power()` as a left-associative while-loop like `expr`/`term`, then reversing — but
  the requirement is genuinely right-associative, and right-recursion expresses that directly with no
  accumulator. The while-loop shape would have been the wrong concept for the rule (refactoring-principles
  §9), so `^` gets the recursion shape rather than being crammed into the loop shape its siblings use.
- No behavior-preserving refactor step was needed before the change (refactoring-principles §0): the
  method chain already is the seam, so `^` lands as a new sibling rung. Reshaping was insertion, not a
  rewrite of any existing rung.
