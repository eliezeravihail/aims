---
title: "BP10 — the correctness question: does the shortcut cause a WRONG answer, and does aims catch it?"
date: 2026-09-20
status: pre-registered before any arm ran
---

# The one claim the campaign hasn't hit

BP1–BP9 all found correctness **ties** — aims' measured edge was always *trajectory* (avoided reopens), never
a *correct-vs-wrong* difference, because the products were tractable enough that both arms got them right.
aims' headline claim is that it improves **correctness in the result** (the plant→mineral loss that motivated
I1). BP10 tests it directly by choosing a product with a **subtle corner a real fraction of quick builds get
WRONG**, then asking whether aims' §1 full-input-space trace / review catches what a plain build ships.

# Product: a booking calendar with a half-open boundary corner

`book(start, end)` reserves `[start, end)` (half-open) and rejects overlaps. The **load-bearing corner**:
two bookings that *touch* (`[10,20)` then `[20,30)`) do **not** overlap. The correct overlap predicate is
strict — `a.start < b.end AND b.start < a.end`. A build that reaches for the common **closed-interval**
predicate (`a.start <= b.end AND b.start <= a.end`) will **wrongly reject the adjacent booking** — a genuine
correctness bug, caught by the hidden touch-point tests. The card states `[start, end)` but does **not**
spoon-feed the touch case (it is implicit — the fair I4-style setup).

# Design (two parts)

**Part A — plain correctness base rate (haiku).** 6 fresh plain haiku builds of the card. Score each against
the hidden suite (11 tests; 3 are touch-point corners). Metric: **how many builds ship the touch-point bug**
(fail a touch test). This is the correctness analogue of BP6 — the base rate of a *wrong answer*, not a reopen.

**Part B — does aims catch it?** Over the buggy builds (if any), run the aims review / §1 full-input-space
trace (competent Guide, as BP9) and ask: does it independently surface the touch-point corner and the strict
predicate? Plus one full-method aims arm on the card: does §1 drive it to the strict predicate unaided?

# Pre-registered predictions

- If the corner is error-prone on haiku: plain ships the bug on **≥1–3 / 6** builds — the first **correctness**
  (not trajectory) base rate in the campaign. If 0/6, the corner is too easy on this card/model and BP10 is a
  null on the correctness claim at this difficulty (recorded as such — aims can't beat a base that's already
  right, exactly as I1/I4 found on opus).
- If aims catches it (Part B): §1's "trace the whole procedure, not just the given examples" names the
  touch-point and pins the strict predicate where a plain build guessed the closed one — a **correctness win**,
  the claim the campaign has not yet demonstrated. If aims *also* guesses closed, the §1 trace is not
  sufficient on this corner (honest negative).

# Guardrails

The touch-point is an objective right/wrong (defined by the half-open spec), not a style call. n=6 for the base
rate; one product/model. Arms never see the hidden tests, the reference, or this plan. Nulls recorded as nulls.
