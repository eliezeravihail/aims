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

- **2026-09-20 — I1 three of four arms in; emerging NULL.** P1-base (interval `WeightReading.worst_case`),
  P1-table (ScaleReading sum), P2-table (Requirement expression tree Atom/All/Any/Not) each represent every
  hidden corner probe for their product. The base arms reached the same correct type models as the table
  arms *without* the mechanical table — the shipped §1 "trace the full input space" plus the cards' explicit
  change-axes already surface the corners. Awaiting P2-base to confirm, then a single blind scorer over all
  four designs. Honest read forming: the input-space table does not beat shipped §1 on stated-axis products
  (same shape of result as I2 and the earlier §7 null — the shipped method is already strong). Will NOT
  manufacture an easier product to force a win.

- **2026-09-20 — I1 resolved: NULL.** All four arms represented 6/6 hidden corner probes on both products;
  base arms reached the same load-bearing types (interval+worst_case; boolean expression tree) as the table
  arms without the mechanical table. Input-space table not adopted. Recorded in i1-.../results.md.
- **2026-09-20 — I3 adopted + shipped.** measurement.md "Comparing designs" now leads with the rubric-free
  outcome profile (trap gate · reopened-owner count · edit locality), rubric grade second; disjoint-
  vocabulary judge added. ADR 0019 + PROTOCOL.md §6 note. Full test suite green.
- **2026-09-20 — synthesis written.** Two nulls (I1, I2), one adopted (I3). Meta-finding: the shipped §1
  "trace the full input space" already does the work the two null additions proposed. The one adopted change
  makes aims *less* flattering (removes the ceiling, defeats vocabulary capture). Discipline held: motivated
  additions rejected by measurement; only the honesty-increasing change shipped.
