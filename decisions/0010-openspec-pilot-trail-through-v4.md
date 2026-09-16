---
title: "the aims-vs-OpenSpec trail through v4 — 0007's negative headline is superseded, with a caveat"
date: 2026-09-16
---

**Context.** `decisions/0007` recorded the aims-vs-OpenSpec pilot's v1 finding — **no design advantage for
aims**, survival reopened the most (11), the falsifier fired — and reads as final. Three further runs have
since happened (v2, v3, and the clean isolated re-run **v4**), and `0007` carries no forward pointer. This
ADR is that pointer; it supersedes `0007`'s *finality*, not the honesty of its method. The full,
unhedged evidence lives in `goals.md` (Evidence status) and `experiments/aims-vs-openspec/results-v4.md`
— this record only states the trail so a session at `0007` is not stranded on the v1 verdict.

**Trail.**
- **v2** (`design-principles.md` §2 sharpened): survival churn ~halved (11 → 5); quality still a wash.
- **v3** (concept-fit pass added to `references/review.md`): the v1/v2 interface-cram fault gone; survival
  trajectory to 1 for the panel arm — **but v3 was flawed** (arms could reach `decisions/0007`, which
  names the fault). Superseded.
- **v4** (clean isolated re-run, arms with no access to the fault-naming records): survival aims-panel **7**
  (best), OpenSpec 8, aims-single 10; **both opposite-prior judges rank aims-panel first** (v3's split did
  not reproduce); both aims arms caught concept-fit mismatches with zero exposure to the tax example — the
  pass **generalizes**, demonstrated clean.

**Decision — the honest post-v4 reading.**
1. **`0007`'s "no design advantage" is superseded by v4**, the strongest result either aims arm has
   produced against OpenSpec. Do not cite `0007` as the current headline; cite `goals.md` + `results-v4.md`.
2. **The win is real but not unqualified:** aims-panel's own v4 design ships a **confirmed real defect**
   (its SOUTH tax mechanism reads a per-line field an earlier stage never populates) — both judges call it
   non-ranking-inverting, but fixing it likely erases part of the survival margin. "aims wins" is true of
   this pilot's *measures*, not yet of a design one should build from unmodified.
3. **The record layer's demonstrated payoff stays narrow and real:** the durable append-only trail of *why
   a superseded decision no longer holds* (this ADR is an instance).

**Consequences.**
- `0007` is not rewritten (append-only); this ADR and `goals.md`'s Evidence status are read with it.
- `results-v3.md` is corrected to point at v4 as the existing clean re-run, not an owed one.

**Alternatives.**
- *Restate v4's full findings here* — rejected: `goals.md` and `results-v4.md` own them; an ADR that
  duplicates them would drift. This record owns only the trail and the superseded-ness of `0007`.
- *Leave `0007` with no forward pointer* — rejected: a session navigating the ADR trail would inherit the
  v1 negative as current, the exact failure append-only supersession exists to prevent.
