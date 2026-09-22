# 0001 — the remainder tie-break is payee_id ascending

- Status: accepted

## The doubt

Largest-remainder allocation leaves N leftover cents to hand out, and when two payees have the **same**
remainder, something has to break the tie. This was genuinely unclear and we went back and forth; all three
candidates are defensible and none is visibly "more correct" in the code.

## Decision

Sort the remainder queue by **descending remainder, then ascending `payee_id`**. The tie-break is the
payee id — deliberately, not incidentally.

## Rejected alternatives (and why)

- **Insertion / input order.** The obvious and most natural choice, and it is what a reader will assume the
  `sorted()` call is incidental to. It is wrong for us: upstream hands us `shares` from a dict whose order
  follows an unstable join, so the same settlement produced **different** payouts on re-run. That broke the
  reproducibility goal and produced two reconciliation tickets before we found it. This is the trap: the code
  looks like ordering does not matter, and it matters more than anything else here.
- **Give the leftover to the largest share.** Biases the *same* payee on every settlement; over a month the
  largest payee systematically gains cents. Rejected as unfair, not as incorrect.

## Consequence

`_allocate` sorts payees by id up front and breaks remainder ties by id. **Any change that re-derives the
allocation must preserve the id-ascending tie-break.** If you find yourself iterating `shares` in dict order,
you have reintroduced the bug.
