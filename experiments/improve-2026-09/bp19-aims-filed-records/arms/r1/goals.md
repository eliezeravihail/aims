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
- **Scheduled ramp** — the percentage is set to climb (or wind back down) linearly over a stated
  window, so the rollout advances on its own without anyone editing a rule. The answer still depends
  only on the user and the instant, so it is the same on every machine at the same second.
- **Early access** — named users get the feature regardless of the rollout.
- **Damage control** — a named user is taken off the feature even though the rollout (up to 100%)
  covers them.
- **An unconfigured flag** — code asks about a flag no rule mentions and gets a safe *off*.

## Non-goals
- No storage, configuration format, remote fetch, or hot reload — rules are handed in by the caller.
- No targeting on anything but the user id and the current time (no country, plan, or device). Time
  enters only as a scheduled ramp of the rollout percentage — never as calendar or time-zone logic:
  instants are integer epoch seconds, supplied by the caller or read from the local clock.
- No multivariate flags or variants: the answer is on/off.
- No exposure logging, metrics, or audit trail.
- No external dependencies.
