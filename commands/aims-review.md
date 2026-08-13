---
description: "aims — run the REVIEW phase: measure the result against the exit criteria with the review panel, producing reproduced readings (no scores). Also works standalone on any diff/branch/PR."
argument-hint: "[optional target: a diff / branch / path / PR to review standalone]"
---

Enter the `aims-guide` skill and run the **REVIEW phase** — which *measures* the outcome against the
objective and feeds the next direction; it is not a gate — following `references/review.md` and
`references/review-panel.md`. **First read the objective's Kind** (`design` | `implementation` |
`refactoring`) and take that kind's lens per `review-panel.md` — a `design` review measures whether the
*structure* is right (not tests), `implementation` measures correctness and conformance, `refactoring`
measures behavior-preservation and whether the named smell went. If the declared kind and the actual
deliverable disagree, that mismatch is the first reading. Two uses, decided by whether a target is given:

**In-loop review (no target given).** Reload `.aims/state.md`; require the Loop cursor at
`executed:awaiting-review`. Measure the Worker's evidence against the objective's **exit criteria**, and
run the review panel scaled to the objective (probe reviewer first; add fidelity, subtractive, and an
opposite-disposition second reviewer as the stakes warrant). Report reproduced readings, describe which
exit criteria the readings show met/unmet, and what this implies for the next direction. Then record
where the loop now is by updating the cursor (`ready-to-choose-next` when the objective is reached, or
back toward `plan`/`build` when the readings say it isn't). **File the round's structural outcome into
the code tree** (`references/design-record.md`): a decision that changed direction is a *new*, superseding
`decisions/` ADR (append-only — never rewrite the old one); a durable lesson is an Insight in the relevant file's companion.
Anchor each. Do not silently repair everything reported — the Guide/human decides what matters now.

**Standalone review (a target is given in the arguments).** Review the target change without requiring
a `.aims/state.md`. Here nothing has told you the kind or the criteria, so **classify first — a required
gate, not a formality** (see `references/review-panel.md`, "Standalone use"). Before any reading, commit
in writing to: (1) the review **kind** — `design`, `implementation`, or `refactoring` — from the target
and stated intent; if the change spans kinds, name the dominant one and add the other lens where it
applies; if the kind is unclear *and* would change what you measure, ask one concrete question first;
and (2) the ground truth to measure against — the change's stated intent / acceptance criteria, asking
one concrete question if it is unstated and material rather than inventing it. Only then take that lens
and run the panel roles, scaled to the change.

Run the panel **inline, in this session, on the currently selected model — do NOT spawn subagents**
(this is an explicit command; the user picked this model and is supervising). Adopt each reviewer lens
in turn, including the opposite-disposition check when the call is a judgment/taste one.

In both uses, obey the panel's core rule: **every reading carries a reproduction (a failing probe /
concrete input→wrong output) or a precise `file:line` citation — no scores, no percentages.** Before a
decisive reading informs direction, reproduce it yourself. An empty set of readings is a valid, honest
measurement.

Target (if any): $ARGUMENTS
