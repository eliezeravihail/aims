---
title: "judges — survival (Q2) and two opposite-disposition design judges (Q1), blind"
date: 2026-09-17
---

# Judges — upgraded-aims re-run

Same readings the frozen [`../aims-vs-openspec`](../aims-vs-openspec/results.md) pilot used, applied to the
upgraded-aims arm only. Q2 (survival) is the pilot's declared **primary** reading; Q1 (design quality) is
the two-opposite-disposition reading that placed old aims third.

## Q1 blind mapping (sealed from the judges)

The two Q1 judges saw three stage-3 designs as **Design P / Q / R**, shuffled, with no method names:

- **Design P = plain arm** (the pilot's saved `run-log/blind/Z/stage-3.md`, 2009 lines)
- **Design Q = OpenSpec arm** (the pilot's saved `run-log/blind/X/stage-3.md`, 1251 lines)
- **Design R = aims-upgraded arm** (this re-run — [`arm/stage-3.md`](arm/stage-3.md))

Both P and Q are the *original pilot's own* plain/OpenSpec stage-3 designs, unchanged — so the only new arm
is R. Judges were told length is not a merit.

## Q2 — survival (primary reading), upgraded aims

Independent judge, blind to method, adversarial (it rechecked the design's own "unchanged"/"extended"
claims against the text). Full report in the run; the counts:

| transition | reopened + discarded |
|---|---|
| stage 1 → stage 2 | **1** (PricingEngine — it took on explanation-assembly + non-stackable arbitration at once) |
| stage 2 → stage 3 | **0** (tax/markets landed entirely at the new `Market` component + wiring) |
| **TOTAL** | **1** |

> "the design's cost across the two minimal extensions is concentrated in this single stage-1→2 change to
> the engine; the market/tax capability added in stage 3 landed entirely at new components plus wiring,
> reopening nothing."

**Compare the pilot (same product, same three cards): old aims = 11 (4 + 7); OpenSpec = 8; plain = 9.**
The decisive stage-2→stage-3 tax/market transition cost **old aims 7** reopens and the **upgraded arm 0**.
README §8's disqualifying falsifier ("the aims arm reopens more than OpenSpec") fired in the pilot (11 > 8)
and is decisively reversed here (1 < 8).

## Q1 — architecture / design quality, two opposite dispositions

### YAGNI / simplicity judge → verdict **Q (OpenSpec)**; ranking **Q > P > R**

> "**tax is a decomposition of a total, and only P and Q model it as one** — a single structure carrying
> `net + tax == payable`, joined to the explanation at exactly one shared number and kept out of the delta
> chain, in BOTH markets. **R crams NORTH's tax into a movement.**" … "the SAME concept (VAT) is an
> Adjustment delta in one market and a `LineTax` decomposition in the other — two structures for one
> concept, for the two markets that exist TODAY … precisely the value-correct cram review.md's concept-fit
> pass targets." It credited R's `Market` interface as "a genuinely EARNED abstraction," but "it does not
> buy back the concept-fit fault, which is latent-architectural."

### Invariant-ownership / encapsulation judge → verdict **no clear advantage (P and Q co-lead; both clearly ahead of R)**

> "The single structural fact … ownership of the tax invariant `net + tax == payable`. Tax is a
> DECOMPOSITION of a settled amount, not a MOVEMENT of it. P and Q each give that decomposition ONE owning
> structure kept OUTSIDE the delta chain … **R fails exactly this test, in the way both P and Q predict is
> fatal.**" It listed four invariant-ownership failures for R, including:
> - "The `Adjustment` type is overloaded with three concepts … a decomposition crammed into the movement
>   shape";
> - "the cart explanation ends at payable (26.33) while line explanations end at the net total (22.50), so
>   line finals no longer sum to the cart final";
> - "**R never assigns an owner to apportioning a cart-level discount onto lines** … so R's own stated SOUTH
>   figure (C2: line 10.80, tax 1.80) is unreachable from its pipeline (line_final stays 12.00, per-line
>   tax 2.00)." — a **correctness gap**, not only a concept-fit one.

### The agreement is the finding

In the **original pilot the two dispositions split** (YAGNI → OpenSpec, ownership → plain), which by the
pilot's own logic made the top verdict "a taste artifact, not a structural fact." **Here they agree**: both
place the upgraded aims arm **third/last**, and both pin it to the *same* deciding fact (tax modelled as a
movement in NORTH and a decomposition in SOUTH — two structures for one concept). By the pilot's agreement
test this is a **structural** finding, not taste.

## The tension worth recording

The choice that **won** the survival count is the same one the quality judges **fault**: reusing the
existing `Adjustment`/`Explanation` delta chain for NORTH VAT is exactly why stage 3 reopened nothing (0),
and it is exactly what the concept-fit pass calls a value-correct cram. Old aims got the worst of both
(dissolved the invariant *and* reopened 11); the upgraded arm got the best survival (1) but bought part of
it with a concept-fit compromise — and, per the ownership judge, a real SOUTH apportionment gap.

**Caveats:** n = 1; the two Q1 judges here ran on the current default model (the pilot's Q1 judges ran on
Opus 4.8 — a possible model difference); and see the deviation in [`results.md`](results.md) — the re-run
ran the panel on *every* stage, not just the opening round, so the arm got more design effort than real
aims would give at stages 2–3 (which makes the Q1 third place a conservative, not inflated, negative).
