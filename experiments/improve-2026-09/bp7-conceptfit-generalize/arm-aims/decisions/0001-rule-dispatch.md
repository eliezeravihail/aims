---
title: "Engine dispatches over rule kinds by polymorphism, not a type switch"
date: 2026-09-20
---
Context → `Engine.total` must apply three different rule kinds (`PercentOff`,
`AmountOffOver`, `BuyXGetY`), and the spec states a new kind may be added later.

Decision → Every rule is a `Rule` with one abstract method `discount(cart) -> int`.
The engine sums `rule.discount(cart)` across its rules without knowing any kind.
Each rule owns its own matching predicate and arithmetic; the engine owns only the
summation and the `max(0, subtotal - discount)` floor.

Consequences → A new rule kind is a new `Rule` subclass; the engine is closed to
it (Open/Closed, §7). One owner per rule (§5): the discount math for a kind lives
only in that kind. The engine has no `isinstance`/type-code branch to grow.

Alternatives → Chose polymorphic dispatch over an `isinstance`/type-code switch
inside `Engine.total` (the naive framing). The switch is a type-code smell (§8),
would force reopening the engine — a second owner — for every new rule kind,
and violates Open/Closed. Rejected. Also chose to pass each rule the whole `Cart`
(read through its published `lines`/`subtotal` surface) rather than pre-filtered
lines, so a rule that needs cart-wide or cross-line data (AmountOffOver needs the
subtotal) is served by the same seam.
