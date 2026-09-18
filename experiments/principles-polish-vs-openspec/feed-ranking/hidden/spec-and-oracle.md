# Feed ranking — hidden spec + oracle (never shown to an arm)

## Architectural axis under test

**Is "how an item earns its place in the feed" modeled as one uniform weighted-sum, or does the design keep
the _kind_ of operation open?** Stage 1 makes a single weighted score look like the whole job. Stage 2
introduces two operations that are **not weights**:

- an **eligibility filter** — a boolean gate that removes an item entirely, and
- a **diversity constraint** — a windowed rule over the *output order*, not over any one item's score.

## The correctness traps (what the judge checks)

1. **Blocked-as-weight cram.** A design that implements a block by pushing the item's score to `-inf` or a
   large negative is **wrong**: a blocked item can still be produced (nothing guarantees absence under
   float/`Decimal` edge cases, and an empty candidate set vs. an all-blocked set become indistinguishable),
   and "absent" is conflated with "ranked last". Blocking is a filter, a different concept from scoring.
   (§4 concept-fit, §5 calibrate-the-interface, §1 functional correctness.)

2. **Diversity-as-penalty cram.** Implementing "no 3 in a row from one author" as a score penalty does **not
   guarantee** the constraint — a high-scored author can still land 3+ in a row. The rule is a property of
   the emitted sequence and must be owned by a sequencing step, not folded into the scalar score. (§1
   interaction coverage, §4 concept-fit.)

3. **Pipeline ownership.** The correct shape is a pipeline with three distinct owners over an ordered domain
   type (a `RankedItem` / `Candidate` with signals): **filter → score/sort → diversify**. Eligibility owns
   the block/mute rule (one place); scoring owns the weighted combination (unchanged); diversification owns
   the windowed constraint. Each rule has **one owner** (§5). A stage-1 design that computed the score inline
   with no seam between "produce a score" and "produce the order" must **reopen** to insert both stages.

## Oracle answers (canonical, if an arm asks)

- "Are weights ever non-linear / learned?" → "No; a weighted sum of the three signals is all stage 1 needs."
- "Can an item have a missing signal?" → "Assume all three signals are present in [0,1]."
- "How large is the candidate list?" → "Hundreds at most; no performance requirement is stated."
- (Stage 2) "Does diversity outrank score?" → "The constraint is hard; within it, preserve score order as
  much as possible."
- (Stage 2) "Is a muted item counted for diversity?" → "No — it is absent; it does not exist in the output."

## Survival oracle (D2)

A stage-1 design **extends** if eligibility and diversity slot in as new stages of an already-seamed
pipeline over a shared item type, with scoring untouched. It **reopens** if the scoring component has to
change to carry filtering or ordering rules, or if there was no item type / no pipeline seam and the order
was produced inline.
