---
title: "[WITHDRAWN] BP18 result — a single root decisions file BEATS per-file companions: floor 31 vs 26 vs 20"
date: 2026-09-22
status: WITHDRAWN — the records in this run were written by hand, not filed by aims, so it tested that construction rather than aims (AUDIT-record-layer-claims.md). Its headline comparison is also void: the single-root-file question is open (decisions/0023).
---

# Result — nine modules, one blind judge, one shuffled pass

| instrument | scores /40 | mean | **worst** | best | **spread** | cost of the instrument |
|---|---|---|---|---|---|---|
| **none** | 20, 25, 35 | 26.7 | **20** | 35 | **15** | — |
| **per-file companions + ADRs** (aims today) | 26, 33, 36 | 31.7 | **26** | 36 | **10** | 142 lines, 6 files, + `anchor.py` + staleness hook + copies-identical test |
| **single root `DECISIONS.md`** | 31, 34, 35 | **33.3** | **31** | 35 | **4** | 49 lines, 1 file, **no machinery** |

**The ceiling is identical across all three** (35 / 36 / 35) — the best design in the *no-records* arm scored
35. The entire difference is the **floor**: 20 → 26 → **31**, and the spread tightens 15 → 10 → **4**.

Supporting measures, all equal: decision survival 4/4 in every arm; token cost 52.6k (none) / 51.8k
(per-file) / **49.2k** (root) — i.e. reading cost is noise, not a differentiator.

# Reading

This reproduces the campaign's constant — **records do not produce the good design, they prevent the bad
one** — and adds a new result: **consolidation beats distribution.** A single short file is read *in full*;
six scattered companions are sampled, and what the reader does not open does not help.

The rarity premise is what makes this work. If the genuinely-unrecoverable deliberations are as rare as six
failed attempts (I5, BP15, BP15b, BP16, BP16b, BP17) suggest, the file stays short, stays read, and stays
coherent. Concentration is then an advantage, not a compromise.

# Consequence for aims (proposed, not applied)

The per-file companion model is the sole reason `knowledge/anchor.py` (hash-stamping each companion), the
`PostToolUse` staleness hook (re-deriving that anchor on read), and the byte-identical copies test exist. A
root file has nothing to anchor and nothing to drift against, so **that entire subsystem is deletable** — and
the measurement says the model it serves is the weaker of the two.

# Honest limits

n=3 per arm, one product, one judge, overlapping ranges at the top; the judge itself called five of the nine
"one design with cosmetic variation, within noise of each other". The load-bearing assumption is the rarity
premise: a root file that inflates stops being read in full, and that is exactly the property it wins on.
A second product, and a test of what happens when the file grows, are the checks this needs before shipping.

---

# CORRECTION — the "per-file companions (aims today)" arm was NOT aims

Checked against the shipped method (`skills/aims-guide/references/design-record.md`). Two errors, both mine:

**1. aims does not prescribe a companion per source file.** The reference says the opposite, explicitly:
> *"A source file gets a companion the first time there is something durable to record about it — **not
> mechanically for every file**."*

I extrapolated "knowledge about one file → its companion" into "a companion beside every source file". That
is my extrapolation, not the method.

**2. I mis-filed the records inside the experiment.** In BP15b I produced six record files for one small
module (`goals.md`, `architecture.md`, `decisions/0001-0003`, `payouts.py.md`). But all three deliberations
were **file-level** facts about `payouts.py`, and the method's split rule is explicit: file-level knowledge
belongs in that file's companion; an ADR is for a **system-wide** decision. Applied correctly, aims would
have produced **one file** — `payouts.py.md`.

## What this does to the result

- The arm labelled "per-file companions (aims today)" measured **my over-application**, not the method. Its
  31.7 is not a score for aims.
- What survives: **142 lines across 6 files scored worse than 49 lines in 1 file** — concentration beats
  scatter. That is real, and it is an argument against *over-filing*, which the method already forbids.
- What does **not** survive: the claim that a root file beats aims' record model, and the consequent
  proposal to delete `anchor.py`, the staleness hook and the copies-identical test. Applied correctly the
  comparison is **one companion beside the file vs one file at the root** — a difference of *location only*,
  which this experiment never tested and which plausibly shows nothing.

**Status: the BP18 conclusion is withdrawn.** The valid residue is a caution against over-filing — which is
the method's own bootstrapping rule, restated by measurement.
