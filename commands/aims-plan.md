---
description: "aims — run only the PLAN phase: choose one design objective, file the durable design records it commits to, and draft the Worker handoff, then stop for review. Does not write code."
---

Enter the `aims-guide` skill and run **only the PLAN phase** (operating-loop steps 1–3), following
`references/modes.md` (stepped mode), `references/objective-selection.md`, and
`references/design-record.md`.

- Set `Mode: stepped` in `.aims/state.md` (create it from `assets/state-template.md` if absent).
- Establish current state, run discovery, and resolve any **open product decisions** by asking the
  user one concrete question at a time — planning is where those questions belong.
- Choose the single most valuable **design/quality objective** now, **declare its Kind** (`design` |
  `implementation` | `refactoring` — see `references/objective-selection.md`; it sets the review lens),
  and draft a bounded Worker handoff per `references/worker-handoff.md`. Write both into `state.md`; set
  the Loop cursor to `planned:awaiting-build`.
- **File the round's durable design as records in the code tree** (`references/design-record.md`): the
  root `goals.md` / `base-dependencies.md` the design commits to, the system `architecture.md` and
  `decisions/` ADRs (with rejected alternatives), and file-level Insights/Decisions/Discussions in the
  companion of each file touched. **Anchor each companion on filing** with `python3 knowledge/anchor.py
  <companion>`. `decisions/` are append-only.
- **Stop here. Do not delegate and do not write implementation code.** **Present a plan report** — an
  executive summary compiled from the objective and the filed records (dependencies, decisions and
  their rationale, chosen architecture, exit criteria) — so the user can read the round's reasoning,
  inspect or edit the objective, and comment before anything is built. It is a presentation, not a new
  stored file: the substance already lives in the records. Then tell them to run the build command.

$ARGUMENTS
