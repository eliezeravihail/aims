---
title: "I5 — does a co-located record of a rejected-alternative trap stop a fresh session re-introducing it?"
date: 2026-09-20
status: pre-registered before any arm ran
---

# Hypothesis (aims' second core claim, at the load-bearing scale)

The paper's Q2 / record-layer claim is **unproven in outcomes** — prior continuity tests were at a scale
where the code was re-derivable, so the record only added legibility. This tests the condition the paper
says the record *should* be load-bearing: the code **hides a rejected-alternative trap** — the obvious
approach is wrong, and only the record explains why.

The target (`target/allocate.py`) uses **largest-remainder** money allocation, which preserves the invariant
`sum(shares) == total` exactly. The obvious alternative — independent per-part rounding — breaks it (loses/
gains a cent). The companion `allocate.py.md` records this rejection and the invariant **R-sum**.

The change (`change-card.md`) asks for a new `split_shipping(fee, line_totals)` — another money split, which
tempts a fresh independent-rounding loop.

# Arms (both are fresh aims add-feature sessions; the ONLY variable is the record)
- **with-record:** given `target/` including the companion + a root note; told to consult the co-located
  records before changing code (the shipped SessionStart reading rule).
- **no-record:** given the identical code with the companion/record **stripped**; same task.

Neither arm is told where the trap is. Both run aims as-is (`/aims-add-feature` flow). Not hand-directed.

# Outcome metric (rubric-free, correctness; fixed now)
Hidden probe: `split_shipping(1000, [1,1,1])` **must sum to exactly 1000** (e.g. 334/333/333). Score per arm:
- **PASS** iff the delivered `split_shipping` preserves `sum == fee` on the probe (i.e. it reuses `allocate`/
  largest-remainder, not a fresh independent-rounding split).
- **FAIL** iff it introduces an independent-rounding split whose shares can miss the total by a cent.

**I5 shows the record is load-bearing iff the with-record arm PASSES where the no-record arm FAILS.** Both
pass (the code is present and a strong model re-derives correctly, or reuses `allocate`) is a **null** —
the same partial-null the earlier continuity experiment found, now at trap scale. Both fail is also a null
(the record didn't help). n=1 → suggestive.
