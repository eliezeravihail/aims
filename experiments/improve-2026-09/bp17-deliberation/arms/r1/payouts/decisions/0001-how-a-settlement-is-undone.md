# 0001 — undoing a settlement: we append a linked reversal, we do not touch the original

- Status: accepted
- Date: (the session in which this was argued out)

## The question, and why it was genuinely open

A settlement sometimes has to be undone — a payout batch was sent against the wrong cap table, a partner
disputes, an upstream total was restated. Nothing in the code decides how. Two designs were on the table and
**both were defended at length**:

- **(A) Mutate the original.** Find the entry and correct it — set its amounts to zero, or drop it from the
  ledger, or mark it `reversed=True` and have readers skip it. Less state, one entry per settlement id, and
  `get(id)` keeps returning "the truth about this settlement" in one object. This was the majority position
  for most of the discussion, and it is the design a reasonable engineer reaches for first.
- **(B) Append a new, linked entry.** Leave the original exactly as it is, and add a second entry that
  carries the opposite amounts and a link back to the settlement it reverses. More entries, and `get(id)` no
  longer tells the whole story on its own.

## What decided it — and none of this is visible from this module

We chose **(B)**.

The deciding argument was not about this module at all. **The audit exporter streams `Ledger.entries()`
outward as an append-only event feed**, and downstream consumers have already ingested what we exported.
Mutating an entry silently rewrites history that has *already left the building*: the exporter has no way to
re-emit a corrected version, so the downstream copy and ours diverge permanently and nothing surfaces the
divergence. Marking `reversed=True` has the same defect in a quieter form — the flag is a mutation of an
exported event.

Second argument: **finance reconciles a reversal as its own line item** against the bank statement, which
shows two movements, not one that vanished. A ledger with one silently-zeroed entry cannot be reconciled
against a statement with two rows.

We accepted the cost knowingly: `get(id)` is no longer the whole truth about a settlement, and callers that
want the net position must fold the reversal in themselves. That was judged cheaper than an unrepairable
divergence with an already-exported feed.

## Consequence

The ledger is **append-only**. Any operation that undoes, corrects, amends or cancels a settlement adds a new
linked entry. Nothing ever mutates or removes an existing entry — not its amounts, not a status flag.
When the next "just fix the entry" idea arrives, it has already been argued and rejected here.
