# Add-feature principles — changing existing code

The professional checklist for **changing code that already exists** — the `add-feature` Kind — used both to
do the change and to grade it. The name is deliberate: the common task here is *adding a feature to*, or
*adapting*, a working system — which **changes behavior**, and so is a different thing from *refactoring*
(behavior-preserving clean-up), even though a good add-feature change often does a refactor first to make
room. It is the brownfield companion to [`design-principles.md`](design-principles.md): that document says
what a *correct structure* is when you build from nothing; this one says what a *correct change* is when a
working system, its behavior, and its recorded decisions are already there. Comprehension checks, not
metrics — none is computed from a diff size or a tool.

**Why a separate document.** Adapting existing code is a different kind of task from first-time design, and
its dominant risks are different. Greenfield's danger is *too little structure*; a change's dangers are
**silent behavior drift**, **changing code you do not understand**, **scattering a rule while patching it**,
and **bolting the new requirement on instead of reshaping to absorb it**. A checklist tuned for a blank file
does not catch these — it assumes the freedom to shape everything, which you do not have here.

**Two kinds of change this covers** (name which one the task is):
- **Add-feature / adaptation** *(the common case)* — absorb a **new requirement** into existing code:
  behavior *does* change, and the existing structure must be reshaped to take the change cleanly. Most
  "change requests" are this — hence the Kind's name.
- **Pure refactoring** *(a sub-case)* — improve structure with **observable behavior preserved** (remove a
  named smell, create a seam). No behavior changes; it is often the first move of an add-feature change (§0),
  and §11 grades it on its own terms.

**How it is used.** Doing the change: make each item hold. Grading it: score each as a binary, cited
sub-check, worst-first — the same severity mechanics as the design form (`measurement.md`), with the
**correctness classes** below. Where a change also creates or reshapes structure, the relevant
`design-principles.md` items still apply to that structure — this document adds the change-specific
disciplines on top; it does not replace them.

- **Preconditions** (a violation makes the change *wrong*, not merely untidy, and caps hardest): §1
  characterize-before-touch; §4 behavior preserved out of scope; §5 one owner survives the change; §6
  interaction re-trace where the change crosses an existing rule.
- **Quality** (a violation lowers quality by pervasiveness): everything else.

**What it guards hardest against:** a change that ships a **wrong number in code nobody re-examined** — the
per-line total that no longer sums, the market that used to work and now rounds differently. That failure is
invisible to a "did structure improve / did it reopen little?" reading, which is exactly why it survives one.

**The measure is a before-and-after review, on the target's own terms.** Grade the module's design quality
**before** the change and **after** it; the bar is **no regression — and ideally a small improvement**. A
change is not judged against this document's ideal in the abstract, but against *the codebase it landed in*:
the question is whether *this* module got worse. Rot is cumulative, so what matters most is the **trajectory
across successive changes** — a design that degrades a little on every adaptation is failing even while each
step "works".

**The overriding constraint — match the target's grain (consistency over dogma).** Adapt to the **existing
code's style and level of abstraction**, *even where that contradicts a principle in this document or in
`design-principles.md`*. A plain-functional module gets a plain-functional change; a module that models with
value objects gets a value-object change. Importing a foreign style — wrapping bare-int code in new value
objects, adding a class hierarchy a flat module never needed — is itself a regression: it makes the module
**inconsistent**, which is a worse mess than the local "impurity" it was meant to fix. The goal is **no new
mess**, not conformance to this list. When a principle here and the target's established grain disagree on the
same change, the grain wins (record the deviation as deliberate). This is what keeps the review a *delta on
the target*, not a rewrite toward an ideal.

---

## 0. The two moves, never blurred (refactor, then change)

- **Make the change easy, then make the easy change** (Beck). Separate the **behavior-preserving** step that
  opens room for the change (expose or create the seam) from the **behavior-changing** step that adds the
  requirement at that seam. Do them as two distinct edits, ideally two commits.
- **Never mix them in one indistinguishable edit.** When a restructuring and a behavior change land together,
  you can no longer tell a bug from an intended change, and the characterization tests cannot protect you.
- **If the seam already exists, there is no refactor step** — add the new case as a sibling and stop. Do not
  restructure for its own sake.

## 1. Characterize before you touch *(precondition)*

- **Know the current behavior before you change it.** Capture the behavior you must preserve — with
  **characterization tests** on the paths the change is near, or, where none can be written, an explicit
  behavior inventory. You cannot preserve what you never captured.
- **Pin it, don't trust it.** "It obviously does X" is not characterization; a run that shows X is. The
  surprising current behaviors are the ones a change breaks.
- **Fail fast on unknown load-bearing behavior.** If behavior the change depends on is genuinely unknown,
  the first objective is to characterize it — not to edit blind.

## 2. Build on the recorded design, don't fight it

- **Read the co-located records first** — the companion of each file you will touch, the root records, the
  decisions in force. Build on the recorded conclusion; **supersede a decision in place**, never silently
  contradict it.
- **A change that violates a recorded invariant without superseding it is a defect**, even if it "works."
- **Re-verify a stale record against the code** before relying on it (the staleness advisory is a prompt to
  check, not a fact).

## 3. Locate the seam; extend at it, don't reopen an owner

- **Find where the change belongs**, then choose: a seam exists → add the new case as a sibling there (OCP);
  no seam exists → **first** do a behavior-preserving refactor to create the seam, **then** add the behavior.
- **Reopening a rule's owner to thread a new case is the reopen that later bites** — it is the move the
  survival reading counts. Prefer creating the seam over threading the case.
- **A reopen to *add* an owner a new force genuinely needs is correct** (YAGNI was right to omit it before;
  the force is real now). Adding the owner is not the fault; shipping the wrong number, or scattering the
  rule, is.

## 4. Preserve what is out of scope — exactly *(precondition)*

- **The parts the change does not touch behave bit-for-bit as before.** The market/mode/path that already
  worked keeps its exact outputs; the characterization tests (§1) guard it and pass **unchanged** (not
  edited to pass).
- **Behavior drift in untouched areas is the cardinal sin** of a change — worse than an ugly diff, because it
  is silent and it breaks users who asked for nothing.

## 5. One owner survives the change *(precondition)*

- **A rule that gains a case keeps its single owner.** Absorb the new case *inside* the owner; a parallel
  "special-case" path bolted on beside the normal one silently creates a **second owner** (a buffer enforced
  once in the occupancy model — not again as a separate trailing filter; a discount allocated in one place —
  not re-derived per consumer).
- **Conservation, precedence, and allocation invariants stay owned in one place** through the change: `Σ
  parts == whole`, deny-over-allow ordering, remainder-penny distribution — each guaranteed by construction
  at one owner, never re-computed by each caller.

## 6. Re-trace the full input space the change implies *(precondition where it crosses a rule)*

- **The new requirement crossed with each existing rule implies interactions no stated case exercises** —
  and that is where a change ships a wrong number. Trace X×R over the whole space, not the listed cases.
- **The classic miss:** a requirement that needs an **allocation nobody stated** (an order-level discount
  distributed down to lines so per-line tax lands on the discounted amount, line finals summing exactly to
  the total). A lean change that reopens nothing is exactly the one that never builds the allocation and
  ships `Σ parts ≠ whole` — invisible to a survival reading, caught only by tracing the interaction.
- **An existing reader that now runs on the change's new data shape is in scope — even if the card never
  named it.** A change to the data model (a balance that becomes per-currency, a field that becomes a list)
  can leave an untouched consumer silently *incoherent*: a statement that lists entries across every currency
  while reporting one currency's balance, a report that sums what used to be a single thing. "Preserve
  out-of-scope" (§4) covers a function the change does **not** reach; a reader that now sees the new shape is
  reached, so it is a §6 interaction to re-trace, not §4 behavior to leave alone. Enumerate every function
  that reads the changed shape and check it still reconciles.
- **Adaptation surfaces latent concept-crams.** A concept that was value-correct as a degenerate shape breaks
  when the change leans on the concept it got wrong (`design-principles.md` §4). See §9.

## 7. Absorb, don't accrete

- **Reshape to take the requirement cleanly** rather than adding a flag/branch that merely works. A pile of
  special-case patches is how a codebase rots — each patch is cheap, the accumulation is fatal.
- **But YAGNI still holds.** Reshape for the present requirement, not a speculative future. The forcing
  question is the same as `design-principles.md` §7: name the present force this new structure serves; none →
  it is over-build.

## 8. Migration & representation evolution has one owner

- **A change to a persisted or exposed shape** (a record's fields, a wire/DB schema, an explanation chain) is
  absorbed at **one place**, with old and new coexisting across the transition — not threaded through every
  consumer.
- **Provide a reversible path** where the change is risky: the ability to run old and new side by side, or to
  back out, is part of a correct change to a live system.

## 9. Re-run the concept-fit pass on what the change adds

- **When the change introduces a concept, ask if it is modelled as the kind it *is*** — or crammed as a
  degenerate/synthetic instance of an existing type because that type is already there. Adaptation is the
  **highest-yield moment** for this pass: the existing types exert pressure to cram the new concept into them
  (a cleanup buffer as a synthetic `Booking`, an explicit `deny` as a missing `allow`, a decomposition as an
  `Adjustment(delta=0)`). The tell is an inert stand-in. Fix it by modelling the concept by its own nature,
  beside the existing one, not inside it.

## 10. Small, reversible steps; green between each

- **Prefer many small verified steps to one big rewrite.** Each step keeps the characterization tests green;
  a step that cannot is too big — split it.
- **Delete with evidence.** Removing code or an abstraction is legitimate work in a change — but only when the
  subtractive pass (`design-principles.md` §7) shows nothing present needs it. Dead code found along the way
  is cut with a citation, not left "just in case."

## 11. For a pure refactoring: the smell must actually go, cleanly

- **Name the specific smell** the refactoring targets (from `design-principles.md` §8's catalogue) and show
  it is **demonstrably gone** — not half-removed, not relocated.
- **Introduce no new coupling or duplication**, and **do not weaken a test** to make the refactor pass. The
  diff is structure-only; every characterization test passes unchanged.

---

*Sources: Refactoring and "make the change easy, then make the easy change" (Beck); Working Effectively with
Legacy Code — characterization tests, seams (Feathers); Refactoring — Fowler (behavior preservation, the
smell catalogue); the aims pilots (`experiments/`) — the survival reading, the cart-discount→line-allocation
S4, the booking one-owner buffer, and the value-correct concept-cram family. Structure-quality items not
repeated here live in `design-principles.md`, which this document builds on rather than replaces.*
