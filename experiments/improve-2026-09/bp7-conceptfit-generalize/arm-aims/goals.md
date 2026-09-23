---
title: "goals"
date: 2026-09-20
---
## Primary goal
Compute the payable total of a shopping cart after promotional rules, entirely in
integer cents, correctly and without rounding drift. The engine holds a set of
rules of three kinds (percent-off-a-category, flat-amount-off-over-a-threshold,
buy-x-get-y-per-sku); their discounts add, and the final total is floored at 0.

## Use scenarios
- Build a cart line by line (`add_item`), read its `subtotal`.
- Construct rules, hand them to an `Engine`, and read `engine.total(cart)` — the
  subtotal minus every rule's combined discount, never below 0.
- Add a *new kind* of rule later (the spec flags this) without editing the engine.

## Non-goals
- Currency/locale handling, floats, or fractional cents — money is integer cents.
- Persistence, serialization, a rule registry/config loader, or I/O.
- Input validation beyond the stated behavior (unknown category/sku contribute 0;
  no precondition contract on qty/price signs is specified, so none is invented).
