---
title: "aims vs. OpenSpec — results"
date: 2026-09-16
---

# Results — run once, three arms, design-only, blind-judged

This pilot was **executed**. Three arms (aims / OpenSpec / plain) each designed the same product — a
checkout pricing service — across three staged requirements, each later stage run by a **fresh session**
with no memory of the earlier ones. Nothing was built. The four readings below are never merged into one
score.

**The headline, stated first and plainly: aims did not win any reading, and lost the design reading to
OpenSpec under both judges.** The full picture is more interesting than that sentence, and the honest
qualifications cut in aims' favour on exactly one reading — but the top line is a loss, and it is reported
as one.

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

## Reading 1 — architecture (Q1). Verdict: **OpenSpec**, under both judges.

Two opposite-disposition judges (invariant-ownership and YAGNI) read the three final designs blind, as
X / Y / Z. **Both returned the same verdict: X = OpenSpec.** Both placed **aims last**. Two opposite
dispositions agreeing is the protocol's signal that a verdict is structural, not a taste artifact
(PROTOCOL §6.3).

Ordering, both judges: **OpenSpec > plain > aims.**

The deciding structural fact, and it is the same in both reports: on stage 3 the arms split on how a tax
law is expressed.

- **aims** made tax **a delta inside the explanation chain** and expressed each market's tax as a
  polymorphic rule *class*. Two costs followed, both in aims' own text: "sum of the deltas" stopped meaning
  "the discount", so aims had to re-cut its own fold to filter by kind (its own documented consequence);
  and a third market becomes a new class rather than a data row.
- **OpenSpec** and **plain** both kept tax **out** of the delta chain, joined at a single number, and
  expressed a tax law as one function branching on a **data profile** — so a third market is a table row.
- **OpenSpec edged plain** because its total-computing fold names no promotion kind, no market and no tax,
  and because plain (Z) carried an audit/`derivation` surface on its tax record that the stateless
  calculator can never use — an over-build the YAGNI judge flagged as plain's one unearned structure.

This is aims' home reading — the design principles the judges used are aims' own (`design-principles.md`).
It lost it anyway, and lost it on a decision aims' method actively led it toward: making the explanation
the single source of truth, which is a genuine aims strength at stage 2, is the very move that put tax in
the wrong place at stage 3.

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
   discipline (OpenSpec), or than a capable agent told only "design it well" (plain).** It produced a
   *worse* one on the design reading and reopened more of its own structure across the evolution. This is
   the single most informative result for aims, and it is negative.
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
