# Results — plan-diversity pilot (n = 1 objective: "responsible doctor" MVP)

Build/verdict kind: **method-internal, blind, judge-scored.** One objective, one run per arm. **Suggestive,
not robust** (PROTOCOL §7). Method commit pinned at the aims checkout used for the run.

## Un-blinding

| Contestant (blind) | Arm | Diversity source | Judge total /40 |
|---|---|---|:-:|
| design-1 | **B** | inter-model (Sonnet · Opus · Fable), synthesized | **38** |
| design-3 | **C** | stance-seeded (minimal / extensible / verifiable), synthesized | 33 |
| design-4 | **A** | same model ×3 (Opus), synthesized | 32 |
| design-2 | **Baseline** | single pass, no synthesis | 24 |

Ordering on the load-bearing axes (M1 citation chokepoint, M3 expected↔reported join, M5 change locality)
matches the totals: **B > C ≥ A ≫ Baseline.** Judge metrics were Fable-formulated *before* seeing any design;
every score carries a structural reading (`scores.md`).

## Reading against the pre-declared rules

1. **Diversity + cross-examination clearly beats a single pass.** Baseline 24 vs. 32–38 for the three
   collapsed arms — an 8–14 point gap, consistent across metrics. This is the strongest signal in the run.
   *Caveat:* Baseline was a single candidate with **no synthesis pass**, so what beat it is "3 candidates +
   a cross-examination," not "more than one model" — the two are not separated here.
2. **Among diversity sources, inter-model (B) scored highest, stance (C) ≈ same-model (A).** Stance-seeding
   did **not** clearly beat plain repetition (33 vs. 32 — one point, inside noise). On the face of it this
   favors "different models"; but see the confound below, which is decisive.

## The decisive confound — this run cannot credit "inter-model"

**The winning design (B) was synthesized primarily from the Fable candidate, and the judge was Fable.**
Arm B's own divergence map records that its final "is built primarily on cand-fable's structure, which wins
the real decision points" (the multi-layer enforcement — type + CI dependency test + DB schema trigger — and
the closed predicate grammar). Those are exactly the traits the judge rewarded most (M1, M3, M8). So B's
+5–6 point lead is substantially **Fable scoring a Fable-lineage design** — the Arm-B self-preference risk
the experiment design flagged in advance, now observed rather than assumed. **Discount B's margin
accordingly:** this run is not evidence that multiple subscriptions earn their cost.

Once B is discounted, the defensible ordering is **A ≈ C** — the *source* of diversity barely moved the
result; what moved it was having three candidates and a disciplined synthesis. That is consistent with the
user's prior "no need for multiple subscriptions," not against it.

## Convergence — the ceiling was shared

All ten independent candidates arrived at the **same architectural spine**: a sealed `Citation` type behind a
single private-constructor gateway, one `manager→subject` edge with an inert relation label, declarative
pathway rails joined against reported state on read, tier stamped at the source. No arm diverged on the big
shape; they differed only in **how deeply the enforcement was carried** (type-only vs. type + build-test +
schema) and in edge wiring (does an instruction reach the *expected* side; is the reported half required on a
gap citation). Diversity could only ever pay off in that detail band — which caps how large any source effect
could be on this objective.

## Honest bottom line

- **What the run supports:** three passes + cross-examination beats one pass, clearly.
- **What it does not support:** that inter-model diversity beats single-model — the one datum pointing that
  way is contaminated by the judge preferring its own lineage.
- **What it hints:** stance-seeding and plain repetition landed together; the diversity *source* mattered
  little next to the synthesis step.
- **Method note for the next run:** either drop Fable from the generation arms while it judges, or use a
  judge outside all generation lineages; and add a second objective — the convergence here means one
  objective under-tests the arms.

*Load-bearing readings, per contestant, are in `judge/scores.md`; the frozen metrics in `judge/rubric.md`;
per-arm candidate pools, finals, and divergence maps under `arms/`. Blind mapping: `judge/mapping-SECRET.md`.*
