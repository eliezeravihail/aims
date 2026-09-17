---
title: "a standardized assessment form is the quality instrument; the operational review is its worst-first, score-less projection"
date: 2026-09-17
---

**Context.** There is no external ground-truth benchmark for design quality (correctness benchmarks measure
correctness; deterministic metrics measure surface complexity — the ledger static-metric cross-check in
`../experiments/judging-rubric/cross-experiment-regrade.md` shows them blind to concept-fit). aims already
scores quality informally in its measurement layer (`quality-metrics.md`); the gap was **formalization** —
turning that into a standardized, fillable, cited instrument so runs and judges are comparable and auditable.
Separately, aims' operational review is deliberately **score-free** ("never a score" / "no weighted
composite" — `SKILL.md`, `references/review.md`, `experiments/PROTOCOL.md`), because a composite verdict in
the loop invites gaming and replaces findings-with-evidence. A scored form and a score-free review looked
like a contradiction.

**Decision.** One instrument, **two projections**.
1. **The assessment form** (`../experiments/judging-rubric/assessment-form.md`) is the standardized quality
   instrument: one row per principle §1–§17, each row a **0–10 score derived from the binary sub-checks**
   (not eyeballed), a severity tier, and a **required cited finding for any score below 10**. Its full form +
   aggregate profile is the **judging / measurement projection** — the research layer that legitimately
   produces a number (comparing arms, benchmarking).
2. **The operational review** (the Guide measuring a Worker's design) is the **worst-first, score-less
   projection of the same form**: take only the rows scored below 10, sort them **ascending by score (most
   severe first)**, present each with its principle and citation, and emit **no aggregate grade**.

**"Never a score" is refined, not reversed.** It means **no composite verdict** decides direction in the
loop — and that holds: the operational projection has no aggregate number, it is a severity-ordered findings
list feeding direction exactly as before. What is new is only that the findings are now **ordered by the
per-principle score** so the most material violation leads, and each finding carries the sub-check-derived
severity that fixes the order. A per-finding severity is the ordering key, not a grade on the design.

**What formalizing buys, and what it does not.** It buys **reliability** — same design → same profile across
judges/runs, because every row is sub-check-derived and cited. It does **not** buy external **validity** — no
benchmark exists to anchor "does this number predict real maintainability." The form's validity rests on the
principles being sound; it is triangulated with survival and deterministic metrics as separate signals that
need not agree, and it is named an *instrument*, never a benchmark.

**Consequences.**
- `assessment-form.md` is added as the fillable instrument, referencing `quality-metrics.md` for the
  sub-check derivation; a worked example (the ledger blind arm) is filled in it.
- `references/review.md` states the operational review presents the worst-first, score-less sub-10 findings
  projection, and clarifies that "never a score" bars a composite verdict, not the per-finding ordering.
- The measurement layer (`quality-metrics.md`, the experiment records) keeps its scored profile; the two
  projections come from the one filled form, so the review and the benchmark can never diverge.

**Alternatives.**
- *Put a composite grade into the operational review* — rejected: reverses "never a score" and installs the
  enforcement/gaming surface aims refuses.
- *Keep the two layers as separate instruments* — rejected: they would drift; deriving both projections from
  one filled form is what keeps the review and the benchmark consistent.
- *Adopt an external benchmark instead of building the form* — rejected as impossible: no external
  ground-truth quality benchmark exists (this ADR's context).
