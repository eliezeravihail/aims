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

A design objective's result is not narrated into the chat and lost — it is **filed as a record in the
code tree, next to the code it describes**, so the next session inherits it. This is what turns a
one-session method into long-term development: months later, a fresh session at some part of the code
reads the conclusions in force there and continues, instead of starting over.

**The idea — the structure carries both the code and the knowledge.** There are two homes. Every source
file has a **companion** with the same name plus `.md`, right beside it (`src/render.py` →
`src/render.py.md`), holding what is known about *that file* under three sections — **Insights**,
**Decisions**, **Discussions**. Cross-cutting knowledge lives at the repo root: `goals.md`,
`architecture.md`, `base-dependencies.md`, `dependencies.md`, and `decisions/` (system-wide ADRs). The
one directory structure is *both* the code graph and the knowledge tree, so knowledge is reached by
**navigating** to the file or the root record — you never read the whole project to find what bears on
the file in front of you.

```yaml
---
title: "render.py"
date: 2026-08-12
---
## Insights
- SVG was chosen over canvas because the pages are static.
## Decisions
- render must not know how the maze was generated.
## Discussions
- Considered PNG; dropped — not crisp when zoomed.
```

**Knowledge is anchored, so drift is detected — not trusted.** The rule is one derivation: a record
`X.md` anchors to a sibling file named `X` (its name with `.md` removed) if it exists — so
`render.py.md` gets a content `hash:` of `render.py`, while `goals.md` (no file named `goals`) is a
system record with no anchor. A small tool stamps the hash; you never compute one or name a path. When a
later session **reads** a companion whose source has changed, one advisory hook says *"re-verify"* — it
**never blocks**. Because the pairing is by name, renaming a source and its companion **together** stays
in sync with nothing to update.

**`decisions/` are append-only** — to change a decision you add a new entry that supersedes it, so the
history of what once bound the code is never rewritten.

The format is [`knowledge/format.md`](knowledge/format.md); the mapping from method output to record is
[`design-record.md`](skills/aims-guide/references/design-record.md).

---

## Commands

- `/aims-plan` — choose one design objective, file the durable records it commits to, draft the Worker
  handoff; stop for review.
- `/aims-build` — delegate the objective to a Worker (or run it inline); stop before evaluation.
- `/aims-review` — measure the result against the exit criteria with the review panel (also works
  standalone on any diff/branch/PR).
- `/aims-plan-and-build` — the full autonomous loop, pausing only for open product decisions.
- `/install-on <path>` — install aims' per-project pieces (the two hooks + the anchor tool) into a
  target project.

## What aims deliberately does not have

No memory tree, no consolidation/doctor/lint machinery, no write hook, no planning lock. The method's
documentation discipline plus navigation-by-structure keep the knowledge current by construction;
the one read-time advisory is the whole of the active machinery. Enforcing a content invariant (a
linter over the code) is an **opt-in** fitness-function, never part of the passive record layer.

## The two moving parts

- [`knowledge/anchor.py`](knowledge/anchor.py) — write-time: stamps a companion's anchor by hashing its same-named source file. Called explicitly by the method, never as a hook. Stdlib only.
- [`knowledge/staleness_hook.py`](knowledge/staleness_hook.py) — read-time: the advisory drift check. Never
  blocks, fail-open.

## License

MIT.
