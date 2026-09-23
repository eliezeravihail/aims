---
title: "design-at-scale Phase 2 — goal 1 supported at stage 3 by the registered panel rule; goal 2 no clear advantage"
date: 2026-09-23
---

# Result

**Goal 1 (design), the primary endpoint — B vs C at stage 3: supported**, by the rule registered before any run
(`PROTOCOL-NOTES.md`). The ownership judge finds *no clear advantage*, the simplicity and disjoint judges find
*supported*; the two disposition judges differ, so the disjoint judge decides by agreeing with one — *supported*.

**Read this first — the verdict depends on one correction made during judging.** The panel's first run scored the
stage-3 card's line "open the file in the reader's own language" — the goal-2 trap, withdrawn by the product owner
for every session that asked, and contrary to stage 1's legal rule — as a design requirement. Under that first spec
the only judge that finished (simplicity) would have **falsified** the prediction (B mean 7.54 < C mean 7.86), because
the unaided designs that built language detection were credited for it. The correction — score design without that
line, either way, as `../DESIGN.md` §3 requires the two goals be kept apart — was made after seeing that one judge's
table and before unsealing; the full panel was re-run from scratch. Both are disclosed in `PROTOCOL-NOTES.md`
("Correction to the stage-3 panel") and `judge-s3-first-run-simplicity.md`.

**Goal 2 (knowledge the code does not hold) — no clear advantage**, by the registered rule: A surfaced the conflict
in 3 of 3, B in 2 of 3, C in 1 of 3; the rule needed B ≤ 1 of 3.

# Goal 1 — stage 3 (the offline export), full panel, blind

Every S3 and S4 finding of all three judges was reproduced against the code before unsealing (`verify-s3/README.md`);
none failed to reproduce. The seal (`MAPPING-SEAL-s3.sha256`) matched.

| design | arm | ownership | simplicity | disjoint | S4s that block it (reproduced) |
|---|---|---|---|---|---|
| T | **b2** | **9.46** | **8.64** | 9.15 | — (the only design CLEAR under all three) |
| W | a3 | 9.23 | 6.33 | 9.33 | simplicity: title escaped twice; SVG `url(#)` broken |
| Q | a1 | 8.29 | 6.14 | 9.31 | simplicity: a theme without `export.html` cannot export; `<style>` `url()` not embedded |
| R | b3 | 8.56 | 6.48 | **9.43** | simplicity: `srcset` not embedded; directory link unresolved |
| U | a2 | 8.18 | 4.73 | 7.41 | simplicity: title escaped twice; SVG broken; `<style>` not embedded |
| S | c3 | 7.76 | 4.69 | 7.05 | simplicity: title escaped twice |
| P | b1 | 6.65 | 6.26 | 6.26 | **all three:** the untranslated notice written a second time — already visibly different from the site's |
| V | c1 | 5.74 | 5.30 | 4.48 | **all three:** the same second notice; a private `build` class; SVG broken |
| N | c2 | 5.67 | 5.12 | 4.73 | **all three:** the same second notice; a private `build` class; title escaped twice |

| judge | A: worst · mean | B: worst · mean | C: worst · mean · range | B vs C |
|---|---|---|---|---|
| ownership | 8.18 · 8.57 | 6.65 · 8.22 | 5.67 · 6.39 · 2.09 | no clear advantage (gap 1.83 ≤ C's range 2.09) |
| simplicity | 4.73 · 5.73 | 6.26 · 7.13 | 4.69 · 5.04 · 0.61 | **supported** |
| disjoint | 7.41 · 8.68 | 6.26 · 8.28 | 4.48 · 5.42 · 2.57 | **supported** |

**What separates them, in the judges' words and in the code:** whether the export reuses the site's one owner of the
untranslated notice (every aims design but b1; one unaided design, c3) or writes a second one; whether it enters the
build through a public seam (all six aims designs but a2) or reaches into `build`'s private functions (all three
unaided designs, and a2); and whether the rewriting of a whole page into one file is complete (only b2's).

**A vs B (records → design; predicted: no meaningful difference).** Mixed: A's mean is higher under ownership and
disjoint, B's under simplicity; A's worst is higher under ownership and disjoint. The best single design is a B
design (b2). No claim.

# The whole trajectory — goal 1, per stage

| stage | judges | aims (Phase 1: A = B) / A | B | C (unaided) | registered comparison |
|---|---|---|---|---|---|
| 1 — multi-language | 3, blind | worst 5.71–6.43, mean 6.65–7.26 | = A | worst 4.36–5.78, mean 5.11–5.84 | aims > unaided, all three judges |
| 2 — incremental rebuilds | 1 (disjoint) | worst 5.42, mean 6.83 | worst 4.95, mean 6.36 | worst 3.55, mean 3.86 | B vs C **supported** |
| 3 — offline export | 3, blind | see above | see above | see above | B vs C **supported** (panel) |

Grades compare within a stage only: each stage's designs are larger, and each stage has its own judges.

**The pattern across the three stages.** The aims designs more often kept the new concern behind one owner and a
public seam; the unaided designs more often reached into existing modules and duplicated an owner. Precondition (S4)
failures, all reproduced:

| stage | aims — with records (A) | aims — records withheld (B) | unaided (C) | the failure |
|---|---|---|---|---|
| 1 | 2 of 3 (A = B) | — | 3 of 3 | unaided: the French-only page; aims: an explicit `nav:` title untranslated |
| 2 | 1 of 3 | 0 of 3 | 3 of 3 | an unguarded Markdown include leaves a page stale |
| 3 (ownership and disjoint judges) | 0 of 3 | 1 of 3 | 2 of 3 | the untranslated notice written a second time |

Under the stage-3 simplicity judge every design but b2 is blocked, by edge cases of the single-file rewrite; there the
count is A 3 of 3, B 2 of 3, C 3 of 3.

# Goal 2 — the non-goal, stage 3

| arm | surfaced the conflict (frozen definition) | named the conflict itself | knew the rule from | implemented detection |
|---|---|---|---|---|
| a1, a2, a3 | 3 / 3 | 3 / 3 | their own records, with the legal reason | 0 / 3 |
| b1, b2, b3 | 2 / 3 | 1 / 3 | b1: the product's user guide (no reason) | 1 / 3 (b2) |
| c1, c2, c3 | 1 / 3 | 1 / 3 | c1: its own stage-1 user guide (no reason) | 2 / 3 (c2, c3) |

By the registered rule (A ≥ 2 of 3 **and** B, C ≤ 1 of 3; falsified if A ≤ B): **no clear advantage** — B's 2 of 3
misses the bar by one. That one is b3, which asked *how* to build the line, naming no conflict; the frozen
definition counts any question about the line. Under the stricter reading (named the conflict) B is 1 of 3 and the
rule would be met — reported, not substituted. The code confirms the record: the three sessions that did not surface
the conflict (b2, c2, c3) are exactly the three whose exports detect the browser language (`floor-notes.md`).

**Goal 1 and goal 2 dissociate.** b2 is the best design of the nine and one of the three that built detection
against the product's legal rule; every A session carried the reason in its records and none built it.

# The floor (enters no verdict)

Stage 2: A 2 of 3 CLEAR, B 0 of 3, C 1 of 3. Stage 3: all nine CLEAR. Two probe corrections were made after seeing
results and are disclosed with their effect (`floor-notes.md`): the stage-2 build-date count (turned a2 and c3 CLEAR)
and the stage-3 query-string allowance (turned b2 and c2 CLEAR).

# Limits

- **n = 3 per arm, one codebase, one model.** A result is suggestive.
- **The goal-1 verdict rests on the stage-3 spec correction** (above), and on the tie-breaker: one of the two
  disposition judges finds no clear advantage.
- **Judging corrections and probe corrections were made during the run.** Each is disclosed with what it changed;
  none was made after unsealing.
- **B's records were stripped, not unwritten.** Residual docstring pointers to decision files remained in b2's code,
  and b2's sessions noticed them (`PROTOCOL-NOTES.md`). B also re-wrote records within each stage.
- **The judges read aims' own standard.** Three opposite dispositions reduce but do not remove that bias.
- **The oracle.** Only sessions that ask get answers; every exchange is in `oracle-log.md`.

# Cost

Arm sessions ≈ 5.4 M tokens at hand-back (stage 2 ≈ 3.0 M, stage 3 ≈ 2.4 M; the sessions that stopped to ask report
a first leg of 57–164 k each, which may or may not be included). Judges ≈ 1.2 M (stage 2: 0.33 M; stage 3: 0.84 M),
plus the stage-3 panel's first run, cut off by the usage limit.
