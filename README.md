# aims

**aims makes design the goal of coding-agent work — and preserves the design knowledge so it compounds
across sessions instead of resetting each time.**

Writing code is cheap now; what stays scarce is *good design that holds as a product grows*, and
*knowledge that survives the session*. aims addresses both, and they are its two halves:

1. **Directing the agent** — make the design the objective the agent optimizes for, then measure the
   result. Design produced at construction time, not policed afterward.
2. **Documenting & preserving knowledge** — file the design knowledge as durable, scoped, anchored
   records, so a later clean session *reads the prior conclusions and builds on them* rather than
   re-deriving from scratch.

The name says it: **aims** — the design *aim* is what the system manages.

---

# Chapter 1 — Directing the agent · הכוונת הסוכן

An implementing agent optimizes toward whatever goal it is handed. Give it a feature ticket and it
optimizes for the feature landing; design quality becomes whatever happens to survive. So if you want
good design out, **the design has to be the goal you give.** aims separates two roles to make that
happen:

- **The Guide** holds the product vision and decides, one at a time, what *design/quality outcome* the
  codebase most needs next — never writing implementation code. Its deliverable is the design quality
  of the codebase across the product's whole evolution.
- **The Worker** — a capable engineer — receives that outcome as its objective, with the feature
  behavior attached as a *constraint the design must satisfy*, and builds it. The Guide then measures
  the returned design and chooses the next objective.

The method has exactly two moves — **direct** (hand the right goal) and **measure** (observe honestly
what came back) — and no coercion: a design is made good at construction time by the goal you set, and
review only measures whether it was reached, feeding the next direction.

What the loop does each round:

- **Ground the product** by asking, not guessing — surface open product decisions, and the day-zero
  foundational substrate (language, framework, base deps), which is *asked of the user*, never
  defaulted.
- **Gate feasibility** — if a new product rests on an unproven premise, the first objective is a spike
  that proves it, before designing on top of it.
- **Choose one design objective** with sharp exit criteria (the edge and break cases named
  adversarially, so a minimal implementation can't satisfy it on paper).
- **Delegate** a bounded objective to the Worker (or run it inline), framed as a design outcome with
  the behavior as a constraint — never a feature ticket.
- **Measure** the result against the criteria with a review panel (reproduced readings, never a score),
  then run a **subtractive pass** that cuts abstractions and affordances that don't pay for themselves.
- **Choose again** from the evidence — the sequence is not planned up front; direction emerges as the
  build proceeds.

It runs two ways: **automatic** (drives the whole loop, pausing only for an open product decision or
the next product change) or **stepped** (stops at every phase for supervision). The loop's position
lives in `.aims/state.md` — run-state only, reloaded at the start of every command — so the goal
survives side-conversations and context compaction.

The method lives in [`skills/aims-guide/`](skills/aims-guide/SKILL.md); the "good design" it aims at is
[`design-principles.md`](skills/aims-guide/references/design-principles.md).

---

# Chapter 2 — Documenting & preserving knowledge · תיעוד ושימור ידע

A design objective's result is not narrated into the chat and lost — it is **filed as a durable record**
in the product's `.capsa/` knowledge capsule, so the next session inherits it. This is what turns a
one-session method into long-term development: months later, a fresh session at some part of the code
reads the conclusions in force there and continues, instead of starting over.

**The idea — placement is scope.** The capsule is a tree of one-record-per-fact files, each **placed at
the node it governs**. A record under `components/api/` governs `api` and everything beneath it; a
record at the root is capsule-wide. So relevance is *derived from the path*: a reader loads only the
records in force where it is working — never one growing file it must read whole. This replaces both
notes glued to a source file (fragile — code moves orphan them) and a central store (bloats).

**A record is lean.** Just a title, a date, and a prose body carrying the decision and its rationale;
the *kind* comes from the folder (`decisions/`, `requirements/`, `insights/`, `components/`,
`charter.md`). Everything else is optional.

```yaml
---
title: "core owns arithmetic"
date: 2026-08-12
code: src/core.py        # only if it concerns specific code
---
core owns all arithmetic — a single owner. Chose X over Y because Z.
```

**Knowledge is anchored, so drift is detected — not trusted.** A record that concerns code names it
once in `code:` (a single cohesive target — a file, a directory, or a `dir/**` glob), and a small tool
stamps a single anchor: a content `hash:`, or a `shape:` fingerprint for a structural record. You never
compute or write a hash by hand. When a later session **reads** a record whose code has since changed,
one advisory hook says *"re-verify"* — it **never blocks**, and it reads the actual file, so it catches
drift whether the change went through aims or was made by hand. That advisory, at the exact moment
someone is about to rely on the record, is what replaces keeping docs true by hand.

**The format is also a design signal.** `code:` deliberately cannot name a *scattered* subset of files.
If a record can't point at one cohesive target, that inability is telling you the concern lacks a single
home (shotgun surgery) or a directory is over-generic — so it becomes a **refactoring objective** in the
code, not a workaround in the record. (The one exception is a genuine project-wide norm — "all types are
PascalCase" — which legitimately applies everywhere: it is a `code:`-less record at the root, carrying
no anchor.)

**`decisions/` are append-only** — to change a decision you write a new one that supersedes it, so the
history of what once bound the code is never rewritten.

The format is [`docs/format-profile.md`](docs/format-profile.md); the mapping from method output to
record is [`design-record.md`](skills/aims-guide/references/design-record.md).

---

## Commands

- `/aims-plan` — choose one design objective, file the durable records it commits to, draft the Worker
  handoff; stop for review.
- `/aims-build` — delegate the objective to a Worker (or run it inline); stop before evaluation.
- `/aims-review` — measure the result against the exit criteria with the review panel (also works
  standalone on any diff/branch/PR).
- `/aims-plan-and-build` — the full autonomous loop, pausing only for open product decisions.
- `/install-on <path>` — install aims' per-project pieces (the two hooks + the anchor tool + capsule
  scaffolding) into a target project.

## What aims deliberately does not have

No memory tree, no consolidation/doctor/lint machinery, no write hook, no planning lock. The method's
documentation discipline plus placement-derived relevance keep the knowledge current by construction;
the one read-time advisory is the whole of the active machinery. Enforcing a content invariant (a
linter over the code) is an **opt-in** fitness-function, never part of the passive record layer.

## The two moving parts

- [`tools/aims_anchor.py`](tools/aims_anchor.py) — write-time: stamps a record's anchor from its
  `code:`. Called explicitly by the method, never as a hook. Stdlib only.
- [`hooks/staleness_read.py`](hooks/staleness_read.py) — read-time: the advisory drift check. Never
  blocks, fail-open.

## License

MIT.
