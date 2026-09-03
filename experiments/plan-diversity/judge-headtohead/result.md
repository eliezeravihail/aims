# Head-to-head — stance protocol, Fable vs Opus as generator (Opus judge)

**Question.** Hold the protocol constant (3 stance-seeded passes + Opus cross-examination) and swap only the
**generation model**: Opus (the original Arm C) vs Fable (new Arm C-Fable). Does the model matter, or was the
protocol doing the work? Judged blind by **Opus on its own frozen rubric** — a judge biased *toward* the
Opus-generated design (its own lineage), which makes any Fable win the harder, cleaner result.

| Contestant (blind) | Arm | Generator | Opus total /45 |
|---|---|---|:-:|
| design-P | Arm C-Fable (new) | **Fable** | **45** |
| design-Q | Arm C (old design-3) | Opus | 43 |

- **Level on all four load-bearing axes** (M1 citation chokepoint, M3 join, M4 provenance/tier, M5 change
  locality) — both 5/5, neither fails a non-negotiable.
- The Fable design leads only on two **secondary** axes: M6 (pathways-as-generic-rails — it decomposes the
  three brief pathway shapes into three schedule primitives; the Opus one models follow-up outside the
  library) and M9 (authorization as an unforgeable compile-time `Scope` capability vs. a middleware check).

## Reading

Under an identical protocol and a judge biased against it, the **Fable-generated** design came out **slightly
ahead** (45 vs 43) and level on everything load-bearing. So:

- **Fable is a genuinely strong generator for this task** — corroborating "maybe Fable is just better." It is
  at least as good as Opus here, with a small edge on secondary structure, seen even by an Opus judge.
- **But the edge is narrow and non-load-bearing** — "Fable is *meaningfully* better" is only weakly
  supported. On the axes that matter, the two models produce equivalent designs under this protocol.
- **The protocol carries most of the weight.** Swapping the strong model changed a couple of secondary
  scores, not the load-bearing shape — consistent with the earlier finding that *three candidates + cross-
  examination* is the dominant ingredient, and the *source* of diversity (model or stance) is second-order.

## For the "multiple subscriptions" question

This reinforces the answer: pick the single strongest model (Fable looks at least as strong as Opus here) and
run the stance protocol on it — no multi-subscription ensemble needed to reach the top of the field.

## Reliability note

Opus scored design-Q (old design-3) at **43** here vs **44/45** in the full three-judge run — a 1-point drift
on the same design, well within the judge-consistency band already flagged. The rank picture is stable; the
absolute total is not precise to the point.

*Caveat unchanged: n = 1 objective, strong cross-candidate convergence — suggestive, not robust.*
