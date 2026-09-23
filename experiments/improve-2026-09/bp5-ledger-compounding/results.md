---
title: "BP5 result — no compounding; both arms absorbed 4 breaks with 0 reopens (the edge is variance-reduction)"
date: 2026-09-20
---

# BP5 — the compounding test: NULL, and it sharpens the whole trajectory finding

A 4-stage money-ledger (single → multi-currency → as-of-time → void), designed so a stored-running-balance
shortcut would reopen at each break. Aims vs plain, fresh session per stage, hidden pytest per stage.

## Result — both arms, 0 reopens across all 4 breaks, correctness tied

Both arms independently chose, at stage 1, a **derive-balance-by-scanning an append-only posting journal**.
Every later break then landed as a single filter clause (`currency ==`, `at <=`, `id not in _voided`) — so
**neither arm ever reopened an owner**, and both passed all 13 hidden tests. The two final modules are
near-identical (both added a `_voided` set + filter for void). aims' module is ~28% larger (docstrings /
records). **No compounding, no divergence.**

## Why this is the run's most precise finding (BP1 + BP2 + BP5 together)

The trajectory edge appears **only when the plain arm takes a bad early shortcut**:
- BP1 / BP2: the plain arm **stored** a running balance/counter at stage 1 → forced **1 reopen** when the
  time-dependent break arrived. aims (review rejects the stored shortcut) stayed at 0.
- BP5: the plain arm happened to pick the **derived** posting-journal design at stage 1 → **0 reopens**, and
  aims' edge vanished.

So aims' measured trajectory benefit is **variance reduction on the early structural choice**, not a
guaranteed per-product win. Its one-owner / derive-don't-store review **reliably** picks the extensible
design; a capable plain builder picks it **sometimes**. The per-product edge is therefore probabilistic —
proportional to how often a plain builder would take the shortcut on that product — and on a product where
the plain builder chooses well, there is no gap at all. This is consistent with, and sharper than, the
paper's "the edge grows with the sequence": here the sequence was 4 breaks long and the edge was **zero**,
because the plain arm's stage-1 choice happened to be good.

## Honest verdict
The paper's compounding-rot claim did **not** reproduce even over a 4-break sequence: capable models tend to
pick an extensible design early, and an extensible design absorbs breaks additively regardless of method. The
method's real, measured value across BP1–BP5 is **reducing the variance of the early structural choice**
(reliably avoiding the occasional shortcut a plain builder takes) — a genuine but probabilistic benefit at a
cost premium — plus durable records (a Q2 continuity signal seen again here: the aims records named each
extension seam and the fresh sessions used them). Compounding rot remains unobserved; it likely needs a
product where the extensible design is *not* the obvious first choice, or a genuinely non-refactoring
executor. n=1.
