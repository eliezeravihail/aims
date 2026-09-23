# Proposal

## Why

Three per-resource rules now change what "bookable" means. Stage 1 cannot express them:
- a cleanup **buffer** after every booking
- a **minimum notice** relative to the current time
- a start-time **granularity** grid

A slot that stage 1 offers can now be unbookable because it falls inside a cleanup buffer, is too soon, or
is off-grid. The availability answer is wrong until the rules are part of the calculation.

## What Changes

- Introduce **resource rules** as an explicit input: `buffer` (≥ 0), `min_notice` (≥ 0) and optional
  `granularity` (> 0). Before this change, "resource" was only the carrier of working hours and bookings
  (stage-1 A7). Now it also carries this policy.
- **Buffer.** Each booking, existing or candidate, occupies `[start, end + buffer)`. Buffers are never
  returned, have no booker, and never count as bookings. A candidate is offered only if its buffer overlaps
  no existing booking, and no existing booking's buffer overlaps the candidate. A buffer may run past the
  end of working hours (assumption).
- **Minimum notice.** The query can carry a `now` (datetime) and the query `date`. Start times earlier than
  `now + min_notice` are not offered. The notice rule filters candidates and never moves them. When `now`
  is absent, no time-based filtering happens (stage-1 behavior).
- **Granularity.** When a resource has a granularity `g`, the offered starts are **every** point
  `working_start + k*g` where the slot (plus its buffer) fits. Adjacent offered slots may overlap each
  other. When there is no granularity, stage-1 back-to-back slotting is kept, with the step widened to
  `duration + buffer`.
- New validation rules: negative buffer or notice, non-positive granularity, and positive notice with no
  `now`/`date`.
- CLI: new optional JSON fields `buffer_minutes`, `min_notice_minutes`, `granularity_minutes`, `date` and
  `now`.
- Compatibility: a stage-1 query (no rules, no `now`) gives exactly the stage-1 result. Not breaking.
- Out of scope: time zones and DST (the stage-1 A4 assumption stands, and `now` is naive local wall-clock
  time of the resource), multi-day queries, buffers before bookings, and carry-over from a previous day's
  bookings that are not supplied in the input.

## Capabilities

### New Capabilities
<!-- none -->

### Modified Capabilities
- `slot-availability`: the query gains resource rules and an optional `now`/`date`. The fit rule accounts
  for buffers. The slotting rule becomes grid-or-back-to-back. The notice filter, new validation errors,
  and new CLI fields are added.

## Impact

- The `model` (new `ResourceRules`, query fields, validation), `slotting` (grid policy, policy
  selection), and `availability` (composition) modules change. New small modules own the buffer rule
  (`occupancy`) and the notice rule (`notice`). `intervals` is unchanged. The `cli` gets new optional
  fields.
- There are no new dependencies. The core stays pure: `now` is always an input and is never read from a
  clock.
