# Substrate — fixed, identical for every arm

Stated so that three designs are comparable, and so the oracle is not asked the same technical question
three times and answers it three different ways. It fixes the ground, and deliberately nothing above it:
no module names, no interfaces, no layering, no example. The shape of the design is what is being measured.

- **Python 3.11+**, standard library only. A new runtime dependency has to be argued for in the design.
- `decimal.Decimal` is available. Nothing requires or forbids it.
- No UI, no network, no database, no persistence.
- The entry point may be a library with a CLI, or a local HTTP endpoint — the design's call.
- Single process, single currency at stage 1.

## The deliverable

An **architecture document**. Components, their responsibilities, the seams between them, the rules each
one owns, and the reasoning that puts them where they are.

**Not** an implementation. A type signature, an interface sketch, or a few illustrative lines where they
make a boundary concrete are welcome; a working program is out of scope and is not read by any judge.

Whatever the arm's method also produces — records, specs, proposals, task lists — is kept as it is, and is
evidence for the continuity reading. It is stripped before the architecture is judged.
