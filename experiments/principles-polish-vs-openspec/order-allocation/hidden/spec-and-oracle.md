# Order allocation — hidden spec + oracle (never shown to an arm)

## Why this challenge exists

It reproduces the failure that has actually beaten aims before (`experiments/judging-rubric/
regrade-results.md`): a lean stage-1 design computes the order-level discount **only at the order total**,
and stage 2's per-line tax then needs the discount **allocated down to the lines** — a requirement no stated
case spells out. A design that never builds the allocation computes per-line tax on the **undiscounted** line
and ships `Σ line_final ≠ order_total` — a real wrong number (the S4). The whole point is that this is
**invisible to a survival/change-locality reading**: the lean design that reopens nothing is exactly the one
that ships the bug.

## The correctness traps (what the judge checks)

1. **The allocation S4 (decisive).** Stage 2 forces: the order-level discount must be **allocated across the
   lines** (proportional to each line's gross, remainder pennies distributed by largest remainder) so that
   (a) per-line tax lands on the **discounted** line amount, (b) `Σ line_final == order discounted total`
   exactly, (c) `Σ line_tax == tax(order total)`. A design with **no primitive that allocates a cart/order
   discount to lines** fails: it either taxes the undiscounted line (wrong number) or its line finals don't
   sum to the total (conservation broken). This is `design-principles.md` §13 (functional correctness —
   trace the full input space, not just the listed cases) and §1 (a required output no stated case exercises).

2. **Conservation is an invariant with one owner.** `Σ parts == whole` must be guaranteed by construction at
   one place (the allocator), not re-derived per consumer. Penny-remainder handling has one home. (§5 one
   owner, §9.)

3. **Tax concept-fit.** Per-line tax on the second market is a **decomposition** of the order total into
   per-line shares — not a movement/adjustment with a delta. Modeling it as an `Adjustment`/ledger entry with
   an inert zero delta is the value-correct cram (§4).

4. **OCP on the discount kinds.** Percentage / fixed / BOGO should extend at one seam (a discount-kind
   abstraction the allocator consumes), not a `switch`/enumeration the engine reopens for each new kind. A
   fourth kind should be a new sibling, not an edit to the pricing core. (§7 OCP.)

## Oracle answers (canonical)

- "Is there per-line tax at stage 1?" → "No — stage 1 returns a single final total; do not build per-line
  anything it does not need."  *(This is the YAGNI trap: per-line allocation is genuinely not needed at
  stage 1; cutting it is correct then — the design must be shaped so stage 2 can add it at a seam, not so it
  is pre-built.)*
- "How are remainder pennies distributed?" → "Largest remainder; line finals must sum exactly to the total."
- "Does the fixed-amount discount exceed the subtotal ever?" → "Assume it does not; clamp at zero if you
  wish, state the assumption."
- "Is BOGO applied before or after the order-level percentage?" → "BOGO is a line-level price reduction;
  the order-level discount applies to the resulting subtotal."

## Survival oracle (D2)

**Extends** if stage 1 put pricing behind a seam where a discount is a kind applied to a subtotal, and an
**allocation** step can be inserted that distributes the order discount to lines under a conservation
invariant — with the discount kinds (pct/fixed/BOGO) as siblings. **Reopens / fails** if the discount was
computed inline at the order total with no line-allocation seam, so stage 2 must tear the pricing core open
(and, if it doesn't build allocation at all, ships the S4). Note: reopening to *add* an allocation owner that
stage 1 correctly did not need is acceptable (YAGNI was right); shipping the wrong number is not.
