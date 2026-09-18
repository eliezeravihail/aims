# aims Guide State

Loop status only — the flags that drive the loop and let it survive compaction. This file is **not**
the design record, and it lives in `.aims/state.md`, outside the design records. The
durable engineering design lives as records in the code tree (facts, kept next to the code they describe,
anchored to it — see `references/design-record.md`). Keep this short; do not use it as a transcript or
a worker task log.

<!-- SCHEMA CONTRACT (this template owns it): the aims commands read the goal from this file by
     heading and marker when they run. The load-bearing anchors are the headings `## Current objective`
     (with its `**Objective:**` and `**Kind:**` markers), `## Mode`, and `## Loop cursor`. Keep those
     headings and marker formats intact — a resuming command re-orients from them; rename one and the
     command reads the wrong thing (or nothing). -->

## Mode

<!-- auto | stepped. `auto` = the loop runs end to end, pausing only for open product decisions and the
     next product change. `stepped` = stop at every phase boundary (plan / build / review) and advance
     only on an explicit command; a returning Worker parks at executed:awaiting-review, it does NOT
     auto-advance. See references/modes.md. Default when unset: auto. -->

auto

## Loop cursor

<!-- Where the loop is parked right now, so any turn (a returning Worker, or a "aims next" / phase
     command from the human) can resume from exactly here. One line, kept current:
     needs-plan | planned:awaiting-build <objective> | awaiting-worker <objective> |
     executed:awaiting-review <objective> | reviewed:awaiting-decision <objective> |
     ready-to-choose-next | awaiting-human <named open decision> -->

## Current objective

<!-- The single unit of work in flight. Transient loop state — it is replaced each objective, not a
     durable design record. When it resolves, its lasting design output is filed as records in the code
     tree (root goals/architecture/decisions, and a companion beside each source file); it does not accumulate here. -->

**Kind:** <!-- design | implementation | add-feature | experiment — sets the review lens.
     `experiment` is a round whose deliverable is a *measurement*, not a product change: it is
     reviewed against whether the comparison discriminates (`../../experiments/PROTOCOL.md`), not
     against built code. An experiment that only produces designs is still `experiment`, not
     `design` — `design` means designing the product, `experiment` means measuring a method. -->

**Objective:**

**Why now:**

**Exit criteria:**
- [ ]

**Preserve:**
-

**Do not optimize for:**
-

## Worker handoff (drafted — do not execute before the build command)

<!-- Part of the schema contract. The plan phase drafts the bounded handoff HERE and stops; the build
     command reads it from this heading. Keep the heading text intact. Sections, in order:
     ROLE / DESIGN GOAL / BEHAVIOR IT MUST SATISFY / WHAT "GOOD" AIMS AT / RELEVANT CONTEXT,
     PRESERVE, NON-GOALS / RETURN TO GUIDE. See references/worker-handoff.md. -->

## Open assumptions (unproven — carried, not filed)

<!-- Things this round is proceeding ON but has not established: an unverified fact, a guess about the
     runtime, a premise the objective rests on. They belong here, not in a design record, precisely
     because a record states what is known. One line each: the assumption, what would falsify it, and
     what breaks if it is wrong. When one is settled, it leaves this list — proven, it becomes an
     Insight in the companion of the file it concerns (or the matching root record); disproven, it
     reopens the objective. An assumption that is still open when the round closes is named in the
     review, never dropped silently. -->

- 

## Open Guide TODO

<!-- Unresolved loop concerns the Guide still owns — intended outcomes, not editing actions. Transient.
     Prefer the host's native task tool when available. -->

- [ ]

## Last evaluated result

<!-- met | partially_met | invalidated | blocked, with brief evidence. -->
