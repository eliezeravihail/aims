REVISE ROUND — O1 (the mandatory one review-and-revise round for a design objective)

Your inputs, in this directory: `objective.md` (the objective, rules R1–R6, cases C1–C14 — unchanged),
`merged.md` (the composed design from three independent axis passes, with the reasoning for each split),
and the three raw drafts `worker-*.md` (read them for detail the merge compressed: traces, proofs, test
tables). The design is yours to revise; the composition's decided splits stand unless your revision shows
one is wrong — then say so with evidence.

Guide's measurement of merged.md — the fix-list, most severe first (directions, not dictated solutions):

1. [§1 contracts / buildability — S3] The merge is a sketch. `DaySchedule.build`, `free_gaps`,
   `tile_starts`, `clip`, `available_starts` lack stated pre/postconditions; the sort key, the ORDER of the
   R4 check vs the R3 clip (the stated assumption is: overlap checked on the raw bookings, before
   clipping), the adjacent-pair sufficiency argument, and "earliest first by construction" are not stated.
   A builder would have to reinvent them. Direction: state each contract concretely.
2. [§5 one-construction-path — S2] `DaySchedule` is a frozen dataclass with a public field constructor
   plus a `build` classmethod: `DaySchedule(hours, busy)` forges an unvalidated schedule, so the "type is
   evidence R4/R3 held" claim is not true by construction. Direction: exactly one construction path.
3. [§8 feature envy vs §5 expose-the-least — S2] `clip` and `tile_starts` are free functions that only
   read a `TimeRange`'s fields, yet are imported across modules while unexported. Either they belong on
   the type (and the surface question must be answered honestly — which of them does a *caller* need?) or
   they are a module-private helper set with a stated reason. Decide and justify; one owner of time
   arithmetic must remain.
4. [§1 edge / stated assumptions — S2] The merge dropped the assumptions all three drafts surfaced:
   overlapping bookings wholly outside hours are rejected; duplicates are rejected; working hours cannot
   end at 24:00 (no `time(24)`); tz-aware times rejected; no output cap / minimum granularity for tiny
   durations; validation precedence; non-`TimeRange` arguments not type-guarded. Each must appear as an
   explicit, stated assumption with where a change to it would land.
5. [§12 / §1 trace — S2] No C1–C14 trace and no test plan in the merge. Restore both, including the
   seeded-random invariant test and the `__all__` surface test.
6. [§3 — S1] Entry-point decision (library function, no CLI) and its reason are missing from the merge.
7. [§3 — S1] An invalid-range error cannot say whether it was the working hours or a booking; either
   accept with a stated reason or fix without a second owner of the range rule.

Run the subtractive and concept-fit passes again on the revision.

DELIVERABLE: write the complete, self-contained revised architecture to
`.aims/panel/2026-09-23-availability/revised.md` (it will become DESIGN.md; a reader must not need any other
file). Structure: assumptions & product rules; module tree and dependency direction; each module's
responsibility and concrete Python 3.11 signatures with contracts; rule→owner table; error vocabulary;
public entry point; trace C1–C14 (+ beyond-list cases); design reasoning and rejected alternatives;
where stage-2 non-goals would land (named only); test plan. Design only — signatures and a few
illustrative lines, no implementation. Then reply with a short summary of what changed per fix-list item
and your result (met | partially_met | invalidated | blocked).
