# aims-v2 re-run — designs complete, MEASUREMENT PENDING

The aims arm was re-run alone against the sharpened §2 (aims @ df18c40, merged to master as 7204326),
same three stage cards, same oracle answers reused verbatim from v1 (see `oracle/`). All three stage
designs are complete and were tagged in the arm's own git tree.

**The measurement is NOT done.** The three judges (survival count + two full-rubric design judges on the
blind P/Q/R set) all failed on the Opus session limit (HTTP 429, resets 09:30 UTC). No v2 verdict exists
yet. Do not read a result into this directory — only the designs and the oracle log are here.

## What can be said WITHOUT the judges (design facts, not a verdict)
- v2 is much more compact than v1: stage-1/2/3 = 3103 / 4962 / 5179 words, vs v1's 5345 / 10022 / 12363.
- v2 kept the discount pipeline tax-agnostic and made tax a `Market` post-pass (`model/promotions/catalog/
  allocation` untouched at stage 3) — structurally cleaner on that axis than v1, which folded tax into the
  pricing path.
- BUT v2 still put a `VAT` entry inside the explanation ledger ("INV-7 now spans the tax step"), the same
  family of move both v1 judges flagged. Whether it recreates v1's delta-sum problem is exactly what the
  survival + design judges must measure — unmeasured as of this commit.

## To finish (after 09:30 UTC or on another model)
Re-run the three judges: survival on /tmp or the preserved designs; the two full-rubric judges on the
blind P/Q/R set. Then compare v2's reopened+discarded count against v1's 11, and v2's design placement
against v1's third-under-both.
