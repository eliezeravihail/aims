# Judge agreement — how far the design grades repeat across judges

**Question.** When different judges score the *same* design with the same assessment form, how much do their
grades agree? This quantifies the paper's claim that the grades "depended on the judge as much as on the
design" (Section 9, Table 4). No new runs: it re-reads the existing judge reports.

**Data.** Every filled form in the two judging rounds of
[`principles-polish-vs-openspec`](../principles-polish-vs-openspec/):

| judge | round | report | designs scored |
|---|---|---|---|
| **R1** | 1 | [`judging-real/*/report.md`](../principles-polish-vs-openspec/judging-real/) | openspec-real, aims-single |
| **R2-own** | 2 | [`judging-aims-real/*/ownership/report.md`](../principles-polish-vs-openspec/judging-aims-real/) | openspec-real, aims-real |
| **R2-simp** | 2 | [`judging-aims-real/*/simplicity/report.md`](../principles-polish-vs-openspec/judging-aims-real/) | openspec-real, aims-real |

A design = (product, stage, arm). **12 designs were scored by two or more judges:** the 6 openspec-real
designs (by all three judges) and the 6 aims-real designs (by both round-2 judges). The aims-single designs had
one judge on this instrument and are excluded.

**Method.**
- [`parse_reports.py`](parse_reports.py) extracts every chapter score and severity from all 36 forms.
- **Parse check:** each form's grade, recomputed from the parsed chapters with the `measurement.md` weights,
  equals the grade the judge reported, to two decimals, in all 36 forms.
- [`agreement.py`](agreement.py) computes:
  - Krippendorff's α, which allows a missing judge;
  - Shrout–Fleiss ICC(2,1) and ICC(3,1), with the variance components behind them;
  - Cohen's κ;
  - 95% bootstrap intervals, resampling designs (5,000 draws, fixed seed).
- **Implementation check:** α and ICC reproduce the published reference examples exactly. Krippendorff's
  2011 example gives nominal .743 / interval .849; Shrout & Fleiss 1979 Table 2 gives ICC(2,1) .29 /
  ICC(3,1) .71.
- **Output:** all numbers are in [`results.json`](results.json). To reproduce: `python3 agreement.py`
  (stdlib only).

**Conventional reading scales** (for orientation only; n is small):
- **Krippendorff (2004), α:** ≥ .800 reliable; .667 is the lowest value for tentative conclusions.
- **Koo & Li (2016), ICC:** < .50 poor; .50–.75 moderate; .75–.90 good.

## Results

### 1. Grade agreement

| designs | judges | α (interval) | 95% CI | ICC(2,1) | variance share: design / judge / residual |
|---|---|---|---|---|---|
| openspec-real (6) | R1, R2-own, R2-simp | **0.11** | −0.32 to 0.31 | 0.27 | 27% / **50%** / 23% |
| aims-real (6) | R2-own, R2-simp | 0.96 | −0.57 to 0.99 | — | — |
| all 12 | all | **0.41** | 0.08 to 0.67 | — | — |
| all 12 | round-2 pair only | — | — | **0.78** | 78% / 2% / 20% |

- The spread of grades for one design averaged **1.41** points and reached **3.29**.
- **5 of 12 designs** differed by 2 points or more between judges; all 5 are openspec-real designs.
- Across the three judges, the judge explained more of the grade variance (50%) than the design did (27%).
- **Within round 2**, the two judges ranked the grades consistently: design 78%, judge 2%. Round 2 used the
  same protocol for both judges, and only their instructed disposition differed.

### 2. Most of the disagreement is whether a correctness bug was found

An S4 finding in chapter 13 (functional correctness) carries weight ×8, so one found bug moves a grade by
about 3 points. The judges found such bugs in different designs:

| judge | designs with an S4 in chapter 13 |
|---|---|
| R1 | none |
| R2-own | 6: all openspec-real except entitlements stage 1, plus aims-real booking stage 2 |
| R2-simp | 4: openspec-real feed stages 1–2, entitlements stage 2, and aims-real booking stage 2 |

Recomputing every grade **without chapter 13**:

| designs | α with ch. 13 | α without ch. 13 | ICC(2,1) without | variance share without: design / judge |
|---|---|---|---|---|
| openspec-real, 3 judges | 0.11 | **0.49** (−0.08 to 0.76) | 0.56 | 56% / 24% |
| all 12 | 0.41 | **0.61** (0.24 to 0.79) | — | — |

### 3. Chapter-level agreement is low even where the grades agree

These figures cover 168 (design × chapter) items, chapters 1–14, each with two or more judges.

| reading | agreement |
|---|---|
| chapter score, α (interval) | **0.38** (95% CI 0.20 to 0.51) |
| chapter passed (10) vs failed (< 10), α (nominal) | **0.32** |
| items where every judge agreed on pass/fail | 114 of 168 |
| an S4 in the chapter, α (nominal) | 0.49 |

Per-chapter α ranges from **0.58** (§5 anemic model), 0.49 (§4 primitive obsession) and 0.44 (§14 state) down
to about zero or below for §1, §2, §3, §6, §7, §8 and §12. §9 has no variance, because every judge scored it
10 everywhere.

### 4. Gates, arm order and verdicts

| reading | agreement |
|---|---|
| gate (BLOCKED/CLEAR), round-2 pair | 10 of 12; Cohen's κ 0.67 |
| gate, all judges | α (nominal) 0.28; **5 of 12** designs BLOCKED by one judge and CLEAR by another |
| which arm scored higher, round-2 pair, per product × stage | same sign 4 of 6; α on the difference 0.63 |
| named verdicts, round-2 pair (D1, survival, D2 form × 3 products) | **5 of 9**; α (nominal) 0.31 |
| reopened + discarded counts, all judges | α (interval) 0.62 |

## What this does and does not show

- **Shows:** across the two rounds, grades of the same OpenSpec designs did not repeat. Agreement was
  α 0.11, well below any conventional threshold, and the judge accounted for more grade variance than the
  design.
- **Shows:** the gap is concentrated in correctness findings. Removing chapter 13 lifts α to 0.49–0.61, still
  below .667. Finding a bug in a design document is itself the unstable step.
- **Shows:** even when two judges gave similar grades (the round-2 pair, ICC 0.78), they often disagreed on
  which chapters failed (chapter α 0.38) and on the named verdict (5 of 9). Similar grades were partly reached
  for different reasons.
- **Does not separate judge from protocol across rounds.** R1 and the R2 judges differed in more than the
  judge:
  - the R2 prompt required a reproducing input for every failure;
  - it assigned opposite dispositions;
  - it used the aligned form.

  The round-1 vs round-2 gap is therefore judge plus protocol. Only the within-round-2 figures hold the
  protocol fixed, apart from disposition.
- **Small and correlated sample.**
  - 12 designs, 3 judges, one model family.
  - Each judge scored designs in pairs (X vs Y), not independently.
  - The aims-real α of 0.96 has a CI reaching −0.57, so it says little on its own.
