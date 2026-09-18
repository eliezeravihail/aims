# Product — an alerting rule engine (design only)

Design a service that decides whether an incoming **metric event** fires any **alert rule**.

STAGE 1 (base): An event has a metric name, a host, and a numeric value. A rule matches on: metric name
(exact), host (exact), and a threshold predicate on the value (`> N`, `>= N`, `< N`, `<= N`). An event fires
a rule if all three match. Return the fired rules for an event.

STAGE 2 (the product now needs these — they are stated requirements, not future ideas):
- **X1 — set match:** a rule's host may be a single host OR a set of hosts (fires if the event host is in
  the set).
- **X2 — band threshold:** a rule's value predicate may be a single bound OR a **band** — the value must lie
  within an inclusive range `[lo, hi]` (e.g., "between 80 and 95").
- **X3 — ranged event value:** an event's value may arrive as a single reading OR as an **aggregated range**
  `min–max` over a collection window (e.g., a value reported as "72–88"). A band/threshold matches a ranged
  event by the stated rule: a `>N` threshold fires if the event's max `> N`; a band `[lo,hi]` fires if the
  event's range **overlaps** `[lo,hi]`.

Deliver the architecture: the components, the types, the seams, the rule each owns, and the reasoning. No
implementation. A type signature or interface sketch where it makes a boundary concrete is welcome.
