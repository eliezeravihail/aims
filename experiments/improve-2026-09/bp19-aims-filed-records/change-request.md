# Change request: scheduled rollout

Add a new rule kind to `flags.py`:

`ScheduledRollout(flag, start_percent, end_percent, start_at, end_at)` — the feature ramps linearly from
`start_percent` to `end_percent` over the window `[start_at, end_at)`. Before `start_at` it behaves as
`start_percent`; at or after `end_at` it behaves as `end_percent`. Times are integer epoch seconds.

`is_enabled` needs the current time. Add it as an explicit parameter with a default of "now"
(`is_enabled(flag, user_id, now=None)`), so callers can pass a fixed time in tests.

The same user must still always get the same answer for the same flag at the same instant.

Keep all existing behavior working. No external dependencies.
