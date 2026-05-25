# hooks/

The runtime hooks that aren't part of the memory subsystem. These
are the channels through which aims injects context into the model's
view (session-start, prompt-submit) and enforces discipline at the
tool-use boundary (pre-write).

## Leaves

- **pre-write.md** — PreToolUse gating. Hard-blocks edits while the
  planning-lock exists; in `block` mode also soft-blocks source
  edits without an in-progress plan.
- **session-start.md** — informational injection at session boot:
  in-progress plans, recent ADRs, the memory tree's top-level
  README.
- **prompt-submit.md** — per-prompt context (in-progress plan
  reminders, routing hints).

Memory-subsystem hooks (`post-edit-marker`, `stop-consolidate`,
`session-end`) live under `memory/phase-a-marker.md` and
`memory/phase-b-consolidation.md`, not here.
