# Booking availability — stage 2

Three new rules now shape what "bookable" means. They apply together.

1. **Buffer.** Each resource needs a cleanup **buffer** of N minutes *after* every booking (N is per
   resource). During the buffer the resource is not free, but the buffer is **not itself a booking** — it is
   never returned as a booking, has no booker, and two bookings may not be scheduled such that their buffers
   overlap a neighbour's booking.

2. **Minimum notice.** A resource has a **minimum-notice** rule: a slot may not start within X hours of the
   current time (X is per resource). Given "now", slots earlier than now + X are not offered.

3. **Granularity.** The offered start times must align to a per-resource **granularity** (e.g. every 15
   minutes from the top of the working hours), not merely back-to-back.

Stage-1 behavior (working hours, existing bookings, duration fit) is unchanged where these rules don't apply.

Update the architecture to absorb these rules. Design only.
