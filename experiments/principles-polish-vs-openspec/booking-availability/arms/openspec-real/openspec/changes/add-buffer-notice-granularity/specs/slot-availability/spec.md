# Spec Delta

## MODIFIED Requirements

### Requirement: Availability query inputs and output
The system SHALL accept an availability query made of these inputs:
- the resource's working hours for one day (a start and end time of day)
- zero or more existing bookings for that day (each a start and end time of day)
- a slot duration
- the resource's **rules**: a buffer (a non-negative duration, default 0), a minimum notice (a
  non-negative duration, default 0), and an optional granularity (a positive duration)
- optionally, the calendar **date** of the queried day and the current moment **now** (a date and a time
  of day). These are supplied together.

It SHALL return an ordered list of slot start times (times of day). Working hours, bookings, and results
are wall-clock times of day on the same single day. The date and now SHALL be used only to apply the
minimum-notice rule. They are in the same wall clock as the resource, and the query SHALL NOT consider
time zones or daylight-saving transitions.

#### Scenario: Day with no bookings
- **WHEN** working hours are 09:00-17:00, there are no bookings, the duration is 60 minutes, and the rules are left at their defaults
- **THEN** the result is 09:00, 10:00, 11:00, 12:00, 13:00, 14:00, 15:00, 16:00

#### Scenario: Query is side-effect free
- **WHEN** the same query is made twice
- **THEN** both results are identical and no booking is created, held, or changed

#### Scenario: Default rules reproduce stage-1 results
- **WHEN** a query has buffer 0, no granularity, and no date or now
- **THEN** the result is exactly what the query without rules returned before this change

### Requirement: A slot fits only in free time inside working hours
A start time `s` SHALL be offered only if all of these hold:
- the booked interval `[s, s + duration)` lies inside working hours
- the booked interval overlaps no existing booking and no existing booking's buffer
- the new slot's own buffer `[s + duration, s + duration + buffer)` overlaps no existing booking

The new slot's buffer MAY extend past the end of working hours.

#### Scenario: Gap too short for the duration
- **WHEN** working hours are 09:00-12:00, bookings are 09:00-10:00 and 10:20-12:00, and the duration is 30 minutes
- **THEN** the result is empty

#### Scenario: Duration longer than working hours
- **WHEN** working hours are 09:00-09:30 and the duration is 60 minutes
- **THEN** the result is empty, and this is not an error

#### Scenario: Slot plus buffer does not fit before the next booking
- **WHEN** working hours are 09:00-11:00, there is one booking 10:00-11:00, the buffer is 15 minutes, and the duration is 50 minutes
- **THEN** the result is empty, because 09:00-09:50 plus its buffer runs until 10:05, into the booking

### Requirement: Slots are laid back-to-back from the start of each free gap
This requirement applies only when the resource has **no granularity**. Busy time is every existing
booking together with its buffer. The free time inside working hours SHALL be split into maximal free
gaps: runs of time not covered by busy time. Within each gap starting at `g`, candidate starts SHALL be
`g`, `g + step`, `g + 2*step`, and so on, where `step = duration + buffer`. A candidate SHALL be offered
only if it satisfies the fit rule. Leftover time at the end of a gap SHALL NOT produce a slot. Alignment
restarts at the start of each gap. It is not a fixed grid anchored to working hours or to the clock.

#### Scenario: Alignment restarts after a booking that ends off-grid
- **WHEN** working hours are 09:00-17:00, bookings are 10:00-11:15 and 13:00-14:00, and the duration is 30 minutes
- **THEN** the result is 09:00, 09:30, 11:15, 11:45, 12:15, 14:00, 14:30, 15:00, 15:30, 16:00, 16:30

#### Scenario: Leftover gap time is dropped
- **WHEN** working hours are 09:00-10:45, there are no bookings, and the duration is 30 minutes
- **THEN** the result is 09:00, 09:30, 10:00

#### Scenario: Back-to-back slots leave room for the buffer
- **WHEN** working hours are 09:00-11:00, there is one booking 09:00-10:00, the buffer is 15 minutes, and the duration is 30 minutes
- **THEN** the result is 10:15

### Requirement: Invalid queries are rejected with a clear error
The system SHALL reject a query, and return no slots, when any of these hold:
- the working hours start is not before their end
- a booking's start is not before its end
- the duration is zero or negative
- the buffer is negative
- the minimum notice is negative
- the granularity is supplied and is zero or negative
- only one of date and now is supplied
- the minimum notice is positive and now is not supplied

The error SHALL identify which input is invalid. A syntactically malformed time, date, or duration given
to the command-line interface SHALL be rejected the same way.

#### Scenario: Non-positive duration
- **WHEN** the duration is 0 minutes
- **THEN** the query is rejected with an error naming the duration

#### Scenario: Inverted booking
- **WHEN** a booking has start 11:00 and end 10:00
- **THEN** the query is rejected with an error identifying that booking

#### Scenario: Empty working hours
- **WHEN** working hours are 09:00-09:00
- **THEN** the query is rejected with an error naming the working hours

#### Scenario: Negative buffer
- **WHEN** the buffer is -5 minutes
- **THEN** the query is rejected with an error naming the buffer

#### Scenario: Zero granularity
- **WHEN** the granularity is 0 minutes
- **THEN** the query is rejected with an error naming the granularity

#### Scenario: Minimum notice without now
- **WHEN** the minimum notice is 120 minutes and no date or now is supplied
- **THEN** the query is rejected with an error naming now

### Requirement: Command-line access
The system SHALL provide a command-line entry point. It SHALL read one availability query as JSON with:
- times as `HH:MM` or `HH:MM:SS`
- the duration in whole minutes
- optional whole-minute fields `buffer_minutes`, `min_notice_minutes`, and `granularity_minutes`
- optional `date` (`YYYY-MM-DD`) and `now` (`YYYY-MM-DDTHH:MM[:SS]`)

Omitted rule fields SHALL take their defaults. The CLI SHALL NOT read the system clock. It SHALL write the
resulting start times as a JSON array of `HH:MM` strings (with `:SS` when non-zero) to standard output, and
exit with status 0 on success. On an invalid query it SHALL write the error message to standard error and
exit with a non-zero status.

#### Scenario: CLI success
- **WHEN** the CLI receives `{"working_hours": {"start": "09:00", "end": "10:00"}, "bookings": [], "duration_minutes": 30}`
- **THEN** it prints `["09:00", "09:30"]` and exits 0

#### Scenario: CLI with rules
- **WHEN** the CLI receives `{"working_hours": {"start": "09:00", "end": "11:00"}, "bookings": [], "duration_minutes": 60, "granularity_minutes": 30, "buffer_minutes": 10, "date": "2026-10-01", "now": "2026-10-01T08:00", "min_notice_minutes": 90}`
- **THEN** it prints `["09:30", "10:00"]` and exits 0

#### Scenario: CLI invalid input
- **WHEN** the CLI receives a query whose duration is -5
- **THEN** it prints an error mentioning the duration to standard error and exits non-zero

### Requirement: Tolerant handling of overlapping and out-of-hours bookings
Existing bookings that overlap or touch each other SHALL be accepted and treated as their combined busy
time. Bookings that fall partly or entirely outside working hours SHALL be accepted. Such a booking
affects the result only through:
- the part of it, together with its buffer, that falls inside working hours
- a new slot's buffer that would reach into it

#### Scenario: Overlapping bookings
- **WHEN** working hours are 09:00-12:00, bookings are 09:30-10:30 and 10:00-11:00, and the duration is 30 minutes
- **THEN** the result is 09:00, 11:00, 11:30

#### Scenario: Booking extends before working hours
- **WHEN** working hours are 09:00-11:00, there is one booking 08:00-09:30, and the duration is 30 minutes
- **THEN** the result is 09:30, 10:00, 10:30

#### Scenario: Booking entirely after working hours without buffer
- **WHEN** working hours are 09:00-10:00, there is one booking 10:00-11:00, the buffer is 0, and the duration is 60 minutes
- **THEN** the result is 09:00

## ADDED Requirements

### Requirement: Cleanup buffer after every booking
Every booking SHALL be followed by a cleanup buffer. The buffer's length is the resource's buffer. This
applies both to existing bookings and to a slot being offered. During a buffer the resource SHALL NOT be
free. A buffer SHALL NOT be treated as a booking: it is never returned in the result, has no booker, and
exists only as an effect of its booking. Buffers apply only after a booking, never before. The buffer of
an existing booking that starts before working hours SHALL still block the time inside working hours that
it covers. A booking outside working hours SHALL still block a new slot's buffer. Existing bookings whose
buffers overlap other bookings SHALL be accepted, and their combined busy time is used.

#### Scenario: Existing booking's buffer blocks the time after it
- **WHEN** working hours are 09:00-10:00, there is one booking 09:00-09:30, the buffer is 30 minutes, and the duration is 30 minutes
- **THEN** the result is empty

#### Scenario: Buffer of a booking before working hours
- **WHEN** working hours are 09:00-11:00, there is one booking 08:00-09:00, the buffer is 20 minutes, and the duration is 30 minutes
- **THEN** the result is 09:20, 10:10

#### Scenario: New slot's buffer may run past closing
- **WHEN** working hours are 09:00-10:00, there are no bookings, the buffer is 15 minutes, and the duration is 60 minutes
- **THEN** the result is 09:00

#### Scenario: New slot's buffer may not overlap a booking after closing
- **WHEN** working hours are 09:00-10:00, there is one booking 10:00-11:00, the buffer is 15 minutes, and the duration is 60 minutes
- **THEN** the result is empty

### Requirement: Minimum notice before a slot may start
When now is supplied, a start time `s` on the queried date SHALL be offered only if `date + s` is not
earlier than `now + minimum notice`. A start exactly at that cutoff SHALL be offered. The notice rule SHALL
only remove candidate starts. It SHALL NOT shift or re-anchor the remaining ones. The cutoff MAY fall on
an earlier day (every slot passes) or a later day (no slot passes). When now is not supplied, no
time-based filtering SHALL occur.

#### Scenario: Slots within the notice period are dropped, not shifted
- **WHEN** working hours are 09:00-13:00, there are no bookings, the duration is 60 minutes, the date is 2026-10-01, now is 2026-10-01 08:30, and the minimum notice is 120 minutes
- **THEN** the result is 11:00, 12:00

#### Scenario: Start exactly at the cutoff is offered
- **WHEN** working hours are 09:00-13:00, there are no bookings, the duration is 60 minutes, the date is 2026-10-01, now is 2026-10-01 08:00, and the minimum notice is 120 minutes
- **THEN** the result is 10:00, 11:00, 12:00

#### Scenario: Notice carried over from the previous day
- **WHEN** working hours are 09:00-13:00, there are no bookings, the duration is 60 minutes, the date is 2026-10-02, now is 2026-10-01 22:00, and the minimum notice is 12 hours
- **THEN** the result is 10:00, 11:00, 12:00

#### Scenario: Notice reaches beyond the queried day
- **WHEN** working hours are 09:00-13:00, the duration is 60 minutes, the date is 2026-10-02, now is 2026-10-01 12:00, and the minimum notice is 48 hours
- **THEN** the result is empty

#### Scenario: Zero notice still excludes the past
- **WHEN** working hours are 09:00-13:00, there are no bookings, the duration is 60 minutes, the date is 2026-10-01, now is 2026-10-01 10:30, and the minimum notice is 0
- **THEN** the result is 11:00, 12:00

### Requirement: Start times align to the resource granularity
When the resource has a granularity `g`, the candidate starts SHALL be exactly the points
`working_hours.start + k*g` (for k = 0, 1, 2, ...) inside working hours. Every candidate that satisfies
the fit rule and the minimum-notice rule SHALL be offered. As a result, offered slots MAY overlap each
other. Candidates SHALL NOT be re-anchored to the end of a booking or buffer: the grid is fixed for the
day. In this mode the back-to-back rule does not apply.

#### Scenario: Every grid point that fits is offered
- **WHEN** working hours are 09:00-11:00, there are no bookings, the granularity is 15 minutes, and the duration is 60 minutes
- **THEN** the result is 09:00, 09:15, 09:30, 09:45, 10:00

#### Scenario: Grid anchored at the start of working hours
- **WHEN** working hours are 09:10-10:40, there are no bookings, the granularity is 30 minutes, and the duration is 30 minutes
- **THEN** the result is 09:10, 09:40, 10:10

#### Scenario: Free time starting off-grid waits for the next grid point
- **WHEN** working hours are 09:00-12:00, there is one booking 09:00-10:05, the granularity is 15 minutes, and the duration is 30 minutes
- **THEN** the result is 10:15, 10:30, 10:45, 11:00, 11:15, 11:30

#### Scenario: Granularity with buffer
- **WHEN** working hours are 09:00-11:00, there is one booking 10:00-10:30, the buffer is 10 minutes, the granularity is 15 minutes, and the duration is 30 minutes
- **THEN** the result is 09:00, 09:15

### Requirement: The three rules apply together
Buffer, minimum notice, and granularity SHALL all apply to the same query at once. A start time SHALL be
offered only if it is a candidate of the active slotting rule (grid or back-to-back), satisfies the fit
rule including buffers, and satisfies the minimum-notice rule. The order in which the rules are checked
SHALL NOT affect the result.

#### Scenario: All three rules combined
- **WHEN** working hours are 09:00-12:00, there is one booking 09:30-10:00, the buffer is 15 minutes, the granularity is 15 minutes, the duration is 30 minutes, the date is 2026-10-01, now is 2026-10-01 08:00, and the minimum notice is 150 minutes
- **THEN** the result is 10:30, 10:45, 11:00, 11:15, 11:30
