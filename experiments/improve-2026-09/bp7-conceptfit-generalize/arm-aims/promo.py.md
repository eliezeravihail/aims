---
title: "promo.py"
date: 2026-09-20
hash: "sha256:fa26f39070ef42ddf4cda6b640ba3d652537f56ee214544cd81c7533971a4ad0"
---
## Insights
- Every computation stays in integer cents; `PercentOff` floors with
  `base * percent // 100` (verified: base 149, 10% -> 14). No float ever enters,
  so there is no rounding drift to reason about.
- `discount(cart)` is a pure query on every rule, so `Engine.total` may *evaluate*
  the rules independently and re-running the engine leaves the cart unchanged
  (verified). The *combination* is no longer a plain sum: since stacking, the
  engine walks rules in ascending `priority` (stable for ties) and an `exclusive`
  rule's nonzero discount stops the rest — so combination order is significant even
  though each rule's own evaluation is not (verified).
- Stacking metadata (`priority`, `exclusive`) is declared once on the `Rule`
  abstraction as keyword-only fields (`field(kw_only=True)`), so each concrete
  kind's positional fields are unaffected and the engine reads the policy off the
  abstraction, not off a concrete class. Defaults (`0` / `False`) reproduce the
  pre-stacking additive behavior exactly (verified: all-default stack == old sum,
  order-independent).

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
- SUPERSEDES the earlier "apply in any order and simply sum" combination: since
  stacking, `Engine.total` walks rules in ascending `priority` (stable sort),
  accumulates each discount, and breaks after an `exclusive` rule that produced a
  nonzero discount (a zero-discount exclusive does not break). The floor is
  unchanged. Combination policy has one owner (`Engine.total`); per-rule discount
  math was untouched. See `decisions/0002-stacking-policy.md`.
- Stacking attributes are plain `int` (`priority`) and `bool` (`exclusive`) fields,
  not a bundled `StackPolicy` value object: the spec fixes the interface as two
  optional keyword arguments per constructor, and both are genuine primitive policy
  attributes (an ordering key, a flag) — no concept-cram (§4/§9).

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
