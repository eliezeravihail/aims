---
title: "Retroactive re-grade under the new rule (weighted grade + gate, no global cap)"
date: 2026-09-18
---

# The grade-rule change, applied to every experiment — not just the one where it helped

`decisions/0018` removes the global graded cap: the grade is the whole-list weighted score, and severity is a
**reported gate** (`any S4 ⇒ BLOCKED`) beside it, not a `min` applied on top. That change was first made in
the round the aims arm **lost** the plant→mineral pilot, where it lifted the reported grade from a capped
5.0 to 6.63. To keep the instrument credible (the concern Pavel raised — never soften a loss by re-tabling
the rule mid-round), the rule is applied here **retroactively to the whole set**, with **both readings shown**
and the **gate derived from the recorded `(#S3,#S4)`** (no re-run, no invented numbers).

| Experiment | Arm | capped grade (old) | (#S3,#S4) | **gate (new)** | uncapped weighted |
|---|---|---|---|---|---|
| plant→mineral | OpenSpec | 8.5 | (0,0) | CLEAR | **9.54** |
| plant→mineral | **aims** | 5.0 | (0,1) | **BLOCKED** | **6.63** |
| checkout | aims | 8.5 | (0,0) | CLEAR | ≥8.5 (form not re-filled) |
| checkout | OpenSpec | 8.5 | (0,0) | CLEAR | ≥8.5 |
| checkout | plain | 8.5 | (0,0) | CLEAR | ≥8.5 |
| marketplace | aims | 9.9 | (0,0) | CLEAR | 9.9 (S1 — uncapped = capped) |
| marketplace | OpenSpec | 7.5 | (1,0) | CLEAR | ≥7.5 |
| marketplace | plain | 7.5 | (1,0) | CLEAR | ≥7.5 |
| ledger | capsule-aware | 10.0 | (0,0) | CLEAR | 10.0 |
| ledger | blind | 8.5 | (0,0) | CLEAR | ≥8.5 |
| checkout (v2 regrade) | aims-upgraded | 2.0 | (1,1) | **BLOCKED** | (the cart-discount→line S4; `judging-rubric/regrade-results.md`) |

*Only where a filled form is recorded is an exact uncapped weighted given (plant→mineral; marketplace aims,
which is S1 so uncapped = capped). Elsewhere the cap only ever lowered a grade, so uncapped ≥ capped; the
forms were not re-filled and no number is invented. The gate needs only `(#S3,#S4)`, which is recorded.*

## What the retroactive reading shows

1. **The rule change does not soften aims' loss — it sharpens it.** Across the recent 0–10 set the **only
   BLOCKED arm is aims, on plant→mineral**; the older checkout v2 regrade has the other BLOCKED aims arm
   (the cart-discount→line S4). Under the gate, aims' two recorded losses are *more* visible, not hidden.
2. **The comparison is now on one rule.** Nobody is comparing plant→mineral's uncapped 6.63 against the
   others' capped 8.5 unknowingly — every row carries both the capped grade and the gate.
3. **The grade change is adopted on its merit, not its convenience.** The old cap double-counted one defect
   (ceiling → weight → cap); the weighted list + gate does not. That is true regardless of who it helped in
   any one round — which is exactly why it has to be applied everywhere, as here.

## Honest caveat

A fully rigorous retroactive re-grade would re-fill the assessment form for each historical arm and report
the exact uncapped weighted. That is the remaining work; this note does the part that is **exact from the
record** (the gate, and the two grades where the form exists) and marks the rest as an inequality rather
than guessing. It is enough to establish the one thing that matters for credibility: the rule change is
applied to the whole set and it does not favour the home method.
