# Run 2 — pre-registered before the arm runs

## Why run 1 could not settle it
Run 1's new arm was given only **4** design-history items, **3** of which the code already carries.
It filed **1** entry. That thinness is partly my prompt, not the gate — the arm never held the material
behind the old companion's genuinely non-recoverable entries (the if-chain resolver, the `Decision`
enum, the value-object types, the unproven assumptions). Confounded on available material.

## What run 2 fixes
The arm gets the **full** design history — every item behind the old companion's 13 entries, the
recoverable and the non-recoverable alike, in one undifferentiated list, with no hint which is which.
Same code, same guidance, same instructions otherwise.

## The prediction, fixed now
Under the gate the arm should file **4–7 entries**, and specifically:

- **DROP** (the code or the tests already assert these — the blind judge rated the corresponding old
  entries RECOVERABLE with file:line): the precedence-has-one-home framing, order-independence,
  the `hash()`-is-salted rationale, the authority/abstention semantics, the bucket contract, the
  validate-at-construction rule, the frozenset copy. **7 items.**
- **KEEP**: the rejected if-chain resolver, the rejected `Decision` enum, the rejected value-object /
  exception types, the 100-vs-10_000 bucket counterfactual, the unproven assumptions (two `Percentage`
  rules on one flag; fractional percent; case-sensitive ids), and the dropped flag→rules index.
  **6 items.**

**The gate passes** if it drops most of the 7 and keeps most of the 6.
**The gate fails** — and is a regression — if it also drops the rejected alternatives or the unproven
assumptions. That is the failure mode the run-1 judge named: "Y has no Insights and no Decisions
sections at all… as documentation of this module it is radically incomplete."

Falsifiable either way. Recorded before the arm runs.
