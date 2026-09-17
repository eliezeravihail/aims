# Design principles

These are comprehension checks, not code metrics. None of them is computed from a line count,
a parameter count, or a diagnostic tool. Each is a question a reader answers by understanding
what the code means and does — the same way a human reviewer would, grounded in established
software-design literature rather than invented for this project.

**This is the single source for both building and grading.** §1–§12 are the design-quality
comprehension checks. §13–§17 add the correctness, reliability, and cross-cutting properties a build
must also satisfy and a review must also measure; §18 names the canonical principles this set already
carries. The **principles are identical for every side** — what differs is only the *how*: when
**building** you make each hold by construction; when **grading** you score it with evidence
(`experiments/judging-rubric/quality-metrics.md` is that scoring layer — the mechanics of how to score
these principles, never a rival list). Asking for one thing and measuring another is the failure this
avoids.

Apply every principle in both directions when building AND when reviewing:
- **Building (Worker):** before delegating or returning work, check the current objective's design
  against these questions — and treat §13 (correctness) as a precondition, not an afterthought.
- **Reviewing (Judge):** for each principle, state per repository whether it holds, cite the
  specific code, and rule out the case that only looks like it holds.

**What these principles guard hardest against.** The dominant failure of unguided code generation is
**under-structuring** — flat procedural code, inline literals and magic values, primitive obsession (§4),
anemic data-bags (§5), a rule enforced nowhere in particular (§9), no owned seams. Over-engineering — a
speculative layer, an interface no consumer needs — is a **real but lighter, secondary** fault: a local
cost, not a spreading rot. Calibrate every judgment accordingly: when unsure, the graver risk is **too
little structure, not too much.**

## 1. Tell, Don't Ask / the Law of Demeter

**The question:** Does calling code *tell* an object what to do and let it decide how, or does the
caller *ask* the object for its internal data and then make the decision itself, outside the
object?

An object that hands out its raw internal state so callers can inspect it and decide what to do
next has effectively moved its own logic outside itself. The Law of Demeter sharpens this: code
should only talk to its immediate collaborators, not reach through one object to manipulate
another it only knows about indirectly (`a.getB().getC().doSomething()` is the classic violation
shape).

**Not the test:** whether Python *can* technically reach in and mutate a field — it always can.
The test is whether there is a small, meaningful public interface that real callers actually use
instead of reaching past it, and whether that interface exposes decisions ("assign this task") or
just data ("give me the fields so I can decide").

## 2. Program to an interface, not an implementation — and ask whether the interface is *generic*

**The bedrock, before any question of genericity.** What crosses a seam between parts is *always* an
abstraction the exposing side owns — a domain type — and *never* a concrete implementation type. This is
the load-bearing move of encapsulation and the first defence against coupling: a caller handed your
concrete class, a vendor's result object, or a framework's `Model` is bound to your implementation and
breaks the day you change it. Expose the abstraction; keep the implementation behind it. Every refinement
below — whether that abstraction is polymorphic, how generic it should be, whether a family holds one
altitude — sharpens this one rule and none of them replaces it. "It has only one implementation" is never a
reason to leak the concrete type across the seam, and — because an unused seam costs little while a missing
one forces a reopen — not by itself a reason to withhold the abstraction either.

**The question:** If this type has an abstraction/interface, does that interface express a genuine
*domain* behavior defined by **what a consumer needs** — or does it just rename one concrete thing's
methods (an `I`-prefix or ABC that mirrors a single implementation and leaks its specifics through the
interface)? The test is the **shape** of the type, not a count of implementations.

The distinguishing example: `Animal.make_sound()` is a real abstraction — many different animals
implement it differently, and calling code that only knows "this is an Animal" is meaningfully
decoupled from which one. `ICat` with a `meow()` method is not an abstraction at all — it's the
concrete thing wearing a costume; nothing is gained, and the interface leaks the concrete
implementation's specific behavior right through its name.

**How to tell them apart:** ask whether the type is defined by *what the consumer needs* (a domain
concept) or by one implementation's own shape. A type that only mirrors a single concrete — its fields
and methods renamed — is decorative; one that names a consumer-facing concept earns its place, **whether
or not a second implementation is in sight.**

**Do not gate the seam on predicting a second implementation.** "Only introduce an interface once you have
two implementations" — and even "once you can *describe* a second" — is a **prediction requirement that
blocks extension**: it makes you write the concrete thing, then reopen it into an interface the day a second
case lands, the very change the seam existed to absorb without a reopen. So expose the abstraction by
default and **lean toward naming the seam when unsure** — the cost is asymmetric: an interface provided
where a second implementation never arrives is a **light, local** cost (a seam nobody used), while a seam
withheld and later needed forces a **reopen** of the owner. What still does *not* earn its place is a type
that only **mirrors one concrete** (the `ICat` costume above) — that is a leak, not an abstraction, judged
by shape, never by count. (`decisions/0013` records this rebalance and why the prediction gate was dropped.)

**The general rule — domain-free; the example below only illustrates it, it is not the rule.** The
type that crosses an interface should be the *most generic type that is still complete for the consumer
and still honestly producible by every implementation you unify*. Two independent bounds pin it: the
consumer's needed information is the **floor** (more generic than that loses information and pushes the
consumer outside the interface), and the least-capable intended producer is the **ceiling** (more
specific than that forces some producer to fabricate or distort). When no single type satisfies both
bounds, that is evidence of *more than one concept* — segregate into distinct types (a shared supertype
for the common part, specializations for the richer ones) so each producer implements only what it
genuinely has and each consumer depends only on what it genuinely needs. Never resolve the tension by
flattening a richer producer (losing information) or by cramming a poorer one into the richer type (a
technically-valid but foreign field); distortion in either direction is the smell. The one invariant
underneath all of it: **minimize the knowledge you force on the other side — no more than the concept
requires, no less than it needs, and never your own implementation choice.** What follows is one worked
example of this rule, in a single domain — do not mistake the example for the principle.

**Keep a family of concepts at one level of abstraction — uniformity in the content model itself.** The
peers in a family must sit at the same conceptual altitude. `Rectangle`, `Triangle`, `Pentagon` is a
coherent family; `Rectangle`, `Triangle`, and then `RhombusBuiltByReflectingTwoTriangles` is not — one
member has dropped from *what a shape is* to *how a particular shape happens to be constructed*, an
altitude the others do not share. The model now conflates a kind with an implementation of a kind: any
operation over "a shape" must either special-case the misfit or is distorted by it, and a reader holds two
altitudes for one idea. A member that breaks the family's altitude is telling you one of two things — it is
**misclassified** (it belongs to a different family, at a different level) or it is **over-specified** (it
has leaked how it is made into what it is, and the construction detail should move behind the abstraction,
not sit beside its siblings as if it were one). The same smell shows up in mechanism, not just in taxonomy:
expressing one member of a family behind an interface and its sibling as an inline `kind`-field-and-switch
puts one idea at two altitudes. Whatever altitude a family is drawn at, hold the whole family to it; do not
let one member sink to an implementation-shaped level because it happens to have a single case today (the
count proxy again), and do not raise one member to a speculative abstraction its siblings do not need.

**A worked example (illustration only).** `ObjectDetectionModel.detect(image) -> list[DetectedObject]` is a real
abstraction: YOLO, DETR, and a hosted cloud API all satisfy it identically. Returning the concrete
`YOLOv26`, or the vendor's `ultralytics ...Results` object, is not — it forces every consumer to know
*which* implementation you chose (an **identity leak**) or the vendor's output schema (a **format
leak**). The fix is a domain type — `DetectedObject{box, label, score}` — defined by *what the
consumer needs*, not the vendor's fields renamed. That last point is the `ICat` trap again: if a DETR
backend can't fill the same `DetectedObject` without contortion, the type only mirrors one vendor and
is decorative. **Operational test — would the type in your public signature survive you swapping your
implementation?** `np.ndarray` survives a Keras→PyTorch swap; `keras.Model` does not — so a
`keras.Model` in a public signature *is* your implementation leaking through the interface.

**Choosing the level of generality — pinned from both sides.** "Your domain type" is a type *you*
define (so it drags in no chosen dependency), that names the concept and carries exactly the
information the consumer needs. How generic should it be? Take the **most generic type that is still
complete** — and that level is pinned by two independent bounds:

- **The consumer's need is the floor — do not lose information.** The type must carry everything the
  consumer legitimately needs. Go more generic than that — `object`, a bare `dict`, `tuple[float, ...]`
  — and the consumer has to reach *outside* the interface to make sense of the value: the abstraction
  is breached from above.
- **The producers' common capability is the ceiling — do not demand what some implementation cannot
  supply.** The type may commit to nothing that an intended implementation can't produce. An
  `OrientedBox` (a box *with an angle*) is the right abstraction **only for models that produce
  oriented boxes**; the moment you must also unify a model that emits an axis-aligned rectangle,
  `OrientedBox` is *too specific for it* — it has no angle to give and would have to fabricate one, so
  the shared type must drop to what *all* the unified implementations can actually supply (here, a
  plain `Box`).

So the right generality is the **common vocabulary of the implementations you intend to unify, still
rich enough for the consumer** — set by both ends at once, not by either alone. When the two bounds
cannot both be met (the consumer needs orientation but one producer cannot supply it), that is a real
design signal — that producer genuinely cannot serve that need behind a single type — not something to
paper over by cramming the weaker producer into the richer type.

Beware the tempting version of that cram: the fabrication can be *value-correct* and still
design-wrong. An axis-aligned rectangle genuinely *is* an `OrientedBox` with `angle = 0`, so the trick
looks free — but encoding it that way (a) forces the orientation concept onto a producer and consumers
that have no notion of it (Interface Segregation, §3), and (b) inverts the specialization: it makes the
*simpler* case a degenerate instance of the *richer* type. The honest direction is the opposite —
abstract **up** to the shared concept (`Box` as the supertype) and let the richer concept live in a
specialization (`OrientedBox` as a subtype), so only the parties that actually need orientation depend
on it.

And note what "abstract up" does *not* mean: it does not mean flattening the oriented producer down to
`Box` and throwing its angle away — that is the opposite error (too generic, information lost). The
unmeetable-bounds case resolves to **two types, because they are genuinely two kinds of object** — not
to one lossy compromise. The oriented producer implements `OrientedBox` and keeps its full information;
the rectangle producer implements only `Box` and is never forced to invent an angle; the shared `Box`
supertype exists *only* for consumers that need the common part, while a consumer that needs orientation
depends on `OrientedBox` and can be served only by producers that actually have it. Nobody is distorted
in either direction (`OrientedBox <: Box`).

**The review lens turns this cram into a standing check** — for every element, *is it the kind of thing
it is, or a different kind forced into this shape?* — run on the design before code, where a value-correct
mismatch is cheapest to see and to move. See `references/review.md`, the concept-fit pass.

## 3. Interface Segregation

**The question:** Does anything that depends on this interface actually use everything on it, or
is it forced to depend on methods it has no use for because they were bundled in?

A fat, bundled interface makes every consumer couple to methods it never calls, and makes every
future change to any one of those methods a risk to every consumer, not just the ones that use it.

## 4. Primitive obsession

**The question:** Does a concept that has its own meaning, validation, and identity (an id, a
status, a name with rules about what makes it valid) get its own small type — or is it a bare
string/int passed around and re-validated ad hoc everywhere it appears?

A raw string standing in for something with real rules (a member id, a provider name) forces every
caller to remember the rules and re-implement the validation, and gives the compiler/reader no
help noticing when the wrong kind of string was passed where another kind belonged.

## 5. Anemic domain model

**The question:** Do the objects that represent the product's core concepts (a task, an agent)
carry real behavior and enforce their own rules — or are they just data bags, with all the actual
logic living in separate "service"/"manager" functions that pull the data out and decide
everything externally?

A model with data but no behavior is not really object-oriented design; it is procedural code
wearing class syntax. The test: could you describe what this type *does*, not just what fields it
holds?

## 6. High cohesion, low coupling — Feature Envy and Shotgun Surgery

**The question, feature envy:** Does a piece of code use another module's data/behavior more than
its own module's? If a method spends most of its body reaching into a different object's internals
to do its work, that logic probably belongs on the other object.

**The question, shotgun surgery:** Does a single product-level change require touching many
unrelated files/classes to be complete — a sign that responsibility for one concept is scattered
rather than owned in one cohesive place?

Both are read from the same underlying question: does "things that change together" actually live
together, and does "things that don't" actually live apart?

## 7. Leaky abstractions are normal — the question is *which* details leak

**The question:** Every abstraction leaks some detail eventually (Spolsky's law) — the standard is
not "does this leak nothing," which is impossible, but "does what leaks through match what a
caller legitimately needs to know?"

A storage interface that lets a caller learn "a write can fail" is a reasonable, necessary leak.
One that forces a caller to know the on-disk field names to use the interface correctly is not —
that's not a necessary leak, it's a missing abstraction.

**Which types may cross a public boundary — decide it at day zero, normatively.** The load-bearing
special case of "which details leak" is the *vocabulary a public seam is allowed to speak*. The
permitted set is exactly two things: (1) generic interface types and your own domain types, and (2) a
small, **closed set of foundational, cross-infrastructure dependencies agreed in advance** (e.g.
`numpy`, `cv2` — illustrative examples, chosen per product; never treat any particular pair as a
canonical list). Nothing else — in particular, never a concrete type from a dependency you chose as an
*implementation detail* (`keras.Model`, `tf.data.Dataset`, a vendor's result object), neither accepted
as a parameter (that forces the caller to know it) nor returned as output (that forces the consumer to
know it).

Decide that permitted set **normatively and up front — not empirically.** "Pass whatever the other
side already depends on" is the wrong, dangerous test: you do not know what a given consumer depends
on, cannot inspect it, and "surely everyone depends on X" is precisely the rationalization that lets
an implementation type leak. The permitted foundation is a *day-zero design decision* — a small,
published, shared vocabulary you commit to (established up front during discovery — see the operating
loop's step 1 and `references/discovery.md`; keep it minimal, only very-infrastructural things whose
replacement would rewrite everything, and note that a heavy but *replaceable* dependency is not
foundational and does not belong in it) — and "the consumer also depends on it" is then a
*consequence* of that decision, not an assumption about the consumer. (This is a shared-kernel /
published-language choice. It is **not** the Stable-Dependencies Principle, which is about the
*direction of dependency between components*, not the payload types allowed at a seam.)

Balance this against primitive obsession (§4): the answer to "don't leak your impl type" is *your own
domain type*, not a retreat to bare strings, tuples, and dicts. `list[DetectedObject]` beats both the
vendor's `Results` (leaks the implementation) and `list[tuple[float, ...]]` (primitive obsession).
"Minimal dependency" means *a small agreed foundation*, not "only primitives."

**The boundary's vocabulary includes its error types.** An implementation can leak through the
exception channel exactly as through a parameter or return value: a public method that lets a
`torch.cuda.OutOfMemoryError` or a vendor exception escape has coupled its consumer to the chosen
implementation just as surely as if it had returned the type. So at a public seam, implementation
exceptions are caught and re-raised as the framework's own error types, phrased in the consumer's
concepts (§11). One deliberate carve-out: failures there is **no utility in catching** — process-fatal
collapses no consumer could act on through the interface (a memory error that takes the process down
anyway). Translating those is decorative machinery; do not force a wrapper on an error nobody can
handle. The test is **actionability**: if a reasonable consumer could respond in the concept's terms
(retry, alternate path, report and continue), translate; if nothing can be done and the process is
lost regardless, let it fall.

**The number of error *types* is set by the number of distinct *handlings*, not by tidiness.** Introduce
your own exception subtype only where some caller catches *that* type specifically to act on it
differently from the rest. Five sibling subtypes that every caller only ever catches through their shared
base (`except BaseError`) are five dead classes: the base already carries the message, and the subtypes
are unpaid machinery the subtractive pass (`review.md`) should cut. The information-hiding rule underneath
this is precise — the sin was never that a caller *can see* a concrete error or implementation, it is
that the design *forces* a caller to *know* one. So an error a caller can do nothing about may freely
"leak" a generic type; and a distinct error type no caller distinguishes should not exist. Throw a custom
error only against a declared catch that needs it — **one error type per handling response, no more.**

This is the **guard on the anti-leak rule above**, and the guard matters because the anti-leak rule is
what tends to breed the dead classes: re-raising an implementation error as *your own* type earns a
*distinct* type only when some caller catches *that* type to act on it. Re-raising every failure as its
own bespoke subtype merely so nothing "leaks" is exactly how a hierarchy of ten classes nobody catches
gets built. When in doubt, one base type carrying a message — and add a subtype the day a real caller
needs to branch on it, not before.

## 8. Single Responsibility, and the God Object smell

**The question:** Can you state, in one sentence, the one reason this class/module would need to
change? If a second, unrelated reason exists ("this class changes if the storage format changes,
*and* if the CLI's argument format changes, *and* if a validation rule changes"), that's two
responsibilities pretending to be one class.

## 9. Where is a stated rule actually enforced?

**The question:** For a rule the product declares must always hold, is there one place every real
path capable of breaking it must pass through — and do all real paths actually route through it,
or does at least one take a shortcut to the same effect (e.g. writing directly to storage instead
of going through the guarded method)?

This is not about whether Python can technically be tricked into bypassing it (it always can, in
any dynamic language) — it's about whether the *intended, documented, actually-used* paths funnel
through one place, so a reader auditing "is this rule safe" only has one place to check.

## 10. Duplication is not automatically wrong — the wrong abstraction is worse

**The question, per Sandi Metz:** "duplication is far cheaper than the wrong abstraction." Before
flagging two similar-looking pieces of code as a DRY violation, ask: are these actually the same
concept that must change together, or two independent things that merely look alike today and
would be harder to change independently if forced to share code?

Only flag duplication when unifying it would remove a real, current coupling — not merely because
two blocks of code resemble each other.

## 11. Naming and failure should not surprise a reasonable reader

**The question:** Does a name accurately describe what the thing does (including any side effect a
reader would care about), and does an error message tell a reasonable reader what happened and
what to do about it, in terms of the concept they're using — not an internal variable name or a
raw exception they were never meant to see? At a public seam this extends to the exception's *type*,
not only its message — see the boundary-vocabulary rule in §7, including its carve-out for
unactionable, process-fatal failures.

## 12. Size as a forcing question, not a verdict

**The question, per Sandi Metz's own framing (including her explicit "Rule 0" — any rule can be
broken with a stated reason):** when a method, class, or parameter list grows large, the question
is not "is it over some line count" but "can you explain, in one sentence, why this much
complexity belongs together here" — and if you can't, that's the actual smell, independent of any
specific number.

## 13. Functional correctness — the precondition quality serves

**The question:** Does the design/code actually produce what the spec requires — **every** stated
acceptance case, and the interactions the cases *imply but do not spell out* (a change-axis crossed with a
rule)? For each declared postcondition or invariant, is there a path that guarantees it, and can every
required output actually be produced from the described pipeline?

A design can score well on §1–§12 and still be **wrong** — a clean structure that computes the wrong
number, or that cannot produce a required output at all. Correctness is not one quality among the others;
it is the **precondition** they serve. An elegant, well-encapsulated design that fails a required case is
not high quality. **Trace every case, and every implied interaction, before declaring the work done** — the
most expensive misses are the interactions no single stated case exercises (a cart-level discount that must
still land on a per-line figure; a completion step no component owns). This is the one principle whose
failure is a defect regardless of how the code reads.

## 14. State and side-effect discipline

**The question:** Is mutable and shared state minimized, and is whatever remains mutated in **one**
localized place? Are the core computations pure — same inputs, same result, no reliance on hidden state?
Is there global mutable data, or a side effect a reasonable caller would be surprised by? Where an
operation can be retried, is it idempotent?

Immutable-by-default, with side effects pushed to thin edges, is easier to reason about, test (§15), and
run concurrently; scattered mutation and global data are where order-dependence, races, and
action-at-a-distance defects live (Fowler's *Mutable Data* / *Global Data*; the functional-core idea).
The test is not "does the language allow mutation" — it is whether the design *chooses* to confine it.

## 15. Testability — verifiable by construction

**The question:** Can the non-trivial decisions be exercised by a fast, isolated test **without** standing
up the whole system? Are dependencies injected rather than hard-wired, side effects confined to a thin
"humble" edge, and the boundaries seam-able so a unit can be driven in isolation?

A design whose correctness (§13) cannot be checked cheaply is one whose correctness will not stay true.
Testability is a property of the design, read before any test is written: deep logic reachable only through
heavy end-to-end setup is a design smell, not merely a testing inconvenience.

## 16. Performance and resource use — on its own terms, never a proxy

**The question:** Against the product's **stated** performance requirements, are the algorithmic
complexity, the allocations, and the I/O appropriate, with no avoidable blow-up (an accidental quadratic, a
reload in a loop)?

Performance is a real requirement and is judged **on its own terms**. Two hard rules: **it is never used as
an estimator or proxy for code quality** (fast code is not thereby well-designed, and slow code is not
thereby badly designed), and **no other principle borrows a performance number** to stand in for a design
judgment. If the product states no performance requirement, this principle is not scored — it is not a free
pass or a free failure.

## 17. Security and trust boundaries

**The question:** Where untrusted input crosses a trust boundary, is it validated and its output encoded?
Does each component run with least privilege and secure defaults, and are secrets and authorization owned at
one boundary rather than scattered? Scored only where the product actually has a trust boundary or sensitive
data (OWASP secure-coding practices).

## 18. Named principles this set already carries

Several canonical principles are the *same* checks under other names — stated here so a reader recognizes
them and does not think they are missing:

- **Open/Closed** — §6: a foreseen change *extends* at a seam that already exists rather than *reopening* an
  owner.
- **Liskov Substitution** — §2: a subtype must honor its supertype's contract, and a family must hold one
  altitude (a member that cannot stand in for the concept is misclassified).
- **Acyclic Dependencies / stable-dependency direction** — §6 and §8: dependencies point one way, toward the
  more stable and more abstract owner, with no cycles.
- **DRY as knowledge, not text** — §10.
- **Principle of Least Astonishment** — §11.
- **YAGNI / earn every element** — §12 and the subtractive pass (`review.md`): every type, interface, and
  layer must answer to a present force; what can be deleted without damaging a current ownership is rent
  paid to nobody.

Naming them adds no new machinery; it points at the principle a reader trained on SOLID or the component
principles will look for.

---

### Sources these principles are drawn from (for context, not to be cited verbatim in a review)

- Tell, Don't Ask; Law of Demeter — object-oriented design literature (Pragmatic Programmer;
  https://sauln.github.io/blog/law-of-demeter/, https://en.wikipedia.org/wiki/Law_of_Demeter)
- "Program to an interface, not an implementation" — Gang of Four, *Design Patterns*
- Interface Segregation Principle — Robert C. Martin, SOLID
- Primitive Obsession, Anemic Domain Model — Martin Fowler, *Refactoring*;
  https://martinfowler.com/bliki/AnemicDomainModel.html
- Feature Envy, Shotgun Surgery — Fowler, *Refactoring* catalog of code smells
- Law of Leaky Abstractions — Joel Spolsky, https://www.joelonsoftware.com/2002/11/11/the-law-of-leaky-abstractions/
- Single Responsibility Principle — Robert C. Martin, SOLID
- Sandi Metz's rules (including Rule 0) — *Practical Object-Oriented Design*, https://sandimetz.com/
- Shared Kernel / Published Language (the day-zero agreed vocabulary a boundary may speak) — Eric
  Evans, *Domain-Driven Design*
- Correctness as precondition; contracts (pre/postconditions, invariants) — Bertrand Meyer, *Design by
  Contract*; ISO/IEC 25010 functional correctness
- Immutability, purity, referential transparency; *Mutable Data* / *Global Data* smells — functional
  programming; Fowler, *Refactoring*
- Testability, seams, the Humble Object — Michael Feathers, *Working Effectively with Legacy Code*
- Performance efficiency as a separate quality (never a proxy) — ISO/IEC 25010
- Secure coding, trust boundaries, least privilege — OWASP Secure Coding Practices
- Open/Closed, Liskov Substitution, Acyclic Dependencies / stable-dependency direction — Robert C.
  Martin, SOLID and the component principles
