---
title: "BP6 result — the shortcut base rate: 1 of 6 plain builds STORED the aggregate (≈17%)"
date: 2026-09-20
---

# BP6 — how often does a plain builder take the shortcut aims' review rejects?

BP1–BP3 pinned aims' trajectory edge to **variance reduction on one stage-1 choice**: aims' §5
one-owner / derive-don't-store review *reliably* derives availability from the reservation ledger, while a
capable plain builder derives it *only sometimes* — and pays a reopen when it stored instead. That makes the
per-product edge **probabilistic**, proportional to *how often a plain builder would take the stored-aggregate
shortcut*. BP6 measures that base rate directly: **6 independent plain builds** (haiku, no method) of the
identical BP1 stage-1 inventory card, classified STORE vs DERIVE on the one axis that matters — whether
`available` reads a **maintained running aggregate** (`_reserved`/`_available` counter kept in sync) or
**derives** it from ground facts on demand.

## The tally — 1 of 6 stored (≈17%)

| run | `available(sku)` computes… | ground state held | class |
|---|---|---|---|
| run-1 | `_stock[sku] − Σ(qty in _reservations for sku)` | `_stock`, `_reservations{id→(sku,qty)}` | **DERIVE** |
| run-2 | `_stock.get(sku,0) − Σ(qty …)` | `_stock`, `_reservations{id→(sku,qty)}` | **DERIVE** |
| run-3 | `_stock[sku] − Σ(qty …)` | `_stock`, `_reservations{id→(sku,qty)}` | **DERIVE** |
| run-4 | `_stock[sku] − Σ(qty …)` | `_stock`, `_reservations{id→(sku,qty)}` | **DERIVE** |
| **run-5** | `_stock[sku] − _reserved.get(sku,0)` | `_stock`, **`_reserved{sku→int}`** *and* `_reservations` | **STORE** |
| run-6 | `_stock[sku] − Σ(qty …)` | `_stock`, `_reservations{id→(sku,qty)}` | **DERIVE** |

**Store fraction = 1/6 ≈ 0.17** (95% CI by Wilson ≈ 3%–56%, n=6 — wide; this is an estimate, not a point).

run-5 is the textbook shortcut aims' review names: it keeps a per-SKU `_reserved` running total **in addition
to** the `_reservations` ledger, incrementing/decrementing it in `reserve`/`release` — a **second copy of the
reservation aggregate** held in sync by matched arithmetic. It passes stage 1 cleanly (the two copies agree),
which is exactly why a plain builder ships it. It is also precisely the design that BP1's plain arm reopened
when time-dependent expiry arrived: a maintained `_reserved` total **cannot** express "count a hold only while
`expiry is None or expiry > now`" without reopening the aggregate, because expiry depends on the query-time
`now`, not on the reserve/release events that update the counter.

## What this quantifies (and its honest limits)

- **This is aims' expected per-product trajectory edge on this axis** — the fraction of products where a plain
  builder would take the shortcut and later pay the reopen aims avoids. On this card, model, and n, that is
  **≈1 in 6**. On the other ~5 in 6, the plain builder already derives and aims' one-owner review changes
  nothing about the trajectory (it still buys records + the review's assurance, at the ~1.85× premium — but
  not a reopen it wouldn't otherwise pay). This is the mechanism behind BP5's *both-arms-derived* null: BP5
  drew from the ~83% where the shortcut isn't taken.
- **Limits, stated plainly.** n=6, **one** product, **one** model (haiku), **one** stage-1 card. The CI is
  wide (≈3–56%); the point estimate is soft. The rate is card-specific: a card that *names* a "reserved
  count" field, or a stickier shortcut, would raise it; a card that makes derivation obvious would lower it.
  What BP6 establishes is not a universal constant but the **shape** of aims' edge: it is a *reliability
  premium on a minority of products*, not a per-build win — and its size is the shortcut base rate, which is
  low for a capable model on a clean card.

**Verdict:** the trajectory edge is real but **rare per product** on this axis (~1/6 here), because a capable
plain builder usually derives on its own. aims' value is converting that *sometimes* into an *always* — worth
most where the shortcut rate is high (weaker builders, cards that bait a stored counter, longer sequences
where one early store compounds) and near-zero where a plain builder already derives. Consistent with BP1–BP5
across the board.
