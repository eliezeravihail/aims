---
title: "Fixed inventory (Step 0) — checkout pricing service"
date: 2026-09-17
---

# Fixed inventory — checkout pricing service

The **Step 0** lists for grading the checkout-pricing designs with
[`quality-metrics.md`](quality-metrics.md). Authored once from the product spec (the pilot's three cards +
oracle), **not** from any design. Identical for every judge and every design. Every deduction a judge makes
must cite an item here (R/X/C) or a named seam of the design under review. A design that **omits** a rule or
fails a case is scored 0–1 on the relevant metric — never N/A.

## R — rules / invariants the product declares

- **R1** Money is one currency, shown to 2 decimals.
- **R2** The cart total is never negative (a line may reach 0 via BOGO; only the cart total is clamped).
- **R3** An unknown or inapplicable code is reported as such, not silently ignored, and does not stop the
  rest of the cart pricing.
- **R4** The same cart yields the same result regardless of the order promotions are applied
  (order-independence).
- **R5** Every price — each line **and** the cart — carries an ordered explanation from list price to final;
  each adjustment names what it was (a code, or the list price) and its exact money delta.
- **R6** The explanation's deltas sum **exactly** to (list − final), to the cent, with no residue and no
  invented "rounding" line.
- **R7** The explanation and the amount can never disagree (the amount is the explanation, not a second
  number).
- **R8** Non-stackable: when two non-stackable codes both qualify, the larger-discount one applies and the
  loser appears in the explanation marked not-applied, naming the superseding code; a tie applies the one
  entered first.
- **R9** A cart is priced for exactly one market (no mixing).
- **R10** Market NORTH: listed prices tax-exclusive; VAT 17% on the discounted cart amount, after every
  promotion; rounded half-up to the cent once, at the cart level; line amounts unchanged; NORTH lines show
  no tax.
- **R11** Market SOUTH: listed unit prices tax-inclusive (20% VAT inside); promotions apply to the gross;
  per-line tax reported; per-line tax rounded half-even, per line; cart tax = the sum of the line tax
  figures, exactly.
- **R12** NORTH keeps behaving exactly as stages 1–2, to the cent (regression).
- **R13** Promotions are editable data (which codes exist, their kind, their parameters live in a data file
  editable without an engineer), not code.

## X — change-axes the product implies

- **X1** Add or retire a promotion **code** (data) — must require no engineer (stated in R13).
- **X2** Add a **fourth promotion kind** — a foreseeable continuation of the three.
- **X3** Add a **third market** with a third tax model — foreseeable (two already exist).
- **X4** *(plausible unstated variant)* a market that is tax-exclusive **but reports per-line tax**, or one
  that both adds and extracts — i.e. a tax shape that fits neither NORTH nor SOUTH cleanly.

## C — acceptance cases (inputs → required outputs)

Stage 1:
- **A1** `WIDGET` 12.50×2, no codes → line 25.00, total 25.00.
- **A2** +`SAVE10` → total 22.50. **A3** +`TENOFF` → 15.00.
- **A4** `COFFEE` 4.00×4 +`COFFEE3` → 12.00.
- **A5** `COFFEE` 4.00×4 & `WIDGET` 12.50×1 +`COFFEE3`,`SAVE10` → 22.05.
- **A6** `WIDGET` 12.50×1 +`NOPE` → 12.50, `NOPE` reported unknown.
- **A7** `WIDGET` 1.00×1 +`TENOFF` → 0.00 (not negative).

Stage 2:
- **B1** `WIDGET` 12.50×2 +`SAVE10` → list 25.00 → `SAVE10` −2.50 → 22.50; deltas sum −2.50.
- **B2** `COFFEE` 4.00×4 & `WIDGET` 12.50×1 +`COFFEE3`,`SAVE10` → 22.05; both adjustments shown in order,
  deltas sum exactly.
- **B3** `WIDGET` 50.00×1 +`SAVE10`,`TENOFF` (both non-stackable) → `TENOFF` wins (−10 > −5) → 40.00;
  `SAVE10` shown superseded by `TENOFF`.
- **B4** `WIDGET` 150.00×1 same → `SAVE10` wins (−15 > −10) → 135.00; `TENOFF` superseded.
- **B5** `WIDGET` 100.00×1 same → tie (−10 each) → `SAVE10` (entered first) → 90.00; `TENOFF` superseded.
- **B6** every stage-1 case unchanged.

Stage 3:
- **C1** NORTH `WIDGET` 12.50×2 +`SAVE10` → net 22.50; VAT 3.825 → **3.83** half-up once at cart; total
  **26.33**.
- **C2** SOUTH `WIDGET` 12.00×1 +`SAVE10` → final gross **10.80**; line tax **1.80**.
- **C3** SOUTH `SACHET` 0.15×1, `CLIP` 0.45×1 → line tax **0.02** (0.025→half-even→0.02) and **0.08**
  (0.075→0.08); cart tax **0.10**.
- **C4** SOUTH `SACHET` 0.15×1, `CLIP2` 0.15×1, `PIN` 0.15×1 → each line tax **0.02**; cart tax **0.06**,
  not 0.08 (per-line rounding, never at cart level).
- **C5** SOUTH `COFFEE` 4.00×4 +`COFFEE3` → BOGO on gross → gross **12.00**; tax **2.00**.
- **C6** NORTH every stage-1 and stage-2 case → unchanged, to the cent.

> **Correctness probe the cases imply (M11):** a **multi-line SOUTH cart carrying a cart-level discount**
> requires the per-line tax to fall on the **discounted** line amount — so the design must allocate a
> cart-level discount down to the lines. C2 is single-line (allocation trivial); a design that cannot
> apportion a cart discount to lines fails this the moment a SOUTH cart has two lines and a `PCT`/`AMT`
> code. Judges test M11 against this, not only against the literal C-cases.
