# HIDDEN corner probes — P2 discount (frozen before any arm ran; arms never see this)

Representability facts about the delivered type model, scored blind yes/no.

| # | corner (which X × R) | concrete value | required output | representable iff the design… |
|---|---|---|---|---|
| H1 | X1 × R1 disjunction | code = "first_order **OR** min_subtotal(100)"; cart: returning customer, subtotal $120 | **applies** (the OR branch holds) | the condition is a **tree/expression** with `any-of`, not a flat AND-list; a `list[Condition]` implicitly AND-ed cannot express OR |
| H2 | X1 negation | code = "category_present(electronics) **AND NOT** category_present(gift_card)"; cart has both | **not-applicable** (the NOT fails) | negation is a first-class node; a flat positive list cannot express "must NOT hold" |
| H3 | X1 nesting | "electronics AND (first_order OR subtotal ≥ 100)" ; cart: electronics, returning, subtotal $40 | **not-applicable** (inner OR both false) | conditions **nest** (an all-of containing an any-of); a one-level list cannot |
| H4 | R1 empty | a code with **no** conditions | a defined verdict (applies-to-all, or rejected at construction) — **not** an ambiguous crash | the empty combination has a defined identity (all-of ∅ = true, or fail-fast), not an unhandled case |
| H5 | X2 new kind | add a `weekday(set)` condition kind | slots in as one new leaf, no change to the combinator or the evaluator | condition kinds are an open set behind one `holds(cart)` seam, not an enum the evaluator switches on |
| H6 | X3 × R4 tie priority | two codes both apply; one has priority 5, one priority 2 | deterministic single winner (priority, then a stated tiebreak) — order-independent | selection among applicable codes is its own owner with a total order, not left to list/iteration order |

**Scoring.** Score = # of H1–H6 the delivered design's **types can represent** without a type change.
H1–H3 are the expression-tree corners (a flat `list[Condition]` fails all three); H4 the empty-combination
corner; H5 the open-kinds seam; H6 the selection corner. A design that models a code's conditions as a flat
list of positive requirements fails H1, H2, H3.
