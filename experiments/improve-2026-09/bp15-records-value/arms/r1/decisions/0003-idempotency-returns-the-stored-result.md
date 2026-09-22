# 0003 — a repeat settlement returns the stored result; it never recomputes

- Status: accepted

## The doubt

`Settlements.settle` is keyed by `settlement_id`. When the same id arrives again, should we (a) return what
we paid, or (b) recompute from the arguments we were just given and return that? Option (b) feels safer —
"the inputs are the truth" — and it is what a careful reader expects.

## Decision

**Return the stored result, unchanged, and ignore the arguments entirely** on a repeat call. We do not
recompute, and we do not compare.

## Rejected alternatives (and why)

- **Recompute and return the new value.** Upstream weights and totals *do* change between retries (a payee's
  share is edited, a total is corrected). A settlement that was already paid would then silently report a
  different split than the money that actually moved. This violates the "once" goal directly.
- **Recompute and raise if it differs.** Tempting as a safety net, but it turns an ordinary retry into a
  production error whenever anything upstream legitimately changed after payment. We chose silence over a
  false alarm, knowingly.

## Consequence

The store holds the **result**, not the inputs. **Any new entry point that computes without paying (a preview
or dry run) must not write to the store, and must not read a stored result as if it were a fresh
computation.** Keep the paying path and the previewing path distinct.
