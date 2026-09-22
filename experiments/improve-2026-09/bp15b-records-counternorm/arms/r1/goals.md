# Goals — payout settlement

Split a payment total across payees and hand the rows to the payment rail.

- **Exact**: the emitted rows sum to the total, to the cent.
- **Current**: a settlement always reflects the *latest* corrected figures from upstream.
- **Rail-safe**: every emitted row must be something the payment rail will actually accept.
- **Contract-true**: rounding follows the partner agreement, not our sense of fairness.

Out of scope: currency conversion, tax, executing the transfer.
