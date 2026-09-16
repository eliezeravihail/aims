---
title: "the shipping surface owns an operating definition; the ADR owns its rationale"
date: 2026-09-15
---

**Context.** The `design`-lens review of the panel-plan mechanism design found two records each claiming
sole ownership of the axis trio. `architecture.md` stated the trio has "exactly one owning definition — in
`decisions/0005-panel-plan-three-advisors.md`; it is not restated here or anywhere else", and the Worker
handoff repeated it; the returned design made `skills/aims-guide/references/panel-plan.md` §Axes the
operating definition and read 0005 as history. Taken literally the design produces exactly the
drift-capable second copy that the objective's criterion 6 fails on — but the relocation has a real force
neither record anticipated:

- `decisions/` is **aims' own history and does not ship to a target project**, while `skills/` does. A
  target project running panel-plan would never see 0005 — it would have no access to the definition its
  advisors must operate from.
- `decisions/` is **append-only** (`CLAUDE.md`), a poor home for a definition already revised once
  in-round (`0005`, "revised in-round").

This is a genuine collision between two true constraints, not a Worker error, and it is resolved by a
decision rather than a wording fix.

**Decision.** Ownership splits **by kind of text, not by record**:

1. The **operating definition** — the text an agent reads in order to *do* the work — lives in exactly one
   **shipping** record. For the axis trio that is `skills/aims-guide/references/panel-plan.md` §Axes.
   Commands, `SKILL.md`, and `architecture.md` **refer to it and never restate it**.
2. The **decision and its rationale** — why this trio, what was rejected, what evidence moved it — stays in
   the ADR (`decisions/0005`). An ADR records what was decided and why, at a date; it is not the text the
   agent operates from.
3. Where the two overlap — 0005 does state the three axes inline — the ADR's copy is **frozen as of its
   date and is not authoritative for operation**. Criterion 6 is therefore read as: exactly one *operating*
   owner, and every other mention names it rather than repeating it.

**Consequences.**
- This **amends the consequence line in `0005`** that reads "The axis trio is defined in one owned place
  and referenced everywhere else" by naming *which* place. `0005` itself is not rewritten — `decisions/` is
  append-only, so the amendment lives here.
- `architecture.md`'s panel-plan bullet names the shipping reference as the operating owner and this ADR as
  the ownership split.
- The rule **generalizes beyond the trio**: any definition an agent operates from belongs on the shipping
  surface; any rationale for it belongs in an ADR. A definition that exists only in `decisions/` is
  invisible to every target project by construction.
- Accepted cost: a reader who opens `0005` alone sees an axis list that can age. It is bounded — an ADR is
  dated history, and the two records that a session actually navigates by (`architecture.md` and the
  reference) both name the operating owner.
- The panel-plan design's §6 is correct as amended; what it got wrong was calling `0005` "history" without
  saying what `0005` still owns.

**Alternatives.**
- *Keep `0005` as the operating owner (architecture.md as written)* — rejected: `decisions/` does not ship,
  so the definition would be unreachable in exactly the projects that must operate from it.
- *State the trio in both, with a "keep in sync" note* — rejected: that is precisely the drift-capable
  second copy criterion 6 exists to forbid; a sync note is a wish, not an owner.
- *Rewrite `0005` to remove the inline trio and point at the reference* — rejected: `decisions/` is
  append-only (`CLAUDE.md`); superseding in place is for companions, and erasing the rationale's own
  subject would damage the record.
- *Make the operating owner `SKILL.md`* — rejected: `SKILL.md` is the method's entry point and already
  delegates mechanism detail to `references/`; putting one mechanism's definition there inverts that.
