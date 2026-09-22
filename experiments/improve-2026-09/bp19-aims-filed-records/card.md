# Task: a feature-flag rollout resolver

Build a Python module `flags.py`. No external dependencies.

## What it must do

Decide whether a feature is on for a given user.

- `Resolver(rules)` — `rules` is a list of rule objects (below), evaluated to a single on/off answer.
- `resolver.is_enabled(flag: str, user_id: str) -> bool`

## Rule kinds

- `Percentage(flag, percent)` — the feature is on for `percent`% of users. The same user must always get
  the same answer for the same flag (stable across processes and restarts).
- `AllowList(flag, user_ids)` — on for exactly these users.
- `BlockList(flag, user_ids)` — off for exactly these users.

## Resolution

Several rules may apply to the same flag. A block beats an allow; an explicit list beats a percentage.
If no rule matches the flag at all, the feature is off.

Money/time are not involved. Keep it clean and correct.
