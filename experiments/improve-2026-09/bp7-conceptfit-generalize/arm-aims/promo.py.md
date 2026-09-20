---
title: "promo.py"
date: 2026-09-20
hash: "sha256:bf134f2f1d12bec45b2243724ab2d6a8ce26d8d653de06b56fd47e6596a27521"
---
## Insights
- Every computation stays in integer cents; `PercentOff` floors with
  `base * percent // 100` (verified: base 149, 10% -> 14). No float ever enters,
  so there is no rounding drift to reason about.
- `discount(cart)` is a pure query on every rule, so `Engine.total` may apply the
  rules in any order and simply sum them; re-running the engine leaves the cart
  unchanged (verified).

## Decisions
- `Engine.total` dispatches over rule kinds polymorphically via `Rule.discount`,
  not a type switch — see `decisions/0001-rule-dispatch.md` (the owning ADR).
- `CartLine` is a frozen value object (concept fit, §4): a cart line is its own
  kind, not a tuple/dict, and carries `total = unit_price * qty`.
- `Cart` hides its line list and exposes a read-only `lines` snapshot + iteration
  + `subtotal()`; each rule filters lines by its own key. Matching a category/sku
  lives in the rule that owns it (§5 one owner), not in `Cart`.
- `Cart` is the one mutable object (add_item appends); `CartLine`, all three
  rules, and `Engine` are frozen — immutability is the default, mutation the
  localized exception (§4).
- `AmountOffOver` uses `>=` (threshold inclusive); the total is floored with
  `max(0, subtotal - discount)` so a stack of rules can never yield negative money
  (verified: two 80-off rules on a 100 cart -> 0).

## Discussions
- `BuyXGetY.discount` divides by `group = x + y`; a rule with `x + y == 0` would
  raise ZeroDivisionError. That is degenerate misuse (a buy-x-get-y with no units
  in a group has no meaning) and the spec states no such case, so no guard was
  added — the core trusts its constructed inputs. Recorded as an unproven-but-safe
  assumption, not enforced.
- Considered a `Protocol` instead of an `abc.ABC` for `Rule`; chose the ABC so the
  three kinds are an explicit, named family (one abstraction level per family) and
  a missing `discount` fails loudly at construction.
- Considered giving each rule only its pre-filtered lines; rejected because
  `AmountOffOver` needs the whole-cart subtotal, so passing the `Cart` keeps one
  uniform seam for all kinds (see the ADR).
