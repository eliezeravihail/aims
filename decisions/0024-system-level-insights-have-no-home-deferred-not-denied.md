---
title: "cross-cutting learning has no root-level home; the gap is recorded and the fix deliberately deferred"
date: 2026-09-22
---

**Context.** `decisions/0022`'s First gate lists what survives into a record — all of it knowledge nothing
in the code asserts. Two of those categories, **"what was tried and failed, and the symptom"** and **"an
assumption stated as unproven"**, have a home only at **file** level: a companion's Insights and
Discussions. The root records are `goals.md` (intent), `architecture.md` (boundaries/seams/invariants/
change axes), `base-dependencies.md`, `dependencies.md`, and `decisions/` (an ADR). Every one is a
statement of **intent, shape, or decision**. Cross-cutting *learning* with no decision attached has
nowhere to go.

Found by running the gate on this repo's own work (`experiments/improve-2026-09/bp22-gate-on-itself/`).
Of 14 candidate items, 10 were correctly declined as already carried. Of the four filed, **two went to the
root and both had to be smuggled**: the "one shape, three times" measurement-error pattern and the
instruction-following caveat both landed in `goals.md` — and they fit only because *this* repo's `goals.md`
has grown an "Evidence status" body far beyond its own template (Primary goal / Use scenarios / Non-goals).
**Had `goals.md` matched the template it ships, neither would have had a home.** A project following the
template as written hits the gap immediately.

**The recursion, named.** This finding is itself an instance of the gap — a cross-cutting insight with no
decision attached, and therefore unfilable under the format it describes. Recording it *as a decision to
defer* is what gives it a home. That is a workaround, not a refutation.

**Decision.** Record the gap; **do not add a record kind yet.** `goals.md`, `architecture.md`, the
dependency records and ADRs stay exactly as they are. Nothing in the method may claim the root level has a
home for cross-cutting learning — it does not, and a filer who cannot place such an item should say so
rather than force it, as the guidance now asks.

**Why deferred rather than fixed.** A new root record is a change to the shipped format — the surface every
installed project inherits — and this campaign's discipline is that a method change enters on evidence
(`decisions/0021` was shipped, then found to be a regression, precisely because a plausible fix went in
ahead of its test). The obvious candidate, a root `insights.md`, is also the half of the
**single-root-file** alternative that `decisions/0023` records as *considered-but-untested*; adding it
piecemeal would prejudge that open question. One gap should not be closed by quietly deciding another.

**What would settle it.** A filing comparison on aims-**filed** records, arms differing only in whether a
root-level home for cross-cutting Insights/Discussions exists, measuring (a) how many items are dropped or
forced for want of a home, and (b) whether the new record collects anything the companions and ADRs would
not have held anyway. Run it together with `0023`'s question, since the answers interact.

**Alternatives.**
- *Add a root `insights.md` now* — rejected: untested format change, and it prejudges `0023`.
- *Rule that cross-cutting learning must become an ADR* — rejected: it forces an observation into a
  decision's shape, which is how a guess gets recorded as a resolution.
- *Say nothing and keep smuggling into `goals.md`* — rejected: it works only where `goals.md` has already
  outgrown its template, so it silently fails for every project that followed it.
