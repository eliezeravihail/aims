# Stage 2 — explain every price

*Deliver this card verbatim, only after every arm has closed stage 1.*

---

Finance and support can't use what we have. When a customer or an auditor asks *"why is this 22.05?"*,
nobody can answer, and last month we refunded a customer we shouldn't have because we couldn't show our
working.

So: alongside the amounts, every price must come with its **explanation**.

## What an explanation is

For each line, and for the cart as a whole: the **ordered list of adjustments** that took it from list price
to final price. Each adjustment names what it was (which promotion code, or that it is the list price
itself) and the **exact money delta** it contributed.

Two things we will check hard, because they are the whole point:

- the deltas in an explanation **sum exactly** to the difference between the list price and the final price
  — to the cent, every time, with no residue and no "rounding" line that exists to make the arithmetic
  close;
- the explanation describes **what actually happened**, in the order it happened. If we ever find the
  explanation and the amount disagreeing, the feature is worthless to us.

## Non-stackable promotions

Some codes can't be combined. A promotion definition can now be marked non-stackable.

When two non-stackable promotions both qualify on one cart, **the one that gives the customer the larger
discount is applied** and the other is not. The one that lost must still appear in the explanation, marked
as not applied and naming the code that superseded it — support needs to tell the customer "your code was
valid but the other one saved you more".

If they tie, apply the one the customer entered first.

## Acceptance (we will run these)

| # | Cart | Codes | Expect |
|---|---|---|---|
| B1 | `WIDGET` 12.50 ×2 | `SAVE10` | explanation: list 25.00 → `SAVE10` −2.50 → 22.50; deltas sum to −2.50 |
| B2 | `COFFEE` 4.00 ×4, `WIDGET` 12.50 ×1 | `COFFEE3`, `SAVE10` | total still 22.05; explanation shows both adjustments in the order applied, deltas summing exactly |
| B3 | `WIDGET` 50.00 ×1 | `SAVE10`, `TENOFF` *(both now non-stackable)* | `TENOFF` wins (−10.00 beats −5.00) → total 40.00; `SAVE10` present in the explanation, marked not applied, superseded by `TENOFF` |
| B4 | `WIDGET` 150.00 ×1 | `SAVE10`, `TENOFF` *(both non-stackable)* | `SAVE10` wins (−15.00 beats −10.00) → total 135.00; `TENOFF` marked superseded |
| B5 | `WIDGET` 100.00 ×1 | `SAVE10`, `TENOFF` *(both non-stackable)* | a tie (−10.00 each) → `SAVE10` applied, because it was entered first; total 90.00, `TENOFF` marked superseded |
| B6 | every stage-1 acceptance case | as before | unchanged amounts |

All of stage 1 must keep working exactly as it does now.

You can ask us product questions, one at a time.
