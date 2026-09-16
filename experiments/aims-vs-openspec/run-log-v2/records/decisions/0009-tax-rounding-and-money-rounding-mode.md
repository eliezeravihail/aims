---
title: "0009 — Tax rounding and Money's rounding mode (reopening INV-2's single mode)"
date: 2026-09-16
---

## Status
Accepted (stage-3 design). Grounded by C1 (NORTH VAT half-up), C3/C4 (SOUTH tax half-even, per line).

## Context
Stages 1–2 fixed a single global rounding mode (ROUND_HALF_UP) owned by `Money`. The second market
breaks that assumption: SOUTH's **per-line tax** is rounded **half-even**, while discounts everywhere and
NORTH's cart VAT stay half-up. So "one fixed rounding mode" is no longer true, and the money layer must
accommodate more than one mode without scattering rounding knowledge.

## Decision
- **`Money` remains the sole owner of "money is a 2-decimal `Decimal`, exact to the cent, never `float`"
  and of quantization — but quantization takes a rounding mode, defaulting to `ROUND_HALF_UP`.** The
  *mechanism* (quantize to 2dp at a given mode) is Money's; the *policy* (which mode, and whether per line
  or per cart) is **not** — it belongs to the `Market` (ADR 0008).
- Concretely, `Money.__init__(amount, rounding=ROUND_HALF_UP)`, `Money.percent(pct,
  rounding=ROUND_HALF_UP)`, and a new `Money.fraction(num, den, rounding=ROUND_HALF_UP)` (a rational
  fraction of an amount, for tax extraction). A `CENT` constant is exposed.
- **Every existing caller is unchanged** because the default is half-up: the discount pipeline, the
  allocator, and NORTH's VAT (`net.percent(Decimal(17))`) reproduce every stage-1/2 number byte-for-byte
  (C6). Only a `Market` passes a non-default mode: SOUTH tax = `gross.fraction(1, 6, ROUND_HALF_EVEN)`.
- No double-rounding: a value already at 2dp quantizes to itself under any mode, so the market rounds
  once at its chosen mode and wraps a clean `Money`.

## Consequences
- INV-2 restated: **Money owns the representation and the quantization mechanism; the rounding mode is an
  argument (default half-up). No component other than Money quantizes; no component other than a `Market`
  chooses a non-default mode.** `float` remains forbidden near money.
- `money.py` is the only pre-existing file whose public surface changes this stage, and only additively
  (a defaulted parameter + one new helper).

## Alternatives rejected
- **A second money type for half-even tax** — splits the currency concept for a rounding-mode difference;
  the mode is a parameter of an operation, not a different kind of money.
- **Letting the market quantize a raw `Decimal` outside `Money`** — moves quantization out of its single
  owner; rejected in favor of Money accepting the mode so it stays the only quantizer.
- **Keeping a single global mode and rounding SOUTH tax half-up** — contradicts C3/C4 (0.075 → 0.08 to
  even; three 0.025 lines → 0.06, not a cart-level 0.08).
