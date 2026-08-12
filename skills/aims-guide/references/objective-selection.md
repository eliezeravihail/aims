# Objective selection

The Guide chooses **one design/quality objective** at a time — one design outcome for the codebase
to reach — not a complete implementation plan and not a feature to ship. This file is the catalogue
of the *kinds* of objectives you formulate. Each is a design outcome; the product change in front
of you supplies the behavior that outcome must satisfy.

## Selection question

Ask:

> Given the current evidence, what uncertainty, structural risk, or missing capability should be resolved next so that subsequent development is less likely to optimize the wrong thing?

The "uncertainty" here can be a **feasibility** uncertainty, not only a design one — and when it is, it
usually outranks every design objective. If the product rests on a load-bearing assumption that is not yet
proven (a brittle or unofficial external integration; an undocumented endpoint; anything whose viability
on the *real target environment* is in genuine doubt), the most important thing to resolve next is not
where a rule should live — it is *whether the ground the product stands on exists at all*. Designing an
elegant boundary over an unproven premise is optimizing the wrong thing: if the premise is false, the
whole design is wasted, and the product likely becomes something else.

So calibrate before you reach for a design objective (see `references/discovery.md`, "Load-bearing
assumptions"):

- **Feasibility is obvious** (a CRUD app, a Monday/Trello-style tool, a second implementation of a proven
  capability) → skip straight to the design objective; do not invent a feasibility question.
- **Feasibility is genuinely uncertain** → the *first* objective is to **prove the assumption with a
  minimal build (an MVP / spike)** — the smallest thing that exercises the risky premise end to end on the
  real target — declared `implementation`, reviewed on whether the premise actually held. The
  ownership/boundary design that assumes it comes *after* it holds, not before.

## Strong objective patterns

These are a catalog, not a lifecycle:

### Clarify behavior
Use when implementation decisions depend on an unresolved product scenario.

### Discover a change axis
Use when the product is expected to evolve but it is unclear what must vary independently.

### Establish an invariant
Use when correctness depends on a rule that should survive implementation changes.

### Establish ownership/boundary
Use when unrelated responsibilities are beginning to change together or knowledge is leaking across components.

### Prove an architectural assumption
Use when the team is designing around a belief that has not yet been demonstrated.

### Build a vertical slice
Use when enough design exists and the greatest uncertainty is whether the chosen structure works end to end.

### Strengthen a failure boundary
Use when failures, retries, partial writes, concurrency, or external services can violate an important product invariant.

### Simplify accidental complexity
Use when abstractions or indirection exist without a present product force that justifies them.

### Localize a known extension
Use when an actual upcoming variation currently requires coordinated edits in unrelated places.

### Preserve a justified cost
Use when a structural cost is real but evidence shows that removing it would make the product worse or more complex. The correct objective can be to document the trade-off and move on.

## Declare the objective's kind

Every objective declares a **Kind**, because it decides how the result is reviewed (see
`references/review-panel.md`). The patterns above partition into three:

- **`design`** — *Clarify behavior, Discover a change axis, Establish an invariant, Establish
  ownership/boundary, Prove an architectural assumption.* The deliverable is a shape; it may ship no
  working feature. Reviewed for whether the structure is right.
- **`implementation`** — *Build a vertical slice, Strengthen a failure boundary.* The deliverable is
  working code conforming to a design already agreed. Reviewed for correctness and conformance.
- **`refactoring`** — *Simplify accidental complexity, Localize a known extension, Preserve a justified
  cost.* The deliverable is a structural change with observable behavior preserved. Reviewed for
  behavior-preservation and whether the named smell actually went.

State the Kind in the objective (it is one of the required fields). A task whose declared kind and
actual deliverable disagree is a defect the review will name first.

## Objective quality test

Reject an objective if:
- success cannot be observed;
- it uses only adjectives such as "clean", "robust", "scalable", or "high quality";
- it contains several independent outcomes joined together;
- it prescribes a named architecture without product evidence;
- it primarily describes file edits;
- it optimizes a metric rather than the underlying product concern.

## The objective is a design outcome; the feature is its constraint

Every strong pattern above is a *design* outcome (an owner, a boundary, an invariant, a proven
abstraction) — not a feature deliverable. That is deliberate. When the product needs a new
capability, the objective you hand down is still framed as the design quality to reach *for* that
capability, with the capability's behavior as the constraint the design must satisfy — not "ship
the capability." The distinction is the whole point: the Worker optimizes toward the objective, so
if you want good design out, the design has to be what the objective names. See
`references/worker-handoff.md` for how to frame it without pre-making the Worker's design.

## Example (unrelated to any particular product domain)

Weak (a bare adjective — unobservable, nothing to optimize toward):

> Refactor this area into clean architecture.

Weak (a feature ticket — the design becomes whatever survives shipping it):

> Add SQLite storage so the user can pick a backend at startup.

Strong (a design outcome, behavior as its constraint, the how left open):

> Establish one owner for the observed rule that is currently implemented in two paths, while
> preserving both paths' behavior. Demonstrate the ownership by exercising both paths against the
> same rule.
