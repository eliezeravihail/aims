---
title: "One root file, or records beside the code? — a valid test of decisions/0023"
date: 2026-09-22
status: DESIGNED — not run. Needs aims-filed records from a real build (see §2); runs after design-at-scale
  Phase 1 at the earliest.
---

# The idea, in plain terms

aims files each record next to what it is about — beside a file, beside a folder, or at the root. The
alternative, proposed by the project's owner: **one file at the project root holding every discussion and
decision**. Its argument: once everything the code can say goes into the code, what is left for records is
rare — and a handful of entries may not need homes of their own.

`bp18` seemed to settle this and was withdrawn: the records in it were written by hand, so it tested that
writing, not aims (`decisions/0023`). This design removes that flaw by construction: **the same records, filed
by aims, in both layouts — one converted from the other by a script that changes no word.** Only the layout
differs.

**Goal 2 only.** It measures whether knowledge that is not in the code is found and acted on. It says nothing
about design quality, and no design score is computed.

# 1. The two layouts

| | what the session gets |
|---|---|
| **beside** — as aims files it | companions `<file>.md`, folder records `<dir>.md`, root records |
| **one file** | a single `DESIGN-NOTES.md` at the root, made by [`merge_records.py`](merge_records.py) from the same records |
| **none** — the control | the code only |

`merge_records.py` carries every record's text over unchanged, under a heading naming what it is about, and
checks that no line of text was lost (tested on this repository: 74 records, 0 lines lost). It drops
frontmatter, including the anchor hash, which means nothing once a record no longer sits beside its source.

**Held constant: the staleness hook is off in all three.** It works by a record's position beside its file,
so it cannot run on the one-file layout at all. Leaving it on would test the hook, not the layout. The
consequence is recorded below as a cost of the one-file layout, not measured here.

# 2. The records — filed by aims, never written for the test

The records come from a real aims build: the aims arm (A) of
[`../design-at-scale/`](../design-at-scale/DESIGN.md), taken as filed at the end of its latest completed stage.
They are real in every sense this campaign learned to require: filed by the skill, on a real codebase, about
decisions the build actually made, including the stage-1 non-goal (no automatic language detection).

If design-at-scale does not run, any other aims build that files records on a codebase of comparable size
will do — provided that **no record is written, edited, padded or removed for this test.** How many records
there are is part of the result: the premise being tested is that they are few.

# 3. The probes — tasks a record should change

A separate agent that has seen **only the records** — no arm output, no result — writes four probe tasks, each
a realistic change request that a specific record should alter, fixed before any session runs:

- the **non-goal**: design-at-scale's stage-3 request to open the export in the reader's language, which the
  stage-1 non-goal rules out;
- a request that tempts **a rejected alternative** a record names;
- a request whose natural implementation **contradicts a recorded decision** that the code does not enforce;
- a request touching an area whose record is **about a different area** — the distractor: a session that
  applies it here has misapplied it.

**A probe counts only if the control fails it.** If a session with the code alone does what the record would
have made it do, the knowledge was recoverable from the code and the probe tests nothing. Probes the control
passes are reported and dropped from the comparison.

# 4. What is measured

For each probe, in each layout, **n = 3** fresh sessions, each told only how the layout works (as the
navigation experiment was), never where the answer is:

| measure | how |
|---|---|
| **found and acted on** (primary) | the session honoured the record — kept the non-goal, avoided the rejected alternative, surfaced the conflict — or asked the product owner about it |
| **misapplied** | the session applied a record about a different area to this one (the distractor probe, and any other probe) |
| **cost** | tokens read to reach the relevant record; number of files opened |

A judge who does not know the layout reads each session's diff and transcript excerpt and scores the first two
against the probe's pre-written pass condition.

# 5. Predictions, fixed now

| question | prediction | falsified if |
|---|---|---|
| found and acted on | **one file ≈ beside**: with few records both are found | beside finds more than one file on ≥ 2 of the valid probes |
| misapplied | **one file misapplies more**: every session reads every record, so an unrelated one is closer to hand | one file misapplies no more often than beside |
| cost | one file reads more tokens per task, opens fewer files; the difference is small while records are few | — reported |

If both of the first two predictions hold, the honest reading is that **the one-file layout is enough at the
record counts aims actually produces**, and its cost is the misapplication risk plus the loss of automatic
staleness detection — which is the trade the owner would then be deciding.

# 6. Threats

- **One set of records from one build.** If aims files few, this cannot say what happens at many; the premise
  under test is that it files few.
- **The staleness hook is excluded by construction.** Moving to one file would need a replacement (for
  example, each entry naming its source file and hash, which `anchor.py` does not do today). That cost is real
  and is not measured here.
- **Four probes, n = 3.** Suggestive, as every run in this campaign.

# 7. Before it can run

- [ ] records from an aims build (§2), frozen as filed
- [x] [`merge_records.py`](merge_records.py) — written; tested lossless on this repository
- [ ] the four probes and their pass conditions, written by an agent that saw only the records
- [ ] the control run, to discard probes the code alone answers
- [ ] the judge prompt, and the sealed layout mapping
