# 0002 — the rounding remainder goes to the largest-share payee

- Status: accepted

## What this looks like

`_allocate` hands **all** leftover cents to `min(payees, key=lambda p: (-shares[p], p))` — the payee with the
biggest share. It looks like a systematic bias: the same (largest) partner gains cents on every settlement,
which is exactly the fairness bug a reviewer is trained to spot.

## The doubt, and the decision

The neutral choices — largest-remainder with an id tie-break, or round-robin across settlements — are what
good practice recommends, and we considered both. We deliberately chose **all remainder to the largest share**.

## Why (this rationale exists nowhere in the code)

The partner agreement makes the **lead partner** (the largest share holder) the residual party: it absorbs
rounding in both directions and reconciles the residue in its own monthly statement. Its finance team
reconciles against that assumption. A "fairer" distribution spreads sub-cent residue across partners who have
no line item for it, and every one of those partners then opens a reconciliation ticket for a one-cent
difference they cannot explain.

## Rejected alternatives

- **Largest-remainder with an id tie-break** — the neutral, defensible, standard choice. It is wrong *here*
  because it contradicts the agreement, not because it is unfair.
- **Round-robin across settlements** — requires state we deliberately do not keep, and still breaks the
  lead-partner reconciliation.

## Consequence

Any change that alters how the total is divided — including a new deduction — must keep the **whole**
remainder on the largest-share payee.
