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
- **Which goal this tests:** **goal 2 only.** The variable is the record layer; the design method (the
  Guide/Worker loop and the review) ran in **neither** arm. See `../../../goals.md` — the two goals are
  judged by different instruments and never merged.
- **The goal-2 measure:** does the knowledge in the records **survive and get acted on** — specifically, is
  a change that contradicts a **declared intent** detected and reconciled, or does it drift silently?
- **Also recorded, for completeness (a goal-1 instrument):** the §0–§14 rubric, scored blind from the code
  by a judge that saw six anonymized `design-{A..F}.py` files — no records, no arm labels, no mapping.
  Mapping sealed in [`blind/MAPPING-SECRET.txt`](blind/MAPPING-SECRET.txt) before the judge ran, unsealed
  after its report. **This is not the measure of the thing BP19 varies**, and it is not read as one.

## Result 1 — the rubric scores (a goal-1 instrument, reported here only for completeness)

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

**Read this honestly: it is not a result about records at all.** The rubric measures **goal 1** (correct
design), and BP19 varies only the **goal-2** instrument. Even taken at face value the gap is one arm — drop
`n3` and the two groups are 36/38/40 vs 36/36, indistinguishable at n = 3. The follow-up below shows why:
all six designs are structurally the same. **Not evidence, in either direction.**

The judge, blind, named the separating property itself: **whether the instant is an argument or ambient
state.** `n3` resolves the clock at three sites (`flags.py:138`, `:220`, `:291` all call `_resolve_now`),
so two rules folded in one `is_enabled` call can be answered at different instants — the module's own
primary goal ("the same answer everywhere and every time") broken by construction. `r2` stamps
`int(time.time())` once (`flags.py:288`) and hands that one instant to every rule.

**And the records are not credited for it.** `change-request.md` told *both* arms to make `now` an explicit
parameter; nothing in the four records says where the clock should be read. `n3` had the same instruction and
still spread it. That is a one-arm lapse on a goal-1 property, in an experiment that does not manipulate the
goal-1 instrument.

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

## Follow-up — a fact about the *task*, not a verdict on the record layer

**First, the framing error this section originally made, so it is not repeated.** aims has **two goals**
(`../../../goals.md`), served by different machinery and judged by **different** instruments:

| | goal 1 — correct design | goal 2 — knowledge not in the code |
|---|---|---|
| served by | the design method (Guide/Worker, §0–§14, the review) | the record layer |
| measured by | the §0–§14 rubric, from the code | does the knowledge survive and get acted on |

BP19 varies **only the records**. Records are a **goal-2** instrument; they are not the design method. So
**BP19 is not a test of goal 1 at all**, and reading its rubric comparison as one — which the first version
of this file did — is a category error. The rubric numbers below are reported as a property of the *task*,
not as a verdict on records, and they neither support nor narrow the goal-2 result above.

With that said, the structural question is still worth asking about **this task**: did the arms differ in
design at all?

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

**What this says: the task had no design difficulty.** All six arms converged, so there was nothing for the
rubric to separate — which is why the scores cluster at 36–40 with no group difference, and why `n3`'s 29 is
a **local** defect (the clock resolved at three sites) rather than an architectural one.

**What this does *not* say.** It is not evidence against the record layer. A record that preserves a
declared intent perfectly changes no structure — *that is the record doing its job, not failing it*. Nor is
it evidence against the design method, which was not the variable here: the design method (the Guide/Worker
loop and the review) ran in **neither** arm. A convergent task simply cannot discriminate on goal 1, by
either instrument.

What it does establish is a **scope limit**: at ~300 lines a strong model reaches the same design unaided,
so this task cannot speak to goal 1 and the goal-1 question needs a scale where the pattern is *not*
recoverable from the code.

## What BP19 establishes — stated per goal

**On goal 2 (knowledge that does not belong to the code) — a clean positive, the campaign's first
non-null.** A record holds a **declared intent the code cannot**, and that intent is acted on: 3/3 vs 0/3,
with the blind arms unable in principle, since the non-goal exists nowhere but the record. Neither the test
floor nor the §0–§14 rubric can see this — a design can score 45/45 while quietly breaking what the project
said it would not do. That is precisely why goal 2 has its **own** instrument.

It also corroborates the earlier goal-2 nulls rather than overturning them: six confounds showed a *rule or
convention* is recoverable from a well-formed codebase. A **non-goal** is the thing that is not — it is the
absence of code, and absence leaves no trace to recover.

**On goal 1 (correct design) — BP19 says nothing, and was never able to.** The design method ran in neither
arm; only the records varied. The task is additionally convergent (6/6 identical structure), so it could not
discriminate on design even in an experiment that *did* manipulate the method. Goal 1's evidence is BP9,
BP13, BP14 and the `aims-vs-openspec` pilots — not this one.

## Threats to validity

Against the **goal-2** claim, which is the one BP19 makes:

- **n = 3 per arm**, one product, one declared intent, one contradiction. A claim about the record layer
  deserves more, and more *kinds* of intent — a rejected alternative and a convention with no code trace,
  not only a non-goal.
- **Amending `goals.md` is the behavior the skill asks for**, so 3/3 partly measures instruction-following.
  What it does establish is that the contradiction was *detectable at all* — which is the claim.
- **The records arms got 117 more lines of context.** More text could produce more attention by itself; the
  control BP19 lacks is an arm given 117 lines of *irrelevant* prose. For the goal-2 finding this is a weak
  worry — irrelevant prose cannot contain the non-goal — but it is the honest control.
- **Detection is not the whole of goal 2.** BP19 shows a contradiction being *caught*. The other half —
  does a record stop a fresh session **re-deriving** — is untested here and needs scale.

Against reading anything **goal-1** into this file:

- **One task, one scale, and convergent.** A ~300-line module is small enough that a strong model reaches
  the same design unaided (6/6). It cannot discriminate on design quality — and BP19 does not manipulate
  the design method anyway.
