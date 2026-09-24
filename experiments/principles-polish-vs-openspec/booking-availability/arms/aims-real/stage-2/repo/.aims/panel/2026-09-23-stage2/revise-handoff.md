ROLE
You are the design Worker for the mandatory revise round of a DESIGN objective. Design only — no
implementation code; create no file other than the one named below.

INPUT
- The objective (unchanged): `.aims/panel/2026-09-23-stage2/objective.md` — read it.
- The design to revise: `.aims/panel/2026-09-23-stage2/merged.md` — the Guide's merge of three independent
  drafts. It is the design in force; revise it, do not restart it.
- Standards: `.claude/skills/aims-guide/references/design-principles.md`,
  `.claude/skills/aims-guide/references/add-feature-principles.md`; product rules: decisions/0004.
- Do not read other files under `.aims/`.

THE GUIDE'S MEASUREMENT (fix-list, most severe first; each cites where it fails)
1. [§1 correctness of a stated claim — S2] §1.2 A5 claims "with a grid the work is proportional to the
   output; without one, and under a late notice cutoff, removed candidates are still enumerated". Both
   paths now go through `fitting_starts` (a k-range), so both are proportional to the *pre-notice* output,
   and both enumerate candidates that notice later removes. Make the claim true. Decide (and justify)
   whether anything should change — remember notice must never move gap anchors (N1) — or whether the
   cost is simply stated.
2. [§1/§5 load-bearing invariant — S2] The gap walk's correctness now rests on I2′ (starts and ends
   non-decreasing), proved in prose from R4 + a uniform buffer. The design must make it impossible for a
   later change to break I2′ silently: name exactly which tests fail if I2′ stops holding (e.g. step order
   changed, clipping moved, non-uniform widening), and make sure at least one deterministic test (not only
   the random generator) exercises overlapping occupancy runs where a naive walk without I2′ would
   produce a wrong gap. State the falsifier where a future builder will meet it (the `DaySchedule`
   docstring), not only in §11.
3. [§5 one owner — S2] "Naive, no tzinfo" (R6/V1) is now enforced in two places with two messages:
   `TimeRange._require_wall_clock` (times) and `AsOf.__post_init__` (`now`). Decide whether that is one
   rule with two owners or two facts with one owner each, and make the design say so with its reason
   (no private name may cross a module line).
4. [§3 contract precision — S2] §1.1 R1 reads "within each place a new booking may lie"; define R1 over
   bookable spans precisely (anchor = span start = free-gap start; step = duration; fit = inside the span).
   Check every other place R1 is restated for the same vagueness.
5. [test plan — S2] §9.5 property 3 speaks of "the end of an occupancy component", but the design keeps
   occupancy runs unmerged. The oracle must compute the union itself; say so, and define the anchor set
   precisely so the property is checkable. Check the other oracle properties for the same issue.
6. [§6 re-trace — S1] Add any new-rule × existing-rule crossing still missing from §7.3 that you find by
   re-tracing (in particular: notice × buffer, notice × opening edge, granularity × a span shorter than g,
   A2 duplicates × buffer). Do not pad: add only crossings whose outcome is not obvious from an existing row.

Also re-run the subtractive and concept-fit passes on whatever you change. Keep everything that is not on
this list unless you find a defect; if you do, fix it and list it.

RETURN
Write the complete revised design (self-contained, same structure as merged.md, ready to become the
repository's DESIGN.md) to `.aims/panel/2026-09-23-stage2/revised.md`. Append a final section
"Revise-round changes" listing, per fix-list item, what changed and why (or why nothing changed). Reply with
a short summary (under 250 words).
