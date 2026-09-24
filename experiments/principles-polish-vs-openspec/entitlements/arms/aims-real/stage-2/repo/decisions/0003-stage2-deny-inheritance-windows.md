---
title: "Stage-2 decision architecture: effects feed one combining owner"
date: 2026-09-23
supersedes-in-part: decisions/0002
---
**Context.** Stage 2 was a new product change: explicit deny, resource inheritance and validity windows. It
was the opening design round of a product change, so three Workers each designed the same objective, pulling
toward one axis each: clean code, encapsulation, or genericity. The Guide merged the three into `DESIGN.md`.
A mandatory review-and-revise round followed.

**Decision.**
- Only one private function, `_combine(frozenset[_Effect]) -> Decision`, produces a `Decision`. It owns
  "deny overrides allow; no applicable grant → deny".
- The clauses feeding it only filter, and each has its own owner:
  - `decide` gathers across all of U's roles;
  - `_Role.effects` reports the effects of the role's applicable grants;
  - `_Grant.applies` checks exact action ∧ resource ∈ lineage ∧ in force;
  - `_Hierarchy.lineage` returns R plus its ancestors, as a set;
  - `_Window.contains` checks the half-open `[from, to)` window.
- Deny is a first-class `_Effect` carried by a grant. It is distinct from the answer `Decision`.
- The hierarchy is a child → parent `Mapping` held inside the one immutable model. Cycles are rejected in
  `_Hierarchy.__post_init__`.
- `now` is a required, keyword-only, timezone-aware `datetime`, normalized to UTC once by `_instant`. Only
  the CLI reads the clock.
- No new public type. A grant is the stage-1 pair or a mapping keyed `action`/`resource`/`effect`/`from`/`to`.

**Strengths harvest.**
- *Clean code:*
  - the reduction proof that stage-1 answers are preserved at every `now`;
  - `_Permission` removed as a lazy class once equality stopped being the match rule;
  - grant-key validation moved into the core, so in-code and file input share one owner;
  - the core kept as one module;
  - a cycle and an undefined role reported together in phase 2.
- *Encapsulation:*
  - `_combine` as the sole producer of a `Decision`, pinned by an AST fitness test;
  - the argument that per-role verdicts are *wrong*: "X allows, Y has nothing" would come out DENY;
  - UTC normalization justified by the Python pitfall that aware datetimes sharing a tzinfo compare by wall
    clock across a DST fold;
  - overflow at `datetime.min`/`max`;
  - adjacent-window and role-collapse cases;
  - the `_ALWAYS` window, so no grant has an optional window.
- *Genericity:*
  - both-ends calibration of the two internal seams. The combining rule's input carries nothing it may not
    use, so "most specific wins" cannot be a local edit;
  - lineage is a set, not a path;
  - a separately supplied hierarchy rejected because it permits torn reads;
  - the 9-pair test of every deny level against every allow level.

**Axis splits.**
- *Decided: grant seam.* Clean code proposed a mapping only. Encapsulation proposed the pair plus a mapping.
  Genericity proposed a public `Grant` dataclass plus the pair. **Chose the pair plus a mapping using the
  file's key names.** Keeping the pair preserves stage-1 host code. The mapping shares one vocabulary with the
  file, so the core alone owns the keys and the `allow`/`deny` words. A public `Grant` would either be a
  second validation owner or a bag that gets validated anyway.
- *Decided: module split.* Genericity proposed `_time.py`/`_hierarchy.py`. **Chose one module.** The
  genericity draft itself flagged the split as thin, and folding it back changes no owner. Falsifier: split
  when a concept gains its own rule family.
- *Decided: `_Question`.* Encapsulation proposed it. **Not built.** Validation before lookup is already the
  first step of `decide`, and nothing else consumes the three values together.
- *Harmonized: where precedence lives.* Clean code and genericity put it inline in `decide`. Encapsulation used
  a `_combine` function. The combined shape: `decide` owns the quantifier over roles (gather), and `_combine`
  owns precedence (decide). This keeps `decide` at one altitude and makes the single owner testable.
- *Harmonized: naming and window invariant.* The set is named `lineage` (clean code, genericity), with
  encapsulation's "governing" meaning documented. `_Window.__post_init__` guards the window (clean code,
  encapsulation) rather than a `between` factory, so no invalid window can be built on any path.

**Revise round (same date).**
- The `_Hierarchy` invariant was moved to `__post_init__`, because a factory classmethod left the generated
  `__init__` as an unchecked path.
- The design now stores the validated parent map and walks it iteratively per question, instead of
  precomputing lineages. Precomputing was O(n²) on deep chains, and a recursive walk could hit the recursion
  limit.
- The fitness tests now name exact AST forms. The `now` parameter must not trip the clock-read check.
- The private `_CycleError` was removed in favour of a plain `ValueError` message.
- The file edge has exactly one grant spelling: objects.

**Consequences.**
- A stage-1 call `decide(u, a, r)` now raises `TypeError`. Callers must pass `now=`. Every stage-1 answer is
  preserved.
- These future changes each reopen one owner:
  - a precedence change reopens `_combine`;
  - multiple parents reopen `_Hierarchy`;
  - recurring windows reopen `_Window`.
- Superseded from 0002:
  - `_Permission`;
  - `_Role.grants`;
  - "deny is the absence of any grant";
  - "`decide` alone owns the grant rule", which is now three owners along the rule's own structure;
  - the loader's grant-key check.
