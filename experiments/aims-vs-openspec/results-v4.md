# Results — v4 (clean, isolated re-run), three-way vs OpenSpec

Re-run of v3 with the design arms rooted in `/tmp/exp/method-clean/` — copies of only the method's
technique files (`SKILL.md`, `design-principles.md`, `review.md`, and the other files those reference,
plus the domain-clean panel-plan ADR). No path back to `/home/user/aims` anywhere in their instructions or
working tree: no `decisions/0007`, no `goals.md`, no `experiments/`. Same product, same three stages, same
card text, same oracle answers (verbatim, reused from v1/v3 where the same question recurred). Full run:
stages 1→2→3, both aims arms, from scratch — not just stage 3.

Mapping (unsealed after judging): **A = openspec · B = aims-single · C = aims-panel.**

## M1 — survival (change absorption; lower better)

| arm | reopened+discarded | 1→2 | 2→3 |
|---|---|---|---|
| **aims-panel** | **7** | 7 | **0** |
| openspec | 8 | 5 | 3 |
| aims-single | 10 | 5 | 5 |

aims-panel leads. openspec second. aims-single third — its stage-1 "no proration of cart-level discounts
into line prices" stance, defended twice, was reversed at stage 3 when the tax requirement needed it,
reopening its central money-shape decision a second time. (See the caveat below on aims-panel's 2→3
reopening count.)

## Concept-fit: transferred, not memorized

Both aims arms caught concept mismatches with **zero exposure** to the tax example that motivated the
pass:
- aims-single (stage 1) caught BOGO-as-decomposition vs PCT/AMT-as-movement, unprompted.
- aims-panel (stage 2) caught a per-line adjustment list that would have been "a movement bolted onto a
  decomposition that doesn't need one."
- aims-panel (stage 3) **drafted the exact v1/v2 cram** — folding NORTH's VAT into `Explanation.adjustments`
  — then caught and reversed it itself, citing C1's "net" vs "total" distinction and C6's "unchanged, to
  the cent" requirement. This is the pass firing in real time, not a recalled answer.
- aims-single (stage 3) made a *different*, independently-reasoned call: modelled NORTH's VAT as a genuine
  movement **inside** the chain (a real, non-zero delta every time — not an inert tell) while keeping
  SOUTH's tax beside it as a decomposition. Correct application of the same test, not a memorized rule.

## Correctness gate — one confirmed defect, in the design that otherwise wins

All three price every stated case's *headline* numbers as claimed in their own text. But verifying
aims-panel's (C) own worked trace against its own earlier-stage definitions surfaces a real bug:

**Stage 3's SOUTH tax reads `line.explanation.final_amount` as the line's gross.** Stage 2 §5 step 3
defines a line's own `Explanation` as BOGO-only (`adjustments = its BOGO entries if any, else empty`) —
cart-level `PCT`/`AMT` discounts are folded only into the **cart's** `Explanation`, never redistributed
back into any line's own. For C2 (one line, `SAVE10`), the design's trace claims
`pricing.lines[0].explanation.final_amount = 12.00 × 0.90 = 10.80` — but per its own stage-2 mechanism,
that field is `12.00` (BOGO-only; no BOGO here), not `10.80`. The design's own SOUTH mechanism, read
literally against its own earlier stages, does not produce the number its own C2 trace claims. Verified
independently against the design text, not just the judge's report.

**This also compromises the 2→3 survival count of 0.** Reaching *0 reopenings* at the tax stage was
possible only because the design silently read a field that doesn't carry what SOUTH tax needs, rather
than reopening the stage-1/2 per-line `Explanation` to make it carry it. A correct fix — making
`line.explanation.final_amount` actually reflect a line's share of cart-level discounts — reopens exactly
the seam the 0-count depended on not touching. The 7 is a real count of what the design *as written*
reopened; it is not a clean measure of what a *correct* design would have needed to reopen.

## Two opposite-prior substantive judges — both rank aims-panel first

| judge (prior) | ranking | deciding measure |
|---|---|---|
| skeptic-of-clean (hard on M2 accidental complexity) | **aims-panel > aims-single > openspec** | M1 given; M2 — openspec's per-market catalogue split is ~6× the unforced machinery of either aims arm, and is itself the rubric's own textbook accidental-complexity example, disproved by both aims arms pricing every case from one shared catalogue; M3 — openspec worst |
| skeptic-of-deferral (hard on M4 hiddenness, M3 blast radius) | **aims-panel > openspec > aims-single** | M1 leads outright; M2 — aims-panel 0 vs aims-single 2 vs openspec 6; M3 — aims-single reopens the shared `price_cart` seam itself under the reduced-VAT change, judged structurally worse than openspec's isolated (if self-inflicted) catalogue reopening |

**Full agreement on first place, disagreement on second.** Both judges independently found the same
correctness defect region in aims-panel (only the skeptic-of-clean judge scored it explicitly, as a
"serious" fault) and both classify it as **local, not pervasive** — it qualifies the win (a required fix)
without inverting it, per the rubric's own rule that only a hidden-and-architectural fault reaching the
far corner may overturn a design leading on the consequence measures. Neither judge treats "local" here as
license to ignore it; both name it as something that must be fixed before this design ships.

## Comparison to v3 (the contaminated run)

v3 found aims-panel first under one judge, third under the other — a genuine split. v4, run clean, finds
aims-panel first under **both**. This is evidence the earlier split was not really about the method: v3's
skeptic-of-clean judge penalized aims-panel/aims-single for a *self-narrated, self-justified* type-split
pattern ("two-implementations-behind-a-seam") without checking whether a leaner shared mechanism actually
covered every case; this run's skeptic-of-clean judge checked that claim directly against openspec's
catalogue split and found it failed its own test — disproved by both aims arms using one shared catalogue.
Whether that's a difference in the *designs themselves* (independently regenerated, not the same text) or
in how thoroughly this round's judges checked self-narrated virtue is not separable from this pilot alone.

## Bottom line (honest)

- **Change absorption:** aims-panel leads clearly, and independently of the earlier contamination concern
  (this run had none). aims-single trails even openspec here — a real result, not noise, driven by
  reversing its own stage-1 stance under the tax requirement.
- **The concept-fit pass generalizes.** Both aims arms applied it to problems with no resemblance to the
  original tax-in-ledger case, and aims-panel visibly caught and reversed the exact cram in real time, with
  zero exposure to the example. This is no longer merely plausible; it is demonstrated, twice, clean.
- **aims-panel wins substantive judging under both opposite-prior judges** — the clearest result either aims
  arm has produced against OpenSpec across v1–v4.
- **But aims-panel's design as written has a real bug**, in exactly the tax mechanism the whole pilot turns
  on, that both judges correctly classified as not ranking-inverting but that a shipping team would have to
  fix — and fixing it likely erases part of the 2→3 survival advantage this run credits it with. The
  win is real; it is not clean.
