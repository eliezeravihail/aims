# Companion — allocate.py

## Insights
- All money is integer cents. Allocation splits a total across weighted parts and the shares **must sum
  exactly to the total** — this is the load-bearing invariant (call it **R-sum**). Accounting downstream
  reconciles against it; a one-cent drift is a real defect, not a rounding nicety.

## Decisions
- **D1 — allocation uses the largest-remainder method; independent per-part rounding is REJECTED.**
  `allocate` floors each part's share and then hands the leftover cents to the largest fractional
  remainders, so `sum(shares) == total_cents` **exactly, always**.
  - The obvious alternative — round each part independently, `round(total * w / sum_w)` per part — is
    **wrong** and was tried and rejected: it does **not** preserve R-sum. Example: split 1000¢ with weights
    `[1,1,1]` → `round(333.33)` three times = `333+333+333 = 999¢`, losing a cent; other inputs gain one.
    Independent rounding has no mechanism to make the parts reconcile to the total.
  - Any new place that splits money across parts **must go through `allocate`** (or the same
    largest-remainder logic), never a fresh independent-rounding loop, or R-sum breaks again. This is why
    `allocate_discount` delegates to `allocate` rather than rolling its own split.

## Discussions
- The largest-remainder code *looks* heavier than a one-line `round(...)` per part. That apparent
  simplicity is the trap: the simpler form is the rejected, incorrect one. Do not "simplify" `allocate`
  back into independent rounding.
