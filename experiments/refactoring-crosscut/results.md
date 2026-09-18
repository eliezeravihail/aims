# Results — cross-cutting capstone (multi-currency across a 4-module ledger)

**Run 2026-09-18.** The non-elementary case: a cross-cutting change (per-currency balances, a
same-currency-per-transaction rule, a group-by-currency report, backward compatibility) touching all four
modules of a double-entry ledger. `aims-refactor` vs `plain`, identical base.

## Correctness — parity
Both arms: `test_ledger.py` unchanged (4/4) **and** the 10-check oracle passes — per-currency balances,
mixed-currency rejection, group-by-currency never summed across, backward-compat `trial_balance`. **Neither
scattered currency checks; neither shipped the cross-currency wrong number.** Correctness parity holds even
at cross-cutting scale.

## Design — essentially a tie (blind review, `judging/report.md`)
`model` / `ledger` / `api` are **equivalent** — the load-bearing 75%. Both absorbed the one forced
representation change (`Account` int → per-currency dict) in one place, owned the same-currency rule solely
in `Ledger.post`, and **kept the plain grain** (currency as a bare string; neither imported a `Money` value
object — no over-abstraction). The only real difference is `report.py`, and it splits:
- **aims won DRY:** `trial_balance` derives from `trial_balance_by_currency` (grouping in one place); plain
  duplicated the summing expression (benign, non-divergent).
- **plain won coherence:** it made `statement` currency-aware; **aims left `statement` unchanged** — literal
  to "preserve out-of-scope" (the card never named it), but a latent incoherence on multi-currency data
  (lines span all currencies, balance is USD-only).

**Verdict: plain by a hair, close to a tie** — and it flips to aims if `statement` is judged out of scope.

## The lesson — a real §6 sharpening (this run earned a doc fix)
aims's one weakness was treating `statement` as §4 "out-of-scope, preserve" when it should have been a §6
"re-trace the interaction": `statement` now *reads the changed data shape*, so it is reached by the change
even though the card never named it. `refactoring-principles.md` §6 now says explicitly that **an existing
reader that runs on the change's new data shape is in scope to re-trace**, and to enumerate every function
that reads the changed shape and check it still reconciles. That is exactly the check that would have caught
aims's `statement` gap here — a generalizable fix, not a patch to one example.

## What the capstone establishes
On a genuinely non-elementary, cross-cutting change, a capable model — **with or without the method** —
produces a correct, coherent, on-grain result; the two are within a hair of each other. The method did not
lose (it won the DRY point and correctly declined to over-abstract), and its one miss produced a real,
generalizing improvement to the document. This is the honest ceiling of a single-session experiment: the
method's edge is structural and modest at this scale, and the correctness-forcing gap the historical S4
represents lives at a scale (many modules, many hands, long time) beyond what one session can stage.

## Re-run after the §6 fix — confirmed
Re-running the aims arm on the **same** change, now with §6 sharpened ("an existing reader that runs on the
change's new data shape is in scope to re-trace"), the arm **caught the exact gap it missed before**: it
re-traced `report.statement`, found it would list entries across all currencies while returning the
default-currency balance, and scoped it to one currency (`statement(ledger, account_id, currency="USD")`) —
lines and balance now always the same currency, backward-compat preserved. Existing tests unchanged + oracle
**10/10**. The one place aims lost is now handled; the doc fix does what it was written to do. (Arm output:
`arms/aims-refactor-rerun/`.)
