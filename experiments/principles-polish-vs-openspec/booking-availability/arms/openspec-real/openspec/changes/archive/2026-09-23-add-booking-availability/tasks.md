# Tasks

## 1. Package scaffold

- [ ] 1.1 Create the `booking_availability` package (`model`, `intervals`, `slotting`, `availability`, `cli`, `__main__`) and a `tests/` directory, stdlib only; verify `python -m unittest discover` runs with zero tests and no import errors

## 2. Model and validation

- [ ] 2.1 Implement `Interval` over day offsets (frozen, `start < end` enforced, half-open `overlaps`/`contains`) and `InvalidQuery`; verify unit tests cover touching-is-not-overlapping and inverted/empty rejection
- [ ] 2.2 Implement `AvailabilityQuery` plus the `of(...)` helper that converts `datetime.time` values to offsets, with field-naming error messages; verify the tests for spec scenarios "Non-positive duration", "Inverted booking" and "Empty working hours" pass and check the error text

## 3. Interval algebra

- [ ] 3.1 Implement `merge` and `free_gaps` (clip busy to the window, merge, complement, ascending); verify unit tests for overlapping, touching, unordered, out-of-window, and fully covering busy sets

## 4. Slot policy and service

- [ ] 4.1 Implement `slotting.back_to_back`; verify unit tests for an exact fit, dropped leftover time, and a gap shorter than the duration
- [ ] 4.2 Implement `availability.find_slots`; verify one test per spec scenario (no bookings, abutting booking, ends at close, too-short gap, duration longer than working hours, off-grid realignment, leftover dropped, unordered bookings, overlapping bookings, booking before hours, idempotence), plus a property-style check that the output is strictly ascending
- [ ] 4.3 Add module docstrings stating the assumptions A1 to A5 where each rule lives; verify each assumption in design.md is referenced by exactly one owning module

## 5. CLI adapter

- [ ] 5.1 Implement `cli` JSON parsing (`HH:MM[:SS]`, `duration_minutes`) and output formatting, mapping `InvalidQuery` and parse errors to stderr with exit code 2; verify subprocess tests for the "CLI success" and "CLI invalid input" scenarios plus a malformed time string
- [ ] 5.2 Add a README section with the CLI usage and one example; verify the documented example command produces the documented output

## 6. Integration check

- [ ] 6.1 Run the full test suite and `openspec validate add-booking-availability --strict`; verify both pass
