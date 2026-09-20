---
title: "BP11 — the high-context test: does an INTERACTION corner induce a correctness slip (and does aims catch it)?"
date: 2026-09-20
status: pre-registered before any arm ran
---

# Why this, after BP10

BP10 found **0/12** correctness bugs — a clearly-specified *single* corner is not error-prone even on haiku.
It named the untested regime: the correctness claim might be real where a builder **slips under interaction
load**. BP11 builds exactly that: a product with **two stated principles that conflict on a corner**, where the
naive implementation of one principle silently violates the other.

# The product & the interaction corner

A layered access evaluator. Two stated rules:
- **P1** most specific (longest matching prefix) wins;
- **P2** at equal specificity, DENY beats ALLOW.

They **conflict** on one corner: a **specific ALLOW under a broader DENY** (`[("a","DENY"),("a/b/c","ALLOW")]`,
path `a/b/c/d`). P1 says the specific ALLOW wins → `ALLOW`. A builder who collapses the two principles into
"**deny always wins**" (a very common simplification) returns `DENY` — **wrong**. The card states both
principles and the tie-break determinately but does **not** spoon-feed this interaction case (it gives the
*opposite* example — specific-DENY-beats-broad-ALLOW — so "deny wins" looks safe).

# Design

- **Part A (opus, not haiku):** 6 fresh plain **opus** builds. The point is to test whether even a *strong*
  model slips on the interaction under load — if it does, that is a real correctness target aims could address.
  Score vs the hidden suite (10 tests; the corner is `test_specific_allow_under_broad_deny`). Metric: how many
  builds fail the interaction corner (return DENY there).
- **Part B (only if Part A shows bugs):** run the aims review / §1 full-input-space trace over the buggy builds
  (competent Guide) — does it independently surface the specific-allow-under-broad-deny corner and flag the
  "deny always wins" collapse? Plus one full-method aims arm: does §1 pin the correct resolution unaided?

# Pre-registered predictions

- If interaction load matters: plain opus fails the corner on **≥1/6** — the campaign's **first** correctness
  bug, and the first product where aims could win on correctness (Part B tests whether it does).
- If opus is 0/6: even under a two-principle interaction, a strong model resolves the corner — then aims'
  correctness claim has no target even in the high-context regime a small pilot can build, and the honest
  reading is that the claim needs a *genuinely large/noisy* task beyond pilot scale (recorded as such).

# Guardrails

The corner is **determinate** (the card's rules fix the answer to ALLOW); it is not ambiguous. Arms never see
the hidden tests, the reference, or this plan. n=6 (Part A). Nulls recorded as nulls; Part B not fabricated if
there is no bug.
