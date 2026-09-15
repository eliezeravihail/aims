# Stage 1 — price a cart

*Deliver this card verbatim. Nothing outside it is visible to the arm.*

---

We sell things online and we need a service that works out what a cart costs.

A cart is a customer id, a list of lines, and a list of promotion codes the customer has entered. A line is
a SKU, its list unit price, and a quantity.

Give us back, for every line, what that line costs, and what the whole cart costs.

## The promotions we run today

Three kinds. A cart can have more than one code on it.

- **`PCT`** — a percentage off the whole cart. e.g. `SAVE10` = 10% off.
- **`AMT`** — a fixed amount off the whole cart. e.g. `TENOFF` = 10.00 off.
- **`BOGO`** — on one named SKU: for every N of it in the cart, one is free. e.g. `COFFEE3` = buy 3 get 1
  free on SKU `COFFEE`.

Promotion definitions (which codes exist, what kind, their parameters) come from a small data file you
provide and we can edit — we add and retire codes constantly and we are not going to ask an engineer each
time.

## Rules

- Money is in one currency, shown to 2 decimal places.
- A cart total is never negative.
- An unknown or inapplicable code is reported back as such, not silently ignored, and does not stop the rest
  of the cart from pricing.

## Acceptance (we will run these)

| # | Cart | Codes | Expect |
|---|---|---|---|
| A1 | `WIDGET` 12.50 ×2 | — | line 25.00, total 25.00 |
| A2 | `WIDGET` 12.50 ×2 | `SAVE10` | total 22.50 |
| A3 | `WIDGET` 12.50 ×2 | `TENOFF` | total 15.00 |
| A4 | `COFFEE` 4.00 ×4 | `COFFEE3` | one free → total 12.00 |
| A5 | `COFFEE` 4.00 ×4, `WIDGET` 12.50 ×1 | `COFFEE3`, `SAVE10` | total 22.05 |
| A6 | `WIDGET` 12.50 ×1 | `NOPE` | total 12.50, `NOPE` reported unknown |
| A7 | `WIDGET` 1.00 ×1 | `TENOFF` | total 0.00, not negative |

Run it however you like — a library with a CLI is fine, an HTTP endpoint is fine. Tests we can run
ourselves, please.

You can ask us product questions, one at a time.
