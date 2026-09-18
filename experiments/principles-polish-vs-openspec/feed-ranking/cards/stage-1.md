# Feed ranking — stage 1

Design a service that produces an **ordered feed** for a user.

Input per request: a `user` and a list of **candidate items**. Each candidate carries three signals:

- `recency` — how fresh the item is (0.0 – 1.0, higher = fresher).
- `affinity` — how close the item's author is to the user (0.0 – 1.0).
- `popularity` — normalized engagement (0.0 – 1.0).

The service combines the signals into a single score per item and returns the candidates **ordered by score,
highest first**. The weight of each signal is **configuration**, set per deployment (e.g. recency 0.5,
affinity 0.3, popularity 0.2), and an operator changes the weights without a code change. Ties break by a
stable item id.

Deliver the architecture of this service. Design only — no implementation.
