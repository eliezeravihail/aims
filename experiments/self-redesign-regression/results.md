---
title: "self-redesign regression check — the polish did not regress, and one probe fix was caught blind"
date: 2026-09-16
---

# Self-redesign regression check

The `claude/aims-self-redesign` branch is **fixes and polish to aims, not a new method** (`decisions/0009`
corrected an over-reaching draft; the panel already existed since `decisions/0005`). So the question this
exercise answers is **improvement, or at least no regression** — not "new beats old". Subject product for
every arm: a two-sided dog-sitting marketplace, design only.

> **Not a PROTOCOL-grade experiment.** n=1 per configuration, real run-to-run variance, and the merges/some
> reviews were run by this session's delegated subagents. One arm (the fixed-probe re-run) was **blind to
> the test's purpose**. Read the readings, not a score. This file records the honest interim state so a
> later session inherits it.

## Two things the polish changed, tested separately

### 1. The panel's merge step (old "master planner" framing → new "merge agent, best-from-each, one shared objective")
Controlled cleanly: the **same three axis-focused Worker designs** were fed to two merge agents — one with
the pre-refactor merge instructions, one with the refactored ones.

| | old merge | new merge |
|---|---|---|
| central harmonization (invariant truth-condition in Booking via Reservation/Authorization proof-tokens; ordering+rollback in a Workflow) | reached it | reached it |
| real subtractive cut | yes (merged two workflow objects) | yes (cut a speculative pricing port) |
| gap note surfaced | yes (workflow idempotency) | yes (capture-time failure) |

**Reading: no regression, near-parity.** Both merges reached the same design. The refactor's structural
intent (the Guide owns the objective; the merge does not invent one) was **visible in behavior** — the old
merge "assembled a round objective", the new merge conformed to the given one — but it did not change design
quality on this product. Note this also retired an earlier *unfair* framing (panel vs single-pass), which
confounded method with 4× effort.

### 2. The review/measurement lens (design lens: quotation-admissible evidence, the quality-requirements list, the probes)
Controlled cleanly: the **same one design** (an ordinary single-pass design of the product) reviewed by
three reviewers — old lens, new lens, and the new lens after a fix.

| finding on the design | old lens | new lens (pre-fix) | new lens (**fixed**, blind) |
|---|---|---|---|
| atomicity "Accepted ⟹ slot-held ∧ funds-authorized" has no owner (central) | ✓ | ✓ | ✓ |
| money-movement rules split / fee-rate home unstated | ✓ | ✓ | ✓ |
| **new service-type semantics falsify the calendar's exclusive-interval model** (group/capacity) | ✓ | **✗** | **✓** |
| new trust-signal shape falsifies `scoreFor(sitterId)` | ✗ | ✗ | ✓ (bonus) |
| frozen-quote (authorize amount vs capture amount) | ~ | ✓ | ✗ (varied) |
| idempotency / event de-dup owner | ✗ | ✓ | ✗ (varied) |
| DST / geography falsifies the interval value type | ✓ | ✗ | ✗ (varied) |

**Reading — a real, caught regression.** The new lens's change-axis probe ("to add X, which components
change?") **narrowed attention to seam-counting** and missed change-axis-*semantics* leaks the old freer
"now-false assumption" look-for caught. The fix folded the **falsification angle** back into the probe
("would a plausible new variant's semantics falsify an assumption an existing owner holds?"). A **blind
re-run** (reviewer not told the test's purpose) confirmed the fix catches the targeted service-type leak
**and generalized** to a trust-signal-shape leak no prior review found.

## Residual, stated honestly
Individual findings (frozen-quote, idempotency, DST) **appear and disappear across runs** — no single
review is complete, and this is n=1 per lens. The targeted regression is closed and blind-confirmed; a
claim that the new lens *dominates* the old across the board is **not** supported by this exercise.

## Conclusion
Net gain, no regression **found**: machinery (hook fail-open) and docs (README truth) are unambiguous gains;
the panel-merge polish is parity; the review-lens polish had one regression that was caught, fixed, and
blind-confirmed. The honest limit is run-variance at n=1 — "only ever gains" is well-supported, not proven.
