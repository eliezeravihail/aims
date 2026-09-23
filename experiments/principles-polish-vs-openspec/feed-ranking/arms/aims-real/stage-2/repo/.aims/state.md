# aims Guide State

## Mode

auto

## Loop cursor

done:awaiting-human — D2 (stage-2 design) met after the mandatory revise round. Design only per operator
instruction: stop before implementation. Next product change or an implementation objective (build stage 1
per DESIGN.md §14 Step 0, then stage 2) waits for the human.

## Current objective

**Kind:** design (the stage-1 product exists only as a design, so the change is a design revision; the
add-feature lens §4/§5/§6 also applies: stage-1 behavior preserved, one owner per rule survives, X×R re-traced)

**Objective:** D2 — absorb eligibility and diversity into the stage-1 architecture as rules that each have
exactly one owner and are modeled as what they are. Eligibility is a filter, never a score. Diversity is a
sequence constraint over the ranked order, never a penalty. Scoring, weights, reload and the one-version
invariant stay untouched.

**Why now:** a new product change has been received. The stage-1 design fixes "order = score desc, id asc"
in one owner (`rank_feed`), and both new rules land on that order.

**Hard decision at the core:** (a) where "never appears" lives so no path can surface an ineligible item,
and whether the filter comes before or after scoring and validation (Q3); (b) diversity reorders a sorted
sequence, so what owns "the order" once it stops being a pure sort key, and how the infeasible tail
behaves (Q4).

**Exit criteria (to finalize after answers):**
- [ ] Buildable: changed signatures and modules in Python and the stdlib, the request/CLI contract for
      the lists (Q1) and the item metadata (Q2)
- [ ] Blocked author / muted topic → absent from the feed, even with the top score; never shown low;
      no sentinel score
- [ ] Empty lists → identical to the stage-1 result (characterization)
- [ ] All eligible items filtered out → empty feed, not an error
- [ ] Diversity: the Q5 examples; same author at 1, 2 and 3+ in a row; interleaved authors; the
      infeasible tail per Q4; deferral preserves relative order; the scores shown are unchanged
- [ ] Diversity runs on the filtered order (a blocked item never "breaks" a run)
- [ ] Ties between same-author items and between different authors still break by id
- [ ] Stage-1 rules each keep a single owner; the rule → owner table is updated
- [ ] Subtractive and concept-fit passes are clean (no -inf weight, no penalty score, no synthetic item)

**Preserve:** everything in DESIGN.md stage 1 (weights, number semantics, version id, reload, errors,
exit codes), except the order rule this change deliberately rewrites.

**Do not optimize for:** a generic rule/filter plugin framework, per-user weights, pagination, stages not
yet revealed.

## Worker handoff

.aims/panel/2026-09-23-stage2/package.md (shared panel package; axis block appended per Worker).

## Open assumptions (unproven — carried, not filed)

- None. Every open point is a PO question in QUESTIONS.md.

## Open Guide TODO

- [x] Receive the PO answers to Q1–Q5 and file them in goals.md
- [x] Panel-plan D2 → merge → measure → mandatory revise round → re-measure
- [x] Rewrite DESIGN.md for stage 2; add a superseding/extending ADR (decisions/0002); update architecture.md
- [x] Stop before implementation (operator instruction)

## Last evaluated result

D1 (stage 1): **met** (decisions/0001).
D2 (stage 2): **met**. Panel of three axis Workers, merged by the Guide (splits in decisions/0002). Round-1
fix-list F1–F6 (.aims/panel/2026-09-23-stage2/fixlist-round1.md) was addressed by the revise Worker. F4 was
applied as amended, because the stage-1 suite pins `signal` on an unknown key. The Guide re-measured:
- the worked CLI example was recomputed independently and matches;
- the run-limit algorithm passes the four goals.md examples, four more cases and 20k random property checks.

The Guide closed two leftovers directly: who writes the `candidates[i]:` prefix, and the trailing newline on
stdout.
