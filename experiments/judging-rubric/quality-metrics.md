---
title: "Quality Metrics List — a grounded, weighted rubric for judging code/design quality"
date: 2026-09-17
---

# Quality Metrics List

A rubric a blind judge uses to score the quality of a design (or an implementation) **one metric at a
time**, then combine the metric scores into a single grade by a **severity-weighted** rule. It exists
because the earlier design judging decided a whole verdict on one contested defect instead of measuring
against named quality dimensions — the failure recorded in
[`../aims-upgraded-rerun/judges.md`](../aims-upgraded-rerun/judges.md).

Every metric below is drawn from an established body of work (the **Sources** line names the worlds it
consolidates — SOLID, Clean Architecture, GoF, Fowler's smells, Clean Code, Structured Design, Connascence,
Design by Contract, DDD, APOSD, the Pragmatic Programmer, ISO/IEC 25010, OWASP, and this repo's own
`design-principles.md` / `review.md`). The sources are the pedigree of each metric, not citations to chase.
Metrics are deliberately **non-overlapping**; each block ends with *Distinct from* to stop double-counting
the same fault under two names.

## How the judge scores each metric (0–4)

| score | meaning |
|---|---|
| **4 Exemplary** | the property holds *by construction*; a reader verifies it in one place |
| **3 Sound** | holds, with a minor non-structural imperfection |
| **2 Weak** | holds but fragile, partially owned, or needs care to stay true |
| **1 Violated** | breached in a way that matters for this product |
| **0 Broken/absent** | the design cannot satisfy it, or it produces wrong results |

Rules for the judge, per metric:
- Any score **≤ 3 requires evidence** — a quotation from the design/code text — and a one-line statement of
  what would raise it. A deduction with no citation is struck (it is exactly the "invented deduction" that
  broke the prior judging).
- Score the property as the design *states* it, not a defect you imagine it might have.
- **Length is never a merit**; a concise design that holds a property by construction scores above a verbose
  one that only asserts it.

## How a fault's severity sets its weight (the escalating rule)

Each deduction is tagged with a severity, and the metric's weight in the final grade scales with the **worst
fault found on that metric**. A clean metric keeps base weight (×1).

| severity | what it is | weight |
|---|---|---|
| **S1 Cosmetic** | naming, formatting, a redundant comment | ×1 |
| **S2 Moderate** | primitive obsession, a local coupling, a dead/decorative abstraction, a data clump | ×2 |
| **S3 High** | a mis-owned invariant, an implementation type leaked across a seam, a shotgun-surgery-prone seam, a *latent-architectural* concept cram | ×4 |
| **S4 Severe / Correctness** | produces a wrong result; a stated rule is unenforceable or bypassable; a security hole; data corruption | ×8 **and caps the grade** |

## Aggregation

```
grade = Σ (score_i × weight_i) / Σ (weight_i)          # weighted average over all metrics
weight_i = base_i × severity_multiplier(worst fault on metric i)     # base_i = 1 unless noted
```

Two hard rules on top of the average:
1. **An S4 finding caps the overall grade at ≤ 2.0**, however clean everything else is — a design that
   returns wrong results, or cannot enforce a rule it declares, is not "high quality" regardless of elegance.
2. **No single S1/S2/S3 finding decides a verdict on its own.** Only S4 is decisive by rule. A contested
   modeling call is **S3 at most** and enters the average weighted — it never caps and never single-handedly
   flips a ranking. (This is the precise guard the prior judging lacked: it let an S3-grade concept dispute
   act like an S4.)

A judge reports, per metric: the 0–4 score, each deduction with its quotation and severity tag, then the
weighted grade and any cap triggered.

---

# The metrics

## Family 1 — Abstraction & Modularity

### M1. Abstraction at the seam
**Sources:** GoF ("program to an interface"); SOLID/DIP; aims §2; APOSD (deep modules); DDD.
**How to measure:** For every seam, what crosses it — a domain abstraction the exposing side owns, or a
concrete implementation type (a vendor object, a framework `Model`, a raw dict)? Then check *generality
calibration*: is the crossing type the most generic type still complete for the consumer (floor) and still
honestly producible by every implementation (ceiling), with no decorative single-purpose interface and no
speculative generality? A module is "deep" (simple interface hiding real work), not "shallow".
**0–4:** 4 = every seam speaks domain/interface types, calibrated both ways. 2 = mostly, but one seam is
over- or under-generic. 0 = an implementation type is a public parameter/return.
**Severity ceiling:** S3 (an implementation leak across a public seam).
*Distinct from:* M6 (hiding *data/decisions*, not the type at the seam); M4 (direction of dependency).

### M2. Single Responsibility & Cohesion
**Sources:** SRP; CCP; GRASP High Cohesion / Information Expert; Structured Design cohesion scale
(coincidental→functional); LCOM; Fowler *Divergent Change*, *Large Class*.
**How to measure:** State, in one sentence, the single reason each component would change. Do the elements
inside it serve that one purpose (functional cohesion), or is it bundled by accident/time/logic? Does a
second, unrelated reason to change exist (divergent change)?
**0–4:** 4 = one-sentence reason per unit, functionally cohesive. 2 = a unit with two loosely-related
duties. 0 = a God object.
**Severity ceiling:** S3.
*Distinct from:* M5 (a change scattered *across* units); M2 is a change concentrated *wrongly within* one.

### M3. Interface Segregation
**Sources:** ISP; CRP (component reuse); Fowler *Refused Bequest*.
**How to measure:** Does every consumer of an interface use all of it, or is it forced to depend on members
it never calls? Are components split so users don't drag in what they don't need?
**0–4:** 4 = no consumer depends on an unused member. 2 = one fat interface with a partial consumer. 0 =
pervasive fat interfaces.
**Severity ceiling:** S2.
*Distinct from:* M4 (amount/direction of coupling); M3 is specifically *unused* surface forced on a consumer.

## Family 2 — Coupling & Dependency

### M4. Coupling & dependency direction
**Sources:** Structured Design coupling scale (content→data); Connascence (type, strength, locality,
degree); SDP/ADP; Law of Demeter; Fowler *Feature Envy*, *Message Chains*, *Insider Trading*, *Middle Man*;
C&K CBO / fan-in-out.
**How to measure:** Rank the coupling at each seam (content/common/control/stamp/data — lower is worse);
name the strongest connascence and whether distant connascence is kept weak and near. Does code reach
through objects (`a.getB().getC()`) or envy another unit's data? Are there dependency cycles (ADP)?
**0–4:** 4 = data-coupling only, no cycles, connascence weak-at-distance. 2 = some control/stamp coupling or
a message chain. 0 = a dependency cycle or content coupling.
**Severity ceiling:** S3.
*Distinct from:* M1 (the *type* at the seam); M5 (whether a change stays local).

### M5. Change locality (no shotgun surgery)
**Sources:** Fowler *Shotgun Surgery*; APOSD *change amplification*; OCP; GRASP *Protected Variations*.
**How to measure:** Take the change axes the product actually implies (and one plausible unstated variant).
For each, count the named components that must change. Does a single conceptual change land in one place
(extend at an existing seam), or scatter across many (reopen)? Would a foreseen variant's *semantics*
falsify an assumption an existing owner holds?
**0–4:** 4 = each implied change is one localized extension. 2 = one change touches several units. 0 = a
core change is shotgun surgery.
**Severity ceiling:** S3 (latent-architectural).
*Distinct from:* M2 (wrong grouping within a unit) and M8 (the modeled *shape* being wrong).

## Family 3 — Encapsulation & Rule Ownership

### M6. Information hiding & Tell-Don't-Ask
**Sources:** Parnas; Clean Code (data/object anti-symmetry, train wrecks); Law of Demeter; aims §1/§7;
APOSD (information hiding).
**How to measure:** Does calling code *tell* an object what to do, or *ask* for its internals and decide
outside it? Does the module hide a real design decision, or expose it? Which details leak — only those a
caller legitimately needs, or the on-disk/vendor shape?
**0–4:** 4 = decisions hidden behind tell-style interfaces; only necessary leaks. 2 = some ask-style access.
0 = callers must know internal structure to use the interface.
**Severity ceiling:** S3.
*Distinct from:* M1 (type identity at the seam); M6 is about *decisions/data* being reached for.

### M7. Rule / invariant ownership & enforceability
**Sources:** aims §9; Design by Contract (pre/postconditions, class invariants); GRASP; "one enforcement
point".
**How to measure:** For each rule the product declares must always hold, is there exactly one place every
real path must pass through, and do all intended paths route through it — or can one reach the same effect
by a shortcut? Are invariants owned by a single component and true by construction?
**0–4:** 4 = one unforgeable owner per rule, all paths funnel through it. 2 = owned but bypassable by an
intended path. 0/S4 = a declared rule has no owner or is unenforceable.
**Severity ceiling:** **S4** (an unenforceable/bypassable stated rule is a correctness failure).
*Distinct from:* M11 (whether outputs are correct); M7 is whether the *rule* has a single guard.

## Family 4 — Modeling Fidelity

### M8. Concept fit
**Sources:** aims §2 concept-fit / value-correct cram; `review.md` concept-fit pass; LSP (behavioral
subtyping); family-altitude (`Rectangle/Triangle` vs `RhombusBuiltBy…`).
**How to measure:** For each element, is it the *kind of thing* it claims to be, or a different kind forced
into this shape? In particular: is a decomposition modeled as a movement (or the reverse), leaving an inert
tell (a zero delta, an always-`None` field)? Do subtypes honor their supertype's contract (LSP)? Do family
peers sit at one altitude?
**0–4:** 4 = every element modeled as its true kind. 2 = a value-correct mismatch with a benign tell. 0 = a
cram that will force a rewrite when leaned on.
**Severity ceiling:** S3 (latent-architectural). *Escalates to S4 only if it already produces a wrong
result* — a *contested* concept call stays S3 and never caps.
*Distinct from:* M11 (numeric correctness today); M8 is "right by value, wrong by kind".

### M9. Model richness (not anemic)
**Sources:** Fowler *Anemic Domain Model*; GRASP Information Expert; DDD tactical (Entity/VO/Aggregate);
Clean Code (objects vs data structures).
**How to measure:** Do core concepts carry behavior and enforce their own rules, or are they data bags with
all logic in external "manager/service" functions? Can you say what the type *does*, not just what it holds?
**0–4:** 4 = behavior lives with the data it guards. 2 = a mix of rich and anemic. 0 = pervasive data bags +
procedural managers.
**Severity ceiling:** S2.
*Distinct from:* M7 (rule *ownership*); M9 is whether *domain objects* hold their own behavior at all.

### M10. Primitive obsession / typed concepts
**Sources:** Fowler *Primitive Obsession*, *Data Clumps*; Object Calisthenics (wrap primitives, first-class
collections); aims §4.
**How to measure:** Does a concept with its own rules/identity (an id, a money value, a code) get a small
type, or travel as a bare string/int re-validated ad hoc? Are recurring field groups made a type?
**0–4:** 4 = concepts with rules are typed. 2 = one or two bare primitives with scattered validation. 0 =
everything is strings/ints/dicts.
**Severity ceiling:** S2.
*Distinct from:* M1 (impl types at seams); M10 is *under*-typing a domain concept, not leaking an impl type.

## Family 5 — Correctness & Reliability *(severe-capable)*

### M11. Functional correctness
**Sources:** ISO/IEC 25010 (functional correctness); Design by Contract (postconditions); the product's own
acceptance cases.
**How to measure:** Trace each stated acceptance case through the design. Does it produce the specified
result, to the stated precision, with no logical gap or unreachable requirement? Is any required output
unproducible from the described pipeline?
**0–4:** 4 = every case reachable and correct. 2 = correct on the common path, a stated edge unhandled. 0 =
a stated case is unreachable or wrong.
**Severity ceiling:** **S4** (caps the grade).
*Distinct from:* M7 (rule enforcement); M11 is whether the *outputs* match the spec.

### M12. Error handling & failure semantics
**Sources:** Clean Code (exceptions over codes, context, no null); aims §7 (one error type per handling;
actionability); APOSD ("define errors out of existence"); fail-fast.
**How to measure:** Are failures modeled as first-class outcomes with enough context? Is there one error
type per distinct handling (not a dead hierarchy)? Are boundary/implementation errors translated to the
consumer's concepts, except unactionable process-fatal ones? Are errors designed *out* where possible?
**0–4:** 4 = failures are typed by handling, translated at boundaries, or designed away. 2 = over- or
under-typed errors. 0/S4 = a failure is swallowed or corrupts state.
**Severity ceiling:** S3 (S4 if a swallowed/mis-handled failure corrupts a result).
*Distinct from:* M11 (happy-path correctness); M12 is the *failure* paths.

### M13. State safety & immutability
**Sources:** FP (purity, immutability, referential transparency, side-effect isolation); Fowler *Mutable
Data*, *Global Data*; idempotency.
**How to measure:** Is shared/mutable state minimized and its mutation localized? Are core computations pure
/ referentially transparent where they can be? Is global mutable data avoided? Are operations that can
re-run idempotent where required?
**0–4:** 4 = immutable-by-default, side effects at the edges. 2 = some avoidable shared mutation. 0/S4 =
mutation that can race or corrupt.
**Severity ceiling:** S3 (S4 on a genuine data race/corruption).
*Distinct from:* M6 (hiding state) — M13 is whether state is *mutable/shared* at all.

## Family 6 — Simplicity & Economy

### M14. Simplicity / no unearned structure
**Sources:** Beck's 4 Rules of Simple Design; YAGNI/KISS; Fowler *Speculative Generality*, *Lazy Element*,
*Middle Man*; APOSD (shallow modules, tactical vs strategic); `review.md` subtractive pass; Metz Rule 0;
McCabe cyclomatic / Cognitive Complexity; Fowler *Long Function/Large Class/Long Parameter List*.
**How to measure:** For every type/interface/layer, what present product force requires it? Would deleting
it damage a current ownership, or only cost "tidiness"? Is each unit's size/branching explainable in one
sentence (not a line-count verdict)?
**0–4:** 4 = every element earns its place; complexity is explainable. 2 = one or two speculative/ceremony
elements. 0 = pervasive unforced machinery.
**Severity ceiling:** S2 (S3 only if the excess itself blocks change).
*Distinct from:* M15 (duplication specifically); M14 is *unneeded* structure.

### M15. Duplication vs the wrong abstraction
**Sources:** DRY (Pragmatic Programmer — knowledge, not text); Metz "duplication is cheaper than the wrong
abstraction" + Rule of Three; aims §10; Fowler *Duplicated Code*.
**How to measure:** Where code repeats, is it the *same knowledge* that must change together (real DRY
violation), or two things that merely look alike and would couple wrongly if merged? Flag duplication only
when unifying removes a real current coupling.
**0–4:** 4 = one owner per piece of knowledge; incidental similarity left apart. 2 = one real duplication or
one premature merge. 0 = knowledge duplicated across many sites, or a wrong abstraction forcing unrelated
things together.
**Severity ceiling:** S2.
*Distinct from:* M14 (structure that shouldn't exist at all).

## Family 7 — Legibility & Knowledge

### M16. Naming & intention
**Sources:** Clean Code (meaningful names); Fowler *Mysterious Name*; Principle of Least Astonishment.
**How to measure:** Does each name reveal intent (including side effects a reader would care about) without
disinformation or encoding? Would a reasonable reader be surprised by what it does?
**0–4:** 4 = names reveal intent, no surprises. 2 = a few vague/misleading names. 0 = pervasively cryptic or
misleading.
**Severity ceiling:** S1 (S2 if a misleading name hides a real behavior).
*Distinct from:* everything structural — M16 is lexical.

### M17. Comments & durable design knowledge
**Sources:** Clean Code (comments); APOSD (comments as design, capture the non-obvious); aims co-located
records (companions / ADRs, append-only).
**How to measure:** Do comments/records capture the *why* the code cannot say (rationale, invariants,
rejected alternatives) rather than restate the code? Is durable design knowledge co-located and kept from
going stale? No commented-out code / journal noise.
**0–4:** 4 = the non-obvious rationale is captured beside the code. 2 = thin or partly redundant. 0 = noise
or none where it's needed.
**Severity ceiling:** S1.
*Distinct from:* M16 (names in code); M17 is the surrounding rationale layer.

## Family 8 — Cross-cutting, measured on their own terms

### M18. Testability
**Sources:** Test Pyramid; FIRST; TDD three laws; Humble Object & seams (Feathers); DI.
**How to measure:** Can the non-trivial decisions be exercised by fast, isolated tests? Are dependencies
injectable, side effects pushed to thin humble edges, and boundaries seam-able? Does the design invite a
broad base of unit tests rather than only end-to-end?
**0–4:** 4 = decisions are unit-testable behind seams. 2 = some logic only reachable through heavy setup. 0
= untestable without the whole system.
**Severity ceiling:** S3.
*Distinct from:* M4/M5 — testability is the *consequence* checked directly, not re-scored coupling.

### M19. Performance & resource use *(own terms — never a proxy for quality)*
**Sources:** ISO/IEC 25010 (performance efficiency); algorithmic complexity; resource footprint.
**How to measure:** Against the product's *stated* performance requirements: are the algorithmic
complexity, allocations, and I/O appropriate; is there an obvious avoidable blow-up? **Score this on its own
terms only.** Per the standing rule: **never use a performance figure as an estimator of code quality**, and
never let a quality metric borrow a performance number. If the product states no performance requirement,
this metric is N/A (excluded from the average), not a free 4.
**0–4:** 4 = meets stated perf needs with no avoidable waste. 2 = a needless inefficiency. 0 = violates a
stated performance requirement.
**Severity ceiling:** requirement-dependent (S1–S4; S4 only when a stated hard performance requirement is
broken).
*Distinct from:* all quality metrics — kept separate by rule so it is never a proxy.

### M20. Security & trust boundaries
**Sources:** OWASP Secure Coding; least privilege; input validation / output encoding; defense in depth;
secure defaults.
**How to measure:** Where untrusted input crosses a trust boundary, is it validated/encoded? Does each
component run with least privilege? Are secrets and authorization handled at a single owned boundary? N/A
(excluded) for a product with no trust boundary or sensitive data.
**0–4:** 4 = trust boundaries explicit and guarded. 2 = a gap with low exposure. 0/S4 = an exploitable hole.
**Severity ceiling:** S4 where a real trust boundary exists.
*Distinct from:* M11 (functional correctness on trusted input); M20 is adversarial input / privilege.

---

## Applying the list (judge's procedure)

1. Score M1–M20 independently, each with evidence for any ≤3 and a severity tag on each deduction. Mark
   N/A metrics (e.g. M19/M20 when the product has no such requirement) and drop them from the denominator.
2. Compute `weight_i = severity_multiplier(worst fault on metric i)` and the weighted average.
3. Apply the caps: any S4 → grade ≤ 2.0. Report which cap fired.
4. Produce the grade **and** the per-metric table — never a bare number, and never a verdict resting on one
   sub-S4 finding.

## Notes

- **Coverage anchor:** the 20 metrics map onto ISO/IEC 25010's maintainability sub-characteristics
  (modularity → M1–M5; reusability → M1/M3; analysability → M16/M17; modifiability → M5/M14; testability →
  M18) plus functional correctness (M11), reliability (M12/M13), performance (M19) and security (M20), so the
  list is checkably complete, not ad hoc.
- **Relation to this repo's method:** M1–M12 are the same properties `design-principles.md` states as
  comprehension checks and `review.md` turns into passes; this list adds the *scoring and weighting* layer
  those references deliberately leave out. It is a judging rubric, not a change to the method's own axes.
