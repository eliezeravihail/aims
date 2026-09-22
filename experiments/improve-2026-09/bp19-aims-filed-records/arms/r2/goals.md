---
title: "goals"
date: 2026-09-22
---

## Primary goal
Answer one question — *is this flag on for this user?* — with an answer that is the **same
everywhere and every time**: same process or another, today or after a restart, whatever order the
rules happen to be listed in. The rules that decide it (a block beats an allow, an explicit list
beats a percentage, an unconfigured flag is off) are product rules, so they have one home and are
stated, not spread across call sites.

## Use scenarios
- **Gradual rollout** — the feature is on for a percentage of users, and a user who has it keeps it
  as the percentage widens; nobody flickers between releases.
- **Scheduled ramp** — the rollout widens on a clock rather than by hand: it moves from one
  percentage to another across a window, and a user picked up on the way up keeps the feature.
- **Early access** — named users get the feature regardless of the rollout.
- **Damage control** — a named user is taken off the feature even though the rollout (up to 100%)
  covers them.
- **An unconfigured flag** — code asks about a flag no rule mentions and gets a safe *off*.

## Non-goals
- No storage, configuration format, remote fetch, or hot reload — rules are handed in by the caller.
- No targeting on anything but the user id and the current time (no country, plan, or device).
  Time is a *schedule* for a rollout, never a condition a caller can target on directly, and it is
  passed in rather than read from the clock by the rules themselves.
- No multivariate flags or variants: the answer is on/off.
- No exposure logging, metrics, or audit trail.
- No external dependencies.
