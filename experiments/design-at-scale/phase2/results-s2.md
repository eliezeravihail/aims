---
title: "design-at-scale Phase 2, stage 2 — B vs C supported under the one stage-2 judge"
date: 2026-09-22
---

# Stage 2 (incremental rebuilds) — a secondary result

The disjoint-vocabulary judge alone (`../DESIGN.md` §4), blind, nine designs. Every S4 and the most common S3 were
reproduced before unsealing (`verify-s2/README.md`). The seal (`MAPPING-SEAL-s2.sha256`) matched.

| design | arm | condition | grade | worst | (#S3, #S4) | gate |
|---|---|---|---|---|---|---|
| E | a3 | A | **8.00** | 5 | (1, 0) | CLEAR |
| H | b2 | B | 7.59 | 0 | (0, 0) | CLEAR |
| K | a1 | A | 7.06 | 0 | (1, 0) | CLEAR |
| J | b1 | B | 6.55 | 4 | (3, 0) | CLEAR |
| G | a2 | A | 5.42 | 0 | (3, 1) | BLOCKED |
| D | b3 | B | 4.95 | 0 | (4, 0) | CLEAR |
| M | c2 | C | 4.23 | 0 | (3, 1) | BLOCKED |
| L | c1 | C | 3.81 | 0 | (2, 1) | BLOCKED |
| F | c3 | C | 3.55 | 0 | (2, 1) | BLOCKED |

| condition | worst (F) | mean (M) | range |
|---|---|---|---|
| A — aims, with records | 5.42 | 6.83 | 2.58 |
| B — aims, records withheld | 4.95 | 6.36 | 2.64 |
| C — unaided | 3.55 | 3.86 | 0.68 |

**B vs C, by the registered arithmetic (`PROTOCOL-NOTES.md`): supported** — F(B) 4.95 > F(C) 3.55, and M(B) − M(C) =
2.50 > R(C) 0.68. Secondary: one judge, stage 2 only. The primary endpoint is stage 3, under the full panel.

**The one precondition failure** (reproduced): nothing guards against a Markdown extension that reads another file,
so editing that file leaves a page stale. All three unaided designs carry it, and one aims-with-records design (a2);
no records-withheld design does. In a2 and c2 it breaks plain `mkdocs serve` too, which pristine always rebuilt in
full.

**A vs B** (records → design; predicted: no meaningful difference): A leads on both the worst (5.42 vs 4.95) and the
mean (6.83 vs 6.36), by less than either arm's own range (≈2.6). Reported, no claim.

**The floor does not line up with the grades.** c3 is CLEAR on the probes and last on design; b3 and b2 are BLOCKED on
the probes and mid-to-high on design. The probes test one-off `build --dirty` minimality; the judge's S4 is a case
no probe exercises.
