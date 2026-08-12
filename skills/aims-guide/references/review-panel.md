# The review panel — measuring the outcome, not gating it

aims **directs and measures; it does not coerce.** A review here is not a gate, a verdict, or a
quality police — it is **honest measurement of the outcome against the objective**, whose result *feeds
the next direction*. The Guide (or the human) decides what to do with what the measurement shows; the
review never forces compliance. (aims could not enforce anyway — it steers a model with prose, not
mechanism — and that is the intent, not a gap: see the mission in `SKILL.md`.)

This is the measurement done at `SKILL.md` step 5 as an explicit, escalating pass. It also runs
**standalone** on any diff/branch/PR that aims did not build. It exists because a plain "is this good?"
LLM judgment is a weak measurement: with no second implementation to contrast against, a solo judge
drifts to vague praise and invented grades. What made the experiment judges a *trustworthy measurement*
was not their authority — it was **an adversarial contrast plus reproduction of every reading.** This
panel rebuilds both without a second arm.

## A task declares its kind; the measurement matches it

Every objective declares a **Kind — `design` | `implementation` | `refactoring`** (see
`references/objective-selection.md`), and the review measures the outcome through the lens for that kind.
This matters because *what "good" means, and what evidence would show it, differ by kind* — and applying
the wrong lens is exactly how a review slides into proxy-checking: grading links, parsing, and file
layout when the task was an **architecture**. (That is the failure this whole project exists to prevent;
a typed measurement has nowhere to hide from the architecture question when the kind is `design`.)

### design — *is this the right structure?*
- **Deliverable:** an architecture/shape for the capability — often with no working feature yet.
- **Measure:** does each truth live in exactly one place; is each invariant owned once; are boundaries
  drawn on the real change axes; has any structural assumption already been *falsified* by the product;
  is anything built for a future with no present force?
- **Evidence:** design reasoning and fit-to-forces — **not** tests (a design objective may have no
  runnable code). Check that the design's *claims* match what exists, but measure the shape.
- **Look for:** absent or split ownership, over- and under-abstraction, an unfalsified or now-false
  assumption, speculative generality. *(This is the blind design-judge lens from the pilots.)*

### implementation — *does it correctly realize the agreed design?*
- **Deliverable:** working code conforming to a design already agreed.
- **Measure:** does it satisfy the behavior **and** conform to the design; does every exit criterion
  actually hold on the paths the tests don't exercise?
- **Evidence:** adversarial probes against the exit criteria (the role that surfaces real defects) +
  conformance to the design + the subtractive pass.
- **Look for:** correctness defects, non-conformance, dead abstractions, missing affordances. *(The
  pilot-#4 lens — the one that measured "win design, lose product.")*

### refactoring — *did structure improve with behavior preserved?*
- **Deliverable:** a structural change; observable behavior unchanged.
- **Measure:** is observable behavior provably identical, **and** did the named smell actually go, with
  no new coupling or duplication introduced?
- **Evidence:** the pre-existing / characterization tests pass **unchanged** (not edited to pass); the
  diff is structure-only; the target smell is demonstrably gone.
- **Look for:** behavior drift (the cardinal sin), a half-removed smell, new coupling, tests weakened to
  make the refactor "pass."

If a task's declared kind and its actual deliverable disagree — a "refactoring" that changed behavior, a
"design" objective that quietly shipped a feature — **that mismatch is itself the first reading.** The
roles below serve whichever lens the kind selects.

## The one rule that makes a reading real: reproduced or cited

A reading is not an opinion and never a number. **Every reading carries either:**

- a **reproduction** — a probe/test that actually fails, or a concrete input → wrong output/state; or
- a **precise code citation** — `file:line` of the dead abstraction, the duplicated rule, the leaked
  boundary, the comment that overstates the code.

No scores, no percentages, no "looks solid," no "8/10." A reading without a reproduction or a citation is
not a measurement — drop it. (Inventing quality numbers is the exact failure this whole project exists to
avoid.) The contrast a second arm used to provide is replaced by the **exit criteria / stated intent**:
measure the deliverable against *that* ground truth, not against taste.

## The roles — use what the task needs, scale to it

Do not convene a panel for a one-line change; the Guide's own step-5 measurement is enough. **Escalate**
for invariant-bearing, cross-cutting, evolving, or high-stakes work.

**Where the roles run.** When review is reached by an explicit command (the `review` phase, or a
standalone `review <target>`), run the roles **inline in this session on the currently selected model —
no subagents**; take each lens in turn. Only in `auto` mode may the roles be spawned as subagents (for
independent contexts when no human is watching). The reproduce-or-cite rule is what keeps an inline
measurement honest — not a process boundary.

Roles, in value order:

1. **Probe reviewer (the one that surfaces real defects).** Writes *adversarial probes* against each
   exit criterion and each invariant/boundary — especially the paths the tests don't exercise — and
   reports the failures it reproduces. In pilot #4 this is the role that measured the shipped defects
   (a cross-room promotion that never fired; a series that booked backwards): behavior probed against the
   spec, not code read for vibes.
2. **Fidelity reviewer.** Design claims and comments vs the code: a decision claimed but not wired up, an
   abstraction that exists but is dead with its rule inlined elsewhere, a comment that overstates. (Same
   pass as the mixed-tier policy in `review.md`.)
3. **Subtractive reviewer.** The subtractive pass from `review.md`: for every type/guard/wrapper, name
   the present force that requires it; note the ones whose removal wouldn't damage a current
   rule/invariant/boundary.
4. **Opposite-disposition second reviewer.** *Only* for genuine judgment/taste calls. A reviewer with the
   opposite bias (minimalist vs rigor) re-measures the call, to test that a reading is not a taste
   artifact. If both dispositions land the same way, the reading is robust; if they split, report the
   split rather than pick.

## Measure the reading yourself before you rely on it

LLM reviewers miss defects and can be confidently vague. So the panel's output is a set of *readings* to
confirm, not a ruling: **before the Guide lets a decisive reading inform direction, it reproduces it
itself** — runs the failing probe, opens the cited line. That is exactly how pilot #4's readings were
confirmed. A reading that cannot be reproduced on demand is set aside, not acted on.

## Standalone use (measure any change, no aims loop required)

`review <target>` where target is a diff, branch, path, or PR. Unlike an in-loop review, **nothing has
told you what kind of review this is or what to measure against** — an in-loop review reads the Kind and
exit criteria from `.aims/state.md`, but here there is no state. So the first move is not to review;
it is to *classify*. Applying the wrong lens (or measuring against invented criteria) makes the whole
review measure the wrong thing.

**Step 0 — classify before you review (a required gate, not a formality).** Before producing a single
reading, commit *in writing* to two things, as the first output of the review:

1. **The kind** — `design` | `implementation` | `refactoring` — inferred from the target and its stated
   intent. A change is not always one kind: if the diff genuinely spans kinds (a refactor that also adds
   behavior), name the **dominant** one and apply the extra lens where it applies, rather than forcing
   one. If the kind is unclear *and* which kind you pick would change what you measure, **ask the user
   one concrete question** before going on — do not guess the lens.
2. **The ground truth to measure against** — the change's stated intent / acceptance criteria. If it is
   unstated and material, **ask the user one concrete question** rather than inventing criteria; a review
   against invented criteria measures nothing.

Why a gate and not a subagent: the classification needs exactly the context the review itself needs (the
diff, the intent), and standalone review runs inline on the user's chosen model — a separate classifier
subagent would only re-load that same context and split one judgment across two. Keep it one inline gate.

**Then review.** Take the kind's lens (above), run the roles scaled to the change, and report **what you
measured, not a grade.**

## Output shape

```
Readings (most consequential first):
- <what> — <file:line> — reproduction: <failing probe / input→wrong output> — significance: <one line>
...
Against the objective: <which exit criteria the readings show met / unmet — a description, not a score>
Implication for direction: <what this suggests as the next objective — the Guide/human decides; the
                            review does not accept or reject>
```

No summary score, no accept/reject stamp — the review measures and reports; direction is the Guide's and
the human's call. If nothing survived reproduction, say so plainly: an empty set of readings is a valid,
honest measurement, not a failure to find something.
