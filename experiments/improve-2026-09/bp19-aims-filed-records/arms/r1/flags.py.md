---
title: "flags.py"
date: 2026-09-22
hash: "sha256:1982f621c2599fc41b35fc3917545f91be7518a97c56c43ac43fa8ce3d81712d"
---

## Insights
- The product rule is an **ordering over the verdicts that apply**, not a property of any one rule.
  Stating it that way (`Verdict.outranks`) left `Resolver` with a fold and exactly one rule of its
  own — *nothing answered, so it is off* — and made "which rule wins" a thing you can read in one
  place.
- Because the ordering is decided by (authority, restrictiveness) and not by position, the answer is
  independent of the order rules are listed in; `test_flags.py` asserts that over every permutation
  of a conflicting set rather than one arbitrary order.
- "Stable across processes and restarts" is what forces the hash choice: Python's built-in `hash()`
  of a string is salted per process, so it reshuffles every cohort on restart while looking correct
  in any single run. Evidence, not assertion: the resolver is run in two fresh interpreters with
  different `PYTHONHASHSEED` values and the answers compared.

## Decisions
- **Precedence has one home: `Verdict.outranks`.** Higher authority wins (`EXPLICIT` over
  `ROLLOUT`); within one authority the restrictive answer wins. Block-beats-allow is a corollary,
  not a separate rule. A new kind of rule declares its `Authority` and returns a `Verdict`; it must
  not add a branch to `Resolver`.
- **A rule that does not apply abstains (`None`); it never returns an "off" verdict.** "Off" is
  always something a rule actually said, so the default-off for an unconfigured flag lives in
  `Resolver` alone and cannot be silently produced by a rule that merely failed to match.
- **The percentage bucket is a published contract, not an implementation detail:**
  `int.from_bytes(sha256(f"{flag}:{user_id}").digest()[:8], "big") % 10_000`, on iff the bucket is
  below `percent`% of that space. It may not be changed without treating it as a user-visible
  migration — a different derivation moves live users between cohorts. A golden vector in
  `test_flags.py` makes such a change fail loudly.
- **A rule object is never in an invalid state:** `percent` is validated at construction (a real
  number, `bool` rejected, within 0–100) and the flag name must be a string; violations raise
  `TypeError`/`ValueError` there, not at resolution time.
- **Membership rules copy their ids into a `frozenset` at construction**, so a caller mutating the
  list it passed in cannot change answers afterwards.

## Discussions
- Considered resolving with an if-chain in `Resolver` (any block → off, else any allow → on, else
  the percentage). Rejected: the chain owns the precedence rule *and* the knowledge of every rule
  kind, so the fourth kind reopens it — an `isinstance` switch over anemic rule objects.
- Considered a `Decision(ON/OFF)` enum inside `Verdict`; dropped. Abstention is already carried by
  returning `None`, so the enum was a boolean with a label.
- Considered `Percent` / `FlagKey` / `UserId` value objects and a module-specific exception type;
  dropped. The public API is strings by contract, `percent`'s only rule is a range enforced at
  construction, and nothing catches a distinct error — none of them would own anything today.
- 10_000 buckets rather than 100, so a rollout can be expressed below 1% (a routine early-rollout
  need). Cost is zero; going from 100 buckets to 10_000 later would be a contract change.
- **Unproven, inherited from an unanswered question:** the task card does not say what *two*
  `Percentage` rules on the same flag should mean. The tier rule makes the restrictive one win, so
  the result is deterministic, but nobody confirmed that is the intended behavior. Also unconfirmed
  with the product owner: that a fractional `percent` is meaningful, and that user ids compare as
  exact, case-sensitive strings.
