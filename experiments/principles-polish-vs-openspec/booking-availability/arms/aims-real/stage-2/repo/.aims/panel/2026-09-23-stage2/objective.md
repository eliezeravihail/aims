ROLE
You are the design Worker — a senior engineer as capable as the Guide. The design is the deliverable.
This is a DESIGN objective that CHANGES AN EXISTING ARCHITECTURE: produce the revised architecture only.
Do NOT write implementation code (type signatures, interface sketches and a few illustrative lines where
they make a boundary concrete are welcome; a working program is out of scope). Do not redefine project
priorities. If evidence invalidates the objective, report it instead of expanding scope.

DESIGN GOAL (the objective — a quality outcome, not a feature)
Adapt the stage-1 availability architecture (`DESIGN.md` in this repository — read all of it first; it is
the design in force, with decisions/0001–0003) so that three new per-resource rules — cleanup buffer,
minimum notice, start-time granularity — are each absorbed at exactly ONE owner, every stage-1 rule keeps
its single owner through the change, and stage-1 behaviour is preserved exactly where the new rules do not
apply — still pinned to a concrete Python 3.11 stdlib module skeleton and signatures a builder could start
from without inventing anything.

The hard decisions at its core (yours to resolve and justify — no answer is implied here):
H1 Buffer. Where does "a buffer is busy time but not a booking" live, given (a) existing bookings'
   buffered occupancy may now overlap each other (decision 0004 §5 accepts such input), which breaks a
   stage-1 invariant of the occupancy owner, and (b) the fit test for a NEW slot is asymmetric: the slot
   must lie inside working hours, but the slot PLUS its buffer must avoid existing occupancy, and the
   buffer may run past closing. A trailing filter over candidate starts, or a buffer modelled as a
   synthetic booking, are the two tempting shortcuts; both are a second owner / a concept cram.
H2 Slot policy. Stage 1 rejected a slot-policy seam because one policy existed. There are now two real
   policies (grid-aligned when the resource has a granularity; stage-1 gap-aligned stepping when it does
   not). Decide how they relate, and make sure the fit rule (H1) is not re-implemented inside each.
H3 Time model. Minimum notice brings a calendar date and an instant ("now") into a design whose core
   works on times of one day. Decide where the date/instant is converted, once, and what the core sees.
H4 Public seam. The entry gains per-resource settings and an optional query context (day, now). Decide
   the shape of that seam (no long primitive parameter list; no internal type leaking), how stage-1
   callers are affected, and where each new validation rule has its one owner.

BEHAVIOR IT MUST SATISFY (constraints — decided product rules, not up for re-decision)
Stage-1 rules R1–R6 and assumptions A1–A9 are in DESIGN.md §1. Stage-2 rules are decisions/0004 — read it;
summary:
- B1 Buffer after every booking: existing booking [s,e) occupies [s, e+buffer). Buffer counts wherever it
  lies inside working hours, including a buffer from a booking that ended before opening. Never returned.
- B2 A new slot [t, t+d) must lie inside working hours; [t, t+d+buffer) must not overlap existing
  occupancy inside working hours. Its buffer may run to/past closing. Occupancy outside hours is ignored
  (R3 unchanged).
- B3 Existing bookings whose buffers hit a neighbour are ACCEPTED. True booking overlaps still rejected on
  raw bookings, pair named (R4/A1 unchanged).
- G1 Granularity is optional. With granularity g: candidates are hours.start + k·g; EVERY candidate that
  fits (B2) is offered. Without granularity: stage-1 R1 unchanged (back-to-back by duration from each
  free gap's start; the buffer only changes where gaps end and which starts fit).
- N1 Notice (timedelta >= 0, any length). Caller supplies `day` (date) and naive `now` (datetime).
  Start t offered iff combine(day, t) >= now + notice (exactly at cutoff is offered). Notice removes
  starts; never moves the grid or gap anchors. Cutoff on a later day → []; on an earlier day → no effect.
- N2 `now` optional; without it no notice filter. Notice > 0 without `now` → caller error. With `now` and
  notice 0, starts before now are dropped.
- V1 Errors: negative buffer; negative notice; granularity <= 0; tz-aware now; notice > 0 without now.
  Buffer 0, notice 0, no granularity, no now → exactly stage 1.
- M1 A buffer running past midnight is cut at end of day; never overflows (hours still end before
  midnight, A3).

Acceptance / break cases — trace EACH through your design (hours 09:00–17:00, d = 30 min unless stated):
- S1 Anchor with grid: bookings 09:00–09:45, 11:00–12:00; buffer 15; granularity 15 →
  10:00, 10:15, 12:15, 12:30, …, 16:30 (18 starts after 12:00).
- S2 Same without granularity (buffer 15) → 10:00, 12:15, 12:45, …, 16:15.
- S3 Characterization: buffer 0, notice 0, no granularity, no now → stage-1 C1–C14 results bit-for-bit
  (DESIGN.md §7). Stage-1's tests must pass unchanged in meaning.
- S4 Closing edge: no bookings, buffer 15, granularity 15 → last start 16:30 (buffer to 17:15 is fine).
- S5 Opening edge: booking 08:00–09:00, buffer 15 → first start 09:15 (grid 15) / 09:15 (no grid);
  booking 08:00–08:50, buffer 15 → busy 09:00–09:05: first start 09:15 (grid 15) / 09:05 (no grid);
  booking 07:00–08:00, buffer 15 → no effect.
- S6 Buffer-violating input: 10:00–11:00 and 11:00–12:00, buffer 15 → accepted; nothing offered in
  [10:00, 12:15); no negative/duplicate gap, no cursor moving backwards. Also buffer 60 with bookings
  10:00–10:30 and 10:45–11:00 (occupancies 10:00–11:30 and 10:45–12:00 overlap).
- S7 True overlap with buffer > 0 → still OverlappingBookingsError naming the raw pair; touching bookings
  with buffer > 0 accepted (S6).
- S8 New slot's own buffer: free gap ending at a booking at 11:00, occupancy before it ending 10:00;
  d = 45, buffer 15 → 10:00 offered (buffer touches 11:00); d = 60, buffer 15 → 10:00 NOT offered even
  though the slot itself fits.
- S9 Booking 17:00–18:00 (after hours), buffer 15, no bookings in hours → 16:30 still offered.
- S10 Grid: g = 20, d = 30 → 09:00, 09:20, …; g = 10 h (> hours) → only 09:00; C1 bookings with buffer 0,
  g = 15 → 09:45 offered (on grid), 10:15 offered, 10:30 offered (every grid point that fits);
  hours 09:10–17:00 with g = 15 → grid is 09:10, 09:25, … (origin = hours start, not clock hour).
- S11 Notice: now = day 08:00, notice 2 h → 10:00 offered, 09:45 not; notice 90 min → cutoff 09:30.
  Gap-aligned without grid, C1 bookings, now = day 09:50, notice 0 → first start 10:15 (not 09:50).
- S12 Across days: now = previous day 20:00, notice 48 h → []; now = previous day 16:00, notice 16 h →
  cutoff 08:00 on the day → no effect; now on the next day → []; now = day 16:40, notice 0 → [].
- S13 Errors: notice > 0 without now; aware now; negative buffer; negative notice; granularity 0 and
  negative → each a clear error; a deterministic precedence among all request-level checks (state it).
- S14 now supplied, notice 0 → starts before now dropped, start exactly at now kept.
- S15 Overflow/totality: duration timedelta.max; buffer timedelta.max; notice timedelta.max (now + notice
  overflows datetime!); booking ending 23:50 with buffer 30 → no stdlib OverflowError anywhere, no hang.
- S16 Order independence (C10) still holds with buffers, including the buffer-violating input of S6.

WHY NOW
A product change has arrived (stage 2). The stage-1 design is agreed but not built; absorbing the change
in the design, before code, is cheaper than after. Nothing is implemented — "existing code" is the design
in DESIGN.md, and it is the ground truth to change, not to replace.

WHAT "GOOD" AIMS AT
The standard is `.claude/skills/aims-guide/references/design-principles.md`, and — because this changes an
existing design — `.claude/skills/aims-guide/references/add-feature-principles.md` (characterize before
touching; make the change easy then make the easy change; one owner survives; re-trace every new rule
crossed with every existing rule; absorb, don't accrete; concept-fit on what the change adds; match the
existing grain). Read both. Not checklists — the target. Where a principle does not apply, say why.

TESTING (for the design)
State the test plan the builder will follow test-first: which existing stage-1 tests are kept unchanged as
characterization, which change and why, which new decisions get a test, at which seam, which S-case each
covers, and how the seeded-random invariant test is extended. Every non-trivial decision gets a test; no
coverage percentages.

RELEVANT CONTEXT / PRESERVE / NON-GOALS
- Substrate (fixed, decisions/0001): Python 3.11+, standard library only; single process; no UI, network,
  DB or persistence. `datetime` may cross seams.
- Preserve: every stage-1 rule and its owner unless you argue (and record) a supersession; stage-1
  outputs for the default settings (S3); the published-surface discipline (DESIGN.md §3.2/§3.5).
- Non-goals: creating/storing bookings; multiple resources per call; breaks; recurrence; time zones/DST;
  multi-day queries; per-booking buffers; buffers before bookings; any output cap. Do not build for these.
- Records: goals.md, architecture.md, decisions/0001–0004 at the repo root.
- The modules, classes and interfaces are YOURS to choose.

BEFORE RETURNING
Run the subtractive pass on what you ADDED or CHANGED (name the present force for every new type, guard,
parameter or seam; remove what fails). Run the concept-fit pass on each new concept (buffer, occupancy,
grid, notice cutoff, the query context, the resource's settings): is each the kind of thing it is?

RETURN TO GUIDE (write it to the file path given in your axis block, and also return a SHORT summary as
your reply — the file is what the Guide reads)
- The revised design, self-contained for what changed: file tree (marking new/changed/unchanged modules),
  each changed module's responsibility and public surface, concrete Python signatures, the rule → owner
  table for R1–R6 AND B1–B3, G1, N1–N2, V1, M1, the error vocabulary delta, and a trace of S1–S16.
- Design reasoning: how H1–H4 were resolved and why; each new abstraction and its present force;
  alternatives rejected.
- Test plan (delta against DESIGN.md §10).
- Result: met | partially_met | invalidated | blocked.
- New facts or risks discovered (especially any product question still open).
