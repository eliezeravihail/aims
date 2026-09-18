# Continuation change — per-line refund

You are continuing work on an existing `checkout.py` you did not write. Add one function:

`refund(lines, discount, tax_rate, loyalty, line_index)` → `(amount_cents, tax_cents)`

When a customer returns the single item on `line_index`, this is how much **money** and how much **tax** to
give back: exactly what the customer **paid for that line** and the tax that was charged on it. (Sanity: if a
customer returned every line in turn, the refunds should give back the whole order total and all of its tax.)

Keep the module's existing plain style. The existing `test_checkout.py` must still pass **unchanged**.
Deliver the adapted `checkout.py` (add your own tests separately).
