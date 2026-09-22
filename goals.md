---
title: "goals"
date: 2026-09-22
---

## Two goals — separate, and never measured together

aims pursues **two** goals. They are different aims, they are served by different machinery, and they are
judged by **different measurements**. Merging them — scoring the record layer on design quality, or
crediting the design method with what a record preserved — is a category error, and the protocol says so
(`experiments/PROTOCOL.md`: Q1 and Q2 are "judged **separately**, never merged into one score").

### Goal 1 — correct design
Make the quality of the code and its architecture an explicit optimization goal **at the design stage** — a
first-class objective the agent optimizes toward, not a byproduct of shipping features.

- **Served by:** the design method — the Guide/Worker loop, `design-principles.md` §0–§14, the review lens.
- **Measured by:** the **§0–§14 rubric scored from the code**, with the S1–S4 gate (`references/measurement.md`;
  `decisions/0021`). Tests are a floor that earns nothing; behavioral change-proxies are gameable.
- **Not measured by:** anything about the records. Records are not the design method.

### Goal 2 — knowledge that does not belong to the code
Keep the durable design knowledge **co-located with the code**, so a later clean session reads the prior
conclusions and builds on them instead of re-deriving — and so what the code *cannot* say stays said.

- **Served by:** the record layer — companions and root records, the anchor, the staleness hook.
- **Measured by:** whether the knowledge **survives and is acted on**: does a fresh session continue from the
  record rather than re-derive; is a change that contradicts a **declared intent** (a non-goal, a rejected
  alternative, a convention with no code trace) detected and reconciled rather than drifting silently.
- **Not measured by:** the design rubric. A record that preserves a decision perfectly changes no structure,
  and that is not a failure of the record.

**Why the split is load-bearing.** The two goals fail in opposite directions. A design can score full marks
on §0–§14 while quietly breaking what the project declared it would not do — the rubric cannot see that. And
a record can do its whole job without moving a single line of code. Any measurement that reads one goal's
instrument as a verdict on the other will report a false result in one direction or the other; this run
produced both mistakes before catching them.

**One shape, three times.** Every measurement error this run made was the same substitution: the thing
aims actually optimizes, replaced by a proxy that was easier to observe. Functional tests stood in for
design quality (`decisions/0021`); then the design rubric stood in for the record layer (the *Withdrawn*
comparisons below); then a structural-convergence result — six agents landing on the same class
hierarchy at ~300 lines — was read as a verdict on records, when it measures how much a strong model
re-derives and says nothing about whether a record was used. None of the three felt like a shortcut at
the time; each felt like rigour, *because* the proxy was the more measurable quantity. The warning sign
is therefore not sloppiness but the opposite — when one candidate measure is conspicuously easier to
observe than the goal, that ease is the thing to distrust, not the justification for adopting it.

## Use scenarios
- **A new product under the method** — the developer runs `/aims-plan-and-build "<product>"` in an
  empty project. aims grounds the product by asking for one concrete start-to-useful-result scenario
  and the day-zero substrate, then loops direct → build → measure per objective, pausing only for open
  product decisions. Ends with working code whose structure was the objective, plus the records
  stating why it is shaped that way.
- **One objective, supervised** — `/aims-plan "<task>"` → read the plan report → `/aims-build` →
  `/aims-review`. The same loop with a stop at every phase, for a developer who wants to approve each.
- **Measuring a change aims did not build** — `/aims-review <branch | diff | path>` over ordinary
  work: reproduced readings against the design principles plus the subtractive pass, with no aims
  history required.
- **Continuing months later** — a fresh session handed a task on `src/render.py` opens
  `src/render.py.md` and the root records, reads the decisions in force, and builds on them instead of
  re-deriving; a source changed since filing makes the read advise re-verification.
- **Adopting aims on an existing project** — `/install-on .` puts the two hooks and the anchor tool
  under `.aims/` and wires `.claude/settings.json`, touching no code and no existing record.

## Evidence status — reported per goal, never as one verdict

### Goal 1 (correct design) — a hypothesis under test, not an established result
The blind design-only pilot
`experiments/aims-vs-openspec/` (vs OpenSpec, n=1) has now been run three times as the method was sharpened:

- **v1** — found **no design-quality advantage for aims**, and it reopened the most of its own structure
  across the evolution (survival 11); see `decisions/0007`. Root cause: the explanation ledger's
  `Adjustment` interface was calibrated (floor/ceiling, `design-principles.md` §2) for one kind of thing —
  a step that changes a running value — and tax, a genuinely different concept (a decomposition: shares of
  a total, not a delta), was crammed into that same interface as a technically-valid but foreign field
  (`Adjustment(delta=0)`) rather than segregated into its own type. §2 already named this failure mode (the
  value-correct cram); nothing made it fire at the interface-design moment.
- **v2** (§2 sharpened) — survival churn halved (11→5) but design quality was still a wash: the cram
  persisted because the check still fired only after the interface already existed, not while it was being
  calibrated.
- **v3** (the **concept-fit pass** added to `references/review.md`, run on the design before code) — the
  interface-cram fault is **gone** from both aims arms: tax is segregated into its own type, a decomposition
  beside the promotion walk rather than crammed into `Adjustment`; no wrong number on any case. Survival:
  aims-panel **1** (decisive best), aims-single 5, OpenSpec 5 — trajectory 11→5→1. Two opposite-prior
  substantive judges **split**: a consequence/future-cost lens ranks the aims arms above OpenSpec; an
  accidental-complexity lens ranks OpenSpec's single-mechanism spec above them. See
  `experiments/aims-vs-openspec/results-v3.md`.

**⚠️ v3 was a flawed experiment** (the design arms could reach `decisions/0007`, which names the exact
fault being tested for) and is superseded by **v4**, a full clean re-run (stages 1→2→3 from scratch, both
aims arms rooted where `/home/user/aims` was never reachable):

- Survival: aims-panel **7** (best), OpenSpec 8, aims-single 10.
- Both aims arms independently caught concept-fit mismatches with **zero exposure** to the tax example —
  including aims-panel drafting the v1/v2 cram itself, mid-derivation, and reversing it unprompted. The
  pass generalizes; this is no longer merely plausible.
- Two opposite-prior substantive judges **both rank aims-panel first** (v3's split did not reproduce
  clean).
- **But** aims-panel's own design has a confirmed, real bug in its SOUTH tax mechanism (reads a per-line
  field that its own earlier stage never populates with what tax needs) — both judges correctly call it
  non-ranking-inverting, but it is real, and fixing it likely erases part of the survival advantage credited
  above. See `experiments/aims-vs-openspec/results-v4.md` for the full, unhedged picture.

Honest current reading: aims **materially improved change-absorption** and the concept-fit pass **causes**
(not merely measures) avoidance of the architectural fault — demonstrated clean in v4, including the pass
firing in real time inside a single design session. Against OpenSpec specifically, v4 is the strongest
result either aims arm has produced — but it ships with a real, acknowledged defect, so "aims wins" is true
of this pilot's measures, not yet of a design anyone should build from unmodified.

The 2026-09 improvement campaign (`experiments/improve-2026-09/`) adds: the edge is **floor-raising and
variance reduction** on an early structural choice, sized by a shortcut base rate that is near-zero on a
strong model; it is carried by the **review** (output inspection), not by injecting principles into a weak
executor; and it is **invisible to functional tests**, which never separate a 43/45 design from a 16/45 one.

### Goal 2 (knowledge that does not belong to the code) — one demonstrated value, one open question
**Demonstrated.** An aims-filed record holds a **declared intent the code cannot**, and that intent is acted
on. In `experiments/improve-2026-09/bp19-aims-filed-records/`, a change request contradicted a filed non-goal
("no targeting on … time window"): **3/3** agents holding the records detected the contradiction and
reconciled it; **0/3** agents with the code alone did, and none could — the non-goal exists nowhere but the
record. Plus the narrower, longer-standing payoff: a durable append-only trail of *why a superseded decision
no longer holds*.

*What the 3/3 does not establish.* Amending a record when a change contradicts it is behaviour the skill
explicitly asks for, so the records arm's 3/3 is in part a measure of instruction-following and must not
be quoted as a clean effect size. The half that instruction-following cannot explain is the **0/3**: no
instruction could have made the code-only arm reconcile an intent that exists nowhere in the code. What
is established is that the contradiction was **detectable at all** on one side and not the other.

**Open.** Whether the record layer also helps a session **re-derive less** at a scale where the pattern is
not visible in the code. Unanswered: at ~300 lines a strong model converges on the same design with or
without records, so the question is untouched there and needs a genuinely large codebase.

**Withdrawn.** Six earlier record-layer experiments (I5, BP15/15b, BP16/16b, BP17) used records written by
hand rather than filed by aims, and are retracted (`experiments/improve-2026-09/AUDIT-record-layer-claims.md`).
Also withdrawn: any reading of a **design-rubric** comparison as evidence about the record layer — that is
the category error this file exists to prevent.

## Non-goals
- Not a background daemon or self-maintaining store: nothing runs between turns except one advisory
  read hook.
- Not an enforcement gate: the method directs and measures; the staleness hook advises, never blocks.
