---
description: "aims — run the PLAN phase convening the panel-plan mechanism: three independent fixed-axis advisor planners, merged by a master planner into one design objective and Worker handoff, then stop for review. Does not write code."
---

Enter the `aims-guide` skill and run **only the PLAN phase** (operating-loop steps 1–3), with the
objective drafted **through the panel-plan mechanism** (`references/panel-plan.md`) rather than
single-pass, following `references/modes.md` (stepped mode), `references/objective-selection.md`, and
`references/design-record.md`.

- Set `Mode: stepped` in `.aims/state.md` (create it from `assets/state-template.md` if absent).
- Establish current state, run discovery, and resolve any **open product decisions** by asking the
  user one concrete question at a time — same as `/aims-plan`; this command changes how the objective
  is drafted, not how state is established.
- **Convene the panel**, per `references/panel-plan.md`: assemble the grounding package once; spawn
  the three advisor planners as isolated parallel subagents on the currently selected model (or
  decline honestly, per the reference, if no subagent facility exists); then run the **master planner
  inline, in this session**, to harvest strengths and compose one objective + handoff. This command
  always convenes the panel — it never falls back to single-pass planning silently.
- **Declare the objective's Kind** (`design` | `implementation` | `refactoring` —
  `references/objective-selection.md`) and write the composed objective and handoff into `state.md`,
  same schema as `/aims-plan`; set the Loop cursor to `planned:awaiting-build`.
- **File the round's durable design as records in the code tree** (`references/design-record.md`):
  the root `goals.md` / `base-dependencies.md` the design commits to, `architecture.md`, and the
  round's `decisions/` ADR — which, for a panel-plan round, also carries the **strengths harvest** and
  **every axis split** the round had (a decided conflict, or a harmonization — both shapes, per
  `references/panel-plan.md`) — plus file-level Insights/Decisions/Discussions in the companion of
  each file touched. **Anchor each companion on filing** with `python3 .aims/anchor.py <companion>`.
  `decisions/` are append-only.
- **Stop here. Do not delegate and do not write implementation code.** **Present a plan report** —
  the same executive summary `/aims-plan` presents, plus one section this command adds: the strengths
  harvest per axis, the harmonizations, and each decided conflict's reason. Then tell the user to run
  the build command.

$ARGUMENTS
