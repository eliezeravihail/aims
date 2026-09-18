# Booking availability — stage 1

Design a service that returns the **bookable time slots** for a resource on a given day.

Input: a `resource` with **working hours** for the day (e.g. 09:00–17:00), a list of **existing bookings**
for that day (each a start/end interval), and a requested **slot duration** (e.g. 30 minutes).

Output: the list of start times at which a new booking of the requested duration would fit — i.e. a
contiguous free interval of at least the duration, inside working hours, not overlapping any existing
booking. Slots are offered aligned to the top of the interval (back-to-back), earliest first.

Deliver the architecture. Design only — no implementation.
