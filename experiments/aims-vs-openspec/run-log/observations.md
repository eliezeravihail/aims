# Running observations (operator's notebook, written as things happen)

Kept so that nothing convenient gets remembered into the results afterwards.

**Stage 1 — the plain arm anticipated the axis unprompted.** Its closing section costs out likely next
asks and names *tax* and *a second currency* among them. Nothing in the stage-1 card, and nothing in any
oracle answer, mentions either — this is the arm's own foresight, not a leak. It matters for the survival
reading: if the plain arm's design survives stage 3 well, part of the reason may be that it guessed the
evolution rather than that its structure absorbed it. Check at stage 3 whether the anticipation is
load-bearing (a seam that actually holds) or merely a sentence in a table.

**Stage 1 — the oracle overturned two arms, confirmed one.** BOGO semantics: aims assumed qty//4, plain
assumed qty//3, OpenSpec assumed qty//4. The identical answer overturned two of the three. Malformed
catalogue entry: OpenSpec argued at length for strict whole-file rejection; the owner said the opposite.
Evidence the oracle was not simply echoing each arm's prior.

**Stage 1 — the dangerous question was asked and not answered.** The OpenSpec arm asked whether any code
should be exclusive of others, which is stage 2's non-stackable rule. Answered from stage-1 facts only.

**Stage 1 — cost did not fall out the way the experiment package assumed.** README §4 says "the extra
reasoning a method arm spends is its treatment". On first pass that held (aims 118.5k, OpenSpec 117.3k,
plain 60.6k). Across all rounds it inverted: the plain arm spent 254k over three rounds, because it asked
the most questions and revised the most. Recorded now, before the outcome is known, so it cannot be
reframed later.

**Stage 1 — the state-template fix from today is in live use.** The aims arm filled the `## Open
assumptions` section that did not exist in the template before this morning (Cowork finding 5). It used it
exactly as intended: each stage-1 assumption is recorded as discharged to the ADR that settled it, and the
one thing that is genuinely still unproven (`LinePromotion` has a single implementation) is carried there
rather than filed as knowledge. That is a small, real validation of the fix, independent of how the pilot
turns out — and it is worth saying plainly that it is a *usage* observation, not evidence the section
improves outcomes.

**Stage 1 — the aims arm's ADR discipline held under revision.** Four new ADRs (0007–0010) supersede
clauses of 0004/0005/0006 by name rather than rewriting them, which is what the append-only rule asks for.
Whether that discipline pays anything at stage 2 and 3 is the open question; that it was followed is not.

**Stage 2 — the plain arm's fresh session had a complete inherited document and said so.** Its report
states the repo held only `README.md`, `design/stage-1.md` and one commit, and that stage-1.md "was the
entire inherited context". That is the plain arm's honest condition and it turns out to be a *strong*
one here, because the stage-1 document it inherited is 766 lines and closes fifteen product questions.
Worth stating plainly: "the plain arm has no durable layer" was never true in this pilot — a design
document IS a durable layer. What it lacks is co-location and indexing, not persistence. The pilot can
only measure the difference between *kinds* of written knowledge, not between knowledge and none.

**Stage 2 — the plain arm claims a large survival.** Its own report says `rules` is unchanged "not one
line", `money` unchanged, phase table and invariants I1–I9 kept, and it names the inherited purity of
`evaluate` as what made speculative evaluation free. It also renamed `ledger` to `journal` with a changed
responsibility (append-only matrix) and removed `LineQuote.attribution`. These are the arm's *claims*;
the survival judge counts them independently against both documents. Recorded here as claims, not
findings.

## A confound that goes AGAINST OpenSpec, found at stage 2 — and it is my fault, not the arm's

The OpenSpec arm's fresh session reported that `openspec list --specs` returns **"No specs found"**: the
baseline capability inventory under `openspec/specs/` is **empty**. It is empty because it is populated by
`/opsx:archive`, which runs after `/opsx:apply` — after the code is written. This pilot forbids building,
so **OpenSpec's durable source of truth never comes into existence in it.**

The consequence is concrete, not theoretical. The session could not open a second change with MODIFIED
requirements, because a MODIFIED delta must name an existing path under `openspec/specs/` and there was
none. It had to fold stage 2 into the still-in-flight stage-1 change instead. Its reasoning is sound and
it followed OpenSpec's own update-change workflow — but it means the OpenSpec arm is running with one hand
tied:

- Its Q3 continuity reading is compromised. What its fresh session inherits is a pending change folder,
  not the archived, capability-indexed spec baseline that is the whole point of the method.
- Its Q2 survival reading is distorted in the other direction. Because everything lives in one in-flight
  change that keeps being revised in place, there is no clean stage-1 vs stage-2 spec boundary to diff —
  the arm is being scored on a `design/stage-N.md` snapshot I asked it to keep in step, not on its method's
  own artifacts.

**This is a design flaw in my experiment package, not a finding about OpenSpec.** README §9 declares that
the no-build constraint costs the product reading; it did not anticipate that the constraint also disables
one method's durable layer entirely while leaving the other two's intact. aims files its records during
design; a plain design document exists as soon as it is written; OpenSpec's specs exist only after code
ships.

It must be reported as a limitation that biases **against** OpenSpec, with the same prominence as the
house-rubric bias that goes the other way. Any Q3 verdict against the OpenSpec arm is unsafe and will be
reported as unsafe. The honest fix for a future run is either to let all arms implement, or to run
`/opsx:archive` between stages and accept that archiving an unimplemented change is itself a deviation —
neither is available retrospectively here.

## Verified continuity evidence (aims arm, stage 2) — checked against the file, not taken on report

The aims arm claimed ADR 0003, written at stage 1, had already marked the path stage 2 needed. Checked:

- `decisions/0003-money-as-integer-minor-units.md` was **added in the `stage-1` commit** (2c905c0) and is
  contained in the `stage-1` tag, so it predates the explanation request.
- Its stage-1 text reads: *"Refunds/credits are a non-goal today. If they arrive, they do not bend
  `Money`: they need a signed sibling concept, and a superseding ADR."*
- Stage 2 needed exactly that — the deltas must sum to a negative difference while `Money` stays
  non-negative — and filed `decisions/0012` (`MoneyDelta`) with a supersession pointer appended to 0003.

**This is confirmed, and it is the single strongest continuity data point in the pilot so far.** State the
limits with it: a fresh session was handed a record that named the shape of a change it had not yet been
asked to make, and made that change in that shape. It does not establish that the session would have
chosen worse without the record — that counterfactual is not available from one arm. The plain arm's
fresh session reached a structurally similar answer (an append-only journal, amounts as folds) from a
design document with no ADR machinery at all, which is the honest counterweight and should be reported
next to it.

**Stage 2 — document length is diverging, and it is the plain arm that is growing.** The plain arm's
stage-2 document is 1340 lines, up from 766. It is the longest in every stage so far. This is exactly why
the Q1 judge prompt says, in as many words, that length is not a merit — and it is worth noting that the
instruction was written into the package before any arm ran, not added once the sizes came in. The
survival count is unaffected by length: a longer document does not reduce how many components it had to
reopen.

**Stage 2 — the aims arm volunteered the one place its design cost real structure.** Its report states
that the two-pass contest "is the first place in this design where a requirement cost real structure
rather than fitting an existing seam", names it as the seam it would expect to give way next, and records
it in state.md to watch rather than pre-solving it. Recorded here because a self-reported weakness is
evidence the survival judge should check *against* the arm, not a point in its favour — the judge is told
to count reopenings from the documents, not from anyone's account of them.

## An experimental fault of mine, at the stage-2/stage-3 boundary — aims arm

I tagged stage 2 and dispatched all three stage-3 sessions at 22:15:21. The aims arm's stage-2 session was
**not actually finished**: it produced a second hand-back and kept writing until 22:16:51, rewriting
`design/stage-2.md`, `architecture.md`, `goals.md`, `.aims/state.md`, ADR 0013 and adding ADR 0014 —
after the tag, and after its stage-3 successor had already started reading the tree.

I treated the first hand-back as the end of the round. It was not. The other two arms were clean (zero
uncommitted changes at their tags), so only the aims arm was affected.

**Action taken:** stopped the aims stage-3 session before it wrote anything (`design/stage-3.md` did not
exist yet), committed the true final stage-2 state, re-tagged (fedb1f9, 10,069 words), and re-ran stage 3
from a genuinely fresh session against a stable tree.

**What is still true after the fix, and what is not.** The re-run is clean. But the aims arm's stage-2
round ran to three working rounds where the other two ran to two, because its session chose to keep going.
That difference is real, stays in the record, and inflates the aims arm's stage-2 cost. It is *not* an
extra oracle round — the third round answered no new questions from me; it was the arm continuing to work
on answers it already had.

Recorded because an experiment that hides its operator's errors is worth nothing. Anyone re-running this
should serialize on "the agent is idle AND the tree has been unchanged for N seconds", not on the first
hand-back.

## Correction to my own earlier note: the plain arm's anticipation was WRONG

At stage 1 I recorded that the plain arm had anticipated the axis unprompted — its extension table named
*tax* and *a second currency* among likely next asks — and I flagged that its later survival might be
owed to guessing rather than to structure.

Its stage-3 session reports the opposite. Stage 2's extension table predicted **"Tax → new phases after
30"**, i.e. tax modelled as another promotion-like phase in the pipeline. Having seen the real
requirement, the stage-3 session *rejected that prediction* and argued against it explicitly: a NORTH VAT
row of +3.83 would make C1's deltas sum to +1.33, which is neither what came off nor what is owed, so tax
cannot be an adjustment at all.

So the anticipation was real but **misdirected**: the arm guessed the topic and got the shape wrong, and
its own stage-3 session had to overrule its stage-2 self. That is a point about foresight being cheap and
structure being what pays — and it removes the confound I was worried about, in the direction *against*
my earlier suspicion. The one prediction that did come good was the other one: stage 2 flagged a second
currency as "genuinely a redesign, not a field", and stage 3 reports that flag came due as the market
profile.

Recorded as a correction, not folded silently into the earlier note.

## The three arms split on the central structural question of stage 3

This is the finding the stage was built to produce, and the arms did not converge:

- **plain** and **OpenSpec** both concluded tax **cannot** be an adjustment in the explanation chain, and
  both gave the same reason from the same number: a NORTH VAT row of +3.83 makes C1's deltas sum to
  **+1.33**, which they read as "neither what came off nor what is owed". Both put tax in a second,
  joined account (`TaxView` / `TaxFigure`), attached to the chain at one number.
- **aims** concluded the opposite and filed `decisions/0016-tax-is-an-adjustment-in-the-explanation.md`.
  Its reading: the card says the deltas sum to the difference between the list price and the **final**
  price, the final price now includes tax, and 26.33 − 25.00 **is** +1.33. Internally consistent, and it
  satisfies the card's literal wording.

Neither reading is obviously wrong, which is what makes this worth reporting rather than scoring. It is a
real design disagreement between three capable sessions given identical information, and the Q1 judges
will see all three without knowing which method produced which.

**A process fact that belongs beside it.** The aims stage-3 session handed back twice with *contradictory*
designs: its first report explicitly discarded "tax as a ledger entry" for the +1.33 reason, then it
continued working and reversed itself to the design now on disk. Only the final document is judged, and
the reversal was the arm's own reasoning, not a response to anything I sent — my oracle answers were still
queued and unread when it reversed. But the double hand-back is the same orchestration weakness that bit
me at the stage-2 boundary: a hand-back is not a commitment. I am verifying tree stability before tagging
this time, not trusting the report.

**Operator slip: I opened the mapping early.** My own rubric says `mapping-SECRET.md` stays closed until
every reading is in; I printed it while checking that the same X/Y/Z assignment had been used across all
three stages (it had — identical md5 for all three files). So from this point I know X = OpenSpec,
Y = aims, Z = plain while the judges do not.

Why it is containable, and what I am doing about it: the judges are isolated sessions that never see the
mapping, and their prompts are identical for X, Y and Z and were written before the cut. The exposure is
to *my* framing of the results, not to the verdicts. I am therefore holding to the rubric's ordering —
survival counted first, alone, before any design verdict is read — and the judge prompts below are
byte-identical per candidate. Recorded rather than quietly skipped; it is the third operator error in this
run and they are all in the log.

**Q2 result, recorded the moment it arrived:** X=8, Y=11, Z=9 reopened+discarded. Unblinded: OpenSpec 8,
plain 9, aims 11. The falsifier "the aims arm reopens more than OpenSpec" fired. Written down before the
design judges run, so the framing of the design verdicts cannot be adjusted around it.

**Q3 result:** all three navigated; none re-derived. The differentiator is not persistence but how a wrong
conclusion is retired. Recorded before the design judges have run.

**Deviation: Q1 design judges ran on Opus 4.8, not Fable.** The plan (and the prior plan-diversity
experiment) used Fable as the design judge. Both Fable judge runs hit the account's Fable session limit
(HTTP 429, resets 01:10 UTC) with ~20h to wait. The user chose to switch to Opus rather than wait. So the
two opposite-disposition Q1 judges run on Opus 4.8. This is a third model in the mix (arms + survival/
continuity judges were the arms' own model; design judges are now Opus). Two opposite dispositions
(invariant-ownership vs YAGNI) reading the same three blind documents still catch a taste artifact; what
changes is that the taste is Opus's, not Fable's. Declared in results.md, not smoothed over.

**Q1 YAGNI judge (Opus): verdict X = OpenSpec.** Decisive fact: all three keep tax out of the total-
computer, but on how a tax law is expressed they split — Y (aims) built it as two polymorphic protocol
classes dispatched by type (a new class per market), X and Z as one function branching on a data profile
(a new market is a table row). Between X and Z, X is smaller and adds no audit/derivation surface; Z
carries a `derivation` enum + self-explaining rate/treatment fields justified by an audit the stateless
calculator never provides (the judge flagged that as Z's overstated self-assessment). So on the
simplicity axis: OpenSpec (X) > plain (Z) > aims (Y). aims placed LAST on YAGNI, and the reason is
specifically the polymorphic tax-rule classes plus making tax an entry in the chain (which forced
kind-filtered folds).

**Q1 ownership judge (Opus): verdict X = OpenSpec.** Same verdict as the YAGNI judge, from the opposite
disposition. Both eliminated Y (aims) first, for the same reason: aims put tax as a delta INSIDE the
explanation chain, so "sum of deltas" stopped meaning "the discount" and its own fold had to be re-cut by
kind (aims' own documented consequence). Two opposite-disposition judges agreeing is, per PROTOCOL §6.3,
the signal that the verdict is structural rather than a taste artifact. Ordering across both design judges:
OpenSpec > plain > aims.
