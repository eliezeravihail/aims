---
title: "0007 — Non-stackable promotions and arbitration"
date: 2026-09-16
---

## Status
Accepted (stage-2 design, final round). The core rule is grounded by cases B3–B5; the three refinements
(grouping, kind/scope, superseded metadata) were confirmed by the owner and are folded in below —
nothing open.

## Context
A promotion definition may now be marked **non-stackable**. When two non-stackable promotions both
qualify on one cart, the one that gives the customer the larger discount is applied and the other is
not; the loser must still appear, marked not applied, naming the code that superseded it (support: "your
code was valid but the other saved you more"). A tie is broken in favour of the code entered first.
Cases: B3 TENOFF −10.00 beats SAVE10 −5.00; B4 SAVE10 −15.00 beats TENOFF −10.00; B5 a −10.00 tie →
SAVE10 (entered first).

## Decision
- **`stackable` is a declarative attribute of a promotion** (from the definitions file, optional, default
  `true`), read by the engine to *select*, exactly as `scope` is read to *order*. It adds no per-kind
  branching: the engine reads the discount amount each promotion already computes.
- **One flat rule, no groups (owner).** Non-stackable means only "cannot sit next to another
  non-stackable." There are no named exclusion groups. At most one non-stackable promotion applies per
  cart. Non-stackable conflicts only with other non-stackable; stackable codes always stack. Applied set
  = every qualifying stackable promotion + at most one non-stackable winner.
- **Arbitration is kind- and scope-agnostic (owner: "the bigger one wins, it doesn't matter what
  kind").** Among the **qualifying** non-stackable promotions (discount > 0), keep the one with the
  **largest discount amount**; ties broken by **first-occurrence entry order**. The engine compares each
  candidate's discount amount — from the `DiscountResult` the promotion already returns — so it needs
  neither the kind nor the scope to arbitrate. A non-stackable BOGO (LINE) and a non-stackable PCT/AMT
  (CART) compete on the raw amount. Comparison base: the cart with all **stackable** promotions applied
  and no non-stackable applied (a `LINE` candidate against the current line amounts, a `CART` candidate
  against that subtotal) — a single, well-defined, order-independent base. The winner joins the applied
  set at its own scope/stage; every other qualifying non-stackable becomes **`SUPERSEDED`**. A
  non-stackable code that does not qualify is `INAPPLICABLE` (it lost to nothing), not superseded.
- **`SUPERSEDED` is a new `CodeOutcome`** with `superseded_by` (the winning code) and — owner-confirmed —
  `forgone_discount`, **what the beaten code would have saved** ("that's the sentence support reads to the
  customer"). Distinct from `INAPPLICABLE` ("your code doesn't apply here") because support must
  distinguish "valid, but another saved you more". In the explanation, a superseded adjustment carries
  delta ZERO (ADR 0006) but keeps `would_be_delta`, so exactness (INV-7) holds.
- Selection lives in the engine (its territory: which codes apply, in what order); per-kind discount math
  stays in the promotion. Because a non-stackable winner may be line-scoped, arbitration is its own engine
  step (after stackable line promotions establish the base, before the winner is committed to its stage),
  not a filter inside the cart stage.

## Consequences
- `promotions.py` gains a `stackable` attribute on `Promotion`; `catalog.py` parses the flag (non-boolean
  → `PromotionDefinitionError` at load); `pricing.py` gains the arbitration step and the SUPERSEDED
  classification; `result.py` gains `CodeOutcome.SUPERSEDED` + `CodeReport.superseded_by` +
  `CodeReport.forgone_discount` + `Adjustment.would_be_delta`.
- The winner is arbitrated on the stackable-only base but its *recorded* delta is what it removes at its
  stage; these coincide whenever the winner is the only discount at its stage (every acceptance case).
- Cross-scope arbitration has no acceptance case, so it must carry its own test (see `design/stage-2.md`
  §11: a non-stackable BOGO vs a non-stackable AMT, bigger amount wins).

## Alternatives rejected
- **Non-stackable suppresses stackable codes too** — contradicts "two *non-stackable* promotions"; the
  conflict is between non-stackable codes only (owner: "only means it can't sit next to another
  non-stackable one").
- **Report the loser as INAPPLICABLE** — loses the "valid but superseded" distinction support needs; a
  dedicated `SUPERSEDED` outcome (one new handling → one new type, §7) is warranted.
- **Named groups** — the owner ruled it out: "one rule: two of them can't sit together. Nothing more
  elaborate." One global set, no group id.
- **Scope-restricted arbitration** (only cart codes can be non-stackable) — the owner ruled it out: "it
  doesn't matter what kind they are." Arbitration compares amounts across scopes.
