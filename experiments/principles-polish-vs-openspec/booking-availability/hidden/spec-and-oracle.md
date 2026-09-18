# Booking availability — hidden spec + oracle (never shown to an arm)

## Architectural axis under test

**Who owns the definition of "free time", and is that definition one place that new constraints refine — or
is "bookable" a computation whose rules get scattered as stage 2 adds them?** Stage 1 makes free =
(inside hours) ∧ (not overlapping a booking). Stage 2 adds three *different kinds* of rule: a resource-time
subtraction (buffer), a wall-clock cutoff (min-notice), and an alignment (granularity).

## The correctness traps (what the judge checks)

1. **Buffer-as-booking cram.** Modeling the buffer by inserting a synthetic booking into the bookings list
   is **wrong**: the buffer would then be reported as a booking, would need a fake booker, and buffer-vs-
   buffer overlap rules differ from booking-vs-booking. The buffer is a distinct concept — a property of a
   booking's footprint on the resource, not a booking. (§4 concept-fit, §1 correctness.)

2. **Scattered "bookable" rule.** The correct shape has **one owner** for "is this candidate start
   bookable?" that composes the constraints (busy intervals incl. buffer, min-notice cutoff, granularity),
   rather than three independent passes that each re-derive the free intervals and can disagree at the
   boundary (e.g. a slot that clears buffer but is filtered again by an inconsistent min-notice check). One
   place computes the occupied footprint; one place enumerates aligned candidates; one predicate admits a
   candidate. (§5 one-owner-per-rule, §6 cohesion.)

3. **Interaction coverage.** buffer + granularity + min-notice interact: a candidate aligned to granularity
   may still be inside a buffer; the last slot before end-of-day must leave room for the *booking*, not the
   buffer beyond close (a buffer may legitimately extend to or past closing). A design that treats them as
   independent filters misses these. (§1 trace-the-input-space.)

## Oracle answers (canonical)

- "Are bookings sorted / non-overlapping on input?" → "Assume valid, non-overlapping bookings; you may sort."
- "Time zone?" → "All times are in the resource's local day; ignore cross-zone for now."
- "Does the buffer after the last booking of the day matter if it runs past closing?" → "The buffer may run
  to or past closing; only the *booking* must fit inside working hours."
- (Stage 2) "Is min-notice measured from slot start or slot end?" → "From slot start."
- (Stage 2) "Does granularity start from the top of working hours?" → "Yes, align from the working-hours
  start."

## Survival oracle (D2)

**Extends** if stage 1 already produced free intervals through a seam (an occupancy/timeline abstraction and
a candidate-enumeration step) that the three rules refine — buffer widens each booking's footprint,
min-notice trims the candidate window, granularity parameterizes enumeration — with the fit predicate in one
owner. **Reopens** if "bookable" was computed inline as one function that now must be torn open to thread
three parameters, or if the buffer is added as a booking.
