# Tasks

## 1. Model: rules and query-time context

- [ ] 1.1 Add `ResourceRules(buffer, min_notice, granularity)` with defaults 0/0/None. Validate that buffer and notice are not negative and that granularity is positive, with messages that name the field. Verify with unit tests for the "Negative buffer" and "Zero granularity" scenarios.
- [ ] 1.2 Add `AsOf(date, now)`. Add `rules` and `as_of` to `AvailabilityQuery`, reject positive notice without `as_of`, and extend `AvailabilityQuery.of(...)` with the new keywords, rejecting "only one of date/now". Verify with the "Minimum notice without now" test, and check that the stage-1 construction tests still pass unchanged.

## 2. Buffer rule (`occupancy`)

- [ ] 2.1 Implement `occupied`, `footprint` and `search_window`, with a module docstring stating assumptions B1 to B3 and the equivalence argument from design.md. Verify with unit tests for buffer 0 (identity), a booking before hours, and a booking after closing.

## 3. Slotting policies

- [ ] 3.1 Refactor `back_to_back` into the `SlotPolicy` protocol with `BackToBack` (step = footprint). Verify that the existing slotting tests pass when footprint equals duration, and add a test with a footprint larger than the duration.
- [ ] 3.2 Implement `Grid(anchor, step)` with a ceiling to the first grid point at or after `gap.start`, plus `policy_for(rules, working_hours)`. Verify with unit tests for a gap starting on the grid, a gap starting off the grid, a gap shorter than the footprint, and anchoring to a working-hours start that is not on the hour.

## 4. Notice rule (`notice`)

- [ ] 4.1 Implement `earliest_start(as_of, min_notice)` returning a day offset or `None`, with a docstring stating assumptions B6 to B8. Verify with unit tests for a same-day cutoff, a previous-day `now` (negative or small offset), a cutoff beyond the day, and `as_of=None`.

## 5. Composition

- [ ] 5.1 Rewire `availability.find_slots` to follow the design's data flow: occupancy, then free_gaps, then policy, then notice filter. Verify with one test per new spec scenario (buffer, notice, granularity, combined, tolerant-after-hours), and check that every stage-1 scenario test still passes unmodified.
- [ ] 5.2 Add a property-style test over random small queries. It checks that the output is strictly ascending, and that each offered start satisfies the spec's fit rule when checked by brute force (booked part in hours, no overlap with booking+buffer, own buffer clear of bookings, on-grid, not before the cutoff). Verify that the test passes for several hundred generated cases.

## 6. CLI

- [ ] 6.1 Parse `buffer_minutes`, `min_notice_minutes`, `granularity_minutes`, `date` and `now`. Map omitted fields to the defaults, and never read the clock. Verify with subprocess tests for "CLI with rules", an existing stage-1 CLI scenario, and a malformed `now`.
- [ ] 6.2 Update the README CLI section with the new fields and the "CLI with rules" example. Verify that the documented command gives the documented output.

## 7. Integration check

- [ ] 7.1 Run the full test suite and `openspec validate add-buffer-notice-granularity --strict`. Verify that both pass.
