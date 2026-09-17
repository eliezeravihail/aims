# Reviewing Worker results

The Guide **measures** the result against the handoff's exit criteria. A review here informs the next
direction; it is not a gate on the Worker. What the measurement shows feeds the Guide's next-objective
choice — never a verdict that forces compliance.

**There is one measurement instrument: the assessment form** (`references/measurement.md`) — one row per
principle §1–§18, each scored 0–10 from binary sub-checks, every deduction cited. The in-loop review,
`/aims-review`, and any comparison of designs all fill this same form; they differ only in the projection
shown. The subtractive and concept-fit passes below are how you fill §12 and §2 — passes *within* the form,
not a separate measurement.

## A design gets one mandatory revise round — measure, return findings, revise

A **`design` objective is never read as met on its first returned pass.** **One** **measure → return the
findings → revise** cycle is mandatory before a design can read `met`. This is the single largest quality
lever the experiments measured, and the evidence is specifically for **one round**: it rescued the worst
checkout arm from an S4 correctness gap (2.0 → 3.5) in a single review-and-revise pass
(`decisions/0011`, `../../experiments/iter-plan/README.md`). Concretely, on a returned design:

1. Measure it — the exit criteria, plus the **subtractive** and **concept-fit** passes below.
2. Return the findings — a leaked boundary, a concept mismatch, an unowned rule, unpaid seam machinery, an
   unproven coverage claim — as the refined direction, and have the Worker revise. Do this **even when the
   first pass already looks good**: the mandated round is what most improves a design that "looks met", so
   it runs regardless. (If the measurement genuinely surfaces nothing substantial, the round is a
   confirming re-read, not busywork — but it is still taken, not skipped.)
3. Re-measure the revision, then read met/unmet.

The mandate is **one** round, not open-ended iteration — that is what you asked for and what the evidence
covers. If that one round still leaves a substantial finding, the ordinary loop continues toward the
objective exactly as it always could (`SKILL.md` step 6); nothing here forces convergence.

This stays **direct-and-measure, not a gate**: the findings are the next direction and the Worker revises —
the same move the loop already makes for an unmet objective. What is mandatory is only that the Guide may
not declare a design `met` without having taken the one revise round; the review still reports and informs,
it does not stamp accept/reject or police the Worker (`SKILL.md`, "Direct and measure — do not coerce"). It
applies to `design` objectives (including the opening panel-plan round's merged result); `implementation`
and `refactoring` objectives keep their single correctness/behavior-preservation measurement — a revise
round there only re-runs passing checks.

## How the review is presented — the build-time projection

Fill the form (`references/measurement.md`), then show the **building projection**: only the rows **below
10**, sorted **most-severe-first**, each its principle + citation + the direction to fix it. **Do not show
the aggregate score.** A design carrying a correctness or ownership fault (§9/§13) heads the list; cosmetic
nits trail it.

Not showing the score in the loop is a **practical device, not a principle** (`decisions/0014`): during
construction the Worker should fix *content*, and a visible number invites polishing the number instead.
The scores still exist underneath — they are simply not what the loop displays. The full scored profile is
shown only when the point is to *compare* designs (ranking arms, tracking a design across revisions).

## Review order

1. Re-read the objective and exit criteria before reading the Worker's suggested follow-up.
2. Check evidence for each material criterion.
3. Distinguish implementation completion from objective completion.
4. Treat newly discovered facts as inputs to objective selection, not automatic TODO additions.
5. Preserve counterevidence: a design cost may be justified.

## Completion rules

Mark a Guide TODO complete only when the underlying outcome is demonstrated.

Examples:

- "Added interface" is not evidence that the intended change or responsibility is localized.
- "Tests pass" is useful but does not prove a boundary unless the tests exercise that boundary.
- "Tests pass" also does not show the suite protects against regression — check that non-trivial
  decisions the diff touches are covered even where they already looked correct, not only the new
  edge cases, and that no test merely restates an assignment, a getter, or a language guarantee.
- "No cycle detected" does not prove responsibilities are coherent.
- A small duplication can be acceptable evidence of deliberate independence rather than a defect.

## The subtractive pass (run this on every returned design)

A design objective reliably produces a domain that is sound at the core and **over-built at the
seams**: value objects that own no rule, guards against callers that don't exist, a "tell-don't-ask"
method that nothing calls, an abstraction placed for a future with no present force. The additive
instinct ("what type would model this cleanly?") does not catch these; you need an explicit
*subtractive* pass — run it on every returned design before its readings inform the next direction. (This
is a required *pass*, not a gate: like the rest of the review it measures and reports; it never stamps a
design accepted or rejected — see `references/review-panel.md`.)

For **every** type, interface, guard, wrapper, or abstraction the Worker introduced, ask one question:

> **What present product force requires this to exist?** If I deleted it, would the ownership of a
> current rule, invariant, or boundary actually be damaged?

- If deleting it damages a real, current ownership — it earns its place. Keep it.
- If deleting it only costs "it's tidier" / "it's more consistent" / "a future change might want it"
  — it is ceremony. Record it as a reading: the next direction is to remove or collapse it.

This is a counter-architecture critique, not a line-count rule. A 25-line class holding four fields
with no behavior, a `Symbol`-guarded constructor on a single-author page, a two-value enum that is a
boolean with a label, an accessor no production path calls — each *reads* as discipline and is in
fact rent paid to nobody. The test is not "is it clean?" but "does its removal break the ownership of
something the product needs today?" Prefer a little duplication to an abstraction that fails this test
(Metz). Apply it hardest to the *edges* — the domain core usually earns its types; the seams are
where the unpaid machinery collects.

A capability the usage scenario requires a user to have — an affordance the product's stated
requirements include — is not machinery this pass cuts: it has a present force (the requirement) and
earns its place. This pass removes *unforced* machinery; making sure the needed affordances are stated
requirements in the first place is discovery's job (see `references/discovery.md`, "Every action implies
its complement"), not a judgment to reconstruct here from the built design.

## The concept-fit pass — is each element the kind of thing it *is*? (run on the design, before code)

Where the subtractive pass asks *should this exist*, this pass asks *is this the right shape for what it
is*. It catches the failure `design-principles.md` §2 names as the **value-correct cram**: an element that
is arithmetically or behaviourally correct while modelled as a degenerate case of a concept it does not
share — the axis-aligned rectangle stored as an `OrientedBox` with `angle = 0`, correct in every number
and wrong in kind.

For **every** element in the design, ask:

> **Is this the kind of thing it is, or a different kind forced into this shape?** In particular: is a
> *decomposition* (a whole partitioned into its parts) being modelled as a *movement* (a step that changes
> a running value), or the reverse? A movement carries a **delta**; a decomposition carries **shares of a
> total**. Forcing one into the other's structure always leaves a tell — an inert member present only to
> make the wrong shape fit: a zero delta, a field that is `None` for every case but one, an entry that
> moves nothing and only restates a number computed elsewhere.

The reason this pass is needed at all: such an element is **correct by value and wrong by concept**. The
numbers come out right, so no test fails and no case breaks — which is exactly why it survives an ordinary
review, and why it is not caught by asking "is this clean?" It is caught only by asking "is this what it
claims to be?" When you find one, the fix is to model the concept by its own nature — the decomposition
*beside* the movement chain, joined at a single shared number, never inside it — and the tell disappears
because the shape now matches the thing.

**Run this on the design, before a line of the body is written** — this is the pass that most rewards
being early. A concept mismatch is legible in the design's own prose (a type's fields, a seam's contract,
an ordered list that quietly contains a non-move); buying it out there costs an edit. The same mismatch
found after implementation costs a rewrite of everything built on the wrong shape, and — because it is
value-correct — it is usually a *latent, architectural* fault: it passes every test today and only forces
the rewrite when a later change leans on the concept it got wrong. Catching it in the design is the whole
point of reviewing the design.

## Mixed-tier execution: a strong review after a cheap implementation

aims already splits *direction* (the Guide) from *execution* (the Worker); that split maps cleanly
onto model cost. Running the Worker on a cheaper model and keeping the review strong is usually
cheaper than running a strong model on the whole task — implementation is the token-heavy phase, a
focused review is not — while still catching what a weaker executor drops. So when the Worker ran on
a cheaper model, do not treat "tests pass" as done: run an explicit **design-fidelity review** (ideally
with a stronger model) that reads the implementation against the design and hunts the specific gaps a
weaker executor leaves:

- a binding design decision that was *claimed in a comment but not wired up* in the code;
- an abstraction the design asked for that exists but is **dead** (nothing in production calls it),
  with the rule it was meant to own quietly inlined elsewhere;
- a boundary the design drew that the code leaks across.

Fix each by making the design's intent real (route the caller through the owner), not by deleting the
intent — unless the subtractive pass says the abstraction should not exist at all. This holds only
while the review stays a *review*: if it turns into re-implementation or many rework rounds, the cost
advantage is gone and a stronger executor was the right call. (Observed directly: a Sonnet Worker
built a difficulty type exactly as designed but left its predicate dead and inlined the rule in the
generator; a strong fidelity review caught and repaired precisely that, at review cost.)

## When the measurement shows the objective not yet reached

These are readings that the objective has not been reached — the Guide takes them as input to the next
direction (continue toward the objective), not as a verdict against the Worker. The measurement shows the
objective unmet when the Worker:
- optimized a proxy metric instead of the stated objective;
- expanded scope without evidence that expansion was necessary;
- created abstractions not tied to a current force;
- changed preserved behavior;
- claims success without observable evidence;
- diverges from a principle in `references/design-principles.md` in a way that matters for this
  objective (cite which one and why — these are understanding checks, use them the same way).
- models a concept as a kind of thing it is not — a decomposition as a movement, or the reverse — carried
  by an inert member (a zero delta, an always-`None` field) that is correct by value and wrong by concept
  (the concept-fit pass above; this is `design-principles.md` §2's value-correct cram, and it is a latent
  architectural fault, so it is worth a direction even when every number is right).
