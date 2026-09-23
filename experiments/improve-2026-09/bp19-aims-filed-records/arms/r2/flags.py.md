---
title: "flags.py"
date: 2026-09-22
hash: "sha256:3888bc7e1547fa6de3ecc531f638897027682b26649475046c1fbe5fe956b2ae"
---

## Insights
- The product rule is an **ordering over the verdicts that apply**, not a property of any one rule.
  Stating it that way (`Verdict.outranks`) left `Resolver` with a fold and exactly one rule of its
  own — *nothing answered, so it is off* — and made "which rule wins" a thing you can read in one
  place.
- Because the ordering is decided by (authority, restrictiveness) and not by position, the answer is
  independent of the order rules are listed in; `test_flags.py` asserts that over every permutation
  of a conflicting set rather than one arbitrary order.
- A ramp is not a new *kind* of question, only a percentage that depends on the instant. Once the
  instant is a parameter, `ScheduledRollout` is a `_percent_at(now)` and nothing else: the bucketing,
  the comparison against the bucket space, and the `ROLLOUT` authority are shared with `Percentage`
  through `_RolloutRule`, and `Resolver` did not learn a third rule kind exists.
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
- **The instant is a parameter of the rule protocol, not something a rule reads.**
  `verdict_for(flag, user_id, now)`; `Resolver.is_enabled(flag, user_id, now=None)` stamps
  `int(time.time())` once when `now` is omitted and hands that one instant to every rule. Rules stay
  pure functions of (flag, user, instant), one call is answered as of a single moment however long
  the fold takes, and a test can pin the clock without patching anything. This widened the abstract
  `Rule` signature — the cost of keeping "same user, same answer" checkable.
- **The bucket derivation has one home for *all* rollout kinds:** module-level
  `_bucket_of(flag, user_id)`, unchanged from the published contract above and still pinned by the
  golden vector. Every rollout rule buckets identically, so replacing a fixed `Percentage` with a
  ramp that passes through the same percentage moves nobody between cohorts — which is what makes a
  scheduled ramp safe to introduce on a live flag.
- **The ramp window is half-open `[start_at, end_at)`:** at `start_at` nothing has moved yet
  (`start_percent`), at `end_at` the ramp is already over (`end_percent`). Consequences worth naming:
  an empty window (`start_at == end_at`) is a well-defined step rather than a division by zero, and
  the interpolation only ever divides inside a non-empty window.
- **Times are integer epoch seconds, enforced at construction and at `is_enabled`:** a float is
  rejected rather than silently truncated, `bool` is rejected as `percent` rejects it, and
  `end_at < start_at` is a `ValueError`. A backwards ramp is a configuration mistake with no sane
  reading; a *downward* one (`end_percent < start_percent`) is not, so it is allowed and documented
  as taking the feature away as it narrows.

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
- Considered letting `ScheduledRollout` read `time.time()` itself and leaving `is_enabled`'s
  signature alone. Rejected: two rules in one fold could then straddle a second boundary, so a
  single call could contradict itself, and the only way to test a ramp would be to patch the clock.
- Considered a `Clock`/`Query` object carrying the instant (and room for later context). Dropped for
  the same reason the earlier value objects were dropped — today it would own nothing but a plain
  `int`, and the abstract method already names it.
- Considered composing a ramp out of existing pieces (a `Percentage` plus a time window rule that
  abstains outside it). Rejected: the window rule would have to answer "off" outside the window or
  abstain inside it, and either way two rules would have to agree on a percentage neither owns.
- Rounding of the ramped percentage is deliberately absent: the bucket space is 10_000 wide, so a
  ramp over a window shorter than ~10_000 seconds simply moves in bucket-sized jumps. Quantising the
  percentage to whole buckets would be the same answers, spelled with more code.
- **Unproven, inherited from an unanswered question:** the task card does not say what *two*
  `Percentage` rules on the same flag should mean. The tier rule makes the restrictive one win, so
  the result is deterministic, but nobody confirmed that is the intended behavior. Also unconfirmed
  with the product owner: that a fractional `percent` is meaningful, and that user ids compare as
  exact, case-sensitive strings.
- **Unproven, from this change:** `goals.md` previously listed "no time window" as a non-goal and the
  change request overturned it; the non-goal was amended rather than treated as a veto, but nobody
  confirmed that time is meant only as a rollout *schedule* (the reading taken here) rather than as a
  targeting dimension callers may eventually want in its own right — e.g. "on only during business
  hours", which this design deliberately does not provide.
