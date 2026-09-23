# Product card — discount-code applicability engine (design only)

Design the architecture (types + interfaces + correctness handling) for a **discount-code applicability
engine**: given a shopping cart and a discount code, decide whether the code **applies**. Design only — no
implementation.

## Rules (R)
- **R1** A code carries **conditions**; the code applies iff its conditions hold for the cart.
- **R2** The starter condition kinds are: `min_subtotal(amount)`, `category_present(cat)`,
  `first_order` (the customer has no prior orders).
- **R3** A code that applies to no line and no cart fact is **reported as not-applicable with a reason**,
  never a silent false.
- **R4** Evaluation is **order-independent** — the same cart and code give the same verdict regardless of
  the order conditions are listed.

## Change-axes (X) — the ways this is expected to vary
- **X1** A code may require a **combination** of conditions — not just "all of them": some codes apply when
  **any** of a set holds, some require **all**, and some **exclude** a case (a "not"). The three combine
  (e.g. "electronics AND (first-order OR min-subtotal ≥ 100) AND NOT gift-card-in-cart").
- **X2** New condition **kinds** may be added (e.g. `weekday`, `member_tier`).
- **X3** A code may carry a **priority** so that when several apply, one is chosen deterministically.

## Acceptance (C) — visible examples
- **C1** code needs `min_subtotal(50)`; cart subtotal $60 → applies.
- **C2** code needs `category_present(books)`; cart has only electronics → not-applicable, reason
  "no books in cart".

Produce the design: the domain types (what a condition, a code, a verdict are), the operations and their
contracts, and how R1–R4 crossed with X1–X3 are handled across the full input space. Then run the method's
mandatory self-review and deliver the final design.
