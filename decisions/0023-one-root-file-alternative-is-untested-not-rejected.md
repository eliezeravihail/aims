---
title: "the single combined root discussions-and-decisions file is considered-but-untested, not rejected (bp18 withdrawn)"
date: 2026-09-22
---

**Context.** `decisions/0002` chose two homes — a same-named companion beside each source file that earns
one, plus root records — and lists the alternatives it rejected (a central folder, a parallel mirrored
tree). A further alternative was proposed during this run and is **not** among them: **one combined
discussions-and-decisions file at the project root**, no per-file companions at all. Its argument is the
same premise the first gate now makes explicit — once a record holds only what the code cannot, the cases
that earn a record at all are rare, and a handful of entries per project may not need per-file homes or
the anchor/staleness machinery that goes with them.

**The evidence that appeared to settle it does not.** `bp18` tested that alternative against companions.
Its records were **written by hand, not filed by aims** — the same defect that retracted the six
record-layer experiments listed as *Withdrawn* in `goals.md` (I5, BP15/15b, BP16/16b, BP17), which `bp18`
is not among. The comparison therefore measured hand-authored documents, not the layer aims produces, and
its conclusion is withdrawn.

**Decision.** `decisions/0002` stands unchanged and un-superseded — co-located companions remain the
shipped design. But the single-root-file alternative's status is recorded as **considered-but-untested**,
not rejected. Nothing in the record layer may be justified by "the one-file alternative was tried and
lost."

**Consequences.**
- A future reading of `decisions/0002` should treat its alternatives list as incomplete on this point and
  read this entry beside it; `0002` is left unedited, per the append-only rule.
- `bp18` is not citable as evidence in either direction.
- The open question is inherited, not closed: a valid test would compare aims-**filed** records in both
  shapes. Its outcome could retire the companion/anchor mechanism rather than merely tune it, so the cost
  of leaving it untested is a whole layer whose necessity is assumed.

**Alternatives.**
- *Record it as rejected* — rejected: no valid evidence rejects it, and filing a withdrawn result as a
  decision is exactly the error `decisions/0008` corrected elsewhere.
- *File nothing and leave the alternative unrecorded* — rejected: an unrecorded alternative is re-proposed
  from scratch, and the next proposer would rediscover `bp18` and read it as settled.
