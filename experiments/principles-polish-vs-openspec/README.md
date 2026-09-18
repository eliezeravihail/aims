# Pilot series — design-principles.md vs. OpenSpec, three products, design-only

**Purpose.** Polish [`design-principles.md`](../../skills/aims-guide/references/design-principles.md) into
a checklist that *leads to a correct design*, by competing it against OpenSpec on the **capabilities
themselves** — not on one product but on a **sequence of three**, so a fix that only patches one example is
visible as such.

A pilot under [`../PROTOCOL.md`](../PROTOCOL.md). Nothing is built: each arm produces a **design** (prose
architecture), and the designs are compared. Deviations from PROTOCOL are declared in §5.

## The two arms (per the task)

| | **aims-single** | **OpenSpec** |
|---|---|---|
| Added line | "follow the `aims-guide` skill; design only" | "use OpenSpec for this; design only" |
| What it runs | one design pass **+ exactly one mandatory review-and-revise round** against `design-principles.md` | `/opsx:explore` → `/opsx:propose` faithfully: capability specs (requirements + scenarios), then `proposal.md` / `design.md` / `tasks.md` |
| Consults at the change stage | its own design + the principles | its `openspec/specs/` and change docs |

No plain arm and no aims-panel arm: the task names these two. aims-single carries the one-revise-round that
`SKILL.md` makes mandatory on a design objective — that round **is** the treatment being measured.

## The two scored dimensions (never merged)

Each challenge is scored on **two separate axes**, exactly as the task sets them:

> **D1 — first-round design.** Reach the best possible architecture in the **first round** (stage 1 only).
> Scored blind on the [assessment form](../judging-rubric/assessment-form.md).
>
> **D2 — change absorption.** A new requirement nobody stated arrives (stage 2). Does the stage-1 design
> **support** the change (extend at a seam, not reopen an owner), **and is the changed result still
> correct and well-formed**? This is a **separate score**: the [survival count](../aims-vs-openspec/README.md)
> (reopened + discarded) plus the form re-filled on the stage-2 design.

Both dimensions are read for **quality** and for **cost** (rounds, model calls, design length — the
PROTOCOL §6 cost recorder; no quality verdict from the cost reading).

## The three challenges

Three distinct domains, each with a stage-2 change that introduces a genuinely **different kind** of
operation — the exact moment the principles must fire (concept-fit §4, calibrate-the-interface §5,
one-owner-per-rule §5, schema-evolution §7, OCP §7):

1. **`feed-ranking/`** — rank a feed by weighted signals; the change adds a **hard eligibility filter** and a
   **windowed diversity constraint** — neither is another weight.
2. **`booking-availability/`** — compute bookable slots; the change adds **inter-booking buffer**,
   **minimum-notice**, and variable granularity — rules that must have one owner, and a buffer that is not a
   booking.
3. **`entitlements/`** — decide allow/deny from role grants; the change adds **deny-overrides**, **resource
   inheritance**, and **time-bounded grants** — where one-owner-per-rule is a *precondition*.

Each folder holds `cards/stage-1.md`, `cards/stage-2.md`, and `hidden/spec-and-oracle.md` (never shown to an
arm; it defines the correctness oracle the judge checks the wrong-number traps against).

## Loop

Run all three, judge both dimensions, then **diagnose every place aims lost or reopened**, trace it to the
principle that failed to fire, and **sharpen that principle** in `design-principles.md`. Re-run the weak
case to confirm the fix lands without breaking the others. Repeat until all three achieve both D1 and D2.
[`results.md`](results.md) records each round.

## 5. Deviations from PROTOCOL, declared

1. **No build** (as `aims-vs-openspec`): the architecture is the deliverable; no product/behavior reading.
2. **Two arms**, not three — the task names aims-single and OpenSpec.
3. **Oracle is non-interactive.** Arms run as isolated subagents; instead of live Q&A, each arm is told to
   **state any material product assumption explicitly and pick a simple sensible approach**. The hidden spec
   is the correctness oracle the *judge* uses to catch a wrong-number trap. A leak-free stage boundary is
   still enforced (stage-2 cards withheld until stage-1 designs are frozen).
4. **The Q1 rubric is aims' own** (`design-principles.md`) — the very document under test. Offset only
   partly: D2's survival count is rubric-free, and D1 verdicts must be structural and quotable.
5. **n = 1 per product**; strength is the **sequence** of three, not any single unit.
