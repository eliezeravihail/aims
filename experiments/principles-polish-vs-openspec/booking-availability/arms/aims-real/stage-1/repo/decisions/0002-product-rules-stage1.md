---
title: "0002 — stage-1 product rules (owner delegated the choice)"
date: 2026-09-23
status: accepted
---
## Context
QUESTIONS.md Q1–Q4. The product owner answered Q1, Q2 and most of Q3 with "not specified; choose a simple,
sensible approach and state it"; Q3 fixed "assume valid, non-overlapping bookings; you may sort"; Q4 fixed
"all times are in the resource's local day; ignore cross-zone".

## Decisions
1. **Gap-aligned slots.** Within each free gap, slots start at the gap's start and step by the duration;
   a remainder shorter than the duration is not offered. Rejected: a fixed grid from the start of working
   hours — it hides the earliest free moment after an off-grid booking (09:45 in the worked example) and
   adds a second alignment concept nobody asked for.
2. **Half-open intervals `[start, end)`.** A booking may start when another ends; a slot may end exactly at
   close of working hours. Rejected: closed intervals — they would forbid back-to-back bookings, which the
   request itself calls for.
3. **Input handling.** Reject (clear error): working hours or a booking with `end <= start`; duration `<= 0`;
   two bookings that overlap (the owner said to assume none — a violation is a caller bug, surfaced rather
   than silently merged). Accept: unsorted bookings (sorted internally); bookings partly or wholly outside
   working hours (only the portion inside counts). Empty result (not an error): no gap fits.
4. **Time model.** Naive wall-clock times of one local day; working hours are one window within that day
   and do not cross midnight.

## Rules out
Grid alignment, buffers, breaks, merging of overlapping bookings, time-zone arithmetic.
