---
title: "flags.py"
date: 2026-09-22
hash: "sha256:7bc2521a875b84beff2ab3e8ad362d7b849c6c706bb470fe5f26f4fbdf01341b"
---

## Insights
- The product rule is an **ordering over the verdicts that apply**, not a property of any one rule.
  Stating it that way (`Verdict.outranks`) left `Resolver` with a fold and exactly one rule of its
  own — *nothing answered, so it is off* — and made "which rule wins" a thing you can read in one
  place.
- Because the ordering is decided by (authority, restrictiveness) and not by position, the answer is
  independent of the order rules are listed in; `test_flags.py` asserts that over every permutation
  of a conflicting set rather than one arbitrary order.
- A ramp is not a new way of picking users, only a new way of arriving at the **share**. Once
  `ScheduledRollout` computes its share from the clock and hands it to the same bucket comparison
  `Percentage` uses, everything the fixed rollout already guaranteed — stable cohorts, monotonic
  widening, no flicker — comes along for free, and mid-ramp membership is provably the membership
  of the fixed rollout it is passing through (`test_flags.py` asserts exactly that).
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
- **The instant is a parameter of the question, not something a rule reads.** `is_enabled(flag,
  user_id, now=None)` settles `now` once (defaulting to `int(time.time())`) and passes it to every
  rule, so one call is answered as of a single instant even while the clock moves, and a test can
  pin the instant without patching time. Rules that do not depend on the clock ignore the argument;
  `Resolver` still gained no branch.
- **`ScheduledRollout` speaks with `ROLLOUT` authority and reuses the published bucket.** It is a
  statement about a population, so it loses to an allow/block list and, against another rollout,
  the restrictive answer wins — the existing tier rule, unchanged. Only the share moves with the
  clock: flat at `start_percent` up to `start_at`, linear inside the window, flat at `end_percent`
  from `end_at` on (the window is half-open, so `end_at` belongs to "after").
- **The bucket contract now has one home, `_BucketedRollout`.** A second rollout rule with its own
  copy of the derivation would be a second contract that could drift; sharing it is what makes a
  user sit in one place in the population however the share is arrived at.
- **A `ScheduledRollout` with `end_at <= start_at` is rejected at construction** (`ValueError`), as
  are non-integer times (`TypeError`, `bool` rejected). An empty or reversed window has no linear
  ramp to describe, so refusing it at construction keeps the resolution path free of a
  divide-by-zero special case — the same "never in an invalid state" rule `percent` follows.

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
- Considered giving `ScheduledRollout` its own `Authority` tier between `ROLLOUT` and `EXPLICIT`,
  so a scheduled ramp could override a fixed rollout. Dropped: nobody asked for it, and a tier is
  a product rule — inventing one would quietly change what "a block beats everything" means.
- Considered reading the clock inside the rule (`time.time()` at verdict time) instead of threading
  `now` through. Rejected: two rules in one call could then land on different instants, and tests
  would have to patch the module clock to ask about a fixed moment.
- Considered accepting a float `now` (so `time.time()` can be passed straight through). Dropped for
  now: the record says integer epoch seconds, and a single strict validator for `start_at`, `end_at`
  and `now` says so in one place; callers pass `int(time.time())`, which the error message names.
- A descending ramp (`end_percent` below `start_percent`) is allowed rather than rejected — winding
  a feature back down is the same shape of operation, and the "nobody loses it" guarantee was always
  a property of a *widening* share, not of the rule kind.
- **Unproven, inherited from an unanswered question:** the task card does not say what *two*
  `Percentage` rules on the same flag should mean (nor a `Percentage` overlapping a
  `ScheduledRollout`). The tier rule makes the restrictive one win, so the result is deterministic,
  but nobody confirmed that is the intended behavior. Unconfirmed too: whether a ramp whose window
  has already passed should keep answering at `end_percent` forever (it does) or be retired. Also unconfirmed
  with the product owner: that a fractional `percent` is meaningful, and that user ids compare as
  exact, case-sensitive strings.
