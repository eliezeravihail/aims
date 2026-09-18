# Order allocation — stage 1

Design a service that prices an **order**.

An order has a list of **line items**, each with a unit price and a quantity. The order may carry one
**order-level discount** — either a percentage off the order subtotal (e.g. 10%) or a fixed amount off
(e.g. $5). Compute and return the order's **final total**: the subtotal (sum of line prices) minus the
order-level discount, in whole cents.

Money is in cents (integers) or `decimal.Decimal` — the design's call. Rounding, where needed, is
half-even.

Deliver the architecture. Design only — no implementation.
