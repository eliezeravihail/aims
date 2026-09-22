---
title: "flags.py"
date: 2026-09-22
hash: "sha256:333037cfecf7e2158edb817dbe28ce92e4a8d55901686ccecda1cd873c4fe559"
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
- A rollout that changes with time does not need a rule that *changes*: `ScheduledRollout` is a pure
  function of the instant it is asked about, so "same user, same answer" simply extends to "at the
  same instant". Time entered as a parameter of the question (flag, user, instant) rather than as
  state inside a rule or a clock the rule reaches for; that is what lets a test replay a ramp second
  by second and what keeps two rules in one call from straddling a tick.
- The ramp turned out to need nothing new below it: percentage-of-a-population was already a
  separate idea from *which* percentage, so lifting the bucket into `_RolloutRule` gave the new kind
  its cohort for free — and gave it, deliberately, the *same* cohort a fixed `Percentage` of that
  size hands out, so a flag can graduate from a ramp to a fixed percentage without churn.

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
- **The instant is an argument, not ambient state.** `Rule.verdict_for(flag, user_id, now)` carries
  it, and `Resolver.is_enabled(flag, user_id, now=None)` reads the clock **once per call**
  (`int(time.time())`) and hands the same instant to every rule. No rule calls the clock itself, so
  one answer is never assembled from two instants, and a caller can pin `now` to replay exactly what
  production returned at that second. Cost, accepted: the rule protocol grew a parameter that
  timeless rules ignore — the alternative (a rule reading the clock) gives up the guarantee.
- **The bucket derivation moved to `_RolloutRule` and is unchanged.** It is the same published
  contract as before, now stated once for every rule that speaks about a population; the golden
  vector in `test_flags.py` still pins it. Any rollout kind, fixed or scheduled, therefore selects
  the *same* users at the same percentage.
- **`[start_at, end_at)` is half-open, and the ramp is flat outside it.** At `start_at` the rollout
  is exactly `start_percent`; from `end_at` on, exactly `end_percent` — read from the endpoint, not
  interpolated, so the ends carry no floating-point drift and an empty window
  (`start_at == end_at`) is a clean step instead of a division by zero.
- **A `ScheduledRollout` is never in an invalid state:** both percentages are validated exactly as
  `Percentage`'s is, `start_at`/`end_at` must be integer epoch seconds (`bool` and `float` rejected,
  matching the stated contract), and `end_at` may not precede `start_at` — all `TypeError`/
  `ValueError` at construction. `now` is checked the same way at the call. A **falling** ramp
  (`end_percent < start_percent`) is *allowed*: it is the planned way to wind a feature back down,
  and on the shared buckets it removes users in the exact reverse of the order it added them.

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
- Considered letting `ScheduledRollout` call `time.time()` itself and leaving `Resolver` alone,
  which would have kept the rule protocol untouched. Rejected: two rules in one resolution could
  then land on different seconds, and nothing could be replayed — the ramp would be the one rule
  whose answer you cannot reproduce, which is the opposite of what `goals.md` asks for.
- Considered bundling `(flag, user_id, now)` into a `Query` value object instead of a third
  parameter. Dropped for the same reason the earlier value objects were: it would own nothing
  today, and it would rewrite every rule signature to buy a name.
- Considered subclassing `ScheduledRollout` from `Percentage` (a percentage that happens to move).
  Rejected: it would inherit a `percent` that is not the answer at any given instant. The shared
  thing is the *bucket*, so that is what the common base (`_RolloutRule`) holds.
- Considered clamping the interpolated percentage into 0–100 defensively. Unnecessary: both
  endpoints are range-checked at construction, so every point between them is in range.
- **Unproven, needs the product owner:** a falling ramp is accepted and read as a deliberate
  wind-down, but nobody confirmed the product wants users *removed* from a feature by a schedule.
  Also unconfirmed: that a rollout scheduled entirely in the past should simply read as
  `end_percent` forever (it does), rather than being an expired rule that ought to be flagged.
- **Time zones and clock skew are out of scope by construction** — instants are epoch seconds, so
  there is no calendar arithmetic here. What is *not* settled is whose clock decides when callers
  run on several machines; today it is each caller's, which can straddle a ramp boundary by the
  size of the skew.
