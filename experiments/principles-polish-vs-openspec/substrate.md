# Substrate — fixed, identical for every arm and every challenge

Fixes the ground and deliberately nothing above it: no module names, no interfaces, no layering. The shape
of the design is what is measured.

- **Python 3.11+**, standard library only. A new runtime dependency must be argued for in the design.
- `decimal.Decimal`, `datetime`, `zoneinfo` are available; nothing requires or forbids them.
- No UI, no network, no database, no persistence. Single process.
- The entry point may be a library with a small CLI, or a local function API — the design's call.

## The deliverable (identical standing instruction for every arm)

> Design only. Produce the architecture: the components, their responsibilities, the seams between them, the
> rules each one owns, and the reasoning that puts them where they are. Do **not** write implementation
> code. A type signature, an interface sketch, or a few illustrative lines where they make a boundary
> concrete are welcome; a working program is out of scope and is not read by any judge.
>
> If a material product question arises that an ordinary product owner would answer, **state your assumption
> explicitly in the design and choose a simple, sensible approach** — do not invent a feature nobody asked
> for, and do not build for a stage that has not been revealed.

Whatever the arm's method also produces — records, specs, proposals, task lists — is kept and is evidence
for continuity; it is stripped before the architecture is judged.
