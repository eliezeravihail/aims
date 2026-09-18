# Order allocation — stage 2

The order now serves a **second market** with two new reporting rules. Both apply to the same order.

1. **Per-line reporting with tax.** Every line must be reported with its **own final amount**, and a
   **per-line tax** computed at that market's rate **on the line's discounted amount** (tax = round_half_even
   (line_final × rate)). The reported line finals, and the reported line taxes, must be **exact**: the sum of
   the line finals must equal the order's discounted total to the cent (no rounding drift), and the sum of
   the line taxes must equal the tax on the order total.

2. **A third discount kind.** Besides percentage and fixed-amount, the order may now carry a **buy-one-get-one
   (BOGO)** promotion on a given line. It, too, participates in the order-level discounting and per-line
   reporting.

The first market keeps behaving exactly as in stage 1 (a single final total, no per-line tax).

Update the architecture to absorb these rules. Design only.
