---
title: "Stacking policy (priority + exclusivity) lives on the Rule abstraction and is honored only by Engine.total"
date: 2026-09-20
---
Context → Rules must now stack under a policy: they apply in ascending `priority`
order (stable for ties), and an `exclusive` rule that yields a nonzero discount is
applied and then stops every lower-priority (later) rule. Each rule constructor
gains two optional keyword arguments, defaulting to the prior additive behavior.

Decision → The stacking metadata (`priority: int = 0`, `exclusive: bool = False`)
is declared once on the `Rule` abstraction as keyword-only dataclass fields, so it
is part of what a rule *is* and the engine reads it off the abstraction — not off a
concrete kind. How rules combine under that policy is owned solely by
`Engine.total`: it sorts by `priority` (stable), accumulates each rule's discount,
and breaks after an exclusive rule whose discount is nonzero. The `max(0, ...)`
floor is unchanged. Per-rule `discount(cart)` math is untouched.

Consequences → This extends the combination step at its existing seam rather than
reopening any rule kind (the discount arithmetic of `PercentOff`/`AmountOffOver`/
`BuyXGetY` did not change). Combination policy keeps one owner (`Engine.total`),
matching ADR 0001's split — dispatch and now stacking both live in the engine,
rule math lives in each rule. `field(kw_only=True)` keeps each concrete kind's own
positional fields ahead of the inherited defaults, so the constructors stay
`Kind(pos_fields, *, priority=0, exclusive=False)`. With all rules at the defaults,
combination reduces exactly to the previous order-free sum (regression-verified).

Alternatives → (a) Adding `priority`/`exclusive` fields to each of the three
concrete dataclasses separately — rejected as duplication and because the engine
would then depend on incidental concrete fields rather than the `Rule` contract.
(b) A `StackPolicy` value object passed to constructors — rejected because the spec
fixes the interface as two optional keyword arguments, and priority/exclusive are
genuine primitives (an ordering key and a flag), not a crammed concept (§4/§9).
This decision does NOT supersede ADR 0001 (polymorphic dispatch is unchanged); it
adds the orthogonal combination-ordering concern.
