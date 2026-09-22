---
title: "BP15 — does the record layer help? Doubt-laden decisions, a blind modifier, records vs no records"
date: 2026-09-22
status: pre-registered before any arm ran
---

# The question (aims' unproven frontier)

aims' second core claim is the **co-located record layer**: durable design knowledge kept next to the code.
The earlier attempt (I5) was confounded — the code itself carried a visible precedent, so the no-record arm
reconstructed the decision from the code and the record changed nothing.

This run fixes that confound by construction: every documented decision is one whose **rationale is not
recoverable from the code**, and whose wrong alternative is the one a careful reader would naturally pick.

# The product and its documented doubts

`payouts.py` splits a total across payees. Three genuinely ambiguous decisions are documented, each with the
doubt, the choice, and the rejected alternative:

- **0001 — remainder tie-break is `payee_id` ascending**, not input order. `sorted(shares)` reads like
  incidental tidy-up; it is the reproducibility guarantee. Input order is the natural (and wrong) reading.
- **0002 — zero-amount payees are retained** (one row per payee, always). Filtering them looks cleaner and
  nothing in the file notices; the cost is entirely downstream.
- **0003 — a repeat settlement returns the stored result and never recomputes.** Recomputing "from the
  inputs" feels safer and is wrong: it would silently contradict money already paid.

None of the three rationales is inferable from the code. All three are load-bearing.

# The change (identical for both arms)

Add a **platform fee** (deducted before the split, emitted as a `"platform"` row, sum still exact) and a
**`settle_preview`** that computes without recording. This change tempts every documented trap: re-deriving
the allocation (tie-break), pushing a payee to zero (row dropping), and building preview out of the paying
path (idempotency/store).

# Arms (both blind to this plan, to the experiment, and to aims)

- **R (records):** 3 independent agents, each given `payouts.py` **plus** the co-located records
  (goals / architecture / decisions 0001-0003 / the companion).
- **N (no records):** 3 independent agents, each given **only** `payouts.py`.
Same change request, no hints, no mention of a method or a comparison.

# Metrics (fixed before the run)

1. **Decision survival (primary).** A scoring-only probe suite — never shown to any arm — checks each
   documented decision independently after the change: D1 tie-break by id (and reproducibility across input
   order), D2 row-per-payee retained, D3 repeat-settle returns the stored result, plus the sum invariant.
   Score = decisions surviving / 4, per arm-run. **This is the record layer's value, if it has one.**
2. **Design quality (§0-§14), blind.** The modified modules scored from the code against the design rubric,
   blind to arm — the correct design measure (`decisions/0021`).

Tests are **not** the measure: the probes exist to detect whether a *documented decision* was silently
reversed, which no ordinary test of the change would catch.

# Pre-registered prediction

If the record layer works, R survives more decisions than N — the traps are invisible in the code, so N must
either guess right or break them. If R == N, the records are not what carries the knowledge (and the honest
reading is that a careful modifier re-derives or preserves by caution). n=3 per arm; a rate, not a proof.
Nulls recorded as nulls.
