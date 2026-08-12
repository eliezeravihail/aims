---
description: "aims — plan and build autonomously, end to end: repeatedly choose the next design objective, delegate it to a Worker, measure the result, file the durable records, and continue the plan → build → review loop until the change is fully delivered. Pauses only for open product decisions."
---

Enter the `aims-guide` skill and run the **full autonomous loop** (`references/modes.md`, automatic
mode). This is the end-to-end driver — **not** a single plan-then-build pass. It keeps going, one
objective after another, until the current product change is delivered. (For a single supervised phase,
use `/aims-plan`, `/aims-build`, or `/aims-review` instead.)

- Set `Mode: auto` in `.aims/state.md` (create it from `assets/state-template.md` if absent), and
  resume the loop from the current Loop cursor — a plan drafted in stepped mode is built and reviewed
  the same way here; switching mode never discards the cursor.
- Drive the full operating loop yourself, **repeating** in the design → implement rhythm: choose one
  objective → delegate to a Worker subagent → measure the evidence yourself → **file the round's
  durable design into the `.capsa/` capsule and anchor it** (`references/design-record.md`) → choose the
  next objective → and so on. A returning Worker **auto-advances** the loop; you do not stop after one
  objective.
- On the first objective of a new product, establish state and run discovery first — including the
  **day-zero foundational substrate** (SKILL step 1), filed as a substrate ADR + `dependencies/` — before
  choosing the objective. If `.capsa/` does not exist yet, create the manifest on the first filing.
- Pause only at the **two legitimate human moments**: an *open product decision* you must not guess,
  and *receiving the next product change*. Do not run away — the same guardrails apply: one objective
  at a time, never mark met on the Worker's word without measuring the evidence yourself, never guess a
  product decision, no pre-planned roadmap.

$ARGUMENTS
