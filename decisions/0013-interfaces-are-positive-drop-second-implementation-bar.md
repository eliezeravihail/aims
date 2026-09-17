---
title: "interfaces are positive: drop the second-implementation criterion, rank under-structuring as the primary failure"
date: 2026-09-17
---

**Context.** aims was tuned with a strong subtractive/anti-over-engineering bias (the subtractive pass "run
on every design", §12 YAGNI, "prefer duplication", "length is never a merit"). Its §2 gated a polymorphic
interface on a **describable second implementation**. Two problems surfaced: (1) that bar requires
*predicting* a future implementation and so **discourages the very seam it exists to create** — you write
the concrete thing, then reopen it when the second case lands; (2) the accumulated one-directional
minimalism cues push toward **under-structuring**, which is the *opposite* of the real failure mode of
unguided code generation (flat procedural code, inline literals, primitive obsession, anemic bags, unowned
rules). aims' purpose was never anti-over-engineering; it is correct **and** clean design — leanness is a
means that had overshot.

**Decision.**
1. **Drop the "describable second implementation" criterion** from §2. It is a prediction/count gate that
   blocks extension. Keep the guard that needs no prediction: is the exposed type a **domain concept
   defined by consumer need**, or a costume mirroring one concrete (a leak)? Judged by **shape, not count**.
2. **State the asymmetry:** an interface provided where a second implementation never arrives is a light,
   local cost; a seam withheld and later needed forces a reopen. So **lean toward naming the seam when
   unsure.** Over-provision of interfaces is the lighter fault; stinginess is the graver one.
3. **Rank the failures** in the preamble: the dominant failure of unguided generation is
   **under-structuring**; over-engineering is a real but lighter, secondary fault. When unsure, the graver
   risk is too little structure, not too much.
4. **Remove one-directional slogans** where they harm: "Length is never a merit" (added to the scoring
   layer this cycle) restated symmetrically — length moves the score in neither direction.

**What is preserved.** The §2 bedrock (always expose a domain type, never leak a concrete), the
floor/ceiling calibration, concept-fit, family altitude, and the subtractive pass — which already carries
its floor ("if deleting it damages a real, current ownership, keep it") and now reads as a **secondary**
guard under the disease-ranking, not a co-equal aggressive mandate. Correctness (§13) and single-owner (§9)
remain the precondition the rest serve.

**Consequences.**
- `design-principles.md` §2 and preamble edited (commit rebalancing §2); `quality-metrics.md` slogan
  restated. The guidance doc and the measurement doc stay two faces of one method (18 principles ↔ the
  §-table).
- The neutral single-pass re-run under this rebalanced method placed aims first on marketplace and tied on
  checkout, retracting the earlier "aims last on checkout" reading
  (`../experiments/single-pass-assessment-rerun/README.md`) — though de-anchoring and this rebalance both
  contributed and are not separable at n = 1.

**Alternatives.**
- *Keep the second-implementation bar, add a counter-slogan for under-building* — rejected: more
  one-directional prose is the harm, not the fix; a model over-indexes on loud refrains.
- *Delete the subtractive pass entirely* — rejected: over-engineering is a real (if secondary) fault; the
  pass stays, demoted and floor-bounded, not removed.
