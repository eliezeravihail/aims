# slot-availability Specification

## Purpose

Tells a caller where a new booking of a given length can go for one resource on one day. It takes the
resource's working hours, that day's existing bookings, and the slot duration, and returns the bookable
slot start times.

## Requirements

### Requirement: Availability query inputs and output
The system SHALL accept an availability query made of: the resource's working hours for one day (a start
and end time of day), zero or more existing bookings for that day (each a start and end time of day), and a
slot duration. It SHALL return an ordered list of slot start times (times of day). All times are wall-clock
times of day on the same single day. The query SHALL NOT consider time zones, dates, or other days.

#### Scenario: Day with no bookings
- **WHEN** working hours are 09:00-17:00, there are no bookings, and the duration is 60 minutes
- **THEN** the result is 09:00, 10:00, 11:00, 12:00, 13:00, 14:00, 15:00, 16:00

#### Scenario: Query is side-effect free
- **WHEN** the same query is made twice
- **THEN** both results are identical and no booking is created, held, or changed

### Requirement: Intervals are half-open
Every interval (working hours, bookings, and offered slots) SHALL be treated as half-open `[start, end)`.
A slot that ends exactly when a booking starts, or starts exactly when a booking ends, SHALL NOT be
considered overlapping. A slot ending exactly at the end of working hours SHALL be considered inside
working hours.

#### Scenario: Slot abuts a following booking
- **WHEN** working hours are 09:00-11:00, there is one booking 10:00-11:00, and the duration is 60 minutes
- **THEN** the result is 09:00

#### Scenario: Slot ends at close of working hours
- **WHEN** working hours are 09:00-10:00, there are no bookings, and the duration is 60 minutes
- **THEN** the result is 09:00

### Requirement: A slot fits only in free time inside working hours
A start time `s` SHALL be offered only if the whole interval `[s, s + duration)` lies inside working hours
and overlaps no existing booking.

#### Scenario: Gap too short for the duration
- **WHEN** working hours are 09:00-12:00, bookings are 09:00-10:00 and 10:20-12:00, and the duration is 30 minutes
- **THEN** the result is empty

#### Scenario: Duration longer than working hours
- **WHEN** working hours are 09:00-09:30 and the duration is 60 minutes
- **THEN** the result is empty, and this is not an error

### Requirement: Slots are laid back-to-back from the start of each free gap
The free time inside working hours SHALL be split into maximal free gaps: runs of time not covered by any
booking. Within each gap starting at `g`, candidate starts SHALL be `g`, `g + duration`,
`g + 2*duration`, and so on. A candidate SHALL be offered only while `candidate + duration` is not after
the end of the gap. The leftover time at the end of a gap that is shorter than the duration SHALL NOT
produce a slot. Alignment restarts at the start of each gap. It is not a fixed grid anchored to working
hours or to the clock.

#### Scenario: Alignment restarts after a booking that ends off-grid
- **WHEN** working hours are 09:00-17:00, bookings are 10:00-11:15 and 13:00-14:00, and the duration is 30 minutes
- **THEN** the result is 09:00, 09:30, 11:15, 11:45, 12:15, 14:00, 14:30, 15:00, 15:30, 16:00, 16:30

#### Scenario: Leftover gap time is dropped
- **WHEN** working hours are 09:00-10:45, there are no bookings, and the duration is 30 minutes
- **THEN** the result is 09:00, 09:30, 10:00

### Requirement: Results are ordered earliest first without duplicates
The result SHALL be sorted in ascending time order and SHALL contain each start time at most once.
This holds whatever order the bookings are supplied in.

#### Scenario: Bookings supplied out of order
- **WHEN** working hours are 09:00-12:00, bookings are given as 11:00-12:00 then 09:00-10:00, and the duration is 60 minutes
- **THEN** the result is 10:00

### Requirement: Tolerant handling of overlapping and out-of-hours bookings
Existing bookings that overlap or touch each other SHALL be accepted and treated as their combined busy
time. Bookings that fall partly or entirely outside working hours SHALL be accepted. Only the part inside
working hours affects the result.

#### Scenario: Overlapping bookings
- **WHEN** working hours are 09:00-12:00, bookings are 09:30-10:30 and 10:00-11:00, and the duration is 30 minutes
- **THEN** the result is 09:00, 11:00, 11:30

#### Scenario: Booking extends before working hours
- **WHEN** working hours are 09:00-11:00, there is one booking 08:00-09:30, and the duration is 30 minutes
- **THEN** the result is 09:30, 10:00, 10:30

### Requirement: Invalid queries are rejected with a clear error
The system SHALL reject a query, and return no slots, when any of these hold: the working hours start is
not before their end; a booking's start is not before its end; the duration is zero or negative. The error
SHALL identify which input is invalid. A syntactically malformed time or duration given to the command-line
interface SHALL be rejected the same way.

#### Scenario: Non-positive duration
- **WHEN** the duration is 0 minutes
- **THEN** the query is rejected with an error naming the duration

#### Scenario: Inverted booking
- **WHEN** a booking has start 11:00 and end 10:00
- **THEN** the query is rejected with an error identifying that booking

#### Scenario: Empty working hours
- **WHEN** working hours are 09:00-09:00
- **THEN** the query is rejected with an error naming the working hours

### Requirement: Command-line access
The system SHALL provide a command-line entry point. It SHALL read one availability query as JSON (times as
`HH:MM` or `HH:MM:SS`, duration in whole minutes) and write the resulting start times as a JSON array of
`HH:MM` strings (with `:SS` when non-zero) to standard output. It SHALL exit with status 0 on success.
On an invalid query it SHALL write the error message to standard error and exit with a non-zero status.

#### Scenario: CLI success
- **WHEN** the CLI receives `{"working_hours": {"start": "09:00", "end": "10:00"}, "bookings": [], "duration_minutes": 30}`
- **THEN** it prints `["09:00", "09:30"]` and exits 0

#### Scenario: CLI invalid input
- **WHEN** the CLI receives a query whose duration is -5
- **THEN** it prints an error mentioning the duration to standard error and exits non-zero
