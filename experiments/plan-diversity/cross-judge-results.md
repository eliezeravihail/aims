# Cross-judge results — same designs, three judges (Fable, Sonnet, Opus)

Re-judging the four frozen blind contestants with three different judge models, to separate **self-preference**
from **genuine quality**. Each judge formulated its own metrics (own rubric) before seeing any design, and
scored every cell with a structural reading. Blind mapping unchanged (`judge/mapping-SECRET.md`).

| Blind | Arm | Fable /40 (rank) | Sonnet /40 (rank) | Opus /45 (rank) | Avg rank |
|---|---|:-:|:-:|:-:|:-:|
| design-1 | **B** — inter-model (Fable-primary synthesis) | 38 (1) | 38 (2) | 44 (1) | **1.3** |
| design-3 | **C** — stance-seeded | 33 (2) | **39 (1)** | 44 (1=) | **1.5** |
| design-4 | **A** — same model ×3 | 32 (3) | 37 (3) | 43 (3) | 3.0 |
| design-2 | **Baseline** — single pass | 24 (4) | 34 (4) | 40 (4) | 4.0 |

*(Opus scored on /45 — 9 metrics — vs /40 for the others; compare ranks, not raw totals, across judges.)*

## Finding 1 — Fable's self-preference was real, but bounded

design-1 is the Fable-lineage design (Arm B's synthesis was built primarily on the Fable candidate). Fable
ranked it **first with a +5 margin** over the next design. **No other judge reproduced that margin:** Sonnet
ranked design-3 first and design-1 second; Opus tied design-1 with design-3. So Fable's *confident lead for
its own lineage* was substantially self-preference — the exact Arm-B risk flagged in advance. The margin,
not the fact that design-1 is good, is what the bias inflated.

## Finding 2 — but design-1 is genuinely top-tier (the clean test passes)

The sharp test was **Opus as judge**: designs 2, 3, 4 are all Opus-lineage; design-1 is the one non-Opus
design. A self-preferring Opus would push its own lineage above design-1. Instead Opus ranked **design-1 tied
first**, above all three of its own-lineage designs. A judge biased *against* a design still placing it first
is strong evidence the design is genuinely excellent — not merely flattered by its author. So the user's
"maybe Fable is just better" is **partly right**: design-1 is a legitimate co-leader; Fable only exaggerated
by how much.

## Finding 3 — what all three judges agree on (the trustworthy part)

- **Baseline (single pass) is last for every judge.** Three passes + cross-examination beats one pass —
  the most robust signal in the study, now confirmed across three independent rubrics.
- **Arm A (same model ×3) is third for every judge** — above baseline, below B and C.
- **Arm B and Arm C are the co-leaders**; which is #1 is judge-dependent and within noise.
- **Arm C > Arm A for all three judges** (33 > 32; 39 > 37; 44 > 43) — a consistent, if small, edge that the
  single-judge run could not establish.

## What this says about the original question (diversity source)

Correcting for Fable's self-preference, **stance-seeding (Arm C) ≈ inter-model (Arm B)** — and Arm C reaches
that on **one model / one subscription**. Two independent results now point the same way and **support the
"no need for multiple subscriptions" position**:

1. Stance-seeded diversity on a single model matches multi-model diversity (C ≈ B across judges).
2. Stance-seeded diversity beats plain repetition on the same model (C > A for all three judges).

The active ingredients, in order of evidence strength: **(1) three candidates + a disciplined cross-examination**
(beats single pass, robustly) › **(2) diverse *instructions*** (stance > plain repetition, consistent) ›
**(3) diverse *models*** (no advantage over stances once self-preference is removed).

## Caveats (unchanged, and one added)

- **n = 1 objective.** Suggestive, not robust. The convergence — all candidates found the same sealed-Citation
  spine — means one objective under-tests the arms; a second objective on a different axis is the next step.
- **Judges differ in generosity/scale** (Fable spread 24–38; Opus compressed 40–44), so cross-judge *totals*
  are not comparable — the agreement is in the **ranks**, which is what matters here.
- **Added:** a judge's self-preference is now a *measured* effect in this study (Fable's inflated margin),
  not a hypothetical — future runs should keep the judge outside all generation lineages.
