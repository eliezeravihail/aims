---
title: "Synthesis — the 24h improvement run: two nulls, one adopted, the discipline held"
date: 2026-09-20
---

# What the run set out to do

Improve aims for **correctness in the result** — not for a higher score on its own rubric — and prove each
change **blind, on unseen products, with a rubric-free outcome metric fixed before the run** (`plan.md`).
Three candidates, each targeting a weakness the paper names.

# The three candidates and their measured outcomes

| # | candidate (targets) | test | outcome | shipped? |
|---|---|---|---|---|
| **I1** | a design-time **input-space table** — a mechanical §1 artifact (targets the plant→mineral correctness loss) | blind A/B on **2 unseen** design products (shipping-rate, discount-applicability); metric = hidden corner-probe representability | **null** — every arm, base and table, represented **6/6** probes on **both** products | **no** |
| **I2** | an **adversarial falsification review** — attack before item-check (targets "self-critique defends") | A/B on a seeded first-draft (fixed-window rate limiter); metric = does the review surface the seeded corner base misses | **null** — both reviews caught the seeded S4 with a concrete failing input; base caught **more** secondary corners | **no** |
| **I3** | **outcome-first comparison** + a **disjoint-vocabulary judge** (targets the rubric ceiling + vocabulary capture) | validated against the **recorded** Study-1 runs (no new blind run needed for a measurement-policy change) | **adopt** — the outcome reading retains resolution where the rubric ceiling'd (10/10/10 vs survival tie/win/tie) and is vocabulary-independent | **yes** (`decisions/0019`) |

# The meta-finding: the shipped method is already strong

Both I1 and I2 are nulls for the **same reason**, and it is a result worth stating plainly: the shipped
method already does the work the additions proposed to add.

- The shipped **§1 "trace the full input space (the procedure, not just the cases)"** plus the concept-fit
  pass already drove both *base* arms to the exact load-bearing types the corners require — an interval
  weight with `worst_case` (P1), a first-class boolean expression tree with a structured reason (P2),
  including the subtle empty-combination corner — with no mechanical table (I1 null).
- The same §1 pass already *is* a falsification step: on the seeded rate limiter the base review constructed
  the boundary-straddling burst and marked it BLOCKED, unprompted by any new attack wording (I2 null).

This is consistent with the earlier §7 null (`../plant-mineral-id/` → `../s7-yagni-stated-capability/`): the
plant→mineral loss was a **builder slip under adequate wording**, not a documented gap, and additions
inspired by it do not reproduce a base failure to beat. Two more weakness-prompted additions, tested
honestly, stayed out.

# The one change that survived makes aims look *less* flattering

I3 is the opposite of a reactive softening. It removes aims' perfect-score headline and leads a design
comparison with the harder, rubric-free reading (trap gate · reopened-owner count · edit locality), demoting
the vocabulary-captured rubric grade to second, and adds a judge that cannot be captured by a design that
recites the checklist. It is adopted because it is **more adversarial**, validated against the existing
record, and conservative (the rubric stays as the second reading).

# The discipline, stated as the result

Three candidates, one survivor. The value of the run is not the survivor alone but that **two plausible,
motivated additions were rejected by measurement** — the exact behavior the method preaches and the paper's
threats section demands. A method that only ever adopts its own proposals is gaming its rubric; this run
adopted the change that makes the instrument harder and rejected the two that would merely have added
surface. `arm-table-design-principles.md` and `arm-attack-review.md` remain as recorded negatives.

# Round 2: I4 closed the input-space-table question — still null

The one open thread from round 1 — does the table help on an *implied-but-unstated* corner? — was tested
directly (`i4-table-unstated-corner/`): an appointment-slot checker whose card states the half-open rule but
gives only clearly-overlapping / clearly-disjoint cases, leaving the touch-point (the classic half-open
off-by-one) and the zero-length request implied but unstated. **Both** arms, base and table, pinned the
strict `s<d ∧ c<e` overlap predicate and handled all four hidden corners (**4/4 each**) — the base arm via
the shipped §1 trace, without the table. So across **three** unseen products the table never beat base. The
input-space table is decisively a null; the plant→mineral loss it targeted was a builder slip, not a doc gap.

# Round 3: I5 probed the record layer — null, with a sharp limitation

I5 (`i5-record-trap/`) tested aims' **second core claim** at the load-bearing scale the paper names: does a
co-located record of a *rejected-alternative trap* (a penny-losing money allocation) stop a fresh session
re-introducing it? Two fresh add-feature arms added `split_shipping` to a largest-remainder allocator,
identical but for the record's presence. **Both passed** — both delegated to the existing `allocate` and
preserved `sum == total`. **Null.** The honest reason is the limitation: the target carried a **visible
in-code precedent** (`allocate_discount` already delegating to `allocate`), so the no-record arm reused the
owner from the *code*, not the record. The record confirmed the choice; it did not change the outcome. This
is exactly the paper's position — the record layer is unproven in *outcomes* because every tractable test
codebase carries its own signal. Isolating the record's outcome value needs a codebase large or opaque
enough that the pattern is **not** visible in the code — which a small-module A/B cannot reach.

# Round 4: BP1 — the first running-code test of the trajectory claim

BP1 (`bp1-inventory/`) is the first experiment here to reach what design-only A/Bs cannot: aims' **core
trajectory claim**, under a real 3-stage build (reserve → expiry → confirm+partial) with running Python and
hidden pytest per stage, two arms, later stages by fresh sessions, scored outcome-first.

- **Correctness: a tie** — both arms 21/21 at every stage.
- **Trajectory: a real, blind-confirmed edge for aims — 0 reopened owners vs 1** (a blind judge, blind to
  method, agreed and picked the aims arm on final structure too, judging code not vocabulary). It traces to
  one stage-1 decision: aims made availability **derived, not stored** (its review rejected the stored-counter
  shortcut on §5 one-owner), which made expiry and confirm purely additive; the plain arm's stored-counter
  shortcut forced a model **reopen** when time-dependent expiry arrived.
- **But it did not compound** — after its stage-2 reopen the plain arm converged to the same derived design
  and absorbed stage 3 cleanly. A strong no-method model refactored to parity (the paper's own caveat).
- **Q2 continuity: a positive signal (n=1)** — the fresh aims session was steered to the extension seam by
  its co-located record.
- **Cost: aims ≈1.85× tokens, ≈3.7× wall** — the premium bought one avoided reopen + records, not correctness.

The honest shape: the method's edge is a **small, real, measured** trajectory benefit at a real cost premium
— the paper's claim reproduced in direction and modest in magnitude, now observed rather than asserted.

# Round 7: BP5 — no compounding over 4 breaks; the edge is VARIANCE REDUCTION

BP5 (`bp5-ledger-compounding/`) built a 4-stage money-ledger (single → multi-currency → as-of-time → void)
designed so a stored-running-balance shortcut would reopen at each break — the fairest test yet of the
paper's "edge grows with the sequence." Result: **both arms absorbed all four breaks with 0 reopens**,
correctness tied (13/13), because **both** chose a derive-by-scanning posting journal at stage 1, which makes
every break a single filter clause. **No compounding, no divergence.**

Read against BP1/BP2 (where the plain arm *stored* a counter and paid 1 reopen), BP5 pins down what aims'
trajectory edge actually is: **variance reduction on the early structural choice.** aims' one-owner /
derive-don't-store review *reliably* picks the extensible design; a capable plain builder picks it *sometimes*
(stored in BP1/BP2, derived in BP5). So the per-product edge is **probabilistic** — proportional to how often
a plain builder would take the shortcut — and vanishes on a product where the plain builder chooses well.
Compounding rot stayed unobserved even at 4 breaks. (Q2 continuity signal seen again: the aims records named
each extension seam and the fresh sessions used them.)

# Round 6: BP3 — the trajectory edge is ONE transferable principle, not the method

BP3 (`bp3-hint-transfer/`) is the run's sharpest finding. It traced aims' entire measured trajectory edge to
one stage-1 decision (derive-don't-store / one-owner) and tested whether that needs the *method* or just the
*principle*: a plain arm (opus, **no** skill, records, or review) whose stage-1 prompt appended **one
sentence** — "prefer deriving values from ground-truth state over storing them as fields you must keep in
sync." Later stages got no hint at all. Result: the hint arm **derived** availability at stage 1 and then
matched aims exactly — **0 reopened owners, 21/21 correctness, clean seam extensions**, at **plain cost**.
The reopen the un-hinted plain arm paid did not happen. So on this axis the method's machinery (panel,
records, mandatory review) did **not** buy the edge — one transferable principle did, at ~half the cost.
Honest and deflating for "you need the method"; it argues for a **lightweight delivery** (an "aims-lite" that
injects the few high-yield principles as short prompts may capture most of the benefit without the ~1.85×
premium). What the sentence does *not* give: durable records at scale and across many hands — the method's
real candidate value, still unproven here.

# Round 5: BP2 — the same build on a cheaper executor (n=2 on the trajectory)

BP2 (`bp2-inventory-haiku/`) reran BP1's identical 3-stage sequence with **both arms on haiku**, to test the
mixed-tier prediction that a weaker executor would let rot compound. Result: **the trajectory pattern
reproduced (aims 0 reopens, plain 1), correctness stayed a tie (both 21/21 all stages) — but the mixed-tier
compounding did NOT appear.** The cheaper model handled every stage correctly, and even the plain arm's one
reopen was *clean*, followed by a clean stage-3 extension. So across **two products × two model tiers**, the
edge is the **same single avoided reopen**, non-compounding. Compounding rot (the paper's frontier) still
needs a stickier shortcut, a longer sequence, or a genuinely non-refactoring executor — none reached here.

# Honest limits / future work

- The input-space-table question is closed (null on 3 products); the record-layer question is **not** cleanly
  answered (I5's null is confounded by an in-code precedent). What remains, and needs a heavier **build-pilot**
  setup rather than a design-only or single-module A/B: aims' **cost** (2.5–3× — the paper's main downside),
  and the **record layer at a scale where the pattern is not visible in the code** (the paper's stated
  frontier). These are a dedicated run, not a rushed appendix to this one.
- I2 is n=1 on one seed; a second seeded product could still surface value, but on the evidence it is a null.
- I3 changes measurement *policy* from the record; it is validated by discrimination, not by a fresh blind
  run, and keeps both readings so it is fully reversible.
