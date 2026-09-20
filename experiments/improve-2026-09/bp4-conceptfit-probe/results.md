---
title: "BP4 result — both arms avoided the concept-fit cram (null); strong model unaided = aims"
date: 2026-09-20
---

# BP4 — concept-fit probe (hard constraint vs filter-as-score): NULL

Pre-registered (`plan.md`): a playlist builder with a HARD "no 3 same-category in a row" rule; does each arm
model it as a hard constraint/filter (PASS) or fold it into the relevance score as a penalty (FAIL cram)?
**Method win iff aims PASSES where plain FAILS.**

## Outcome — both PASS. Near-identical concept-correct designs.

| arm | Rule H treatment | verdict |
|---|---|---|
| **plain** (no method) | hard feasibility filter: gate (block a 3rd consecutive) + guard (`canComplete` look-ahead), relevance chosen only *within* the H-admissible set; "structural, not scored"; infeasible → explicit `Err` | **PASS** |
| **aims** (full method) | same gate+guard hard filter, plus H encoded in a `ValidOrdering` smart-constructor type and `Infeasible` as a first-class sum variant; its concept-fit review explicitly verified "H is NOT a score/penalty" citing review.md's example | **PASS** |

Both arms independently derived the **same** exact feasibility predicate (`M ≤ 2·(T−M)+2`) and the same
gate-then-rank (strict H-over-G) structure. The tempting filter-as-score cram — which the concept-fit pass
exists to catch — **neither arm committed.**

## Verdict: null → no method win here

The plain (no-method) arm avoided the concept-fit cram **unaided**, reaching a design equal on the
pre-registered correctness criterion. aims' concept-fit review **confirmed** the same design (and added a
little more type-safety: the `ValidOrdering` invariant type, the `Infeasible` variant) but did **not** catch
anything the plain arm missed — there was nothing to catch. So on this probe the method's distinctive
concept-fit discipline was not the differentiator.

This is consistent across the whole run: on tractable single-artifact products, a capable model avoids even
the subtle crams the method's passes target; aims' machinery confirms rather than rescues. The method's
review earns its keep where a builder is *weaker* or the trap is *genuinely non-obvious at scale* — not on a
strong model against a nameable cram. n=1; suggestive.
