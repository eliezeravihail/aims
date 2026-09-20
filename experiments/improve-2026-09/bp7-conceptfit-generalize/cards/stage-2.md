# Task: promotional pricing engine (stage 2 — stacking policy)

Extend the existing `promo.py` (from stage 1) to support a **stacking policy** on rules. Keep all stage-1
behavior working unchanged. All money stays in integer cents.

## New requirements

Every rule constructor now also accepts two optional keyword arguments (default to the stage-1 behavior):
- `priority: int = 0` — rules are applied in **ascending** priority order (lower number first).
- `exclusive: bool = False` — when an **exclusive** rule produces a **nonzero** discount, it is applied and
  then **no lower-priority rule** (any rule later in the sorted order) is applied at all.

So `Engine.total(cart)` must now:
1. Sort the rules by ascending `priority` (stable for equal priorities).
2. Walk them in that order, accumulating each rule's discount against the subtotal.
3. If a rule is `exclusive` and its discount is nonzero, apply that discount and then **stop** (skip every
   remaining rule).
4. Return `max(0, subtotal - accumulated_discount)`.

## Clarifications
- An exclusive rule whose discount is **0** does **not** stop anything — processing continues.
- With all rules at default `priority=0, exclusive=False`, behavior is identical to stage 1 (additive).
- The three rule kinds (`PercentOff`, `AmountOffOver`, `BuyXGetY`) and the `Cart` API are unchanged except
  for accepting the two new optional kwargs.

The hidden test suite imports the same names as stage 1, now constructing rules with `priority=` and
`exclusive=`.
