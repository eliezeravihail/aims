---
title: "Audit — which campaign conclusions rest on a wrong reading of aims' record model"
date: 2026-09-22
---

# The error being audited

For the whole campaign I worked from a compressed summary and extrapolated a record model aims does not
prescribe: **a companion beside every source file**. The shipped reference says the opposite
("most files never get a companion"). I also mis-filed **file-level** deliberations as **root ADRs**, which
the method's split rule forbids.

The decisive question for each conclusion: **who authored the records in that arm?**

- **Agent-filed** — the arm invoked the real aims skill and filed its own records by reading
  `design-record.md`. That *is* aims. My misunderstanding does not touch it.
- **Hand-authored by me** — I wrote the record set myself, to my invented model. That arm tested **my
  construction**, not the method.

# Verdict per experiment

| round | records authored by | status |
|---|---|---|
| BP1, BP2, BP5, BP7, BP12 | **the agent, via the real skill** | **VALID** — these are genuine aims arms |
| BP3, BP6, BP8, BP10, BP11, BP13, BP14 | no records involved | **VALID** — unaffected |
| BP9 | no records (review lens only) | **VALID** |
| I5, BP15, BP15b, BP16, BP16b, BP17, BP18 | **me, by hand, to the wrong model** | **NOT a test of aims' record layer** |

# Verdict per conclusion

## Survives — rests on what the BLIND arm did (which had no records at all)

- **"A convention or rule is always recoverable"** (from code, a docstring, or one usage example). The
  evidence is entirely the no-records arm's behaviour. My authoring is irrelevant. **VALID.**
- **"A well-formed codebase encodes its own decisions"** — same basis. **VALID.**
- **"Self-reported counterfactuals are unreliable"** (BP17: two arms claimed the record was decisive; the
  controls prove it was not). This is a claim about agent self-report, and it holds however the records were
  written. **VALID — and it now applies to me as well as to the agents.**

## Withdrawn or downgraded

- **"Records raise the design floor" (BP15b: 33.3 vs 29.0; worst 30 vs 20).** The records arm read **my**
  six-file set. The effect may be real, but the number cannot be attributed to aims' record layer.
  **DOWNGRADED to: a hand-written record set raised the floor on one product.**
- **"A single root file beats per-file companions" (BP18).** Already **WITHDRAWN** — the comparison arm was
  my over-application, and correctly applied aims would have produced one companion, making the test a
  difference of *location only*, never run.
- **"The record layer is unproven after six attempts."** Restated honestly: **six attempts failed to test
  it.** Five of the six used records I authored to the wrong model; the sixth (I5) likewise. The record
  layer's value is not disproven here — it is **untested**.
- **Every "what aims buys from records" statement in SYNTHESIS** sourced from BP15–BP18 is suspect and is
  marked as such there.

## Untouched — nothing to do with records

- **I3 / `decisions/0021`** (design rubric leads a comparison; tests are a floor). Measurement policy.
- **I6 / `decisions/0020`** (anemic-model / type-switch as a mixed-tier review gap). Review content.
- **BP1–BP14's trajectory, cost, and correctness findings** — variance reduction on the early structural
  choice, the ~1.85–2.34× cost, the four correctness nulls. None depends on record authoring.

# What would actually test the record layer

Arms that **invoke the real skill** and let it file its own records (as BP1/BP7/BP12 did), rather than a
hand-built record set. Then the thing under test is aims, not my reading of it.

# The meta-finding, which is the most useful output here

I am the best-case reader — inside the repo, skill installed, a SessionStart hook pointing at the records —
and I built the wrong model and held it through six experiments without once opening
`design-record.md`. That is stronger evidence about the method's discoverability than any A/B in this
campaign, because it needs no control arm: the heading stated one rule and the body meant another. Fixed in
`knowledge/format.md`, `references/design-record.md` and `CLAUDE.md`; the two documents now split by role
(shape vs filing decision) instead of duplicating each other with different gaps.
