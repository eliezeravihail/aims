# BP4 aims arm — verdict: PASS (concept-correct)

Same gate+guard hard-filter design as the plain arm, plus: Rule H encoded in a `ValidOrdering` type (smart
constructor — holding one is proof H holds), and "no valid ordering" as a first-class `Infeasible` sum
variant (not a degenerate empty ordering). Its mandatory review ran the concept-fit pass and explicitly
verified H is a candidate-set filter, not a score/penalty, citing review.md's "no-3-in-a-row as a penalty
does not guarantee the rule." PASS — but it caught nothing the plain arm missed (both concept-correct).
