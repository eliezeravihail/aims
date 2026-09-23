---
title: "Re-evaluation — every valuable attempt re-checked against the CORRECT measure (§0–§14 design rubric), not tests"
date: 2026-09-21
---

# Why this file

The correct measure of design quality is **the design scored against the §0–§14 rubric** (`design-principles.md`
+ the review lens' S-severities) — *not* functional tests (a floor, gameable) and *not* behavioral change-probes
(reopened-owner / edit-locality — also gameable, proven in BP13 part-1). aims already *is* that rubric; it was
the instrument from the project's first experiments ("design-only", "blind-judge both dimensions"). During the
build-pilot phase the measurement drifted to test-pass and behavioral proxies. This file re-checks each
attempt of value against the correct measure.

# The shipped changes

## I6 — name the anemic-model / type-switch as a review gap → HOLDS UP
Re-read against §0–§14: this is a **§8** item (OO-abusers: type-code/switch instead of polymorphism) plus **§4**
(anemic vs rich domain) and **§7** (OCP). It adds design-rubric coverage, in rubric terms. BP14 confirms it is
exactly what collapses a design's rubric score (type-switch build: OCP 1, concept-fit 1, no-type-switch 1 →
16/45). **Verdict: correct under the right measure. Keep.**

## I3 — outcome-first comparison + disjoint-vocabulary judge → WENT THE WRONG WAY (reconsider)
What I3 did: for *comparing designs*, it **demoted the §0–§14 rubric grade to "secondary"** and made the lead
signal a **correctness-trap gate** (a hidden test), **reopened-owner count**, and **edit locality** — all
behavioral proxies. The disjoint-vocabulary judge it added scores only *"did this design absorb the change with
fewer edits and no reopened owner?"* — a change-absorption behavior, forbidden from reasoning about the design.

Re-checked against the correct measure — using my own later data:
- **BP13 part-1** proved the lead signal is **gameable**: a strong model absorbed the change with a ~3-line
  seam edit and **0 reopens** while leaving a textbook type-switch in place (an accumulator before/after hack).
  Fewer edits + no reopen, *worse* design. I3's lead signal scored that build as the winner.
- **BP14** proved the **§0–§14 rubric is the real separator**: two designs passing the identical tests scored
  **43 vs 16** on the rubric. The instrument I3 demoted is the one that works.

So I3's *motivation* was real (the rubric ceilinged at 10/10/10; judges were pulled toward designs that recite
the vocabulary), but its *fix* fled the rubric instead of fixing how the rubric is scored. **Verdict: reconsider.**
The salvageable core is the **disjoint-vocabulary judge** — but re-pointed: it should score the **design against
§0–§14 from code properties** (does the engine actually dispatch on type? is there truly one owner? is the rule
a rich object or an anemic bag?), *not* the change-absorption behavior. BP14's judge is exactly that judge done
right — blind, code-grounded, uncaptured, and it separated 43 vs 16. The correct fix to the ceiling/capture
problem is a **code-grounded rubric judge + the S-severity gate**, keeping §0–§14 as the lead — not demoting it
beneath behavioral proxies.

# The tests of value

## BP9 — the review flags green-but-bad designs → VALID (it IS a rubric measurement)
Four builds all green on tests; the review scored them structurally rigid (S3: §7/§8). That is a §0–§14
measurement, and it is right: tests were blind to it. BP14 puts a number on the same builds (16/45). **Valid and
central.**

## BP14 — blind rubric scoring separates identical-tests designs 43 vs 16 → THE correct measurement, demonstrated
This is the right instrument in action: score the design against the metric list from the code, no tests as a
measure. Caveat now corrected: the list is **§0–§14 itself** (my ad-hoc 9 were a strict subset — see below);
BP14 should be read as scoring §0–§14, which its metrics mirror. **Valid.**

## BP6 / BP7 base rates → RE-READ as design-rubric distribution, not "trajectory"
Originally framed as store-vs-derive / type-switch-vs-polymorphic "shortcut rate" measured by reopen. Correct
re-read: the fraction of plain builds that produce **low-§0–§14-score** designs (a type-switch build ≈ 16/45; a
polymorphic one ≈ 43/45). aims' value, in rubric terms, is **raising the floor / cutting the variance** of the
design-rubric score — not a behavioral reopen count. Same finding, stated in the correct currency.

## I1 / I2 / I4 / I5 → already measured correctly (design-only, blind-judged) — remain nulls
These pre-date the drift; they were scored against the rubric with the S-gate. They stay nulls under the correct
measure.

# The metric list — checked against the existing one (per instruction)
The 9 metrics proposed in BP14 (OCP, one-owner, cohesion, coupling/hiding, concept-fit, no-type-switch, DRY,
appropriate-abstraction, readability) are a **strict subset** of §0–§14 (they map into §7, §6/§5, §6, §5/§6,
§4, §8, §7, §7, §3). The existing §0–§14 also carries §1 correctness/contracts/full-input-space, §2
functions/CQS, §10 architecture, §11 concurrency, §12 testability, §13 performance, §14 security, **plus the
S1–S4 severity/precondition machinery my list lacked entirely.** **The existing rubric needs no addition from my
list; it is the superset.** BP14 was a partial rediscovery of what aims already had.

# Net correction
- **I6:** correct, keep.
- **I3:** reconsider — do not demote §0–§14 beneath behavioral proxies; keep the rubric as the lead, scored by a
  **code-grounded disjoint-vocabulary judge** (BP14-style) plus the S-gate. The behavioral proxies (reopen,
  edit-locality) are gameable (BP13) and belong at most as weak secondary evidence, never the lead.
- **Instrument:** the design rubric (§0–§14) is and always was the measure. Tests are a correctness gate only.
