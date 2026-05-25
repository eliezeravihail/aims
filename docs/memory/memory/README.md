# memory/

The ADR-0007 memory subsystem. A two-phase design: a cheap marker
hook flips leaves to `dirty: true` on every edit (Phase A); a
throttled Stop hook lets Sonnet update the dirty leaves only when
the throttle trips (Phase B). SessionEnd runs the consolidation
un-throttled as a safety net.

## Leaves

- **helpers.md** — the eight bash scripts under `templates/memory/`
  that form the deterministic substrate (`_lib.sh` + 7 commands).
- **phase-a-marker.md** — the `post-edit-marker` hook + `mark.sh`.
  ~27ms per call. Never blocks.
- **phase-b-consolidation.md** — `stop-consolidate.sh` (throttled),
  `session-end.sh` (un-throttled safety net), `consolidate.sh`,
  `classify-inbox.sh`, `check-refs.sh`. The LLM hot path.
- **commands.md** — `/memory-init` (Sonnet, one-time cold start)
  and `/remember` (Haiku, fast-lane note filing).

Related: `discipline/done.md` invokes a forced consolidation as
step 7 of `/done`.
