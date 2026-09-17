---
title: "Quality Metrics List — a grounded, weighted rubric for building AND judging code/design quality"
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

## Step 0 — the fixed inventory (before any scoring; identical for every judge)

Reproducibility requires that two judges measure the *same* thing. So before scoring, three product-level
lists are pinned **from the fixed spec the judge is given — never from what a design says about itself**, and
handed unchanged to every judge and applied to every design:

- **(R) the rules / invariants** the product declares it must hold;
- **(X) the change-axes** it implies, plus one plausible unstated variant;
- **(C) the acceptance cases** (inputs → required outputs).

Then, per design, the judge first **enumerates that design's seams and named elements** (its own list).
Every deduction later must cite a specific item — an R/X/C entry or a named seam. A design that simply
**omits** a required rule (R) or fails a case (C) is scored 0–1 on the relevant metric, **not** N/A: silence
is a miss, not an exemption. N/A is decided only by the spec (the product genuinely has no such
requirement), never by a design choosing not to mention one.

## Scoring a metric — one judgment (severity), not two

The judge does **not** pick a 0–4 score and a severity independently (they could contradict). Instead: find
the **worst fault** on the metric, cite the inventory item it violates, and tag its **severity**. Severity
then fixes *both* the score ceiling and the weight — a single choice:

| worst fault on the metric | score | weight |
|---|---|---|
| **none** — property holds *by construction* | **4** | ×1 |
| **S1** cosmetic (naming, formatting, a redundant comment) | **3** | ×1 |
| **S2** moderate (primitive obsession, a local coupling, a dead/decorative abstraction, a data clump) | **≤ 3** (2–3 by pervasiveness) | ×2 |
| **S3** high (mis-owned invariant, an implementation type leaked across a seam, a shotgun-surgery-prone seam, a *latent-architectural* concept cram) | **≤ 2** (1–2) | ×4 |
| **S4** severe / correctness (wrong result; a stated rule unenforceable or bypassable; a security hole; data corruption) | **≤ 1** (0–1) | ×8 |

**Every score needs a citation — including 4.** For a 4, quote *the single place the property holds by
construction* (the one owner / the one enforcing seam); for any deduction, quote the defect **and** name the
R/X/C or seam item it violates. A score with no citation is struck — this closes the "default everything to
4" gap.
**Length is never a merit**: a concise design that holds a property by construction outscores a verbose one
that merely asserts it.

## One defect, one metric

A single defect is deducted under **exactly one** metric — the most specific one that applies — and the
judge names it there. Related metrics may *reference* it ("see M4") but must **not** re-deduct. (E.g. a
Law-of-Demeter / train-wreck violation is scored under **M4** and only referenced from M6; an
"anemic-model-with-rules-outside-the-owner" defect is scored **once**, under M9 *or* M7, and the judge
states which.) This stops the same fault sinking a design three times through overlapping metrics.

## Aggregation — report a profile, not a single number

Compute and report **all** of the following over the non-N/A metrics:

```
weighted_average = Σ (score_i × weight_i) / Σ (weight_i)      # weight_i from the severity table above
worst_metric     = min score_i
counts           = (#S3 findings, #S4 findings)
```

Then apply **graded caps** to the reported grade (a single structural fault must not read as "Sound"):

| any finding at | grade capped at |
|---|---|
| S2 | ≤ 3.5 |
| S3 | ≤ 3.0 |
| S4 | ≤ 2.0 |

The **grade** is the capped weighted average, but it is always reported **beside** `worst_metric` and the
S3/S4 counts — never as a bare number. Rank by capped grade, then by `worst_metric`, then by fewer S3/S4.
This fixes the extremes Pavel flagged: one metric at 0/S3 among 19 clean 4s no longer averages to ~3.3
"Sound" — the S3 cap pins it at ≤ 3.0 and `worst_metric = 0` is reported alongside.

**No single sub-S4 finding decides a ranking on its own** — a contested modeling call is S3 at most; it caps
at ≤ 3.0 and enters the average, but the worst-metric and counts keep it honest without letting it act like a
correctness failure (the exact confusion that broke the prior judging).

## Applicability — Design / Code / Both

Score a metric only where the artifact can show it. On a **design** document, code-level metrics are marked
`N/A (code)` and dropped from the denominator unless the design's own text gives a basis.

| Both (design & code) | M1 M2 M3 M4 M5 M6 M7 M8 M9 M10 M11 M12 M14 M15 M17 M19 M20 |
|---|---|
| Code-leaning (score on design only if the text supports it) | **M13** (races/immutability), **M16** (naming), **M18** (testability) |

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
**Sources:** Parnas; Clean Code (data/object anti-symmetry); aims §1/§7; APOSD (information hiding).
**How to measure:** Does calling code *tell* an object what to do, or *ask* for its internals and decide
outside it? Does the module hide a real design decision, or expose it? Which details leak — only those a
caller legitimately needs, or the on-disk/vendor shape? *(Law-of-Demeter / train-wreck reach-through is
scored under M4, not here — reference it, do not re-deduct.)*
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

0. **Fix the inventory first** (Step 0 above): pin R (rules), X (change-axes), C (acceptance cases) from the
   spec — identical for every judge — then enumerate each design's seams/elements. Everything scored below
   must cite one of these items.
1. For each metric M1–M20: find the worst fault, cite the R/X/C or seam item it violates, tag its severity,
   and read the score off the severity table (clean = 4, with a citation of the one place it holds). Mark a
   metric `N/A` **only** when the spec carries no such requirement (not when a design is silent), and drop it
   from the denominator. Apply the Design/Code applicability table.
2. Enforce **one defect, one metric** — deduct each defect once, name where; cross-reference, never
   re-deduct.
3. Compute the **profile**: capped weighted average, `worst_metric`, and (#S3, #S4). Apply the graded caps
   (S2 ≤3.5, S3 ≤3.0, S4 ≤2.0) and report which fired.
4. Produce the per-metric scorecard **and** the profile — never a bare number, and never a verdict resting on
   one sub-S4 finding. Rank by capped grade, then `worst_metric`, then fewer S3/S4.

## Using the list as build instructions (not only for judging)

The list is **bidirectional**, exactly as `design-principles.md` says its principles are ("apply in both
directions when building AND reviewing"). The same 20 metrics a judge scores, the builder builds toward — and
the re-grade is the proof of why this matters: aims-upgraded's S4 (no cart-discount→line allocation) existed
because the build side optimized change-locality and minimalism and **never held M11 (functional correctness
against the whole spec) as a build target**. A builder who ran M11's trace before returning would have caught
the missing allocation. Building to the list closes that hole.

At build time the metrics become obligations, in this order (highest-leverage first, mirroring severity —
because an S4 caps the whole design, correctness is built and checked **first**, not last):

1. **Step 0, before designing.** Pin the fixed inventory from the spec: **R** (every rule/invariant), **X**
   (every change-axis + one plausible unstated variant), **C** (every acceptance case). Then design so that
   **every R has exactly one owner** (M7), **every X is a localized extension point, not a future reopen**
   (M5/M1/M8), and **every C has a trace** (M11). This is discovery's output (`references/discovery.md`), now
   used as a build contract.
2. **The correctness trace is mandatory (M11), before "done".** Trace every C-case **and every implied
   probe** — a change-axis × rule interaction the cases don't spell out — through the design. The canonical
   example is the one that caught aims-upgraded: *a multi-line SOUTH cart with a cart-level discount* forces
   per-line tax onto the discounted amount, which needs an allocation owner the literal cases never exercise.
   A design that cannot produce a required output carries an S4, however clean it reads.
3. **Build each remaining metric so it holds by construction**, then **self-verify with the same
   evidence rule the judge uses**: before returning, for each metric either cite the single place it holds
   (a 4) or record the fault, tag its severity, and fix it. **Never return a design carrying an S4, or an
   uncapped S3, without surfacing it** — the build side gates on the same profile the judge reports.

Where it plugs into aims: the review side already runs this list; at build time it becomes the **Worker's and
merge agent's pre-return checklist** and the panel's return gate (`references/panel-plan.md`,
`references/worker-handoff.md`), with Step 0 as the discovery deliverable. It does **not** replace
`design-principles.md`; it adds the measurable, spec-anchored, **correctness-first** checklist the build side
was missing — the exact gap the re-grade exposed.

## Notes

- **Coverage anchor:** the 20 metrics map onto ISO/IEC 25010's maintainability sub-characteristics
  (modularity → M1–M5; reusability → M1/M3; analysability → M16/M17; modifiability → M5/M14; testability →
  M18) plus functional correctness (M11), reliability (M12/M13), performance (M19) and security (M20), so the
  list is checkably complete, not ad hoc.
- **Relation to this repo's method:** M1–M12 are the same properties `design-principles.md` states as
  comprehension checks and `review.md` turns into passes; this list adds the *scoring and weighting* layer
  those references deliberately leave out. It is a judging rubric, not a change to the method's own axes.
