# Discovery guidance

Discovery exists to ground product behavior that changes engineering direction. It is not a requirements questionnaire, but implementation readiness is not permission to invent product behavior.

## Mandatory discovery gate

For a new product, obtain one concrete start-to-useful-result scenario before delegation unless the user already supplied one with comparable detail.

For every request, sort unresolved choices into:

1. **Grounded product facts** — supported by the request, repository behavior, or a recorded user answer.
2. **Open product decisions** — affect observable behavior, persistent data, identity/ownership, lifecycle rules, failure handling, or scope.
3. **Technical freedoms** — affect implementation only and can be chosen sensibly by the Worker.

Do not delegate while a material open product decision is unresolved. Ask about it. Do not ask the user about technical freedoms.

## Start from behavior

Prefer:

> Give me one concrete example of a user using this product from start to useful result.

over:

> What are all your functional requirements?

Concrete scenarios expose responsibilities, ownership, state transitions, failure behavior, and likely boundaries more reliably than architecture vocabulary supplied by the user.

After receiving the scenario, check only the dimensions the request actually touches:

- Who acts, and how are relevant people or things identified?
- What starts the flow, and what observable result ends it?
- What data must survive, and what may be absent?
- Which state changes are allowed or blocked, and what should the user see on failure?
- Which stated constraints or exclusions bound the work?

An unanswered item is not automatically a blocker. It is a blocker only when different answers would materially change current product behavior, persistent representation, an invariant, or the current objective.

### Every action implies its complement — surface it, don't leave it to be guessed

A usage scenario, as a user first states it, runs in the **forward direction only** — "add an item,"
"join the waitlist," "book a slot" — and silently omits the complements a real user of that scenario
needs: the **inverse action**, and the **sight of the state the user was just placed in**. Adding
implies removing; creating implies editing and deleting; joining a queue implies leaving it *and* seeing
your place in it; booking implies cancelling *and* seeing what you booked. For the scenario as described
these are not features to invent or niceties to defer — they are **requirements**, and a design that
omits one ships a product that traps its user: a cart you cannot take an item out of, a waitlist you can
neither see nor leave.

So for each action the product introduces, and each state it puts a user into, **ask** whether its
complement is in scope — the ordinary grounding question, answered by the user, not assumed by you. A
confirmed complement becomes a stated requirement the design must build; a confirmed exclusion becomes a
recorded non-goal. What you may not do is let it stay **unstated** — because unstated is the forward-only
scenario's default, and unstated is exactly what a design silently drops. Surfacing the complement here,
as a requirement, is the fix; do not rely on catching its absence later when reviewing the built design.

## Product-assumption test

Before treating an unspecified choice as an assumption, ask:

> If another reasonable answer were chosen, would a user observe different behavior, would stored data mean something different, or would an important rule move to a different owner?

If yes, record an open product decision and ask. If no, record a technical freedom and let the Worker choose.

For example, whether exporting a report overwrites the prior report or creates a new user-visible version is a product decision. Within an **established** stack, which incidental library performs the write, how modules are named, and what internal interface connects them are technical freedoms when the user has expressed no relevant constraint. But for the **first** design of a new product the language, the core framework, and the foundational dependencies are not free — they are the foundational substrate, and you ask about them (see below).

## Follow the forces

When a scenario reveals a dimension that may evolve independently, test whether it is real.

Useful questions include:
- In the concrete scenario just described, which responsibilities or concepts have clearly different reasons to change?
- Is a suspected variation part of the product the user actually expects, or merely something that can be imagined?
- What behavior must remain true as the product evolves?
- What current uncertainty would cause materially different engineering choices?
- What should *not* be generalized yet?

Do not present the user with a catalog of possible future extension points. Derive candidate forces from the product scenario and the user's answers.

## Entering an existing codebase — learn it before you redesign it

When the task changes code that **already exists** (a redesign, an extraction, a second implementation,
a refactor), the codebase is ground truth — and most of a design's claims are *claims about that code*,
which are checkable. Do not jump to a targeted fix, and do not sketch an abstraction over what you
*assume* is there. Learn it first, in order:

1. **Map the substrate and dependencies as they actually are** — the language(s), framework, and
   foundational deps the code truly stands on, read rather than assumed. For a redesign the substrate is
   *discovered* (already chosen), not asked; surface it and flag any conflict (e.g. one module in
   Python, its sibling in JS).
2. **Read the real seams and interfaces** — the actual module boundaries and public interfaces, and how
   the parts talk: the architecture in the code, not the one you would imagine.
3. **Read the actual implementation of every case your change claims to touch or unify.** If the design
   says an abstraction covers cases A, B, C, D, you must have *read* A, B, C, and D. Reading two and
   assuming the rest fit is the classic failure — a real case often has a different shape than your model
   (an *authored editor* with no seed, where you assumed a *seeded generator*).
4. **Surface the existing problems and debt from the code** — the duplication, coupling, and pain that
   actually justify the change — observed, not guessed.
5. **Only then design** — and every statement the design makes about the existing code ships with its
   evidence (the read from step 3) or is labelled **unverified**. An abstraction or boundary may not
   claim to cover a case it has not read.

## Foundational substrate (day zero) — ask, don't guess

Establish the **foundational substrate** at the start: the very-infrastructural base everything will be
built on, whose replacement would mean rewriting essentially everything. The test is pervasiveness, not
weight — *if every object ends up standing on it, replacing it rewrites everything.* This always
includes **the language**, and for most products **the core framework** (React, Django, Rails, a game
engine); numpy/scipy/cv2 are the numeric-work version (illustrative, **not** a canonical list — run the
pervasiveness test on *this* product; do not reach for a familiar name as the answer). A heavy but
replaceable dependency (a specific
model, a data loader, an augmentation library) is confined behind a boundary and is **not**
foundational; it is adopted later.

Because replacing the substrate rewrites everything, it is never guessed or deferred: **first ask the
user whether they want to set the foundational substrate *with you* or have *you* choose it** — offer
both. If they want to set it, ask about the language, the core framework, the foundational dependencies,
any stack constraint or preference. If they hand it back (*"you choose"*), record that and decide.

This is a **gate, not a courtesy**: asking is mandatory and you have no discretion to skip it. You may
not choose the substrate on your own until you have actually asked and the user has handed the choice
back. The two — and only two — legitimate paths to a fixed substrate are (a) the user set it, or (b) you
asked and the user told you to choose. "It was obvious," "the task implied it," or "I'll just pick the
standard one" are not substitutes for the answer. It is *not* a technical freedom the Guide quietly
picks. Record the outcome in a substrate `decisions/` ADR at the capsule root
(the foundational substrate *only* — never the full manifest, never the confined libraries), with the
concrete packages as `dependencies/` records. The foundational set, plus the framework's own domain
types, are the only types permitted to cross a public seam (`design-principles.md` §7).

## Load-bearing assumptions — prove the uncertain ones before designing on them

A product decision gets surfaced to the user; a load-bearing **feasibility assumption** gets *proven*,
not assumed. The trap is designing an elegant boundary on top of a premise that may simply be false — a
beautiful design over a false premise is wasted work, and when the premise is the product's core, a false
premise means a *different product* entirely (the excluded official API, a different channel).

Calibrate — this is not a licence to spike everything:

- **Feasibility already known to hold → design straight away.** Most products stand on proven ground: a
  CRUD app, a Monday/Trello-style tool, a second implementation of a capability that already works. There
  is no real doubt that it can be built; the value is entirely in *how well* it is designed. Proceed to
  the design objective — do not manufacture a feasibility question that isn't there.
- **A new product resting on a genuinely uncertain load-bearing assumption → prove it first.** Typically a
  brittle or unofficial external integration whose viability in the *target environment* is unproven (does
  a headless browser session survive on a cloud host past a restart without being blocked? does the
  undocumented endpoint behave as assumed?). Here the doubt itself is the **first-order objective**:
  record it, and make the first objective a **minimal build (an MVP / spike) that proves the assumption is
  plausible** — the smallest thing that exercises the risky premise end to end on the real target — before
  any design is built on top of it. Only once it holds do you invest in the ownership/boundary design that
  assumes it.

The test: *if this assumption turned out false, would the product have to become something else?* If yes,
and it is not yet proven, proving it is objective number one. If the assumption is obviously safe, don't
slow down — design.

## Ask one question at a time

Choose the highest-impact open product decision, ask one concrete question, record the answer, and re-evaluate. Stop only when no material open product decision blocks the next objective.

Do not bundle a questionnaire. Do not volunteer a catalog of hypothetical future features. A short discovery may still contain several turns when each answer exposes the next material decision.

## Record only actionable forces

Translate useful answers into concise **records in the code tree** — not into `.aims/state.md`, which
carries only loop status. Each kind of fact has a home, placed where the code it governs lives (location
is scope); record it as a fact + reason, never as a write-up of the discussion, and let the anchor tie
it to the code rather than restating it (`references/design-record.md`):

- **root `charter.md` + `requirements/`** — the primary goal, core use scenarios, explicit non-goals,
  and product-rule invariants (a rule the product must always honor).
- **a substrate `decisions/` record at the root** — a foundational dependency (day-zero substrate,
  boundary-crossing allowed). Foundational *only*.
- **a `component.md` in the part's directory + structural `decisions/` beside it** — a likely change
  axis (with its reason), a structural invariant, a real constraint, a boundary decision.

An *open* product decision is not yet a fact: it stays a live question (Loop cursor `awaiting-human`,
or the Guide TODO) until answered, then it is filed in the record it belongs to. A *technical freedom*
is not durable design — it rides in the Worker handoff for the objective that needs it.

Do not turn vague possibilities into requirements. Do not record a guess as a durable decision.
