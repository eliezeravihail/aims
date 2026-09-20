---
title: "BP4 — does the method's concept-fit review catch a cram a plain designer ships? (filter-as-score)"
date: 2026-09-20
status: pre-registered before any arm ran
---

# Question
BP1-3 found aims' TRAJECTORY edge reducible to one transferable principle. This probes a DIFFERENT, subtler
place the paper says the method helps: CONCEPT-FIT — a hard constraint mis-modeled as a soft score, which is
value-plausible but does NOT guarantee the rule. Does aims' concept-fit review catch a cram a plain designer
ships?

# Product (design-only): a playlist/queue builder with a hard adjacency constraint
Card states: build an ordering of items (each has a `category`) satisfying: **no more than 2 items of the
same category may appear consecutively** (a HARD rule — the output must never contain 3-in-a-row), plus
maximize a per-item relevance score. Two arms design it (aims as-is vs plain), stated identically.

# The cram (hidden)
The tempting wrong model: treat the adjacency rule as a **penalty added to the relevance score** and pick a
best-scoring order (soft). That is value-plausible but does NOT guarantee no-3-in-a-row: a high relevance can
outweigh the penalty and ship a 3-run. The concept-correct model treats it as a **hard feasibility
constraint** (a filter on legal placements), with relevance optimized only among feasible orders.

# Metric (rubric-free, fixed now)
Read each delivered design's treatment of the adjacency rule:
- **PASS (concept-correct):** the rule is a hard constraint/filter that structurally cannot emit 3-in-a-row
  (e.g. a legality check on each placement; a constraint the search may not violate).
- **FAIL (cram):** the rule is folded into the score as a penalty/weight, so a high enough relevance can
  produce a 3-in-a-row. (The tell: no place in the design structurally forbids the 3rd consecutive.)
**Method win iff aims PASSES where plain FAILS.** Both pass = null (strong designers avoid the cram); both
fail = null (the product is too hard / the cram too tempting for either). n=1; suggestive.
