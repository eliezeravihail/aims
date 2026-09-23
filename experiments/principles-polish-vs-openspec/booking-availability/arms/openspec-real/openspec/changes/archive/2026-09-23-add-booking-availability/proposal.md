# Proposal

## Why

Callers need to know when a resource can take a new booking of a given length on a given day. Today nothing
answers that question. Stage 1 sets up the core availability calculation: working hours minus existing
bookings, cut into slots of the requested duration.

## What Changes

- Add a pure, in-process **availability query**. Inputs: one resource's working hours for one day, that
  day's existing bookings, and a slot duration. Output: the ordered list of start times where a booking of
  that duration fits.
- Define the **domain value types** (time interval, working hours, booking, slot request) and their input
  validation rules.
- Define the **slot-offering policy**. Slots are laid back-to-back from the start of each free gap, earliest
  first. A slot is offered only if it fits completely inside that gap.
- Expose it as a local function API with a thin CLI adapter (JSON in, JSON out) for manual use.
- Out of scope: persistence, creating or holding bookings, multi-day or multi-resource queries, time zones
  and DST handling beyond what the input carries, buffers between bookings, and a fixed global alignment
  grid.

## Capabilities

### New Capabilities
- `slot-availability`: computing bookable slot start times for one resource on one day, from working hours,
  existing bookings, and a requested duration, including input validation and the slot-offering policy.

### Modified Capabilities
<!-- none: no existing specs -->

## Impact

- New greenfield Python 3.11+ package, standard library only (per `substrate.md`). No runtime
  dependencies, persistence, or network.
- New public API: one query function plus value types; one CLI entry point.
