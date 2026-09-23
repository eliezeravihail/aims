ROLE
You are the design Worker — a senior engineer as capable as the Guide. The design is the deliverable.
This is a DESIGN objective: produce the architecture only. Do NOT write implementation code (type
signatures, interface sketches, and a few illustrative lines where they make a boundary concrete are
welcome; a working program is out of scope). Do not redefine project priorities. If evidence invalidates
the objective, report it instead of expanding scope.

DESIGN GOAL (the objective — a quality outcome, not a feature)
A buildable stage-1 architecture for a "bookable slots" service in which every product rule below has
exactly one owner, input is validated once at the public boundary (the core trusts it), and the slot
computation is a pure core over well-chosen value types — pinned down to a concrete Python 3.11
(standard library only) module skeleton with concrete public signatures, so a capable engineer could start
building from it without inventing anything.

The hard decision at its core: the domain has several distinct concepts that are easy to cram into one
another — the working window, a booking, the free time between bookings, a candidate slot, the requested
duration, and the policy that turns free time into slot starts. Decide what each one IS, which one owns
each rule (the half-open overlap rule; clipping to working hours; gap-aligned stepping; validity), and
where the public boundary sits — and justify each placement.

BEHAVIOR IT MUST SATISFY (constraints — decided product rules, not up for re-decision)
Input: a resource's working hours for one day (one window, e.g. 09:00–17:00), that day's existing bookings
(each a start/end interval), and a requested slot duration (e.g. 30 min).
Output: the start times at which a new booking of that duration fits entirely inside working hours without
overlapping any existing booking, earliest first.
- R1 Gap-aligned stepping: within each maximal free gap, slots start at the gap's start and step by the
  duration (back-to-back); a leftover shorter than the duration is not offered. (NOT a fixed day grid.)
- R2 Half-open intervals [start, end): a slot may start exactly when a booking ends, and may end exactly at
  close of working hours; touching is not overlapping.
- R3 Only the portion of a booking inside working hours matters; a booking wholly outside is irrelevant.
- R4 Bookings may arrive unsorted; the service sorts. Bookings that overlap each other are rejected with a
  clear error (the owner said to assume none; a violation is a caller bug). Touching bookings are fine.
- R5 Reject with a clear error: working hours or any booking with end <= start; duration <= 0.
  Not an error: no gap fits → empty list.
- R6 Time model: naive wall-clock times within the resource's single local day; no time zones, no DST;
  working hours do not cross midnight.

Acceptance / edge cases the design must be shown to handle (trace each through your design):
- C1 Worked example: hours 09:00–17:00, bookings 09:00–09:45 and 11:00–12:00, 30 min →
  09:45, 10:15, 12:00, 12:30, 13:00, …, 16:30.
- C2 No bookings → every back-to-back slot from opening (09:00 … 16:30 for 30 min).
- C3 Bookings cover the whole day → [].
- C4 Duration longer than every gap (or longer than working hours) → [].
- C5 Gap exactly equal to the duration → exactly one slot; gap of 2.5× duration → two slots.
- C6 Booking ends exactly at opening / starts exactly at close → no effect (R2, R3).
- C7 Booking straddling opening or close → clipped.
- C8 Two touching bookings (10:00–10:30, 10:30–11:00) → accepted, no slot between them.
- C9 Overlapping bookings → rejected, error names the offending pair.
- C10 Same bookings in any order → identical output.
- C11 end <= start on a booking or on working hours → rejected; zero-length booking is end <= start.
- C12 duration zero or negative → rejected.
- C13 Duration not dividing the gap (e.g. 45 min in a 2 h gap) → 2 slots, 30 min remainder unused.
- C14 Last slot ends exactly at close (16:30–17:00) → offered.

WHY NOW
New product, nothing built. The substrate is fixed; the product rules are decided. The shape is the
highest-leverage uncertainty before any code is written.

WHAT "GOOD" AIMS AT
The standard is `.claude/skills/aims-guide/references/design-principles.md` in this repository — read it;
it is the target the design should reach, not a checklist. Where a principle does not apply at this scale,
do not force it; say why. The graver risk is too little structure (primitive obsession, unowned rules,
anemic bags); over-engineering is the lighter fault — but every type/seam must answer to a present force.

TESTING (for the design)
State the test plan the builder will follow test-first: which decisions get a test, at which seam, and which
case (C1–C14) each covers. Every non-trivial decision gets a test; no coverage percentages.

RELEVANT CONTEXT / PRESERVE / NON-GOALS
- Substrate (fixed): Python 3.11+, standard library only; single process; no UI, network, DB or
  persistence. `datetime` is available and may cross seams. The entry point may be a library with a small
  CLI or a local function API — your call, justified.
- Non-goals (stage 1): creating/cancelling/storing bookings; multiple resources; recurrence; breaks inside
  working hours; buffers; fixed-grid alignment; time zones; multi-day. Do not build for these. You MAY name
  which of them your seams would absorb and where, but add no machinery that only a future stage pays for.
- Records already filed at repo root: goals.md, base-dependencies.md, decisions/0001, decisions/0002.
- The modules, classes and interfaces are YOURS to choose.

BEFORE RETURNING
Run the subtractive pass on your own design: for every type, guard, wrapper or abstraction you introduced,
name the present product force that requires it; remove what fails. Run the concept-fit pass: is each
element the kind of thing it is (e.g. is free time modelled as its own concept, or as a fake booking?).

RETURN TO GUIDE (write it to the file path given in your axis block, and also return it as your reply)
- The design: module skeleton (file tree), each module's responsibility and public surface, concrete
  Python signatures for the public types/functions, which rule each owner enforces, the error vocabulary,
  the public entry point, and a trace of C1–C14 through it.
- Design reasoning: where each rule lives and why; each abstraction and what present force it answers;
  which alternatives you rejected and why.
- Test plan.
- Result: met | partially_met | invalidated | blocked, against the design goal.
- New facts or risks discovered (especially any product question you think is still open).
