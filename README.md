# aims

**AI Manager System**

When an AI agent writes code, two things tend to go wrong:

- **The architecture and the code quality suffer.** The agent optimizes for the goal it was given —
  get the feature working — so the design is whatever happens to fall out of that, not something
  anyone chose.
- **What the work learned is lost.** Insights and decisions made while building do not reach the
  next session, so later work re-derives them from scratch, or contradicts them.

aims answers each of these:

1. **Directing the agent** — the goal handed to the agent is the design outcome itself, with the
   feature attached as a constraint it must satisfy. Quality is built in at construction time, not
   reviewed in afterward.
2. **Documenting & preserving knowledge** — insights and decisions are filed as records beside the
   code they describe, so a later session reads them and continues from there instead of starting
   over.

> **Status: in development.** aims is still being developed, and its effectiveness has not yet been
> demonstrated. The main obstacle is measurement: there is no accepted benchmark or measure of design
> quality, and in our own comparisons the grades depended on the judge as much as on the design. The
> results in `experiments/` should be read as exploratory.

📄 **Paper:** [*Design as the Objective*](paper/aims_paper.pdf) — the argument (a model optimizes the
goal it is given), and an evaluation that could not show the method helps, with the reasons: design
quality has no measurement yet that gives the same answer twice.

---

# Chapter 1 — Directing the agent

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

# Chapter 2 — Documenting & preserving knowledge

A design objective's result is not narrated into the chat and lost — it is **filed as a record in the
code tree, next to the code it describes**, so the next session inherits it. This is what turns a
one-session method into long-term development: months later, a fresh session at some part of the code
reads the conclusions in force there and continues, instead of starting over.

**The rule.** Discussions and decisions that are **not evident from the code itself** go in a `.md`
file next to what they are about: beside the relevant file (`src/render.py` → `src/render.py.md`), in
the relevant module's folder (`src/parsers/` → `src/parsers.md`), or at the project root if they concern
the whole project (`goals.md`, `architecture.md`, `dependencies.md`, `decisions/`). **Everything else
belongs in the code's own documentation** — names, docstrings, comments, tests. If the code can say it,
no record is written, so most files never get one.

The one directory structure is then *both* the code graph and the knowledge tree: knowledge is reached by
**navigating** to what you are working on, never by reading the whole project. A record holds what the
code cannot — a road not taken, a deliberate non-goal, a failed attempt, an unproved assumption:

```yaml
---
title: "render.py"
date: 2026-08-12
---
## Insights
- Canvas was tried first and dropped: its text nodes rasterise, so a zoomed page lost the labels.
## Decisions
- render never generates — it takes a finished maze. This rules out the "render(seed)" convenience
  overload that has now been asked for twice.
## Discussions
- PNG output was weighed and dropped: not crisp when zoomed. Worth revisiting only if pages go to print.
```

Nothing there restates the code — that `render` takes a maze and returns SVG is what its signature is for.

**Knowledge is anchored, so drift is detected — not trusted.** The rule is one derivation: a record
`X.md` anchors to a sibling file named `X` (its name with `.md` removed) if it exists — so
`render.py.md` gets a content `hash:` of `render.py`, while `goals.md` (no file named `goals`) is a
system record with no anchor. A small tool stamps the hash; you never compute one or name a path. When a
later session **reads** a companion whose source has changed, one advisory hook says *"re-verify"* — it
**never blocks**. Because the pairing is by name, renaming a source and its companion **together** stays
in sync with nothing to update.

**`decisions/` are append-only** — to change a decision you add a new entry that supersedes it, so the
history of what once bound the code is never rewritten.

Where things go is [`design-record.md`](skills/aims-guide/references/design-record.md); what a record
looks like is [`knowledge/format.md`](knowledge/format.md).

---

## Install

aims is a Claude Code plugin. Requirements: Python 3 (standard library only) and bash — nothing else.

1. **Add the marketplace and install the plugin**, from within Claude Code:
   ```
   /plugin marketplace add eliezeravihail/aims
   /plugin install aims@aims
   ```
   This makes the `aims-guide` skill and the `/aims-*` commands available in every session —
   including `/aims-sharpen-prompt`, which is useful on its own and needs no project setup.

2. **Set up a project** — in the project you want to use aims on:
   ```
   /install-on .
   ```
   Idempotent. It installs the two per-project hooks (`session-start`, and the read-time staleness
   advisory) plus the anchor tool under `.aims/`, and wires them into `.claude/settings.json`. It never
   touches your code or any existing design records.

## Getting started — how to run it

Drive the design from within a session in your project:

- **Autonomous** — `/aims-plan-and-build "build a URL shortener with pluggable storage"` runs the whole
  loop (discovery → design objective → build → review → file the records), pausing only for open product
  decisions.
- **Supervised, phase by phase** — `/aims-plan "<task>"` → read the plan report → `/aims-build` →
  `/aims-review`.
- **Review any change on its own** — `/aims-review <branch | diff | path>`.

As it works, aims files what the code cannot say **next to what it is about** — a companion beside a file
that earned one, a record beside a folder, root records for the whole project. A later fresh session
reads those by navigating to what it is working on, and continues instead of re-deriving. If you read a
companion whose source has since changed, the staleness hook says *"re-verify"*.

## Sharpening any task — `/aims-sharpen-prompt`

The framing discipline on its own, detached from software and from the rest of aims.
[`/aims-sharpen-prompt`](skills/aims-sharpen-prompt/SKILL.md) turns a vague, hand-waving ask into a
brief worth executing — *before* the work starts. Installing the plugin is all it needs: no
`/install-on`, no records, no loop, and the task does not have to be code.

An agent optimizes whatever it was told, so the framing decides whether the result helps. "Plan a
pension" collapses into "list some funds"; "find the bugs" into "skim for the obvious ones". The
skill reasons through six things in the task's own terms:

1. the real outcome, not the easy-to-produce proxy for it;
2. the hard judgment the task hides — faced, not routed around;
3. what is known vs. what only the person can decide (**ask, never guess**) vs. what is free to pick;
4. what "done" means, said so it can actually be checked;
5. what *not* to optimize, and what must not break;
6. what evidence must back the claims, in place of a self-report.

It is deliberately **not a form to fill in** — a frame you can tick without thinking is the failure it
exists to prevent. For a software product that will evolve, it hands off to `aims-guide`.

The framing discipline behind this skill was inspired by **Kritt-ai**'s
[open·kritt](https://github.com/Kritt-ai/open-kritt) — whose approach is to break work into small,
well-defined tasks rather than point a model at a broad goal; aims adapts that idea to sharpening a
single task before you execute it.

## Commands

- `/aims-sharpen-prompt` — sharpen any task into a real brief before executing it; standalone, and not
  limited to software.
- `/aims-plan` — choose one design objective, file the durable records it commits to, draft the Worker
  handoff; stop for review.
- `/aims-panel-plan` — the opening-round variant: set one objective, then fan the design across three
  axis-focused Workers and compose the best of each with a merge agent; stop for review.
- `/aims-add-feature` — plan a change to code that **already exists** (a pure refactor, or an adaptation that
  absorbs a new requirement): learns the code and characterizes its behavior first, then chooses one
  `add-feature` objective against [`add-feature-principles.md`](skills/aims-guide/references/add-feature-principles.md);
  stop for review. Not the greenfield design flow.
- `/aims-build` — delegate the objective to a Worker (or run it inline); stop before evaluation.
- `/aims-review` — measure the result against the exit criteria with the review panel (also works
  standalone on any diff/branch/PR).
- `/aims-plan-and-build` — the full autonomous loop, pausing only for open product decisions.
- `/install-on <path>` — install aims' per-project pieces (the two hooks + the anchor tool) into a
  target project.

## The evidence

[`experiments/README.md`](experiments/README.md) lists **every experiment** behind aims — what it asked, what
it found, and whether it stands, was superseded, or was withdrawn — split by the two goals, since they are
measured separately. The short version:

- **The measurement does not hold yet.** In the latest design comparison, aims against the real OpenSpec
  tool over two rounds ([`results-openspec-real.md`](experiments/principles-polish-vs-openspec/results-openspec-real.md),
  [`results-aims-real.md`](experiments/principles-polish-vs-openspec/results-aims-real.md)):
  - the two rounds pointed in opposite directions;
  - the same, unchanged designs received grades from 5.7 to 9.8 depending on the judge;
  - all nine judges recognized which method produced each design;
  - the one measure independent of aims' principles (components reopened) favoured OpenSpec in 5 of 6
    readings.

  A rubric difference smaller than that spread, which is most of them, cannot be read as a result.
- **Design.** Tests do not separate designs: two designs passing an identical suite scored 43 vs 16, but on
  the same rubric whose spread is shown above. When adding a feature, an agent without the method was equally
  correct every time. Over a sequence of three additions a judge saw aims' design improve; the coupling count
  did not confirm it.
- **Knowledge.** A recorded non-goal catches a change that contradicts it; the code alone cannot (3/3 vs
  0/3). On small code a record does not change the outcome, because the pattern is recoverable from the code.
- **Losses are recorded as losses**: aims lost the plant → mineral pilot decisively, and its best design
  pilot (v4) ships a real defect.

Every experiment follows [`experiments/PROTOCOL.md`](experiments/PROTOCOL.md): a controlled comparison against a
control arm, with anonymized designs judged by a separate agent — a demonstration is not an experiment.
Anonymized is not blind: in the latest comparison every judge recognized which method produced each design.

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
