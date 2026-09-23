# BP4 plain arm — verdict: PASS (concept-correct, no cram)

The plain arm (no method) modeled Rule H as a **hard structural constraint**, NOT a score penalty:
- `buildQueue -> Result<Ordering, InfeasibleUnderRuleH>` — H is a total guarantee; infeasibility is an
  explicit error, not best-effort.
- Algorithm "Guarded Relevance Greedy": a **gate** (a category at runLen==2 is removed from the choice set)
  + a **guard** (a move is admitted only if `canComplete` leaves the remainder completable), forming a loop
  invariant; relevance (Goal G) chooses only *within* the H-admissible set (gate-then-rank, strict H-over-G).
- Explicitly: "Rule H is structural, not scored ... G can never override H."

This is exactly the concept-correct model (hard feasibility filter), not the filter-as-score cram. **PASS.**
The plain arm avoided the cram unaided — a strong-model baseline the method would have to beat.
