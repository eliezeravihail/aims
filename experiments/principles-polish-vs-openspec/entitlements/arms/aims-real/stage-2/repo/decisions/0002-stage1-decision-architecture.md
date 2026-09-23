---
title: "Stage-1 decision architecture: one immutable model owns the grant rule"
date: 2026-09-23
---
**Context.** The opening design round of a new product. Three Workers designed the same objective, each pulling
toward one axis: clean code, encapsulation, or genericity. The Guide merged their designs into `DESIGN.md`,
and a mandatory review-and-revise round followed.

**Decision.**
- A single immutable `EntitlementModel` holds the model.
- Its keyword-only constructor is the only seam a model source goes through.
- `decide(user, action, resource) -> Decision` is its only public member, and the grant rule lives there
  alone.
- The public seam takes strings. The internal types (`Permission` and the role type) never cross it.
- JSON loading and the CLI are edge modules that call the constructor. The core imports no I/O.
- There is no holder, source protocol or builder. To replace the model, a host builds a new one and rebinds
  its reference.

**Strengths harvest (what each axis contributed).**
- *Clean code.*
  - The core is one module, because its parts share one reason to change.
  - A single identifier validator replaces four look-alike id types.
  - `Permission` value equality stands in for matching code.
  - `import entitlements` does not pull in the edges.
  - No dependency beyond the stdlib, not even for tests.
- *Encapsulation.*
  - Each user maps to resolved role objects, so a dangling role cannot be represented.
  - `decide` is the only public member.
  - A question is validated before any lookup, so a malformed question about an unknown user raises
    instead of returning deny.
  - One error lists every undefined-role pair.
  - Unknown file keys are rejected.
  - Guards stop a bare string from being unpacked into characters.
  - Architecture fitness tests keep the seams honest.
- *Genericity.*
  - A table sets each seam's floor (what the consumer needs) and ceiling (what producers can supply).
  - The seam takes strings because a raw string never equals a typed id in Python, which would turn a
    wrongly typed argument into a silent deny.
  - One error type per distinct handling, so a file failure shares `InvalidModelError`.

**Axis splits and how each was resolved.**
- *Four id types (genericity, encapsulation) vs. one validator (clean code).* Chose one validator. The four
  types carry one identical rule and never cross a seam. Falsifier: when one kind of id gains a rule of its
  own, it gets its own type.
- *`bool` (clean code) vs. a `Decision` enum (the other two).* Chose the enum. A5 names two outcomes, and the
  CLI maps each to text and an exit code in one place.
- *`ModelFileError` (clean code) vs. folding file failures into `InvalidModelError` (genericity).* Chose the
  shared type, because a host handles both the same way: reject the new model, keep the old one.
- *Duplicate JSON keys: merge (encapsulation) vs. reject (clean code, genericity).* Chose reject (A7). A
  repeated block in a hand-edited file is more likely a mistake than intent, and rejecting it loses no
  expressiveness.
- *Harmonized: public `Permission` (clean code) vs. strings at the seam (the other two).* Tuples of strings
  cross the seam and `Permission` stays internal. This keeps clean code's "equality is the matching rule"
  and still closes the silent-deny hole.
- *Harmonized: `_Role` objects (encapsulation) vs. name-keyed maps (clean code, genericity).* Resolving
  names at construction satisfies both. The model stays small, and A3 holds by the model's structure
  rather than by a check at query time.

**Consequences.** A later stage that adds deny rules, wildcards or hierarchy reopens `decide` and the role
clause. That is the intended single owner for those changes. A reload lifecycle would be the force that
introduces a holder.

**Revise round (same date).**
- *Identifier inputs.* Any `str` instance, including an `enum.StrEnum` member, is accepted. It is then
  normalized to a plain `str`, which keeps exact matching safe from a subclass that overrides equality.
  The earlier design rejected subclasses instead, which is no longer done. As a consequence, two in-code
  keys that become the same string after normalization are rejected. This is the in-code counterpart of A7.
- *Role name.* `_Role` no longer stores its name, because nothing read it.
- *Rule owners.* The grant rule has three owners, one per clause: `decide` owns "any role",
  `_Role.grants` owns what one role grants, and `_Permission` owns when two permissions are equal.
- *Error policy.* Constructor errors come in two phases. A parse error reports the first problem found. A
  consistency error reports every undefined-role pair at once.
