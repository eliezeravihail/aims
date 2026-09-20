# Running log — 24h autonomous improvement run (started 2026-09-20)

Append-only. Each entry: timestamp · what happened · next.

- **2026-09-20 — start.** Branch `claude/aims-improve-blind-outcomes` from master @04e0b76. Pre-registered
  `plan.md`: three candidates (I1 input-space table, I2 falsification review, I3 outcome-first measurement),
  each with a rubric-free outcome metric fixed before running, validated on unseen products, aims-as-is.
  Next: build I1's frozen product packages and launch the blind A/B arms.

- **2026-09-20 — I1 + I2 arms launched.** I1: 4 design arms (P1 shipping, P2 discount × base/table),
  aims-as-is, design-only, differing only by the §1 input-space-table variant. I2: 2 review arms on one
  seeded first-draft (rate limiter, fixed-window burst seed), differing only by the falsification-pass
  variant of review.md. Hidden probe sets frozen before launch; arms told not to read them. Next: while
  arms run, draft I3 (outcome-first measurement) and prepare blind scoring for I1/I2.

- **2026-09-20 — I2 resolved: NULL.** Both review arms caught the seeded fixed-window burst (S4) with a
  concrete reproducible failing input; the BASE arm additionally caught both secondary seeds (clock,
  memory) while the ATTACK arm tunneled on the primary and caught fewer. Pre-registered rule (attack must
  catch where base misses) not met → falsification pass **not adopted**. The shipped §1 "trace the full
  input space" already is a falsification step. Recorded in i2-.../results.md.
- **2026-09-20 — I3 drafted + validated from the record.** Outcome-first comparison discriminates where the
  rubric ceiling'd (Study-1 rubric 10/10/10 vs survival tie/win/tie; plant→mineral caught by the gate).
  Proposed measurement.md addition + disjoint-vocabulary judge drafted; adopt in synthesis.
- **2026-09-20 — I1 first arm back:** P1 shipping TABLE arm's review caught a scalar-weight S4 via the
  input-space table and fixed it (ScaleReading sum type). Awaiting P1 BASE + both P2 arms before blind
  scoring. Open question: the card states X1 explicitly, so BASE may also handle the headline range — the
  subtler corners (boundary inclusivity, degenerate-range unification, composition) may still discriminate.
