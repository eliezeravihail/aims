---
title: "architecture"
date: 2026-09-20
---
## Boundaries & seams
- **`CartLine`** — the value object that is the working currency: an immutable
  (sku, category, unit_price, qty) with a `total` = unit_price*qty. It is what
  crosses between the cart and the rules, so neither side traffics in raw tuples.
- **`Cart`** — owns the lines; hides its list, exposes a read-only `lines`
  snapshot (and iteration) plus `subtotal()`. Rules read the cart through this
  published surface only.
- **`Rule`** — the one seam over the rule-kind change axis. Abstract method
  `discount(cart) -> int`, plus the stacking policy (`priority`, `exclusive`) as
  keyword-only fields on the abstraction. The three concrete kinds (`PercentOff`,
  `AmountOffOver`, `BuyXGetY`) are peers under it, each owning its own matching
  predicate and its own arithmetic; none of them knows about combination.
- **`Engine`** — depends on the `Rule` abstraction, never on a concrete kind.
  `total` combines `rule.discount(cart)` polymorphically under the stacking policy
  (ascending `priority`, stable; an `exclusive` rule's nonzero discount stops the
  rest) and floors the result. Combination policy has one owner: `Engine.total`.

## Invariants
- All arithmetic is integer; discounts are non-negative by construction in every
  rule; `total(cart) == max(0, subtotal - accumulated discount)` and is never
  negative.
- `discount(cart)` is a pure query — it never mutates the cart — so rules may be
  *evaluated* in any order. Their *combination* follows the stacking policy:
  ascending `priority` (stable for ties), accumulate, and stop after an exclusive
  rule's nonzero discount. With all rules at the defaults (`priority=0`,
  `exclusive=False`) the combination is the order-free additive sum.

## Likely change axes
- **New rule kind** (spec-anticipated): add a `Rule` subclass; the engine is
  closed to it (Open/Closed). This axis drove the polymorphic seam — see
  `decisions/0001-rule-dispatch.md`.
- A rule needing cross-line aggregation is already supported: every rule receives
  the whole cart, not a single line.
- **Stacking policy** (priority + exclusivity) — absorbed at the combination seam
  in `Engine.total`; the rule kinds' discount math was untouched. See
  `decisions/0002-stacking-policy.md`.
