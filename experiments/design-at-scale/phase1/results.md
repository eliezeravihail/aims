---
title: "design-at-scale Phase 1 — at stage 1, aims' designs score higher, by all three judges"
date: 2026-09-22
---

# Result

**By the rule frozen before any run (`PROTOCOL-NOTES.md`), the verdict is aims.** All three blind judges — with
opposite dispositions — found aims ahead on both the worst design and the mean. The ownership and simplicity
judges agree, so the rule is decided before the tie-breaker is needed; the tie-breaker agrees too.

| judge | aims: worst (F) | aims: mean (M) | unaided: worst (F) | unaided: mean (M) | per judge |
|---|---|---|---|---|---|
| ownership | 6.00 | 6.65 | 5.31 | 5.48 | aims |
| simplicity | 6.43 | 7.26 | 5.78 | 5.84 | aims |
| disjoint | 5.71 | 6.87 | 4.36 | 5.11 | aims |

**The gate.** Of six designs, one is clean in the eyes of all three judges: U — an aims arm. The other five are
each blocked by at least one precondition (S4) failure. aims: 1 of 3 clean; unaided: 0 of 3.

**The floor prediction (`../DESIGN.md` §6) comes out true by its letter — and is not counted.** aims' floor was
3/3 CLEAR against 0/3, but the whole gap is one file, the translators' template, which a reader never sees
(`floor-notes.md`). On that one point the unaided arms did the fuller job.

# The six designs

Unsealed after every finding was verified; the seal's SHA-256 (`MAPPING-SEAL.sha256`) matched.

| blind | arm | condition | ownership | simplicity | disjoint | its S4 (verified) |
|---|---|---|---|---|---|---|
| **U** | w2 | aims | **7.82** | **8.86** | **8.17** | — (all three: CLEAR) |
| P | w1 | aims | 6.00 | 6.43 | 6.73 | an explicit `nav:` title stays untranslated in every language |
| T | w3 | aims | 6.14 | 6.48 | 5.71 | the same |
| Q | w4 | unaided | 5.31 | 5.91 | 5.83 | a page written only in French is dropped from every site |
| S | w5 | unaided | 5.78 | 5.78 | 5.13 | the same |
| R | w6 | unaided | 5.34 | 5.84 | 4.36 | the page exists only in the French site; (disjoint only) search reads core's private attribute; a path collision only warns and leaves a stray page in `/fr/` |

Every S3 and S4 any judge raised was reproduced against the code before unsealing (`verify/README.md`). None
failed to reproduce, so no verdict was recomputed. R's collision finding resembles Phase 0's contested one
(warn and continue), but is worse here: the build exits 0 and the page it says is replaced stays in the French
site. R is blocked without it.

# What the verdict rests on — read this before quoting it

**1. Most of the gap is one question the aims arms asked.** Each aims arm stopped before building and asked what
happens to a page written only in a non-default language. The answer, by the frozen rule, was the card's own two
sentences — *"A page may exist in any subset of the languages."* and *"Every page exists in every language."* All
three aims designs then publish that page in every language. No unaided arm asked; all three dropped or confined
the page. That is the S4 blocking every unaided design.

The unaided arms are not always wrong here. The same test run on Phase 0's four unaided designs: three publish the
page everywhere, one drops it. Across all seven unaided runs: **3 right, 4 wrong**. Across the three aims runs: 3
right. The answer quoted no new text, but it put the two relevant sentences side by side — which is a form of
pointing. What aims contributed is that its arms asked; what the answer contributed cannot be separated here.

**2. aims introduced a defect no unaided arm made.** Two of the three aims designs (P, T) keep a title set by hand
in `nav:` untranslated in every language — against "using that language's page titles where a translation
exists". No unaided design does this: 0 of 7 (all four of Phase 0's and all three of Phase 1's translate it). Both
arms had asked about an explicit `nav:` and got the default, *"I don't know — choose a simple, sensible technical
approach."* Both then chose, deliberately (each has a test asserting it), to keep the author's text verbatim. The
default answer may have steered them there. The third aims arm (U) asked the same, got the same words, and
translated the titles.

**3. Beyond the S4s, the aims designs keep the language logic out of mkdocs' existing pipeline.** Changed lines
mentioning languages in the existing modules (`verify/README.md`):

| | nav.py | pages.py | files.py | build.py | search |
|---|---|---|---|---|---|
| P (aims) | 0 | 0 | 0 | 8 | 0 |
| T (aims) | 0 | 0 | 0 | 12 | 0 |
| U (aims) | 0 | 0 | 0 | 12 | 7 |
| Q (unaided) | 0 | 1 | 8 | 28 | 7 |
| S (unaided) | 0 | 14 | 0 | 41 | 0 |
| R (unaided) | 12 | 27 | 4 | 30 | 11 |

All three judges name this as what separates the designs apart from the S4s: T and P enter through one existing
seam; Q, S and R thread a hidden config attribute through several owners. And none of the three aims designs
carries the log-rewriting filter each unaided design built (30–50 lines no one asked for).

**4. How much the grades depend on the S4 calls.** The disjoint judge recomputed its grades without the two S4s
that each block a single design (the nav-title one and the French-only-page one): P 9.47, T 8.14, Q 8.00, S 6.88 —
all CLEAR; R stays blocked. On that recount aims still leads (worst 8.14 vs 4.36; mean 8.59 vs 6.41), and it leads
too with only one of the two dropped. The other two judges gave no recount, so this check covers one judge.

# Cost

| | tokens at hand-back | tool calls |
|---|---|---|
| aims w1 / w2 / w3 | 318.7 k / 288.1 k / 320.9 k | 74 / — / 75 |
| unaided w4 / w5 / w6 | 373.0 k / 287.7 k / 328.2 k | 115 / 86 / 121 |

The aims figures were reported at hand-back after a stop to ask; whether they include the first leg (≈156–163 k)
is not stated by the tooling (`floor-notes.md`). Either way, cost is of the same order. The three judges together
used ≈ 0.74 M tokens.

# Limits

- **Three runs against three, one task, one model, stage 1 only.** Unaided variance is large: Phase 0's four arms
  got the French-only page right 3 times of 4; Phase 1's three, 0 of 3.
- **The oracle.** Only arms that ask get answers. Asking is the method's behaviour, so its effect is fairly aims';
  but the card-quote answer (point 1) and the default answer (point 2) each may have moved the result, in
  opposite directions.
- **U alone carries much of the mean.** U is also the arm that wrote the fullest aims records (goals,
  architecture, two decisions). One case — noted, not concluded.
- **The judges read aims' own standard** (`design-principles.md`) — the same form for all six, blind; three
  opposite dispositions agreeing reduces, but does not remove, the chance that the form favours designs made
  under it.

# What this does and does not show

It shows: on a real 7k-line codebase, with a change where unaided agents sometimes get the design wrong, three
aims runs produced better-scored designs than three unaided runs under three blind judges, and the structural
difference (where the language logic lives) is visible in the code, not only in the grades.

It does not show: that aims prevents the S4 class — its arms made one S4 no unaided arm made; nor that the
advantage holds as changes accumulate. That is what stages 2 and 3 (Phase 2) measure.
