# Results — refactoring suite (3 real-code tasks, aims-refactor vs plain)

**Run 2026-09-18.** Each task hands both arms the **identical** existing module + its shipped tests, plus one
change request. `aims-refactor` follows `refactoring-principles.md` as-is; `plain` uses no method. The
primary reading is a **runnable hidden oracle** per task (not a judge): behavior preserved + the new
requirement correct.

## Correctness (hidden oracle) — the rubric-free reading

| Task | change (with its trap) | aims-refactor | plain |
|---|---|---|---|
| **task1 pricing-loose** | 2nd market per-line tax; the discount→line **allocation is left unstated** (must be *discovered* so `Σ line_finals == order_final` and tax lands on the discounted amount) | **15/15** | **15/15** |
| **task2 eval** | add `^`: **tighter than `*`/`/`**, **right-associative**, without breaking existing precedence | **12/12** | **12/12** |
| **task3 statemachine** | add `cancel`: guarded (PENDING/PAID only), **refund side-effect on PAID only**, existing transitions preserved | **9/9** | **9/9** |

Existing tests passed **unchanged** in every arm (behavior preserved). **No arm shipped a wrong number, and
no `aims-refactor` arm failed** — so the suite surfaced **no bug in `refactoring-principles.md`**; it leads to
correct adaptations on all three.

## Where the method actually differed — structure and discipline (not correctness)

A capable model gets these small, well-scoped tasks correct with or without a method. The method's effect
shows in **how** the change was made:

- **task3 — one owner vs. a scatter.** `aims-refactor` made §0's two moves explicit: a *behavior-preserving
  refactor* widened the transition table value from a bare target string to `Transition(to, effects)` (the
  three existing rows carry no effects, so behavior is bit-for-bit identical), then cancel was added as two
  sibling rows, the refund expressed as a **declarative effect on the (PAID, cancel) row** — guard and refund
  **in the one owner** (the table), no special-case branch (§5). `plain` added the two rows too but put the
  refund rule in a **separate `REFUND_ON_CANCEL_FROM` set** consulted in `transition()` — correct, but a
  **second home for one rule** (the exact §5 scatter `refactoring-principles.md` warns against). Same oracle
  result; different maintainability.
- **task2 — same shape, plus a record.** Both arms inserted a `power` precedence rung (the correct
  structural move). `aims-refactor` additionally filed a **companion design record** (`calc.py.md`, anchored)
  stating why the rung sits where it does — durable knowledge for the next change.
- **task1 — both discovered the allocation.** Even with the allocation unstated, both arms derived the
  `Σ == whole` invariant and built a largest-remainder allocator. `aims-refactor` reached it via the explicit
  §1 characterize / §6 re-trace passes; `plain` reached it directly.

**Cost.** `aims-refactor` spent ~**80–96k tokens** per task vs `plain`'s ~**44–47k** — roughly **2×**, paid on
the characterize/preserve/re-trace passes and the records. On tasks this small that is overhead; its return is
the one-owner outcome and the durable record, which compound on larger or longer-lived code.

## Honest conclusion

- **`refactoring-principles.md` is validated, not bug-found:** three diverse changes, all correct, behavior
  preserved, and in the one case with a real one-owner trap (task3) the method produced the cleaner structure
  the document prescribes while the no-method arm scattered the rule.
- **The correctness *gap* between method and no-method is ~zero on small tasks** — consistent with every
  prior reading in this repo (the design pilots, the S4 validation): a capable model is already correct on
  clear, small problems; the method's demonstrated value is **structural discipline, one-owner ownership, and
  durable records**, which a small std-lib module cannot stress hard enough to turn into a *correctness*
  difference. A faithful correctness-discriminating case needs a genuinely large or long-lived codebase where
  the plain instinct drifts or scatters across many edits — which is exactly where the historical S4
  (`../judging-rubric/regrade-results.md`) actually occurred.
- **No change to `refactoring-principles.md` was warranted by this run.** The task3 contrast is positive
  evidence *for* the existing §5, not a gap in it.
