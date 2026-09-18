# Results — refactoring-principles.md validation (round 1)

**Run 2026-09-18.** Two arms adapted the **identical** stage-1 `pricing.py` to the same new requirement:
`aims-refactor` (followed `refactoring-principles.md` as-is) vs `plain` (no method). Primary reading is the
runnable hidden oracle (`hidden/oracle_test.py`), not a judge.

## The runnable reading (rubric-free)

| Arm | Oracle | Market-1 tests unchanged | Cost |
|---|---|---|---|
| **aims-refactor** | **15/15 pass** | pass unchanged | ~88k tokens, 15 tool-calls |
| **plain** | **15/15 pass** | pass unchanged | ~46k tokens, 6 tool-calls |

**Both arms shipped a correct adaptation** — the discount→line allocation (`Σ line_finals == order_final`,
largest-remainder), per-line tax on the **discounted** amount (not the S4's undiscounted line), half-even
rounding, and market 1 preserved bit-for-bit. No correctness gap between them.

## What this does and does not show

- **It confirms `refactoring-principles.md` produces a correct, disciplined adaptation.** The aims-refactor
  arm's transcript shows it doing exactly what the document asks: characterize market 1 across its input
  space first (§1), preserve it unedited (§4), *not* manufacture a needless refactor because the seam
  (`order_total`) already existed (§0), model the allocation as a decomposition with a single owner (§5/§9),
  and re-trace the X×R interactions (§6). That is the method firing as designed.
- **It does NOT reproduce the historical S4**, and the honest reason is a flaw in this round's change card:
  **it over-specified the trap.** The card explicitly said "allocate the order-level discount to the lines,"
  "tax on the discounted amount," and "line finals must sum to order_final." The real S4
  (`../judging-rubric/regrade-results.md`) was insidious precisely because **no stated requirement mentioned
  allocation** — a correct adaptation had to *discover*, from the per-line-tax requirement, that the discount
  must flow down to the lines. Handed the spelled-out invariant, a capable agent simply implements it — so
  the plain arm passes too, and the card cannot discriminate.
- **Cost signal:** the aims arm paid ~2× the tokens to reach the same runnable outcome, spent on the explicit
  characterize/preserve/re-trace passes the plain arm did implicitly. On a small, clearly-specified change
  that is overhead; its value shows on changes that are large, subtle, or under-specified.

## What a faithful reproduction needs (round 2, if run)

State only the *requirement*, never the *mechanism*: "the second market shows a per-line breakdown of what
the customer is charged and its tax, and the per-line charges must add up to the order's total charge" — with
**no mention of allocation or of taxing the discounted amount**. The correct realization must then *derive*
that the order-level discount has to be pushed into the per-line charges (else `Σ charges = subtotal ≠ order
total`) and that tax therefore lands on the discounted amount. That is the §6 "re-trace the interaction the
change implies" discovery the S4 tests. An oracle can still grade it (the `Σ parts == whole` invariant is
inherent to "a breakdown of a charge," not an added instruction).

**Caveat, stated honestly:** even a loose card may not reliably reproduce the S4 with a capable modern arm on
a module this small — the original failure was a *design* that cut the allocation primitive as "speculative"
and never restored it. The correctness gap between method and no-method is small on small, clear tasks; the
method's demonstrated value is disciplinary (preserve out-of-scope, one owner, records, discovery) and shows
most on large or under-specified change — consistent with the design pilots, where aims' edge was structural,
not raw correctness against a careful competitor.
