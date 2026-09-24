---
title: "Design quality assessment form — the fillable instrument, one row per principle"
date: 2026-09-17
---

# Design quality assessment form

> **Canonical instrument:** the single shipped measurement is
> [`../../skills/aims-guide/references/measurement.md`](../../skills/aims-guide/references/measurement.md)
> (the rules, severity table, aggregation, and the two projections). This file keeps the fillable layout and
> a worked example; the mechanics live there (`../../decisions/0014`).

A **standardized, fillable instrument** for scoring one design against the principles — the *output shape*
of `measurement.md`: one row per principle, so two judges (or two runs) produce comparable, auditable
records rather than free prose.

It is honest about what it is: a **reliable** instrument (same design → same profile across judges/runs,
because every row is sub-check-derived and cited), **not** an externally **valid** benchmark — no external
ground truth for design quality exists (the static-metric cross-check in
[`cross-experiment-regrade.md`](cross-experiment-regrade.md) shows deterministic metrics measuring a
different construct). Its validity rests on the principles being
sound; triangulate it with survival and deterministic metrics as separate signals that need not agree.

## One instrument, two projections

The same filled form feeds both activities aims separates:

- **Judging / measurement projection** (research — comparing arms, benchmarking): the **whole scored form**
  plus the aggregate **profile** block. Scoring here is legitimate and deliberate — this is the layer that
  already produces a weighted number (`quality-metrics.md`).
- **Operational-review projection** (the Guide measuring a Worker's design, in the aims loop): **only the
  rows scored below 10**, presented as a **findings list sorted ascending by score — most severe first** —
  each with its principle and citation, and **no aggregate grade**. This keeps the operational review a
  direction-feeding findings list, faithful to aims' "never a score" (which forbids a *composite verdict* in
  the loop, not a per-finding severity ordering — `decisions/0012`, `../../skills/aims-guide/references/review.md`).

## Filling rules (summary — full rationale in `quality-metrics.md`)

1. Pin **Step 0** (R/X/C from the spec) first; it is identical for every design and every judge.
2. **Each row's score is sub-check-derived, never eyeballed:** decompose the principle into a handful of
   binary structural checks, mark each pass/fail with a citation, and set `score = round(10 × passed /
   applicable)`. Eyeballing a holistic number reintroduces the ±0.5 judge noise the sub-checks exist to
   absorb.
3. **Severity = the tier of the worst *failed* check** (S1–S4); it sets the row's ceiling (S1→8, S2→7, S3→5,
   S4→2) and the aggregation weight (×1/×2/×4/×8). The reported row score is `min(sub-check score, ceiling)`.
4. **The score reflects how materially the design violates *this* principle** — a cosmetic breach of a rule
   is 8–9; the principle essentially unhonored is 0–2. Scores run **0–10** (0 = the principle is wholly
   unhonored — we keep 0 reachable rather than a 1–10 floor). Cross-principle importance (correctness and
   ownership dominating) is **not** put into the row score — it lives in the weight; the S4 gate is reported
   beside the grade, never folded into it.
5. **A score below 10 REQUIRES a finding line with a citation** (the defect + the R/X/C or seam item it
   violates). A 10 needs a one-line cite of where the principle holds by construction. No citation → the row
   is struck, not counted as a pass.
6. **One defect, one principle** — the most specific; other rows may reference it, never re-deduct.

## The form (blank)

```
Design: <id>            Product: <name>            Judge: <id>            Step-0 inventory: <link>

| §  | principle (short)                                  | applies | score 0–10 | severity | finding + citation (required if <10) |
|----|----------------------------------------------------|---------|-----------|----------|--------------------------------------|
| 1  | Tell-Don't-Ask / Law of Demeter                    |         |           |          |                                      |
| 2  | Interface + generic calibration + concept-fit (LSP)|         |           |          |                                      |
| 3  | Interface Segregation                              |         |           |          |                                      |
| 4  | Primitive obsession                                |         |           |          |                                      |
| 5  | Anemic domain model                                |         |           |          |                                      |
| 6  | Cohesion/coupling (Feature Envy, Shotgun, OCP)     |         |           |          |                                      |
| 7  | Leaky abstractions — boundary vocabulary, errors   |         |           |          |                                      |
| 8  | Single Responsibility / God Object                 |         |           |          |                                      |
| 9  | Rule enforcement — one unforgeable owner           |         |           |          |                                      |
| 10 | Duplication vs the wrong abstraction (DRY)         |         |           |          |                                      |
| 11 | Naming and failure (least astonishment)            |         |           |          |                                      |
| 12 | Size as a forcing question (YAGNI / subtractive)   |         |           |          |                                      |
| 13 | Functional correctness — every case + interaction  |         |           |          |                                      |
| 14 | State & side-effect discipline (immutability)      |         |           |          |                                      |
| 15 | Testability — verifiable by construction           |         |           |          |                                      |
| 16 | Performance — on its own terms (N/A if unstated)   |         |           |          |                                      |
| 17 | Security & trust boundaries (N/A if none)          |         |           |          |                                      |

Profile (judging projection only):
  grade            = Σ(score×weight)/Σweight   (weight from severity; no global cap)
  worst_chapter    = min score
  counts           = (#S3, #S4)
  gate             = any S4 ⇒ BLOCKED · else CLEAR   (reported beside the grade, not folded into it)
  reported         = grade=<n>   worst=<n>   (#S3,#S4)=(,)   gate=<BLOCKED|CLEAR>
```

(§18 is not scored — it only names OCP/LSP/ADP/DRY/least-astonishment/YAGNI, folded into the rows above.)

## Worked example — ledger blind arm (`led-2.py`)

Filled honestly against the running `Ledger`; citations are line numbers in that file. Rows not shown are
**10** (each cites the place the principle holds — omitted here for length; §14 passes: `Entry` frozen, no
stored balance field, memo invalidated on write, lines 14–26; §9 passes: the derive-and-memoize invariant
has one owner, `balance()`, lines 28–36; §13 passes: balance derived from entries, correct by construction).

| §  | principle | applies | score | severity | finding + citation |
|----|-----------|---------|-------|----------|--------------------|
| 4  | Primitive obsession | Y | 7 | S2 | `statement()` returns `tuple[list[Entry], int]` — a bare positional pair at a public seam; the closing balance is an anonymous `int`, not a named `Statement`/closing-balance concept (line 41–43). One localized clump; `Entry` itself is a named type (line 7), so the principle is not broadly violated → ceiling S2 = 7. |
| 7  | Leaky abstractions | Y | 10 | — | boundary types are domain types; error is a `ValueError` on the zero-delta rule (line 21–22). *(References the §4 clump, does not re-deduct it.)* |

**Judging projection — profile:** with §4 = 7 (weight ×2) and every other applicable row 10, the grade is
the weighted average, **9.63**; `worst_chapter = 7`, `(#S3,#S4) = (0,0)`, gate **CLEAR**. Reported:
**9.63, worst 7, (0,0), CLEAR**. (The capsule-aware arm `led-1.py` scores **§4 = 10** — it returns a named
`Statement{account, entries, closing_balance}`, lines 13–17 — so its profile is a clean 10s. The
form captures **exactly the difference the deterministic static metrics were blind to**: Halstead identical,
MI even favored the shorter blind arm.)

**Operational-review projection — worst-first findings, no grade:**

```
1. §4 Primitive obsession — 7/10 [S2] — statement() returns tuple[list[Entry], int]; closing balance is an
   anonymous int, not a named Statement type (led-2.py:41–43). Direction: give the seam a named return type.
```

(Here the list is one item because the arm has one sub-10 row; on the checkout aims-panel arm it would lead
with §13 correctness ≈ 2/10 [S4], then the §6 OCP row, illustrating the ascending-score order.)
