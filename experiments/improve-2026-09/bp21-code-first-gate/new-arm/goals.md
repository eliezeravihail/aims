---
title: "goals"
date: 2026-09-22
---
## Primary goal
Answer "is this flag on for this user?" and give the same answer every time — same (flag, user) pair,
any process, any machine, after any restart. Consistency is the product; the rule kinds exist to serve
a rollout that can be widened without anyone's answer flipping back.

## Use scenarios
- A percentage rollout widened in steps, where a user who already has the feature must not lose it.
- A named user let in ahead of a rollout, or held out of one, with several rules live on the same flag.
- Answering in the caller's own process, from a rule set it already holds — no service to ask.

## Non-goals
- **No external dependencies.** The resolver is meant to be dropped into any process without pulling
  anything in, so the standard library is the ceiling, not the current state of the imports. A
  dependency that would improve hashing, config parsing or rule storage is still out of scope; the cost
  of being addable anywhere is paid deliberately.
- **No money and no time.** Nothing here is billed on, metered or scheduled, and it was not built to
  be. There is deliberately no audit trail of who was in which bucket when, no clock, and no
  activate-at-a-date rule — a flag's answer depends on the rule set and the user, and on nothing else.
  A caller that needs a decision it can later prove, or one that turns over at a moment, needs a
  different component, not another rule kind here.
