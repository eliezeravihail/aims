---
title: "BP5 — does the trajectory edge COMPOUND across a multi-break sequence? (the paper's central claim)"
date: 2026-09-20
status: pre-registered before any arm ran
---

# Question
BP1/BP2 had ONE model-breaking change (expiry), so the edge was one avoided reopen. The paper's core claim is
the edge GROWS with the sequence. BP5 uses a 4-stage money-ledger where EACH later stage breaks a naive
stored-aggregate model differently, so a stored-balance shortcut should reopen REPEATEDLY while a
posting-ledger (derive-from-immutable-events) design absorbs all as extensions.

# Product: an in-memory accounting ledger (`ledger.py`), 4 staged unforeseen changes
1. post/balance, single currency (integer cents, +/-).
2. multi-currency (per-currency balances) — breaks one-int-per-account.
3. as-of-time balances (postings timestamped; balance up to a time) — breaks a stored running total.
4. void a posting (undo its effect) — breaks an anonymous aggregate (needs posting identity).

The design that stores a running balance per account must REOPEN at 2, 3, and 4. The design that keeps an
immutable posting list and DERIVES balances absorbs 2-4 as pure extensions.

# Arms & measure (as BP1)
aims (add-feature + records, fresh session per stage) vs plain (build it well, fresh session per stage), same
cards + hidden tests, later stages fresh. Correctness gate (hidden pytest per stage) + reopened-owner count
per arm per stage + cost. 

# Pre-registered reading
- **Compounding shown** iff the plain arm's reopened-owner count ACCUMULATES across stages (e.g. 2-3 reopens)
  while aims stays at 0-1 — a widening gap, not a one-off.
- **Null** iff both stay tied (both derive from stage 1, or both reopen equally) — the edge does not compound
  even over a multi-break sequence (consistent with BP1-4: strong models pick the good model early).
n=1; suggestive; correctness must hold for both.
