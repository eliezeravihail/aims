# Stage 2 — questions for the product owner

Stage 2 adds buffer, minimum notice and granularity. Most of what these rules mean is already clear from the
brief, and I have treated that as settled (listed at the end). The four questions below are still open. For
each one, two reasonable answers produce **different slot lists**, so I have not guessed. Each question has a
proposed default. If you reply "default", that answer will be used and written down as a decision.

Reference setup used in the examples: working hours 09:00–17:00, duration 30 min, buffer 15 min,
granularity 15 min.

---

## Q1. Buffer at the edges of working hours

A booking's buffer can run past the end of working hours, and a booking that ends before opening can have a
buffer that runs into the hours. Does the buffer count in those cases?

- **(a) Closing edge.** Can a new booking end at 17:00 when its 15-min buffer would run to 17:15? This
  decides whether **16:30** is offered.
- **(b) Opening edge.** An existing booking runs 08:00–09:00. Is the resource free at 09:00, or only from
  09:15? This decides whether **09:00** is offered.

*Proposed default:* (a) yes, a booking may end at close. Cleanup after hours doesn't block anything, so 16:30
is offered. (b) yes, the buffer runs into the hours, because the resource really is being cleaned then.
09:00 is not offered and 09:15 is.

## Q2. Existing bookings that already break the buffer rule

The input contains bookings 10:00–11:00 and 11:00–12:00 with a 15-min buffer. The first booking's buffer
overlaps the second booking. Stage 1 rejects overlapping bookings as a caller error. What happens here?

- **(a)** Reject the input, the same way as an overlap (an error that names the pair).
- **(b)** Accept it. The buffer rule applies only to the new slot being offered. Existing bookings are
  historical fact, for example bookings made before the buffer was configured.

*Proposed default:* **(b)** accept. True overlaps are still rejected.

## Q3. What granularity replaces

Stage 1 lays slots back-to-back from the start of each free gap. Stage 2 says starts must align to a grid,
for example every 15 min from the start of working hours.

- **(a) Which grid points are offered?** Every grid point where a slot fits: 12:00, 12:15, 12:30, …
  Or only grid points that step by the duration, back-to-back: 12:00, 12:30, 13:00, …
- **(b) Is granularity required for every resource?** Or can a resource have none, and if so, does it keep
  the stage-1 back-to-back behaviour (09:45, 10:15, … in the stage-1 worked example)?
- **(c) Is the grid always counted from the start of working hours?** Or can it be counted from somewhere
  else, such as the top of the clock hour?

*Proposed default:* (a) **every** grid point where the slot, and its buffer as defined in Q1, fits. (b)
granularity is optional. With none, the stage-1 back-to-back behaviour is kept unchanged. (c) the grid is
counted from the start of working hours.

## Q4. How "now" and the day are given (minimum notice)

Stage 1 works with times of day only and never knows which date it is. Minimum notice compares slots against
"now". Now can be on an earlier day (a 48-hour notice), and now + X can cross midnight. So the question has
to say which date it is about.

- Is it acceptable for the caller to pass the calendar **date** being queried and **now** as a local date
  and time? Both would be in the resource's local time, with no time zones, as in stage 1.
- Is the notice always a whole number of hours, or can it be a fraction (e.g. 90 minutes)?

*Proposed default:* yes, the caller passes `date` and a naive local `now`. The notice can be any
non-negative length of time, not just whole hours. When "now" is supplied, the rule applies. When it is
not, no notice filter is applied.

---

### Treated as settled from the brief (tell me if any of these is wrong)

- A new slot also needs its own buffer. The slot plus its buffer must not overlap the next booking ("buffers
  may not overlap a neighbour's booking").
- A buffer is never returned, has no booker, and is not a booking.
- A slot starting **exactly** at now + X is offered. Only starts earlier than that are dropped.
- Minimum notice removes starts but does not move the grid. The next offered start is the first grid point
  at or after now + X.
- Buffer 0 and notice 0 behave exactly like stage 1.
- Buffer, notice and granularity are set per resource. One call is still made for one resource on one day.
