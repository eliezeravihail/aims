# Design principles

The single, professional checklist that defines **what correct code and architecture mean** — used both
to build and to grade. Comprehension checks, not code metrics: none is computed from a line count or a
tool. Organized by topic; each item is one checkable principle.

**This document is the single source of correctness.** Everything else in the method is a *tool* that
*reads* it — the build instructions, the measurement (`references/measurement.md`), the fix-list, the code
review — none defines correctness on its own. (aims rests on one assumption: a model optimizes the goal it
is given, not the instructions it is handed; so if you want correct code you make correctness the goal, and
this list is what "correct" means. See `SKILL.md`.)

**How it is used.** Building: make each item hold by construction. Grading: score each item as a binary,
cited sub-check; `measurement.md` turns the results into a number. The scoring reads each item's
**correctness class** from here — it does not redefine it:

- **Preconditions** (a violation makes the code *wrong*, not merely less clean, and caps the result
  hardest): all of §1; §5's one-owner-per-rule and the module-seam rules of §0 and §5; §11
  concurrency-safety under real concurrency; §14 where a trust boundary exists.
- **Conditional** (scored only where the product states the need): §13 (performance), §14 (security).
- **Code-leaning** (N/A on a pure design document): §12 (testability), the runtime items of §11.
- **Quality** (a violation lowers quality by its pervasiveness): everything else.

**What it guards hardest against:** the dominant failure of unguided generation is *too little structure* —
flat code, inline literals, primitive obsession, anemic bags, unowned rules, modules reaching into each
other. Over-engineering is a lighter, secondary fault. When unsure, the graver risk is too little structure.

---

## 0. Foundational principles (they dominate the rest)

- **Encapsulation behind an exposed interface — the primary discipline.** A module exposes an interface
  outward and hides its internals, so it is maintained and changed independently without breaking its
  callers. Build in **small, well-bounded parts** — what keeps a design tractable to write, review, and
  (critically for an LLM) generate correctly.
- **Across a module seam, speak only published types — never a concrete implementation.** Between large
  modules (e.g. a dataset → a model → a measurer) exchange a shared foundational object, or the *other
  module's published, generic type* (e.g. `OrientedDataset`) — never a specific implementation of it
  (e.g. `CvOrientedDataset`). A module never references a class living inside another module.
- **Inside a module, build on foundational value objects.** Small foundational types (e.g. `OrientedBox`,
  `Point`) are the working currency between a module's own classes.
- **Where foundational objects come from.** Either defined up front as part of the interfaces, or taken from
  foundational libraries that will never be replaced (e.g. a numpy tensor — a dependency fixed before the
  design). Both may cross seams.
- **When in doubt, add an interface, don't omit it.** A missing seam later forces exposing an implementation
  or a breaking internal change; a spare seam is a light, local cost. (When this collides with YAGNI on the
  same element, the tie-break in §7 decides it by the change-axes — not by taste.)

## 1. Correctness & contracts *(precondition)*

- **Functional correctness** — produces the required result for every specified case and every interaction
  they imply (a change-axis crossed with a rule).
- **Contracts** — each operation states its preconditions, postconditions, and invariants; the invariant
  holds before and after.
- **Edge & boundary coverage** — empty/one/many, zero/negative/overflow, ordering, duplicates, the absent
  optional, time.
- **Fail fast** — reject an invalid state at the boundary, at once, with a clear error; never propagate a
  bad value.
- **Defensive at the edge, trusting inside** — validate untrusted input once at the boundary; the core
  assumes valid inputs.
- **Trace the full input space (the procedure, not just the cases)** — verify every acceptance case, and
  for each change-axis (X) crossed with each rule (R) the interaction it *implies*, over the whole input
  space — not only the listed cases. This is the step that surfaces a required output no stated case
  exercises; skipping it is how a clean design ships a wrong number.

## 2. Functions & control flow

- **Do one thing** — a function has a single, well-defined job.
- **Single level of abstraction (SLAP)** — a function mixes only one altitude; high-level steps don't sit
  beside low-level detail.
- **Command–Query Separation** — a function either changes state or returns a value, not both.
- **Few parameters, no flag arguments** — long lists and boolean flags signal a function doing too much.
- **Guard clauses over deep nesting** — return early; keep nesting and cyclomatic complexity low.
- **No surprising side effects** — an effect the name doesn't imply is a defect.

## 3. Naming, comments & readability

- **Intention-revealing names** — the name says what it is/does; searchable, pronounceable.
- **One word per concept** — consistent vocabulary; no synonyms, noise words, or encodings.
- **Comments say *why*, not *what*** — explain intent/trade-off the code can't; delete redundant or
  commented-out code.
- **Comments stay true** — a comment that contradicts the code is worse than none.
- **Failure speaks the consumer's concept** — an error message says what happened and what to do, in the
  reader's terms, not an internal variable or a raw exception.

## 4. Types & domain modeling

- **Value objects over primitives** — a concept with rules/identity gets its own type, not a bare
  string/int.
- **Rich domain model** — objects own their behavior and enforce their rules; not data bags with logic in
  "managers." Tell-Don't-Ask: tell an object what to do, don't pull its state and decide outside it.
- **Make illegal states unrepresentable** — model with sum types/enums so invalid combinations can't be
  built.
- **Concept fit** — model a thing as the kind it *is*, not as a degenerate or synthetic instance of a
  neighbouring type. The cram is value-correct and concept-wrong, so it passes every test and only breaks
  under a later change; its tell is always an inert stand-in. It recurs in several shapes: a decomposition
  forced into a movement (tax as an `Adjustment(delta=0)`), a distinct concept forced into a neighbouring
  entity (a cleanup buffer as a synthetic `Booking`), a first-class effect modelled as the *absence* of
  another (an explicit `deny` as a missing `allow`), a filter or sequence rule modelled as a score (a
  blocked item as a `-inf` weight).
- **One abstraction level per family** — peers share a conceptual altitude (LSP); no member that is really
  an implementation detail.
- **Immutability by default** — prefer immutable values; mutation is the justified, localized exception.

## 5. Encapsulation & information hiding

- **Program to an interface** — expose an owned abstraction (a domain type), never a concrete
  implementation type.
- **Calibrate the interface** — the crossing type is the most generic still complete for the consumer and
  producible by every implementation (floor = consumer's need, ceiling = weakest producer).
- **Information hiding** — expose the least; hide representation and decisions likely to change.
- **Law of Demeter** — talk to immediate collaborators; don't reach through object chains.
- **Errors are boundary vocabulary** — at a public seam, translate an implementation exception into the
  module's own error type; define one error type per distinct handling (no dead subtype nobody catches);
  let an unactionable, process-fatal failure fall rather than wrap it.
- **One owner per rule** *(precondition)* — each stated rule has one home and one path all callers use. A
  design intent, not a language-enforced guard (a dynamic language can always be tricked; the point is that
  the intended paths funnel through one place). When a rule **gains a case under a change**, absorb the new
  case in that one owner; a parallel "special-case" path bolted on beside the normal one silently creates a
  second owner (a cleanup buffer enforced once inside the occupancy model — not again as a separate trailing
  filter).

## 6. Coupling, cohesion & dependencies

- **High cohesion** — a module's parts serve one purpose.
- **Low coupling** — minimize what one module must know of another; prefer the weakest coupling that works.
- **Single Responsibility** — one responsibility / one reason to exist; avoid the God class.
- **Interface Segregation** — no client depends on methods it doesn't use.
- **Dependency Inversion** — depend on abstractions; policy doesn't depend on detail.
- **Acyclic & stable dependencies** — no cycles; dependencies point toward the more stable, more abstract
  side.
- **Connascence** — prefer weaker forms (name > position > meaning); keep any strong connascence local.

## 7. Change & extensibility

- **Open/Closed** — a foreseen change extends at an existing seam, not by reopening an owner.
- **Localize change axes** — what changes together lives together; what changes for different reasons/rates
  lives apart.
- **DRY as knowledge** — one authoritative home per fact — yet duplication is cheaper than the wrong
  abstraction (Metz).
- **YAGNI** — build for present forces; no speculative generality. Size is a forcing question, not a line
  limit.
- **Subtractive discipline** — every type/layer/abstraction answers to a present force; cut what pays for
  nothing.
- **Schema/representation evolution has one owner** — a change to a persisted or exposed data shape (a
  record's fields, a wire/DB schema, an explanation chain) is absorbed at one place, not threaded through
  its consumers. The reopen usually lands exactly here; §6/§9 cover only half of it.
- **Structure vs YAGNI — the tie-break.** When "add a seam" (§0/§5) and "cut what pays for nothing"
  (YAGNI / the subtractive item above) disagree on the *same* element, resolve by the change-axes (X): a
  seam no X-item would ever use
  is over-build — a §7 finding, **at most S1** (a light, local cost); a seam a foreseeable X-item would
  force open is under-provision — a §6/OCP finding at **S3**. **Falsifier:** name the X-item the seam
  serves — none → over-built; one → omitting it is the fault. (This asymmetry is the registered decision
  rule, so the structure-vs-minimalism call is not left to a judge's taste.)

## 8. Code smells (Fowler's catalogue)

- **Bloaters** — long method, large class, long parameter list, primitive obsession, data clumps.
- **Change-preventers** — divergent change, shotgun surgery, parallel inheritance.
- **OO-abusers** — type-code/switch instead of polymorphism, refused bequest, temporary field, alternative
  classes with different interfaces.
- **Couplers** — feature envy, inappropriate intimacy, message chains, middle man.
- **Dispensables** — duplicated code, dead code, lazy class, data class, speculative generality, comments
  compensating for bad code.

## 9. Design patterns (by force, not fashion)

- **Choose by the force** — a pattern is a named solution to a recurring problem; apply it when that force
  is present, not for sophistication.
- **Composition over inheritance** — prefer delegation; inheritance only for genuine subtyping (LSP).
- **Know the common ones** — Strategy, Factory / Abstract Factory, Adapter, Decorator, Observer, Template
  Method, State, Command, Composite, Repository.
- **Avoid pattern abuse** — indirection with no present force is a smell, not a merit.

## 10. Architecture & separation of concerns

- **Layered separation** — presentation, domain, and data are distinct; each depends only inward.
- **UI/domain separation** — MVC / MVVM: the domain never depends on the view.
- **Ports & Adapters (Hexagonal / Clean Architecture)** — the domain is independent of I/O, frameworks, and
  databases, reached through interfaces.
- **Component principles** — cohesion (REP/CCP/CRP) and coupling (ADP/SDP/SAP) govern how modules group and
  depend.
- **Boundaries on real change axes** — draw a seam where variation is foreseeable, not by default.

## 11. State, side effects & concurrency

- **Minimize mutable & shared state** — less shared mutable state, less action-at-a-distance.
- **Functional core, imperative shell** — pure logic at the center; side effects at thin edges (humble
  object).
- **Idempotency** — a retryable operation applied twice equals once.
- **No global mutable state** — global data is where order-dependence and races live.
- **Concurrency safety** *(precondition under real concurrency)* — shared state under concurrent access is
  synchronized or confined; no data race.

## 12. Testability & tests *(code-leaning)*

- **Verifiable by construction** — non-trivial decisions reachable by fast, isolated tests; dependencies
  injected, edges seam-able.
- **Test behavior, not implementation** — assert the observable contract, so a refactor doesn't break the
  tests.
- **FIRST & the pyramid** — fast, isolated, repeatable, self-validating, timely; many unit, fewer
  integration, few end-to-end.
- **Cover every non-trivial decision** — including paths that already look correct (regression guard), never
  a coverage percentage.

## 13. Performance & resources *(conditional — scored only against a stated requirement)*

- **Against stated requirements** — complexity, allocations, and I/O fit the declared need; no accidental
  quadratic or reload-in-a-loop.
- **Measure before optimizing** — optimize the proven hot path, not a guess.
- **Never a proxy for quality** — fast isn't thereby well-designed; slow isn't thereby badly designed.

## 14. Security & trust boundaries *(conditional — scored only where a boundary exists)*

- **Validate & encode at the boundary** — untrusted input validated in, output encoded out.
- **Least privilege & secure defaults** — each component runs with the minimum it needs; safe by default.
- **Own secrets & authorization at one boundary** — not scattered; follow established secure-coding practice
  (OWASP).

---

*Sources: Clean Code and Code Complete (function-level clean code, naming, comments); The Pragmatic
Programmer (DRY, orthogonality, Law of Demeter); Refactoring — Fowler (the smell catalogue, anemic model,
primitive obsession); Design Patterns — GoF (pattern selection, composition over inheritance); SOLID and
Clean Architecture — Martin (SRP/OCP/LSP/ISP/DIP, the component principles, layering, ports & adapters);
Domain-Driven Design — Evans (value objects, published language / shared kernel); Design by Contract —
Meyer; ISO/IEC 25010 (functional correctness, performance, security as separate qualities); OWASP (secure
coding).*
