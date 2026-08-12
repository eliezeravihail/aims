---
description: "aims — run only the BUILD/execute phase: delegate the current planned objective to a Worker, then stop before evaluation."
---

Enter the `aims-guide` skill and run **only the BUILD phase** (operating-loop step 4), following
`references/modes.md` (stepped mode) and `references/worker-handoff.md`.

- Reload `.aims/state.md`. Require the Loop cursor at `planned:awaiting-build` (or a reopened
  objective). If there is **no current objective**, stop and tell the user to run the plan command
  first — do not invent an objective here.
- Execute the drafted handoff **yourself, inline, in this session, on the currently selected model — do
  NOT spawn a subagent** (this is an explicit stepped-mode command; the user chose this model and is
  supervising the phase). Run it as a clearly separated phase that *conforms to* the objective and
  handoff produced by `plan` — do not re-open the design or expand scope beyond the handoff.
- When the Worker returns, record the result and an evidence pointer in `state.md`; set the Loop cursor
  to `executed:awaiting-review`. File any **engineering lessons** the build surfaced as `insights/dev/`
  records and anchor them (`references/design-record.md`) — do not manufacture insights, file only what
  is durable.
- **Stop here. Do NOT evaluate, accept, or choose the next objective** — that is the review phase.
  Report what was built and where the evidence is, and tell the user to run the review command.

$ARGUMENTS
