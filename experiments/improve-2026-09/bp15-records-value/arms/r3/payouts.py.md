# payouts.py

## Insights

- The whole module exists to hold three properties that are cheap to break and expensive to notice: the sum
  is exact, the split is reproducible, and a paid settlement never changes. None of the three is visible as a
  test failure inside this file — each was found in production.
- `_allocate` is the **one owner** of how the total is divided and where the remainder lands. The temptation,
  every time a new deduction appears, is to adjust an amount *after* allocation ("just take the fee off the
  biggest row"). That second adjustment site is exactly how the penny drift came back the first time. New
  deductions belong **inside** the allocation, not after it.
- `sorted(shares)` at the top of `_allocate` is **not** cosmetic and not incidental — it is the reproducibility
  guarantee. It reads like tidy-up code. It is load-bearing.

## Decisions

- Remainder ties break by **payee_id ascending**, never by input order — `decisions/0001`.
- **Zero-amount payees are retained**, one row per payee always — `decisions/0002`.
- A repeat settlement **returns the stored result**; it never recomputes — `decisions/0003`.

## Discussions

- We considered making `Payout` carry the remainder or the raw weight for debuggability, and dropped it: the
  extra field would have to be kept in sync by every future deduction, and the debugging it bought was
  available from the inputs anyway.
- `weight_total <= 0` returns all-zero rows rather than raising. This was a close call. Raising is arguably
  more honest, but a settlement with no active payees is a normal end-of-month state upstream, and an
  exception there would page someone every month. Revisit only if a *negative* weight becomes possible — that
  case is currently unrepresented and would silently produce nonsense.
