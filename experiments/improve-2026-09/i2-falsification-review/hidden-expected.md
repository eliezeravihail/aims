# HIDDEN — the seeded defects and the pre-registered scoring (arms never see this)

The first-draft design is a **fixed-window** limiter described as if it enforces "N per 60 seconds." It does
not. The scoring asks whether each review **surfaces a reproducible failing case** for each seeded corner.

## S1 — PRIMARY seed: fixed-window boundary burst (the pre-registered metric)
`allow` buckets by the integer minute `floor(now/60)` and resets the count at each minute boundary. So a
client can send N requests at the end of one minute and N more at the start of the next — **2N requests in a
sub-second real interval** — while never exceeding N *per calendar minute*. This violates R1 ("N per
60-second window") for a sliding 60s window.

- **Failing input:** N=3, requests at t = 59.8, 59.8, 59.8 (minute 0) then t = 60.1, 60.1, 60.1 (minute 1).
  Design returns True six times → 6 allowed within 0.3 s. Requirement: at most 3 in any 60 s window.
- **Score S1 = surfaced** iff the review states this input (or an equivalent boundary-straddling burst) and
  its wrong output — not merely "consider using a sliding window" as a style note. A concrete failing case
  is required.

## S2 — secondary seed: clock non-monotonicity
`now` is passed in; if a later call has a smaller `now` (clock adjustment, NTP step, out-of-order), a stale
`minute` resets or mis-buckets the counter. No contract forbids it. (Credit if surfaced with a case.)

## S3 — secondary seed: unbounded `counters` map
Every distinct client ever seen keeps a `Counter` forever; no eviction. A memory-growth defect under many
clients. (Credit if surfaced.)

## Pre-registered outcome (from plan.md, I2)
**I2 wins iff the falsification (attack) arm surfaces S1 with a concrete failing case where the base-review
arm does not.** Both surfacing S1, or both missing it, is a **null** → not adopted. Secondary count (S2/S3)
is reported but is not the deciding metric. n=1 here is suggestive; a second seeded product is needed before
adopting into the skill.
