---
title: "Synthesis — the 24h improvement run: 1 change shipped, the rest measured honestly, and aims' edge pinned down"
date: 2026-09-20
---

# What the run set out to do

Improve aims for **correctness in the result** — not for a higher score on its own rubric — and prove each
change **blind, on unseen products, with a rubric-free outcome metric fixed before the run** (`plan.md`).
It ran in two phases: first three method-change candidates (I1–I5), each targeting a weakness the paper names;
then a build-pilot campaign (BP1–BP9) that stopped asking *"what can we add?"* and instead **measured what
aims' edge actually is** under running-code tests, across three structural axes and two model tiers.

**The one-paragraph result.** **Two** changes shipped, both hardening the instrument rather than flattering the
method: **I3** (outcome-first measurement + a disjoint-vocabulary judge) and **I6** (naming the observed
anemic-model / type-switch as a specific mixed-tier review gap — `decisions/0020`, backed by BP7–BP9 on unseen
builds, no new gate). Every *additive* candidate (I1/I2/I4/I5, aims-lite) was rejected by measurement. The
build pilots pinned aims' benefit precisely: **correctness ties everywhere**; aims'
real edge is **avoided-reopen variance reduction on an early structural choice**, sized by the **shortcut base
rate** on each axis×model (≈0% for a strong model, ≈17–33% for a weak one). That edge **transfers as a one-line
principle on a strong model** (BP3) but **not on a weak one** (BP8); what survives compression is the
**review** — output inspection by a competent Guide caught the shortcut **4/4** on weak-model output where the
prompt-principle scored 0/6 (BP9). Net: aims earns its cost as a **mixed-tier** method (cheap Worker + competent
review), not as a prompt of principles.

The first phase (three method-change candidates) follows; the build-pilot campaign (rounds 4–11) follows that.

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

# Round 8: BP6 — the shortcut base rate that sizes the whole edge

BP6 (`bp6-baserate/`) closes the loop opened by BP1–BP5. If aims' trajectory edge is **variance reduction on
the stage-1 derive-vs-store choice** (BP5's finding), then its expected per-product size is simply *how often
a plain builder takes the stored-aggregate shortcut*. BP6 measures that directly: **6 independent plain haiku
builds** of the identical BP1 stage-1 card, classified STORE vs DERIVE. Result: **1 of 6 stored** (run-5 kept
a `_reserved` running total in sync alongside the ledger — the exact drift-risk design aims' §5 review
rejects); the other **5 derived** availability from the reservation ledger on read. So on this axis the
shortcut base rate is **≈17%** (wide CI, n=6, one card/model).

This gives the campaign's central finding a number: aims' trajectory edge is a **reliability premium on a
minority of products** — it converts the plain builder's *sometimes-derive* into *always-derive*, buying the
avoided reopen only on the ~1/6 of builds that would have stored. It explains BP5's both-arms-derived null
(BP5 drew from the ~5/6 that derive anyway) and BP1/BP2's single reopen (those plain arms drew the ~1/6 that
stored). The edge is real, mechanistic, and now *sized*: proportional to the shortcut rate, which is low for a
capable model on a clean card and rises with weaker builders, baited cards, or longer sequences where one
early store compounds.

# Round 9: BP7 — the edge generalizes to a second axis (concept-fit), as the SAME variance-reduction mechanism, and is model-dependent

BP7 (`bp7-conceptfit-generalize/`) asked whether the trajectory edge is specific to derive-don't-store or a
general property, and tested it on an unrelated axis — **concept-fit** (model each promo rule as a first-class
object vs an `isinstance` type-branch inside the engine) — with a 2-stage build (rules → priority+exclusivity
stacking) across three arms: **plain**, **aims-lite** (a 4-principle prompt block, no method), and **full aims**.

- **Opus 3-arm result: a three-way tie, 0 reopens for all.** Every opus arm — including the un-prompted plain
  arm — modeled rules as first-class objects at stage 1, so the stacking change was a pure seam extension for
  everyone (`total()`'s sum → a sorted walk + exclusivity break; per-rule `discount()` untouched). Correctness
  tied 19/19. On opus the shortcut simply isn't taken, so aims' review had nothing to save. The aims records
  did name the seam and the fresh session used it (Q2 continuity, n=1), but bought no avoided reopen.
- **Base-rate probe: the shortcut IS taken on a weaker model.** 6 haiku plain builds of the stage-1 card:
  **2/6 wrote the `isinstance` type-branch** (the reopen-inducing shortcut), 4/6 polymorphic — vs **0/3 on
  opus**. So the concept-fit shortcut base rate is **~0% opus / ~33% haiku**.

The reading sharpens the whole campaign rather than repeating it. **The edge generalizes off derive-don't-store
onto a second, unrelated axis — but as the identical mechanism (variance reduction on an early structural
choice), and it is model-dependent.** aims' concept-fit edge is *invisible on opus* (a strong model already
picks the good design — the 3-arm null is a **ceiling null, not an absence**) and *real on haiku* (2/6
shortcut → 2/6 avoided reopens). This is the cleanest demonstration yet of the paper's mixed-tier prediction:
the review's value scales inversely with how good the raw executor already is. **aims-lite tied** here only
because the opus environment couldn't discriminate any delivery (all arms derived) — a weak, inconclusive
datapoint for lite, not a win. Across three axes (derive · ledger · concept-fit) and two tiers, the honest
constant holds: **correctness ties; aims' benefit is avoided-reopen variance reduction, sized by the shortcut
base rate on each axis×model (~0–17% strong, ~33% weak here).**

# Round 10: BP8 — aims-lite (principle injection) does NOT transfer to a weak model; the review is the load-bearing part

BP8 (`bp8-lite-baserate/`) put the campaign's most attractive improvement candidate — **aims-lite**, a
lightweight principle injection (BP3 showed the derive-don't-store sentence transferred on opus) — to its
critical test: does prepending the concept-fit principle *lower* the shortcut rate on the weak model where the
edge is largest? Six haiku plain builds branched **2/6** (BP7); six haiku builds **with the explicit
concept-fit principle** branched **2/6** as well. **No effect — 2/6 → 2/6, zero signal of reduction.**

This flips the earlier optimism into a sharp, honest boundary. The principle transfers on a **strong** model
(BP3, opus) and does **nothing** on a **weak** one (BP8, haiku) — i.e. aims-lite helps only where the executor
is already good enough that the base shortcut rate is ~0, and fails on the tier where the shortcut rate (33%)
and thus the potential edge is highest. A principle a model can ignore is not a substitute for a step that
**inspects the artifact**. That step is aims' **mandatory review**, which reads the built code and rejects the
type-branch — the part a prompt line cannot replicate on a model that doesn't self-apply advice. So the
method's irreducible value, on weak executors, is the review, not the advice; BP9 tests that directly by
running a review pass over the two branched haiku builds. (n=6 per arm, one card/model/axis; null is real but
small-sample.)

# Round 11: BP9 — the review catches (4/4) what the principle missed (0/6); output inspection is aims' irreducible value

BP9 (`bp9-review-vs-principle/`) closes the BP6–BP9 arc. It ran the real aims review instrument
(`references/review.md`), applied by a competent Guide (opus) as the mixed-tier architecture intends, over the
**4 branched builds** the weak model (haiku) produced — the very outputs the aims-lite principle failed to
prevent. **The review flagged the type-switch as a structural finding on all four (detection 4/4)** — naming
the anemic-rules / type-code-switch / OCP-reopen defect and the exact repair seam (polymorphic
`rule.discount(cart)`), by section — where the principle-in-prompt scored **0/6**. Applying the recommendation
to one build (b1) yielded a polymorphic module passing the hidden suite **12/12** with zero `isinstance`
(repair validated). The review also caught representation-leak defects the metric never looked at, including a
genuine cross-boundary violation in b2 that gates (S4).

Two honest qualifications: the type-switch itself rates **S3 (structural, non-gating)** — so the review
reliably *surfaces and names* the shortcut and its fix, but at the gate it informs rather than forces (only b2
BLOCKS, on a separate S4). And n=4, one axis/card.

The arc resolves against the convenient answer: **aims cannot be compressed to a prompt of principles for a
weak executor** — the principles don't stick (BP8, 2/6 → 2/6) — but its **review** does the job that advice
cannot, catching the shortcut on weak-model output (BP9, 4/4). aims' irreducible, non-transferable value is
**output inspection by a competent Guide**, exactly the mixed-tier configuration the paper argues for: cheap
Worker builds, competent review catches what the Worker (and any ignored prompt line) missed.

# Round 12: BP10 — the correctness claim has no target on clean specs (0/12 bugs, even on haiku)

BP10 (`bp10-correctness-baserate/`) went looking for the one thing every prior pilot lacked — a **correctness**
difference, aims' headline claim. Two determinate, classically error-prone corners, each built 6× by plain
haiku: a half-open interval boundary (touching bookings must not overlap) and a remainder allocation
(`split(n,k)` must sum exactly to n). **Bug rate 0/12** — every build used the strict overlap predicate and
distributed the remainder. With no bug to catch, the "does aims' review catch it?" arm correctly did not run.

The null is the finding, and it is the third confirmation (with I1 and I4) of a robust boundary: **on
clearly-specified corners a capable model — even the cheap one — does not lose correctness, so aims has no
correctness deficit to repair.** aims cannot win a correctness contest that has no loser. The plant→mineral loss
that motivated the correctness thread was a **slip under specific conditions**, not a systematic failure a small
blind A/B reproduces. This locks in the campaign's honest shape: on tractable, clearly-specified work aims'
benefit is **structural/trajectory** (variance reduction on the early design choice), **not correctness**;
correctness ties because the base is already right.

# Honest limits / future work

- **A concrete, motivated improvement candidate surfaced by BP9 (not yet shipped, by discipline):** the
  type-code-switch / OCP-reopen finding currently rates **S3 (non-gating)** even when the reopened change-axis
  is **explicitly named by the spec/goals** and served by a foreseeable near-term item. One could argue that
  *spec-named-change-axis + forced reopen* should gate (S4). This is exactly the kind of weakness-prompted
  tweak the campaign's discipline (Pavel's rule) says must **beat base on an unseen product before entering the
  method** — it is recorded here as a candidate to test, not a change to ship reflexively (raising a gate risks
  over-blocking correct-but-simple code; it needs a blind A/B showing it catches real reopens without false
  positives).

- The input-space-table question is closed (null on 3 products); the record-layer question is **not** cleanly
  answered (I5's null is confounded by an in-code precedent). What remains, and needs a heavier **build-pilot**
  setup rather than a design-only or single-module A/B: aims' **cost** (2.5–3× — the paper's main downside),
  and the **record layer at a scale where the pattern is not visible in the code** (the paper's stated
  frontier). These are a dedicated run, not a rushed appendix to this one.
- I2 is n=1 on one seed; a second seeded product could still surface value, but on the evidence it is a null.
- I3 changes measurement *policy* from the record; it is validated by discrimination, not by a fresh blind
  run, and keeps both readings so it is fully reversible.
