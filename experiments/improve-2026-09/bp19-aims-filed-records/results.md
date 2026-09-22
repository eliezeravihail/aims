---
title: "BP19 — do aims-filed records help a blind agent make a non-elementary change?"
date: 2026-09-22
n: 3 per arm
---

# What this test is, and why the earlier record-layer tests were not it

Six earlier attempts (I5, BP15, BP15b, BP16, BP16b, BP17) claimed to test the record layer. They did
not: **I wrote the records by hand**, having never read
[`design-record.md`](../../../skills/aims-guide/references/design-record.md), so they tested my
construction, not aims (see [`../AUDIT-record-layer-claims.md`](../AUDIT-record-layer-claims.md)).

BP19 is the first where **aims filed the records**. An agent invoked the real `aims-guide` skill on the
build task, produced `build/flags.py` + `build/test_flags.py`, and filed four records by the skill's own
filing rule — `goals.md` (26 lines), `base-dependencies.md` (14), `decisions/0001-…` (23), and one
companion `flags.py.md` (54); **117 lines total**. It explicitly declined to create `architecture.md`,
citing the "count the files it binds" discriminator. That is the treatment.

## Design

- **Task:** the change request in [`change-request.md`](change-request.md) — add
  `ScheduledRollout(flag, start_percent, end_percent, start_at, end_at)` and thread an explicit
  `now=None` through `is_enabled`. Non-elementary: it introduces a second kind of "percentage", and it
  introduces *time* into a module whose stated non-goal forbade time targeting.
- **Arms (n = 3 each), all blind to this session and to each other:**
  - `r1 r2 r3` — given `flags.py`, `test_flags.py`, **and the four records**.
  - `n1 n2 n3` — given `flags.py` and `test_flags.py` **only**.
- **Floor (a gate, never a ranking signal — `decisions/0021`):** the *original* 29-test suite must still
  pass. **All six arms: 29/29.** Each arm's own extended suite also passes (r1 53, r2 46, r3 50,
  n1 48, n2 47, n3 51). Per `0021`, passing earns nothing.
- **Measure:** the §0–§14 design rubric, scored blind from the code by a judge that saw six anonymized
  `design-{A..F}.py` files, no records, no arm labels, and no mapping. Mapping sealed in
  [`blind/MAPPING-SECRET.txt`](blind/MAPPING-SECRET.txt) before the judge ran; unsealed after its report.

## Result 1 — the rubric scores (weak, n = 3)

Judge totals on the BP14 9-metric §0–§14 instrument (45 max), with the mapping unsealed afterwards:

| blind | arm | total |
|---|---|---|
| F | **r2** (records) | **40** |
| B | **r3** (records) | **38** |
| A | n2 (no records) | 36 |
| C | n1 (no records) | 36 |
| D | **r1** (records) | **36** |
| E | n3 (no records) | **29** |

- records: mean **38.0**, floor **36**, spread 4
- no records: mean **33.7**, floor **29**, spread 7

**Read this honestly: it is not a win.** The whole gap is one arm — drop `n3` and the two groups are
36/38/40 vs 36/36, indistinguishable at n = 3. What the numbers are *consistent with* is the shape BP6/BP7
already found — aims raising the **floor** and cutting the **spread**, not lifting the ceiling — but three
points per arm cannot establish that. **Directional at best; not evidence.**

The judge, blind, named the separating property itself: **whether the instant is an argument or ambient
state.** `n3` resolves the clock at three sites (`flags.py:138`, `:220`, `:291` all call `_resolve_now`),
so two rules folded in one `is_enabled` call can be answered at different instants — the module's own
primary goal ("the same answer everywhere and every time") broken by construction. `r2` stamps
`int(time.time())` once (`flags.py:288`) and hands that one instant to every rule.

**But the records cannot be credited for that.** `change-request.md` told *both* arms to make `now` an
explicit parameter; nothing in the four records says where the clock should be read. `n3` had the same
instruction and still spread it. The mechanism is unproven, so the rubric result stays what it is: a
suggestive floor difference with no demonstrated cause.

## Result 2 — the one clean, categorical finding: 3/3 vs 0/3

The filed `goals.md` carried this non-goal:

> - No targeting on anything but the user id (no country, plan, device, **or time window**).

The change request **contradicts it**. Every records arm caught that, independently, and amended the
record rather than silently violating it:

- **r1:** "No targeting on anything but the user id **and the current time** … Time enters only as a
  scheduled ramp of the rollout percentage — never as calendar or time-zone logic."
- **r2:** "Time is a *schedule* for a rollout, never a condition a caller can target on directly, and it
  is passed in rather than read from the clock by the rules themselves."
- **r3:** "The clock enters only as the instant a question is asked about — `is_enabled(flag, user_id,
  now=None)` — and only a scheduled ramp reads it."

All three also added a **Scheduled ramp** use scenario, and all three amended the companion
`flags.py.md` with new Insights/Decisions and re-stamped its anchor hash (r1 +51 lines, r2 +43, r3 +42).
None added a new ADR — correctly: no new system-level decision was taken.

**0/3 blind arms did any of this**, and could not have: the non-goal exists nowhere but the record. The
code compiles, the tests pass, and nothing in `flags.py` says "time was ruled out on purpose."

`r1 r2 r3` = 3/3. `n1 n2 n3` = 0/3.

## Follow-up — did the declared intent change the *code*? **No. 6/6 null.**

The 3/3 amendment above is worth nothing if it is only bookkeeping. So: **did the records arms, having
narrowed the non-goal to "time is a schedule for a rollout, never a targeting condition", build that
constraint into the code more than the blind arms did?**

Predicate fixed before inspecting the blind arms ([`followup-predicate.txt`](followup-predicate.txt) —
and honestly labelled there as *not* blind on the records side, since it was derived from those arms' own
companion prose):

> Does `ScheduledRollout` compute a **percentage** for the instant and hand it to the **same bucket
> derivation and comparison `Percentage` uses** — so mid-ramp membership *is* the membership of the fixed
> percentage it is passing through — rather than re-deriving its own membership test? And does `Resolver`
> gain a branch for the new kind?

| arm | shared rollout base | `ScheduledRollout` reuses the bucket | `Resolver` branch |
|---|---|---|---|
| r1 | `_RolloutRule` | ✅ | none |
| r2 | `_RolloutRule` | ✅ | none |
| r3 | `_BucketedRollout` | ✅ | none |
| n1 | `_RolloutRule` | ✅ | none |
| n2 | `_RolloutRule` | ✅ | none |
| n3 | `_BucketRollout` | ✅ | none |

**6/6 pass. 0/6 type-dispatch.** Every `isinstance` in every arm is argument validation; not one is
dispatch. All six independently produced the *same* hierarchy — `Rule` → `_FlagRule` → {shared-rollout
base → `Percentage`, `ScheduledRollout`} and {`_MembershipRule` → `AllowList`, `BlockList`} — differing
only in the private base class's name. `r1`'s and `n1`'s `Resolver.is_enabled` bodies are near-identical
line for line.

**This is a null, and it narrows BP19's claim sharply.** The declared intent changed the *record* and not
the *code*. It also explains the rubric cluster (36–40, no group separation): the designs are structurally
the same, so there was nothing for the rubric to separate. `n3`'s 29 is a **local** defect — the clock
resolved at three sites — not an architectural difference, which is why one arm moved the whole mean.

It is consistent with everything the campaign already found: on a well-formed codebase a strong model
converges, and the record adds nothing the code was not going to say anyway. What it cannot add is what is
**not** in the code — which is exactly, and only, the non-goal.

## What BP19 actually establishes

1. **A non-null, at last** — the first in this campaign, and **narrower than it first looked.** It is
   **not** about code quality: the follow-up above shows all six arms built the *same* design, so the
   records changed nothing structural. What a record holds is a **declared intent the code cannot**, so a
   change contradicting that intent is *visible* and gets reconciled instead of drifting silently. Neither
   the test floor nor the §0–§14 rubric can see that: a design can score 45/45 while quietly breaking what
   the project said it would not do. **The value demonstrated here is record fidelity, not better code.**
2. **The design-quality claim is not merely unproven — it came back null here.** n = 3 with one outlier
   and no mechanism, *and* a 6/6 structural convergence saying there was no design difference to find.
   BP19 does **not** license "records produce better designs"; on this task it is evidence against.
3. **It corroborates the earlier nulls rather than overturning them.** Six confounds showed a *rule or
   convention* is recoverable from a well-formed codebase. A **non-goal** is the thing that is not — it
   is the absence of code, and absence leaves no trace to recover.

## Threats to validity

- **n = 3 per arm**, one judge, one product, one change. Protocol §3 wants n ≥ 2 for a wording change;
  this is a claim about the record layer and deserves more.
- **The records arms got 117 more lines of context.** More text could produce more care by itself; an
  arm given 117 lines of *irrelevant* prose is the control BP19 lacks. (The 6/6 convergence makes this a
  weaker worry than it was: there is no structural difference for the extra text to explain.)
- **One task, one scale.** A single ~300-line module is small enough that a strong model converges on the
  right design unaided. The design-quality question needs a codebase where the pattern is **not** visible
  in the code — the frontier the synthesis already names.
- **Amending `goals.md` is the behavior the skill asks for**, so 3/3 partly measures instruction-following.
  What it does establish is that the contradiction was *detectable at all* — which is the claim.
- The judge's separating property was found blind, but the attribution to records is mine, post-hoc, and
  I have marked it unproven above.
