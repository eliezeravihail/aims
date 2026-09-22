# Goals — payout settlement

Split a payment total across payees, exactly, reproducibly, and once.

- **Exact**: the payouts must sum to the total, to the cent. No rounding drift, ever.
- **Reproducible**: the same settlement inputs must produce byte-identical payouts on any run, on any
  machine, regardless of the order upstream happens to hand us the payees.
- **Once**: a settlement that has been paid must never change, for any reason.

Out of scope: currency conversion, tax, payment execution.
