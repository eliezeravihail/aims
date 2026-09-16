---
description: "aims — run the opening design round through the panel: the Guide sets one objective, three axis-focused Workers work it independently, and a merge agent composes one result and the Worker handoff, then stop for review. Does not write code."
---

Enter the `aims-guide` skill and run **only the PLAN phase** (operating-loop steps 1–3), with the design
fanned out **through the panel** (`references/panel-plan.md`) rather than a single pass, following
`references/modes.md` (stepped mode), `references/objective-selection.md`, and
`references/design-record.md`.

- Set `Mode: stepped` in `.aims/state.md` (create it from `assets/state-template.md` if absent).
- Establish current state, run discovery, and resolve any **open product decisions** by asking the
  user one concrete question at a time — same as `/aims-plan`.
- **Set the one objective yourself, the ordinary way** (`references/objective-selection.md`): a design
  outcome with the behavior as a constraint, adversarial exit criteria, the hard decision at its core,
  and its Kind. The panel does **not** generate the objective; it fans out the design that meets it.
- **Convene the panel**, per `references/panel-plan.md`: assemble the grounding package once (it carries
  that one shared objective); spawn the **three axis-focused Workers** as isolated parallel subagents on
  the currently selected model (or **decline honestly** and fall back to single-pass `plan`, per the
  reference, if no subagent facility exists); then run the **merge agent inline, in this session**, to
  harvest the good from each and compose one result — refusing winner-picking / union / averaging. This
  command always convenes the panel; it never falls back to single-pass silently.
- Write the **merged handoff (conforming to your one objective)** into `state.md`, same schema as
  `/aims-plan`; set the Loop cursor to `planned:awaiting-build`.
- **File the round's durable design as records in the code tree** (`references/design-record.md`):
  the root `goals.md` / `base-dependencies.md` the design commits to, `architecture.md`, and the
  round's `decisions/` ADR — which, for a panel round, also carries the **strengths harvest** and
  **every axis split** the round had (a decided conflict, or a harmonization — both shapes, per
  `references/panel-plan.md`) — plus file-level Insights/Decisions/Discussions in the companion of
  each file touched. **Anchor each companion on filing** with `python3 .aims/anchor.py <companion>`.
  `decisions/` are append-only.
- **Stop here. Do not delegate and do not write implementation code.** **Present a plan report** —
  the same executive summary `/aims-plan` presents, plus one section this command adds: the strengths
  harvest per axis, the harmonizations, and each decided conflict's reason. Then tell the user to run
  the build command.

$ARGUMENTS
