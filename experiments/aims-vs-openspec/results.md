---
title: "aims vs. OpenSpec — results"
date: 2026-09-16
---

# Results — run once, three arms, design-only, blind-judged

This pilot was **executed**. Three arms (aims / OpenSpec / plain) each designed the same product — a
checkout pricing service — across three staged requirements, each later stage run by a **fresh session**
with no memory of the earlier ones. Nothing was built. The four readings below are never merged into one
score.

**The headline, stated first and plainly: aims won no reading. On the design reading it placed third of
three under both judges — but there is no clear winner above it (the two full-rubric judges split between
OpenSpec and plain), and its third place traces to one late coupling decision, not to broadly unclean
code.** The full picture, below, is more textured than a one-line loss, and the honest qualifications cut
in aims' favour on more than one axis; the top line is still that aims led nothing.

## Pins

- aims commit: `3eab41d` (the fix + this experiment package), run from a fresh `/install-on .` clone.
- OpenSpec: `@fission-ai/openspec@1.13.0`; Node v22.22.2.
- Arm model: identical across all three arms.
- Judge models: **survival and continuity** on the arms' model; **the two Q1 design judges on Opus 4.8**,
  not Fable — see *Deviations*.
- Dates: 2026-09-15 (arms) / 2026-09-16 (judging).

## The product and the axis

A checkout pricing service. The single axis its evolution stresses: **who owns the composition of a price**
— the ordered application of adjustments, and where money is rounded. Stage 1: price a cart with three
promotion kinds. Stage 2: every price carries an ordered explanation whose deltas sum exactly, plus
non-stackable promotions with supersession. Stage 3: a second market with an inverted tax model and a
different rounding rule, while the first market keeps behaving to the cent.

---

## Reading 1 — architecture / code quality (Q1). Result: **no clear winner; aims third under both judges.**

This reading was run **twice**, and the correction matters. The first pass used six structural questions
the operator wrote (rounding-place count, tax placement, ordering ownership, extensibility) — a narrow
seam-placement probe that never touched clean-code / smells / interfaces / encapsulation / genericity, and
that happened to concentrate on the one axis where aims made its weakest decision. It returned
OpenSpec > plain > aims under both dispositions. Because the probe did not judge against aims' own
`design-principles.md` as `PROTOCOL` §6.2 requires, it was re-run.

**The corrected reading judges the three blind designs against aims' actual twelve-axis rubric**
(`design-principles.md`: Tell-Don't-Ask, generic interfaces, interface segregation, primitive obsession,
anemic model, cohesion/coupling, leaky abstractions, single responsibility, rule enforcement, duplication
vs wrong abstraction, naming, size), two opposite-disposition judges, every finding carrying a `file:line`.

**The two judges split:**

| Judge disposition | Verdict | aims placed |
|---|---|---|
| YAGNI / simplicity | **OpenSpec** | third |
| invariant-ownership / encapsulation | **plain** | third |

Two opposite dispositions disagreeing on the winner means the design verdict between the top two is a
**taste artifact, not a structural fact** (the inverse of PROTOCOL §6.3's agreement test). So there is no
clear "best design" above aims. What is robust is that **aims placed third under both** — and both judges
pinned that to the *same single decision*, independently:

- **aims folded tax into the explanation chain** (a fourth `AdjustmentKind`, `CartLedger.assess_tax`),
  which dissolved its own "deltas sum to what came off" invariant into per-kind folds and forced a
  documented fold repair. Both judges note aims paid this coupling "for a single-producer guarantee X and
  Z **both obtain without it**" — i.e. the coupling bought nothing the others didn't get for free.
- Tellingly, the **encapsulation-maximizing** judge picked plain over aims *because* plain confines tax to
  an import-checkable boundary while aims pulled tax into the record — so even the disposition that most
  rewards information-hiding found aims' encapsulation weaker here, on this one decision.

**One of the two knocks on aims is contestable on aims' own principles.** The YAGNI judge penalized aims
for two single-implementation tax protocols (`LineTaxRule`/`CartTaxRule`), treating "one impl per class, a
data field would do" as the fault. But `design-principles.md` §2's actual test is *"ask what a second,
legitimately different implementation would need to look like … if you can't describe one that isn't a
trivial variation, the interface is decorative"* — **describable second implementation, not two
implementations already in the tree.** For tax that test is met outright: NORTH (cart-level, half-up) and
SOUTH (per-line, half-even) are two genuinely different tax laws already, and a third market is the
explicitly anticipated axis. By §2's own criterion aims' tax interface is earned, not decorative.

Worse for the judge's reading: X and Z model *promotions* as a rule protocol (three implementations) but
model *tax* as inline data-field branching — two different mechanisms for the same conceptual thing (a
policy that varies by market/kind), i.e. **non-uniform abstraction levels**. aims used the *same* mechanism
(a rule protocol) for both promotions and tax. That uniformity is a real merit the judging never weighed,
and it cuts toward aims, not against it. The honest status of the interface criticism is therefore
*contested*, not settled — and aims' third place on the YAGNI axis rests partly on a criterion §2 does not
endorse.

**What does stand, independently, is the other knock:** aims folded tax *into* the explanation chain (a
fourth `AdjustmentKind`, `CartLedger.assess_tax`), which dissolved its own delta-sum invariant into
per-kind folds and forced a documented repair — a coupling the other two arms avoided while getting the
same single-producer guarantee. Both full-rubric judges flagged this one independently, and it is the same
decision that drove roughly half of aims' extra survival churn. **aims' real, defensible loss on this
pilot is that one coupling decision — not the interface count.**

**aims was not broadly unclean — the opposite.** Both judges credited it with the **least primitive
obsession** of the three (it wraps every domain type: `PromotionCode`, `Sku`, `MarketId`, `Percent`), a
`promotions.py` genuinely untouched across the whole evolution, well-argued tax protocols, and the most
explicit subtractive pass (it records what it removed). Its one real cleanliness fault is the *opposite* of
dirt: **over-abstraction** — two tax protocols with a single implementation each where a data field
sufficed, exactly the over-generic case `design-principles.md` §2 warns against. On five of six seam axes
in the first pass, and on most cleanliness axes here, aims was level or ahead; it is third because of one
coupling decision the other two arms declined.

The uncomfortable part for aims, stated plainly: that decision — make the explanation the single source of
truth — is a genuine aims **strength** at stage 2, and it is the very instinct that put tax in the wrong
place at stage 3. The method's own move, over-applied.

## Reading 2 — survival (Q2), the primary reading. Result: **aims reopened the most.**

The countable reading. For each arm, across both stage transitions, every named component and seam of the
earlier design classified against the later one; the score is **reopened + discarded**.

| Arm | S1→S2 | S2→S3 | **Total** |
|---|---|---|---|
| OpenSpec | 4 | 4 | **8** |
| plain | 3 | 6 | **9** |
| **aims** | 4 | 7 | **11** |

**A falsifier named in advance fired.** README §8 listed "the aims arm reopens more than OpenSpec → the
central claim fails on this product" as a disqualifying outcome. That is what happened. aims reopened the
most; OpenSpec the fewest; plain between them. The survival judge also found eleven overstated
self-assessments spread across all three arms — every arm overstated at least one "nothing changed" claim
— so no arm's own narration of its stability survived checking.

## Reading 3 — continuity (Q3). Result: **all three navigated; none re-derived.** The differentiator is
not what aims claims.

Every stage-2 and stage-3 session — fresh, no memory — found and used a specific record written before its
requirement existed, proven with git in each case. aims' strongest single data point is real and verified:
a stage-1 ADR (`0003`) predicted a "signed sibling" type, and the stage-2 session built exactly that
(`MoneyDelta`) and cited the ADR by number. But **the plain arm did the same thing with three markdown
files and no machinery** — no ADR directory, no anchors, no hooks, no state file — and the OpenSpec arm did
it with its change folder.

The judge's decisive finding: **the three durable layers did not differ in whether knowledge survived.
They differed only in what happens to a conclusion that turns out to be wrong.**

- aims marks it superseded in place and keeps the original text — **5 times out of 6** (it missed one
  back-stamp, `0003`→`0017`, leaving a stale clause a later reader would trust).
- plain writes a paragraph headed "Stage 3 gives up one stage-2 claim and must say so" — **3 of 3**.
- OpenSpec overwrites the text, so a superseded claim survives only in git, and the spec format's own
  MODIFIED/REMOVED markers went unused across all three stages.

So aims' continuity machinery earned its keep on exactly one thing the others do more loosely — a durable,
append-only trail of *why a past decision no longer holds* — and even there it slipped once. That is a
narrow, real win for the machinery, on a sub-question, not for the method overall.

## Reading 4 — cost. Result: plain cheapest; the two methods ≈ equal; the gap is small.

Final cumulative tokens per arm (see `../../` note on interpretation in the run log):

| Stage | aims | OpenSpec | plain |
|---|---|---|---|
| 1 | 153k | 160k | 102k |
| 2 | 222k | 196k | 146k |
| 3 | 290k | 276k | 210k |

The plain arm is consistently cheapest, by ~1.3–1.5×. But README §4's assumption that "the method arms'
extra reasoning is the treatment" did not hold cleanly: across question rounds the plain arm asked *more*
product questions than either method (15 vs 10) and revised more, so the first-pass gap (which looked like
2×) shrank once every round was counted. All three arms spend the same order of magnitude, because the
dominant cost is reasoning about pricing, not running a method. Notably, the plain arm produced the
**longest** documents on the **fewest** tokens.

---

## What the pilot shows, stated at the honest altitude

On this product, judged blind:

1. **Making design the explicit goal (aims) did not produce a better architecture than spec-first
   discipline (OpenSpec) or than a capable agent told only "design it well" (plain).** On the design
   reading aims placed third under both dispositions — but the two judges disagreed on the winner, so the
   result is "no advantage for aims", not "aims is worst-quality code". aims' third place is one late
   coupling decision (tax folded into the explanation chain), which both judges flagged independently and
   which the other two arms avoided; on the cleanliness axes aims was often ahead (least primitive
   obsession, cleanest domain-type wrapping). It also reopened the most of its own structure across the
   evolution — and roughly half of that extra churn traces to the same tax decision. The informative
   negative for aims is real: the method showed no design advantage, and its one distinctive instinct
   (explanation as the single source of truth) over-applied into the stage's weakest call.
2. **The one thing aims' machinery uniquely delivered** is a durable, append-only record of *why a
   superseded decision was superseded*, kept beside the code — the plain arm reaches the same live
   conclusions but keeps no trail of the retired ones, and OpenSpec keeps none outside git. Whether that is
   worth its cost is a question this pilot cannot answer, because **the pilot is three stages deep and the
   value of a durable trail is a function of project age.** Restatement (plain) is O(n) per stage;
   navigable records (aims) are O(1). At n = 3 the difference has not bitten. aims' own `goals.md` is
   written for the n = 8 case this pilot never reached.
3. **The plain arm is the finding that should trouble aims most.** Not because it won — it placed second on
   design, middle on survival — but because it matched both methods on continuity with no machinery at all,
   at lower cost. On a product this size, a capable model given a clear brief and told to keep one design
   document is hard to beat, and neither method beat it decisively on anything except the retired-decision
   trail.

## Deviations and limitations (declared, not smoothed)

0. **The Q1 design reading was judged twice.** The first pass used six seam-placement questions the
   operator wrote, not aims' `design-principles.md`, so it never assessed smells / interfaces /
   encapsulation / genericity and it over-weighted the one axis where aims was weakest. It was discarded
   and re-run against the twelve-axis rubric (`run-log/judge-reports/quality-*.md`). The corrected reading
   is the one above. Both passes are kept in the run log for audit.
1. **The Q1 design judges ran on Opus 4.8, not Fable** — both Fable runs hit the account session limit with
   ~20h to wait, and the operator switched models rather than wait. Two opposite dispositions still guard
   against a taste artifact, but the taste is Opus's. A third model is now in the mix.
2. **The Q1 rubric is aims' own** design principles — a house-rubric bias *toward* aims. aims lost anyway,
   which makes the negative result stronger, not weaker.
3. **OpenSpec ran with one hand tied.** Its durable baseline, `openspec/specs/`, is populated only by the
   archive step, which runs after implementation — and nothing was implemented. So its fresh sessions
   inherited the un-archived change folder, not the capability-indexed spec baseline that is the method's
   point. The continuity judge notes this cut *for* OpenSpec here (the change folder carried more rationale
   than the baseline would have), but the survival and design readings scored it on a `design/stage-N.md`
   snapshot the operator asked it to keep, not on its own artifacts. This biases against OpenSpec on two of
   four readings and is a flaw in the pilot's no-build constraint, not in the method.
4. **A design is prose.** The longest arm (plain, 2,009 lines at stage 3) is not the best; the judges were
   told length is not merit, and the survival count is length-independent by construction. This defended
   the readings but is a permanent hazard of judging designs rather than builds.
5. **n = 1 per arm.** Suggestive, not robust. The strength of any aims finding is the *sequence* of pilots,
   not this one.
6. **Three operator errors, all logged** (`log/observations.md`): a stage-2/3 boundary where the aims arm
   kept writing after I tagged (caught, re-run clean); the mapping opened before all readings were in
   (contained — judges never saw it); and the judge-model switch above.

## Artifacts

`cards/` (the three stage cards as delivered), `hidden/spec-and-oracle.md` (the oracle script),
`substrate.md`, `judging/rubrics.md`, and the run log under the experiment's working tree
(`log/oracle-stage{1,2,3}.md`, `log/cost.md`, `log/observations.md`, the four judge reports, and the
blind X/Y/Z snapshots with their sealed mapping). Each judge finding carries a quotation or a `git` proof.
