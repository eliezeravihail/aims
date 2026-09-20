---
title: "goals"
date: 2026-09-20
---
## Insights
- The product is an **in-memory accounting ledger** exposed as a single module `ledger.py` with one
  class `Ledger`. Stage 1 is the seed of a product that compounds (later stages add capability on top
  of this same core), so the stage-1 shape is load-bearing for everything that follows.

## Decisions
- **Primary goal.** Let a caller *record postings* against named accounts and *ask an account's
  balance*. A posting is a money movement (`amount_cents`, an integer, may be negative). The balance of
  an account is the sum of that account's postings.
- **Core scenario.** `L = Ledger()`; `pid = L.post("cash", 500)` records a posting and returns a unique
  opaque id; `L.post("cash", -200)`; `L.balance("cash")` returns `300`; `L.balance("unknown")` returns
  `0`.
- **Product rules (from the stage-1 card).**
  - R1 — an account's balance equals the sum of its postings; an account with no postings has balance 0.
  - R2 — every `post` returns an id that is unique across the ledger and opaque (callers treat it as a
    handle and must not depend on its structure).
  - R3 — amounts and balances may be negative (no non-negativity constraint).

## Discussions
- **Out of scope for stage 1** (do not build now; later stages may introduce): persistence/durability,
  thread-safety/concurrency, double-entry balancing or validation across accounts, currencies/units
  beyond integer cents, deletion/reversal of a posting, statements/history queries, lookup of a posting
  by id. These are deliberately excluded — see the architecture record for why the stage-1 representation
  (an append-only journal of postings) is chosen so these can be added later without disturbing the core.
