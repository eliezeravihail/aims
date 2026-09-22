---
title: "flags.py"
date: 2026-09-22
hash: "sha256:1982f621c2599fc41b35fc3917545f91be7518a97c56c43ac43fa8ce3d81712d"
---
## Discussions
- An if-chain in `Resolver` (any block -> off, else any allow -> on, else the percentage) was considered
  and rejected: it would have owned the precedence rule *and* knowledge of every rule kind at once, so a
  fourth kind reopens it — an isinstance switch over anemic rule objects. The road not taken is why
  precedence sits on `Verdict` and `Resolver` is a fold.
- A `Decision(ON/OFF)` enum inside `Verdict` was considered and dropped: abstention is already `None`,
  so the enum would have been a boolean with a label on it.
- `Percent` / `FlagKey` / `UserId` value objects and a module-specific exception type were considered and
  dropped: the public API is strings by contract, percent's only rule is a range already enforced at
  construction, and nothing anywhere catches a distinct error type.
- 10_000 buckets were chosen over 100. Both cost the same, but 100 cannot express a rollout below 1%,
  and moving from 100 to 10_000 afterwards would have been a change to the published bucket contract —
  a user-visible migration. The count was picked once, up front, for that reason.
- An index from flag to the rules that mention it was considered for `Resolver` and dropped: it would
  have pulled "a rule names exactly one flag" up into the `Rule` contract, where today it is a
  convenience of `_FlagRule` alone. The price paid instead is a linear scan of every rule per lookup,
  which rests on the unproven assumption that rule sets stay small.
- Three behaviours were never confirmed with anyone; they fell out of the mechanism rather than being
  specified, and the tests pin them only as they stand: what two `Percentage` rules on one flag should
  mean (the tier rule makes the restrictive one win, deterministically), whether a fractional percent is
  meaningful, and whether user ids compare as exact case-sensitive strings.
