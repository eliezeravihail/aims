# Stage 3 — a second market

*Deliver this card verbatim, only after every arm has closed stage 2.*

---

We are opening in a second country, and their tax law does not work like ours. A cart is now priced **for a
market**.

## Market `NORTH` — what we have been doing all along

Listed prices are **tax-exclusive**. VAT of **17%** is applied to the discounted cart amount, **after every
promotion**, and the result is rounded **half-up** to the cent — **once, at the cart level**. Line amounts
stay as they are today.

Everything in stages 1 and 2 describes this market and must keep behaving exactly as it does now.

## Market `SOUTH` — the new one

- Listed unit prices are **tax-inclusive**: the price on the shelf already contains **20%** VAT.
- Promotions apply to the **gross (tax-inclusive)** amount, exactly as a customer would expect — 10% off a
  12.00 shelf price is 1.20.
- We must report, **per line**, how much of that line's final amount is tax — their invoices are required to
  show it.
- Per-line tax is rounded **half-even** to the cent, **per line**, not at the cart level.
- The cart's tax is the sum of the line tax figures. It must equal what the invoice shows, exactly.

## And it must still explain itself

Everything stage 2 gave us still applies, in both markets: the ordered adjustments, the deltas that sum
exactly, the superseded non-stackable codes. Tax is part of what a customer asks about, so an explanation
that cannot account for the tax is not an explanation.

## Acceptance (we will run these)

| # | Market | Cart | Codes | Expect |
|---|---|---|---|---|
| C1 | `NORTH` | `WIDGET` 12.50 ×2 | `SAVE10` | net 22.50; VAT 3.825 → **3.83** half-up, once at cart level; total 26.33 |
| C2 | `SOUTH` | `WIDGET` 12.00 ×1 | `SAVE10` | final gross 10.80; line tax **1.80** |
| C3 | `SOUTH` | `SACHET` 0.15 ×1, `CLIP` 0.45 ×1 | — | line tax **0.02** (0.025 → half-even → 0.02) and **0.08** (0.075 → 0.08); cart tax 0.10 |
| C4 | `SOUTH` | `SACHET` 0.15 ×1, `CLIP2` 0.15 ×1, `PIN` 0.15 ×1 | — | each line tax **0.02**; cart tax **0.06** — *not* 0.08. Tax is rounded per line, never at cart level |
| C5 | `SOUTH` | `COFFEE` 4.00 ×4 | `COFFEE3` | BOGO applies to the gross shelf prices → gross 12.00; tax 2.00 |
| C6 | `NORTH` | every stage-1 and stage-2 acceptance case | as before | unchanged, to the cent |

You can ask us product questions, one at a time.
