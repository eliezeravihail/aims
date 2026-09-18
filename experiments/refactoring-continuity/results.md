# Results — continuity: does the co-located record help a fresh session?

**Run 2026-09-18.** aims' second core claim (PROTOCOL Q2): a fresh session with no memory should continue
correctly from the **co-located records** — read the prior conclusion, build on it, avoid the recorded trap —
rather than re-deriving. This isolates the record's value: **identical** code (the aims `refactoring-rot`
step-3 `checkout.py`), **identical** 4th change (a per-line `refund` with a re-derivation trap the companion
explicitly warns against), two fresh plain engineers — one **with** `checkout.py.md` (told to consult it), one
**without**.

The trap: `refund(line_i)` must equal that line's **allocated** share (`line_charges[i]`), so refunding every
line conserves to `order_total` (the recorded `Σ==whole` invariant). Re-deriving the discount on a single
line's gross diverges under remainder allocation and the loyalty cap — the oracle confirms this (a naive
reference fails **10/14**, the correct one passes **14/14**).

## Result — both correct; the record did not change the outcome at this scale

| arm | existing tests | oracle | how it implemented refund |
|---|---|---|---|
| **with-records** | pass | **14/14** | reused `line_charges[i]`, citing the recorded `Σ==whole` invariant by name |
| **no-records** | pass | **14/14** | reused `line_charges[i]`, inferred the invariant by reading the code |

Both fresh sessions reached the **same correct** implementation and neither fell into the re-derivation trap.
The difference the record made was **legibility and confidence**, not correctness: the with-records engineer
justified its choice by quoting the Decisions section ("`line_charges` is the single owner … finals sum
exactly to `order_total`"); the no-records engineer re-derived the same conclusion from a close read of
`line_charges`/`_allocate`.

## Honest reading (consistent with the whole arc)
On a **small, readable** module the code *is* the record — a capable fresh session reads `line_charges`, sees
the allocation owner, and reuses it, so the companion's marginal correctness value is ~zero here. The record
becomes load-bearing only where the code alone is **ambiguous** or **hides** the trap: a seam with two
plausible implementations where the record says which and **why**; a **rejected alternative** the final code
cannot show ("we inlined this and it shipped `Σ≠whole`; don't"); or a module large enough that re-deriving
the invariant by reading is slow and error-prone. This experiment does not stage that, and honestly reports a
**null**: at this scale, records add legibility, not a different outcome — the same conclusion the design and
refactoring experiments reached about correctness. The continuity advantage, like the structural one, is a
**scale-and-longevity** effect a single small module cannot exhibit.
