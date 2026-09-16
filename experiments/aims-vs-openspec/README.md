# Pilot — aims vs. OpenSpec, on the architecture only (planned, not yet run)

**Nothing is built in this pilot.** Each arm produces a **design** — the architecture of the product,
in prose — and it is the designs that are compared. No implementation, no test suite, no running code.

A pilot under [`../PROTOCOL.md`](../PROTOCOL.md), with the deviations of §7 declared. The package here is
frozen: `cards/`, `hidden/` and `substrate.md` may not be edited once the first arm runs.
[`results.md`](results.md) is written afterwards.

---

## 0. What is being compared, and why it is not obvious

Both are methods laid over a capable agent, and both leave documents behind. They aim at different things:

| | aims | OpenSpec |
|---|---|---|
| The explicit goal | the **quality of the design** — the architecture is what is being optimized | **agreement on what to build**, before code |
| What it writes down | design rationale, beside the code it describes (a companion per file; root `goals` / `architecture` / `decisions`) | behavioral **requirements and scenarios** in `openspec/specs/`, plus a per-change `proposal.md`, `design.md` and `tasks.md` |
| Indexed by | the file you are about to change | the capability whose behavior you are about to change |
| What a later session inherits | *why this seam is shaped this way, and what it enforces* | *what this capability must do, and the scenarios that pin it* |

Both produce a design document without writing code — OpenSpec's `/opsx:propose` emits `design.md`, aims'
plan phase emits an architecture. So a design-only comparison is fair to both, and it isolates the thing
aims actually claims.

Three questions, judged separately and **never merged into one score**:

> **Q1 — is the architecture better?** Read blind, against structural criteria.
>
> **Q2 — does it survive?** When a requirement nobody stated arrives, how much of the earlier architecture
> stands, and how much has to be torn open? This is the measurement the pilot is built around.
>
> **Q3 — does a fresh session continue from what was written?** With no memory of the earlier round, does
> it navigate the arm's documents and build on the prior conclusion, or re-derive it?

## 1. Why Q2 is the heart of it

Judging two prose designs on "which is nicer" is soft and rubric-dependent. Q2 is not: it is **countable**.

Each arm produces three designs — one per stage. For each arm we compare its stage-2 design against its
stage-1 design, and its stage-3 against its stage-2, and classify every named component and seam:

| Class | Meaning |
|---|---|
| **survived** | present, unchanged, still doing the same job |
| **extended** | present, unchanged in responsibility, given more to do at an existing seam |
| **reopened** | its responsibility or its boundary changed |
| **discarded** | gone |

The reading is the **reopened + discarded count**, with each instance named. A design that anticipated the
right seam extends; one that did not, reopens. This does not depend on anyone's taste, and either method can
win it.

## 2. The product and the single axis

**A checkout pricing service.** No UI, no network, no persistence — so the design is about structure and
nothing else.

The axis its evolution stresses:

> **Who owns the composition of a price** — the ordered application of adjustments to a list price, and the
> single place money is rounded.

At stage 1 an opaque price computed inline is a perfectly reasonable design; nothing visible argues against
it. That is the latent decision. Stage 2 and stage 3 are what falsify it.

## 3. The three stages

Only the current card is visible. No card hints that another stage exists.

- **Stage 1** — [`cards/stage-1.md`](cards/stage-1.md): price a cart; three kinds of promotion.
- **Stage 2** — [`cards/stage-2.md`](cards/stage-2.md): **explain** every price — the ordered adjustments,
  each with its exact money delta, summing precisely; and non-stackable promotions, where the superseded
  one still has to be reported.
- **Stage 3** — [`cards/stage-3.md`](cards/stage-3.md): a **second market** — tax-inclusive listed prices,
  per-line tax reporting, a different rounding rule — while the first market keeps behaving exactly as
  described in stages 1 and 2.

The staged spec and the oracle's pre-written answers are in
[`hidden/spec-and-oracle.md`](hidden/spec-and-oracle.md). No arm ever sees that file.

Three stages and not two: a single evolution that falsifies nothing leaves nothing to measure — the finding
of the [instance-seg pilot](../instance-seg-annotator/results.md). Stage 2 applies the pressure; stage 3 is
where it accumulates.

## 4. The three arms

Each arm gets the identical card plus one line, and the standing instruction below.

| | **aims arm** | **OpenSpec arm** | **plain arm** |
|---|---|---|---|
| The added line | "follow the `aims-guide` skill" | "use OpenSpec for this" | "design it well" |
| What it runs | the plan phase — objective, design, records | `/opsx:explore` then `/opsx:propose`, exactly as OpenSpec's docs prescribe | nothing; one capable agent designing as it sees fit |
| The deliverable | an architecture document | the change's `design.md` (+ whatever `/opsx:propose` writes) | an architecture document |
| What it may consult at the next stage | its companions and root records | `openspec/specs/` and its archived changes | its own earlier design document |

**The standing instruction, identical for all three arms:**

> Design only. Produce the architecture: the components, their responsibilities, the seams between them,
> the rules each one owns, and the reasoning. Do not write implementation code. A type signature, an
> interface sketch or a small illustrative snippet is fine where it makes a boundary concrete; a working
> implementation is not.

**Stages 2 and 3 are run by a fresh session in every arm**, given the arm's documents and the new card, told
to consult those documents — and never told where the seam is. That a fresh session finds it by navigating
is the Q3 result.

The plain arm is not a courtesy. Without it, aims and OpenSpec coming out level is unreadable: *both methods
work* and *neither method is doing anything the model would not do alone* look identical. The plain arm is
what separates them.

## 5. Held constant, and the two contamination risks

Identical across arms: model and version, effort setting, the [substrate](substrate.md), the exact cards,
the oracle's verbatim answers, one equal ceiling per arm, and no sight of a later card before the current
stage closes.

**Pins, recorded before the first run:** the aims commit SHA; the OpenSpec version and Node version; the
model id and effort level; the date. A pilot whose pins cannot be named is not reproducible.

1. **aims is installed in this repository.** Each arm runs in its own directory outside the aims tree. The
   OpenSpec and plain arms must have no aims plugin, skill, hook, `CLAUDE.md` or record in context; the aims
   arm must have no `openspec/`. Paste each session's loaded-skills listing into that arm's log.
2. **Operator fluency is asymmetric** — the operator knows aims and not OpenSpec. Run the OpenSpec arm
   strictly through its own commands, with no aims-flavoured improvement and no hand-editing of what the
   tool writes. Log every command verbatim. A degraded OpenSpec arm makes Q1 worthless.

## 6. Oracle

[`../PROTOCOL.md` §4](../PROTOCOL.md) in force: answer only from the current stage; volunteer nothing; never
reveal a later requirement; neutral wording — one leak word disqualifies the stage; log every question and
answer; the same question from another arm gets the same answer word for word. The answers are pre-written
in [`hidden/spec-and-oracle.md`](hidden/spec-and-oracle.md) so the operator never improvises.

## 7. Judging

Judges are not the sessions that produced any design. Prompts and criteria:
[`judging/rubrics.md`](judging/rubrics.md).

Every arm has a tell, so all three are stripped identically — method names, directory names, file headers,
provenance, commit messages — and relabelled **X / Y / Z** in an order the judges are not told. A judge that
can name a method has not judged blind.

- **Q1 — architecture.** Two opposite-disposition judges (invariant-ownership vs. YAGNI) read the three
  stage-3 designs against [`design-principles.md`](../../skills/aims-guide/references/design-principles.md).
  Verdicts must turn on a structural property answered **from the design text**, with a quotation.
- **Q2 — survival.** The countable reading of §1, done per arm across both transitions, each reopened or
  discarded component named and quoted from both versions.
- **Q3 — continuity.** From the fresh session's transcript: did it read a specific document and cite it
  before changing the design, or not?
- **Cost.** Tokens, turns, wall-clock, model calls. No quality verdict.

**The rubric problem, stated plainly.** Q1 judges against aims' own design principles — a house rubric,
against a rival method. Two things offset it and neither removes it: **Q2 is rubric-free** (a count, not a
judgment) and is the reading the pilot is built around; and Q1 verdicts must be structural and quotable, so
a reader who rejects aims' principles can still check the fact. Recorded as a limitation in `results.md`,
not as a solved problem.

**And the one that cannot be offset:** a design is prose. A method that produces *more* prose can look more
thorough without being better. Q2 is the defence — volume does not help you when the count is of seams that
had to be reopened — but a Q1 judge should be told explicitly that length is not a merit.

## 8. Falsifiers, fixed in advance

- **The plain arm's designs survive as well as both methods'** → on a product this size, method does not
  pay.
- **The OpenSpec arm matches aims on Q1 and Q2** → making design the explicit goal adds nothing that
  spec-first discipline already delivers. The most informative possible result for aims.
- **The aims arm reopens more than OpenSpec** → the central claim fails on this product.
- **The fresh aims session never cites a companion** → the continuity claim is unsupported here.

## 9. Deviations from PROTOCOL, declared

1. **No build.** PROTOCOL assumes both arms build a product and the final architecture is judged. Here the
   architecture is the deliverable itself. The product reading (behavior, acceptance) is therefore **not
   available** and is not reported — this pilot cannot say anything about whether either method ships
   working software.
2. **Three arms instead of two.**
3. **Survival (Q2) replaces the built-code reading** as the primary evidence, because it is countable where
   a prose comparison is not.
4. **The Q1 rubric is aims' own**, bias declared and partly offset.
5. **n = 1 per arm.** Suggestive, not robust; strength is in the sequence of pilots.

## 10. Artifacts to keep

Per arm: the three designs as delivered, the oracle Q&A log, the loaded-skills listing, the fresh-session
transcripts for stages 2 and 3, the verbatim OpenSpec command log, the anonymized X/Y/Z designs, the
survival tables, and the judge reports — each claim carrying a quotation.

## 11. Status

**Run once, 2026-09-15/16.** See [`results.md`](results.md) for the four readings and the full run under
[`run-log/`](run-log/) (oracle logs, cost, the operator's notebook, the judge reports, and the blind
X/Y/Z snapshots with their sealed mapping).

Headline: **aims won no reading, but showed no broad quality deficit either.** On the design/code-quality
reading — judged against aims' own twelve-axis `design-principles.md` — the two opposite-disposition
judges *split* (YAGNI → OpenSpec, encapsulation → plain), so there is **no clear design winner**; aims
placed third under both, traced by both judges to one late coupling decision (tax folded into the
explanation chain), while being credited with the least primitive obsession and the most explicit
subtractive pass. On survival aims reopened the most of its own structure (the §8 falsifier fired), about
half of it the same tax decision. On continuity all three arms navigated their prior records rather than
re-deriving, and the plain arm matched both methods with no machinery — aims' record layer earned exactly
one narrow thing: a durable trail of *why* a superseded decision no longer holds. Cost: aims ≈ OpenSpec,
both ~1.3–1.5× the plain arm. n = 1 — suggestive, not robust.

The design reading was **judged twice**: an initial pass on six operator-written seam questions (which
never touched smells / interfaces / encapsulation and over-weighted aims' weakest axis) was discarded and
re-run against `design-principles.md`. Both passes are in `run-log/judge-reports/`; the narrow ones are
marked superseded.
