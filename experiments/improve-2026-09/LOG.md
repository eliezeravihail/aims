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

- **2026-09-20 — Round 2: I4 launched (fair, one-shot).** The sharper test of the input-space table: an
  appointment-slot checker whose card states the half-open rule but gives only clearly-overlapping /
  clearly-disjoint cases, so the touch-point (adjacency) and zero-length corners are IMPLIED but UNSTATED.
  Two arms (base vs table), aims-as-is, design-only. Pre-registered as a distinct hypothesis in
  i4-.../plan.md; one shot; a win is suggestive-only (n=1) and does not overturn the I1 n=2 null.

- **2026-09-20 — I4 resolved: NULL.** Both arms (base, table) pinned the strict half-open overlap predicate
  and handled all 4 unstated corners (adjacency free, zero-length rejected, identical = conflict): 4/4 each.
  The base arm reached it via the shipped §1 trace, without the table. Input-space table decisively closed
  as a null across 3 unseen products. Recorded in i4-.../results.md; SYNTHESIS updated.
- **2026-09-20 — run conclusion.** Shipped: I3 (outcome-first measurement). Null and not shipped: I1, I2,
  I4. Meta-result: the shipped design method (esp. §1 "trace the full input space") is robust; motivated
  additions did not beat it and were rejected by measurement. Remaining real weaknesses (cost, record layer
  at scale) need build pilots — flagged as a future dedicated run, not rushed here.

- **2026-09-20 — Round 3: I5 launched (the record-layer frontier).** Does a co-located record of a
  rejected-alternative trap stop a fresh session re-introducing it? Target: a largest-remainder money
  allocator (preserves sum==total); the companion records the REJECTED independent-rounding alternative and
  "any new split must go through allocate". Change: add split_shipping (a new money split). Two fresh
  aims add-feature arms, identical but for the record's presence. Metric: split_shipping(1000,[1,1,1]) must
  sum to 1000 (pass iff it reuses largest-remainder, fail iff a fresh independent-rounding split). n=1
  suggestive. Pre-registered in i5-.../plan.md.

- **2026-09-20 — I5 resolved: NULL (confounded).** Both arms delegated split_shipping to allocate and
  preserved sum==total (scored mechanically). The record confirmed but didn't change the outcome — the
  no-record arm reused allocate from a visible in-code precedent (allocate_discount). Limitation recorded:
  the test didn't isolate the record because the code carried the pattern; isolating it needs a codebase
  where the pattern is not visible (the paper's frontier). Recorded in i5-.../results.md; SYNTHESIS updated.
- **2026-09-20 — RUN CONCLUDED.** Five candidates tested honestly, blind, aims-as-is, pre-registered:
  I1/I2/I4 (design & review additions) null; I5 (record layer) null (confounded); I3 (outcome-first
  measurement) ADOPTED and shipped. Headline: the shipped design method is robust; the one change that
  shipped makes the instrument harder on aims, not softer. Remaining real weaknesses (cost, record layer at
  non-visible scale) need a dedicated build-pilot run. Deliverable: branch claude/aims-improve-blind-outcomes,
  draft PR #65.

- **2026-09-20 13:20 UTC — RUN RESUMED (user: keep going ~24h while credits last).** Design-only additions
  exhausted (robust nulls). Pivoting to the higher-value work they can't reach: BP1, a real 3-stage build
  pilot (inventory reservation service) measuring aims' core TRAJECTORY claim with running code + hidden
  tests, scored outcome-first (correctness gate + reopened-owner/edit-locality + cost). Frozen package:
  cards/stage-{1,2,3}.md, hidden/test_stage{1,2,3}.py. Stage-1 arms launched (aims w/ records vs plain).
  Next: score stage 1 on hidden tests, reveal stage 2, repeat; then judge the trajectory blind.

- **2026-09-20 — BP1 COMPLETE (round 4, the trajectory claim under running code).** 3-stage inventory
  service, aims vs plain, later stages fresh sessions, hidden pytest per stage. Result: correctness TIE
  (both 21/21 all stages); trajectory edge for aims — **0 reopened owners vs 1**, blind-confirmed by a
  method-blind judge that also picked the aims arm on final structure. Root cause: aims' stage-1 derive-
  don't-store (§5) made both later changes additive; plain's stored counter forced a stage-2 model reopen.
  Did NOT compound (plain refactored to parity). Q2 signal: the record steered the fresh aims session to
  the seam. Cost aims ~1.85x tokens / ~3.7x wall. Honest: real, small, measured edge at a real premium —
  the paper's claim reproduced in direction, modest in magnitude. Recorded in bp1-inventory/results.md.
  Next: BP2 — same sequence on a CHEAPER executor model, where the plain arm should NOT refactor to parity
  and rot may compound (the paper's mixed-tier condition).

- **2026-09-20 — BP2 COMPLETE (round 5, cheaper executor, n=2).** Same 3-stage inventory sequence on haiku
  both arms. Result: correctness TIE (both 21/21 all stages — the weak executor did NOT break); trajectory
  reproduced (aims 0 reopens, plain 1 at stage 2); NO mixed-tier compounding (haiku refactored its reopen
  cleanly). So across 2 products × 2 model tiers the edge is the same single avoided reopen, non-compounding.
  Recorded in bp2-inventory-haiku/results.md. Next: BP3 — a sharp cheap probe: give the PLAIN arm a one-line
  "derive-don't-store / one-owner" hint at stage 1 and see if it then also gets 0 reopens (does the edge need
  the METHOD or just the PRINCIPLE?).

- **2026-09-20 — BP3 COMPLETE (round 6, the sharpest finding).** A plain arm (opus, no method) given ONE
  "derive-don't-store" sentence at stage 1 reproduced aims' full trajectory edge: derived availability →
  0 reopened owners across all 3 stages, 21/21 correctness, clean seam extensions — at plain cost. The
  model reopen the un-hinted plain arm paid did NOT happen. So on this axis aims' edge is one transferable
  principle, not the method's machinery; the ~1.85x premium did not buy it. Argues for a lightweight
  "aims-lite" (inject the few high-yield principles as short prompts). Method's real candidate value —
  records at scale + across many hands — remains untested. Recorded in bp3-hint-transfer/results.md;
  SYNTHESIS updated.

- **2026-09-20 — BP4 resolved: NULL (concept-fit).** Playlist builder, hard "no-3-in-a-row" rule. Both arms
  (aims, plain) modeled H as a hard feasibility filter (gate+guard, same M<=2(T-M)+2 predicate), NOT the
  filter-as-score cram. aims' concept-fit review confirmed the design but caught nothing plain missed. The
  strong no-method model avoided the cram unaided. Consistent with the whole run: on tractable single
  artifacts the method confirms rather than rescues. Recorded in bp4-conceptfit-probe/results.md.

- **2026-09-20 — BP5 COMPLETE (round 7).** 4-stage money-ledger (single→multi-currency→as-of-time→void),
  built to make a stored-running-balance shortcut reopen at every break. Both arms chose a derive-by-scanning
  posting journal at stage 1 → both absorbed all 4 breaks with 0 reopens, 13/13. NO compounding, no
  divergence. Pins the edge as VARIANCE REDUCTION on the early structural choice: aims reliably derives, a
  plain builder derives only sometimes; the per-product edge is probabilistic and vanishes when the plain
  builder chooses well. bp5-ledger-compounding/results.md.

- **2026-09-20 — BP6 COMPLETE (round 8).** Shortcut base-rate probe: 6 haiku plain builds of the BP1
  inventory stage-1 card, classified STORE vs DERIVE. Result: 1/6 stored (run-5 kept a _reserved running
  total in sync alongside the ledger), 5/6 derived. So the derive-axis shortcut base rate ≈17% — the size of
  aims' expected per-product trajectory edge on this axis. bp6-baserate/results.md.

- **2026-09-20 — BP7 COMPLETE (round 9).** Generalization to a CONCEPT-FIT axis (first-class rules vs
  isinstance type-branch), 2-stage promo engine, arms plain/lite/aims. All 3 opus arms modeled rules
  polymorphically → 19/19, 0 reopens each (ceiling null). Base-rate probe: shortcut 0/3 opus, 2/6 haiku. The
  edge generalizes as the SAME variance-reduction mechanism and is model-dependent (invisible on a strong
  model, real on a weak one). bp7-conceptfit-generalize/results.md.

- **2026-09-20 — BP8 COMPLETE (round 10).** Does aims-lite (principle-in-prompt) lower the shortcut rate on
  a weak model? 6 haiku builds with the concept-fit principle block → 2/6 branch, IDENTICAL to plain's 2/6.
  No effect. The principle transfers on opus (BP3) but not haiku. aims-lite helps only where the executor is
  already capable; the method's value on weak executors is the review, not the advice. bp8-lite-baserate/results.md.

- **2026-09-20 — BP9 COMPLETE (round 11, closes the arc).** The real aims review, run by a competent Guide
  over the 4 branched haiku builds, flagged the type-switch structurally on ALL 4 (detection 4/4) and named
  the fix (repair validated: b1 → polymorphic, 12/12, 0 isinstance) — where the prompt-principle scored 0/6.
  aims' irreducible value is output inspection (mixed-tier: cheap Worker + competent review). Caveat: the
  type-switch rates S3 (non-gating), so the review surfaces-and-names rather than forces. Recorded a
  motivated-but-untested improvement candidate (gate the spec-named-change-axis reopen as S4).
  bp9-review-vs-principle/results.md. SYNTHESIS retitled + summary paragraph; PR #65 body updated.
