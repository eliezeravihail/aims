---
title: "Synthesis — what the 2026-09 improvement campaign established"
date: 2026-09-22
---

**Current conclusions only.** The round-by-round history, including every correction, is in
[`LOG.md`](LOG.md); each run's own result is linked from [`../README.md`](../README.md). Where a conclusion was
revised during the campaign, only the revised one appears here.

# The two goals, and how each is measured

aims pursues two goals, and the campaign learned the hard way that they must be measured separately
([`../../goals.md`](../../goals.md)):

- **Goal 1 — correct design**, served by the design method (the Guide/Worker loop, the principles, the review)
  and measured by the **§0–§14 rubric scored from the code**.
- **Goal 2 — knowledge that is not in the code**, served by the record layer and measured by whether that
  knowledge **survives and is acted on**.

They fail in opposite directions: a design can score full marks while breaking a declared intent the rubric
cannot see, and a record can do its whole job without moving a line of code. Reading one goal's instrument as
a verdict on the other gives a false result. This campaign made that mistake in both directions before
catching it.

# Goal 1 — correct design

**Tests do not measure design.** Passing is a floor that earns nothing. Two designs passing an identical suite
scored **43 vs 16** on the rubric, blind and from the code ([`bp14`](bp14-design-rubric/results.md)). Behavioural
proxies — reopened owners, edit locality — are gameable too: a capable model absorbed a change with a
three-line seam edit and zero reopens while leaving a textbook type-switch in place
([`bp13`](bp13-design-under-surprise/results.md), part 1). → `decisions/0021`.

**Design quality is real, and it shows on the right change.** Builds that pass every test but dispatch on type
reopen their engine when a new rule kind arrives (4/4); polymorphic builds add a class (0/2), at identical
test results ([`bp13`](bp13-design-under-surprise/results.md), part 2).

**The review is the part of aims that carries its weight.** It flagged all four green-but-badly-built designs
from the code alone (4/4, [`bp9`](bp9-review-vs-principle/results.md)), where the same principle written into
the Worker's prompt had not prevented them. On a weak model the principle-in-prompt did nothing (2/6 either
way, [`bp8`](bp8-lite-baserate/results.md)); on a strong model one sentence of it made a plain arm match aims
([`bp3`](bp3-hint-transfer/results.md)). What does not compress into a prompt is the **inspection of the
output**. → `decisions/0020` names the type-switch / anemic-model pattern as a review gap.

**The edge is floor-raising, not ceiling-lifting.** How often a plain build takes the structural shortcut is
model-dependent: about 1 in 6 on one axis ([`bp6`](bp6-baserate/results.md)); 0/3 on a strong model and 2/6 on a
weak one on another ([`bp7`](bp7-conceptfit-generalize/results.md)). aims' measured benefit is avoiding that
minority — it raises the floor and narrows the spread of design quality. It did **not** compound over
successive changes ([`bp5`](bp5-ledger-compounding/results.md), [`bp2`](bp2-inventory-haiku/results.md)).
*(These runs counted reopens; read under the corrected measure they describe a spread of design scores, the
same finding in the right currency — [`REEVALUATION.md`](REEVALUATION.md).)*

**There is no correctness gap to close at pilot scale.** No-method builds made no errors on clear specs (0/12,
[`bp10`](bp10-correctness-baserate/results.md)), nor on a deliberately designed interaction corner (0/6,
[`bp11`](bp11-interaction-corner/results.md)).

**Method changes tested and not adopted:** an input-space table ([`i1`](i1-input-space-table/results.md),
[`i4`](i4-table-unstated-corner/results.md)) and a falsification review pass
([`i2`](i2-falsification-review/results.md)) — the shipped method already did what each added. A change to
measurement policy ([`i3`](i3-outcome-first/validation.md)) was shipped and then retracted — see below.

# Goal 2 — knowledge that is not in the code

**A record holds a declared intent the code cannot, and that intent is acted on.** A change request
contradicted a non-goal filed by aims ("no targeting on a time window"). All three agents holding the records
caught the contradiction and reconciled it; none of the three with the code alone did, or could — the non-goal
existed nowhere but the record ([`bp19`](bp19-aims-filed-records/results.md)). The 3/3 is partly
instruction-following; the **0/3** is the half no instruction explains.

**On small code a record does not change the design.** In the same run all six agents built the same class
hierarchy, with records or without. At that scale a strong model recovers a rule or convention from the code
itself; what it cannot recover is what is *absent* from the code, which is exactly what a non-goal is.

**Most of what a design session learns belongs in the code, not in a record.** 62% of a companion aims filed
before the rule existed restated its own docstrings. With the code-first gate an agent dropped 8/8 items the
code already carried and kept 6/6 it could not, matching a prediction registered before the run
([`bp21`](bp21-code-first-gate/results.md)). → `decisions/0022`.

**The rule, stated plainly.** Discussions and decisions not evident from the code itself go in a `.md` file next
to what they are about — beside the file, in the module's folder, or at the project root if they concern the
whole project; everything else belongs in the code's own documentation. → `decisions/0026`. Running that rule on
the campaign's own work declined 10 of 14 items as already carried and found four real defects in the guidance
([`bp22`](bp22-gate-on-itself/results.md)).

# What changed in the method

| change | why |
|---|---|
| `0020` — the type-switch / anemic-model pattern named as a review gap | the review caught it 4/4 where the prompt did not |
| `0021` — a design comparison leads with the rubric scored from the code; tests are a floor | tests and proxies both failed to separate designs the rubric separated |
| `0022` — a record holds only what the code cannot | 62% restatement before; 0% with the gate, nothing valuable lost |
| `0023` — the single-root-file alternative is open, not rejected | the run that seemed to decide it was invalid |
| `0025` — cross-cutting learning goes in the root record it concerns | supersedes `0024`, which claimed a gap that does not exist |
| `0026` — a record sits beside a file, a folder, or at the root | knowledge true of one folder had no home |

# Retracted during the campaign

- **`0019` / `i3`** — leading a design comparison with behavioural proxies. It demoted the rubric beneath
  measures that `bp13` then showed to be gameable. Superseded by `0021`.
- **Six record-layer runs** (`i5`, `bp15`, `bp15b`, `bp16`, `bp16b`, `bp17`) and **`bp18`**'s conclusion. The
  records in them were written by hand to a model aims never had, so they tested that construction, not aims
  ([`AUDIT-record-layer-claims.md`](AUDIT-record-layer-claims.md)).
- **`0024`** — a claimed gap in the record format. There was none.

# Cost

≈**1.85–2.34× tokens** against a no-method build across the campaign's two measurements
([`bp1`](bp1-inventory/results.md), [`bp12`](bp12-cost/results.md)); wall-clock 3.7–12×, worst on small tasks,
where aims' fixed overhead dominates. The paper's own study measured 2.5–3×. aims pays that on every build to
avoid a structural shortcut on the minority where one would be taken — the mixed-tier trade the method is
built around: a cheap Worker plus a competent review.

# What is still open

1. **Does aims produce better design at a scale where the right design is not obvious?** Every task here was
   small enough for a strong model to converge unaided. This is aims' central claim, and it is untested.
2. **Does a record stop a fresh session re-deriving**, on code large enough that the pattern is not visible?
   `bp19` showed a contradiction being *caught*; this other half is untested.
3. **Are per-file companions worth their cost over one root file?** Given that most knowledge now belongs in
   the code, what remains for records is rare — which is the premise of the single-root-file proposal
   (`0023`).
