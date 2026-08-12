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
- **File the round's durable design into the `.capsa/` capsule** (`references/design-record.md`): the
  charter / requirements the design commits to, the substrate ADR + dependencies, the structural
  `decisions/` with their rejected alternatives, and any `insights/`. Place each record at the node it
  governs, and **anchor it on filing** with `tools/aims_anchor.py`. `decisions/` are append-only.
- **Stop here. Do not delegate and do not write implementation code.** **Present a plan report** — an
  executive summary compiled from the objective and the capsule records (dependencies, decisions and
  their rationale, chosen architecture, exit criteria) — so the user can read the round's reasoning,
  inspect or edit the objective, and comment before anything is built. It is a presentation, not a new
  stored file: the substance already lives in the capsule. Then tell them to run the build command.

$ARGUMENTS
