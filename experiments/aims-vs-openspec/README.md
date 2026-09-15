# Pilot — aims vs. OpenSpec (three arms, blind-judged) · **planned, not yet run**

A **build pilot** under [`../PROTOCOL.md`](../PROTOCOL.md), with one deliberate extension: the control is no
longer a single method-less arm but **two** comparators — a rival method (**OpenSpec**) and a plain arm.
This file is the frozen experiment package (PROTOCOL §1). Nothing in `cards/`, `hidden/` or `starter/` may
be edited once the first agent runs; [`results.md`](results.md) is written afterwards.

---

## 0. Why this comparison is not obvious — and what it is actually measuring

aims and OpenSpec are both "a method layered on a capable coding agent", and both leave durable artifacts
behind. They are **not competitors on the same axis**, and a pilot that pretends otherwise would produce a
rigged number:

| | aims | OpenSpec |
|---|---|---|
| What it makes the explicit goal | the **quality of the design/architecture**, at the design stage | **agreement on what to build**, before code |
| The durable layer | design rationale **co-located with the code** (a companion beside each source file; root `goals`/`architecture`/`decisions`) | behavioral **requirements + scenarios** in `openspec/specs/`, capability-indexed and central; per-change `proposal.md` / `design.md` / `tasks.md`, archived by date on `/opsx:archive` |
| Indexed by | the file you are about to edit | the capability whose behavior you are about to change |
| What a later session inherits | *why this seam is shaped this way, and what it enforces* | *what this capability must do, and the scenarios that pin it* |

So the pilot does **not** ask "which method wins". It asks three separate, separately-judged questions, one
of which is each method's own home claim, and it is designed so that **"each wins its home reading"** is a
distinguishable — and entirely publishable — outcome:

> **R1 — direction (aims' home claim).** After an evolution nobody stated up front, is the aims arm's final
> **architecture** better than the OpenSpec arm's and the plain arm's?
>
> **R2 — requirement fidelity (OpenSpec's home claim).** Does the product actually do everything that was
> asked, across all three stages — including the stage-1 and stage-2 behaviors **after** stage 3 rewrites
> the pricing path? Is each revealed requirement pinned by something (a test, a scenario) rather than
> merely implemented?
>
> **R3 — continuity (both claim it, differently).** Does a **fresh session with no history** continue
> correctly by navigating its arm's durable layer — reading the prior conclusion and building on it — rather
> than re-deriving it or tearing the seam open?

Cost is recorded as a fourth, verdict-free reading. **The four are never merged into one score** (PROTOCOL
§7).

### The plain arm is load-bearing, not a courtesy

The [instance-seg pilot](../instance-seg-annotator/results.md) found no gap between method and no-method
because a strong executor independently made the one decision that mattered. Without a plain arm here, an
aims/OpenSpec tie would be unreadable: *both methods work equally well* and *neither method does anything
the model would not have done alone* look identical. The plain arm is what separates them.

## 1. The product and the single axis

**A checkout pricing service.** Small, deterministic, fully testable, no UI, no network, no model calls.

The one architectural axis its evolution stresses:

> **Who owns the composition of a price** — the ordered application of adjustments to a list price, and
> the single place where money is rounded.

A stage-1 design may quite reasonably return a price as an opaque number computed inline. That choice is
**not wrong on the evidence available at stage 1** — it is the latent decision the feature framing glosses
over, which is exactly the condition the prior pilots identified as necessary for any gap to appear at all.
Stage 2 (explain every price, adjustment by adjustment, with deltas that must sum exactly) and stage 3 (a
second market with a different tax model and a different rounding rule) are what falsify it.

## 2. The staged reveal

Three stages. **Only the current card is visible**; the next is revealed only after all three arms close the
current one. No card hints that a later stage exists (PROTOCOL §1.2).

- **Stage 1** — [`cards/stage-1.md`](cards/stage-1.md): price a cart. Line amounts, a cart total, three
  kinds of promotion. *Nothing suggests anything else is coming.*
- **Stage 2** — [`cards/stage-2.md`](cards/stage-2.md): **explain** every price — the ordered adjustments
  that produced it, each with its exact money delta, summing precisely; plus non-stackable promotions,
  where the superseded one must still appear in the explanation.
- **Stage 3** — [`cards/stage-3.md`](cards/stage-3.md): a **second market** — tax-inclusive listed prices,
  per-line tax reporting, a different rounding mode — while every stage-1 and stage-2 behavior still holds
  for the first market.

The hidden staged spec and the oracle's canonical answers are in
[`hidden/spec-and-oracle.md`](hidden/spec-and-oracle.md). No agent sees that file, ever.

**Why three stages and not two.** The instance-seg pilot's own finding was that a one-step evolution that
falsifies nothing collapses the gap. Stage 2 applies pressure; stage 3 is where it accumulates, and it is
also the only stage that can test R2's regression half.

## 3. The three arms

| | **aims arm** | **OpenSpec arm** | **plain arm** |
|---|---|---|---|
| Prompt | the identical stage card **+ one line**: "follow the `aims-guide` skill" | the identical stage card **+ one line**: "use OpenSpec for this work" | the identical stage card **+ one line**: "build it well" |
| Method loop | Guide selects a design objective → Worker → measure → files **co-located records** | `/opsx:propose` → review → `/opsx:apply` → `/opsx:archive`, per stage, exactly as OpenSpec's own docs prescribe | none; one capable agent, free to plan, inspect, code, test and refactor as it likes |
| Durable layer it may consult later | companions + root records | `openspec/specs/` + archived changes | the code and its tests only |
| Right to ask | yes — one material product question at a time, to the oracle | same channel, same right, same oracle | same channel, same right, same oracle |

**Stages 2 and 3 are run by a fresh session in every arm** (PROTOCOL §2), given the repository, its durable
layer, and the stage card — and told to consult that layer, but **never told where the seam is**. That a
fresh session finds it by navigation is the R3 result. The plain arm's fresh session gets the code alone;
that is its honest condition, not a handicap.

The extra reasoning a method arm spends **is its treatment**. Record cost; never equalize it, and never feed
any arm a hint the others did not get.

## 4. Controlled variables, pins, and the two contamination risks

Held constant (PROTOCOL §3): model + version, reasoning/effort setting, tool and permission set, a fresh
empty repository per arm, the identical starter substrate, the exact stage cards, the oracle's verbatim
answers, the test/runtime environment, one equal time/cost ceiling per arm, and no access to any later-stage
file before the current stage is closed.

**Pins to record in `results.md` before the first run** — a pilot whose pins you cannot name is not
reproducible:

- the **aims** commit SHA the aims arm ran under (`git rev-parse HEAD`);
- the **OpenSpec** version (`npm ls -g @fission-ai/openspec`, installed with `@latest` at pin time) and the
  Node version;
- the **model id** and effort level, identical across arms;
- the date.

Two contamination risks are specific to this pilot and must be actively prevented:

1. **aims is installed in this repository.** Every arm runs in its **own fresh repository outside the aims
   tree**. The OpenSpec and plain arms must have no aims plugin, skill, hook, `CLAUDE.md` or record in
   context; the aims arm must have no `openspec/` directory and no OpenSpec commands. Verify by listing the
   loaded skills/plugins at the start of each run and pasting that listing into the arm's log.
2. **Operator fluency is asymmetric.** The operator knows aims and does not know OpenSpec. Run the OpenSpec
   arm **strictly as its own documentation prescribes**, through its own slash commands, with no
   aims-flavored improvement, no hand-editing of `openspec/` files the tool would have written, and no
   coaching. If the OpenSpec loop is run in a degraded way, the R1 reading is worthless. Log every OpenSpec
   command invoked, verbatim.

## 5. Oracle policy

[`../PROTOCOL.md` §4](../PROTOCOL.md) applies unchanged and strictly: answer only from the **current**
stage's hidden facts; volunteer nothing; never reveal a later-stage requirement ("will there be X later?" →
*"not now — build for today"*); for a technical choice an ordinary buyer would not make → *"I don't know;
choose a simple sensible technical approach"*; word every answer neutrally — one leak word (*"still"*,
*"yet"*, *"for now"*) disqualifies the run; log every question and the verbatim answer, and give any arm
that asks the same question **the same answer, word for word**.

The canonical answers are pre-written in [`hidden/spec-and-oracle.md`](hidden/spec-and-oracle.md) precisely
so that the operator is not improvising under time pressure.

## 6. Judging — four readings, four separate judges, never merged

Judges are **not** the sessions that built any arm (PROTOCOL §6). Rubrics and the exact judge prompts are in
[`judging/rubrics.md`](judging/rubrics.md).

**Anonymization is harder here than in a two-arm aims pilot, because every arm has a tell.** The R1 judges
receive **code-only snapshots** — `.aims/`, companions, root records, `openspec/`, `CLAUDE.md`, `AGENTS.md`,
`.claude/`, git history and commit messages stripped from **all three** arms — relabelled **X / Y / Z** in an
order the judges are not told. A judge that can name the method has not judged blind.

- **R1 — design.** Two **opposite-disposition** judges (invariant-ownership vs. YAGNI/simplicity) read the
  same three snapshots against [`design-principles.md`](../../skills/aims-guide/references/design-principles.md)
  and [`review.md`](../../skills/aims-guide/references/review.md). A verdict must turn on a **structural**
  property — *can the set of adjustments be extended without editing the total calculation? is rounding one
  owner or N? does the explanation derive from the same structure that computes the price, or is it a second
  implementation that can disagree?* — never on a removable local blemish, and "small is not unearned".
  Every load-bearing claim carries a reproduction or a `file:line`.
- **R2 — requirement fidelity.** A black-box judge, given only the three stage cards and the hidden final
  probes, never the method label: run the probes against each arm, including the **stage-1 and stage-2
  probes re-run after stage 3**. Then a coverage reading: for each revealed requirement, name the artifact
  that pins it (a test, a scenario) or record that nothing does.
- **R3 — continuity.** Per arm, from the fresh stage-3 session's transcript and diff: did it **read a
  specific durable artifact and cite it** before touching the pricing path, and does the diff **reuse** the
  composition seam rather than reopen it? Three outcomes per arm: *navigated and built on it* / *re-derived
  the same conclusion independently* / *contradicted or tore open the prior conclusion*. For the plain arm
  the question is whether the code alone sufficed.
- **R4 — cost.** A recorder: tokens, turns, wall-clock, model calls, dependencies added, per arm per stage.
  No quality verdict.

**Verify the judge, don't trust it** (PROTOCOL §6.4): re-run every arm's suite independently before
believing any "tests pass", and reject any claim without a reproduction or a `file:line`.

### The rubric-symmetry problem, stated plainly

R1 judges against **aims' own** design principles. In an aims-vs-clean pilot that is fair — it is aims' own
claim, judged blind. Against a rival method it is a **house-rubric bias**, and this pilot does not pretend
otherwise. Two things offset it, and neither fully removes it:

- **R2 is scored on OpenSpec's own standard** — requirement coverage and scenario fidelity — so each method
  is measured against its own claim as well as the other's.
- The R1 verdicts must be **structural and reproducible**, so a reader who rejects aims' principles can still
  check the finding ("rounding happens in four places" is true or false regardless of rubric).

Recorded as a declared limitation in `results.md`, not as a solved problem.

## 7. Falsifiers — fixed in advance

The pilot is worth running only because these outcomes are possible, and each would be reported as found:

- **The plain arm matches both methods on R1** → on a product this size, method does not pay; the honest
  reading is that the executor is strong enough alone, exactly as the instance-seg pilot found.
- **The OpenSpec arm matches the aims arm on R1** → making design the explicit goal adds nothing that
  spec-first discipline does not already deliver. This is the single most informative result for aims.
- **The aims arm loses R2** → design focus costs requirement fidelity; a real, reportable trade-off.
- **The aims arm's fresh stage-3 session does not cite a companion** → the continuity claim is unsupported
  for this product, whatever the code looks like.
- **Both methods lose R3 to the plain arm** → the durable layers are overhead the code did not need.

## 8. Protocol deviations, declared

Per PROTOCOL's own rule that an experiment must instantiate it or **say which part it waives and why**:

1. **Three arms instead of two.** An added rival-method arm; the clean arm is retained as the plain arm.
   Justified in §0.
2. **Four readings instead of three.** PROTOCOL's design/product/cost becomes design/requirement-fidelity/
   continuity/cost — continuity is promoted from a Q2 sub-check to a first-class per-arm reading because,
   with two durable layers of different shapes, it is the reading that actually discriminates them.
3. **The R1 rubric is aims' own**, with the bias declared and partly offset (§6).
4. **n = 1 per arm.** Suggestive, not robust (PROTOCOL §7); the strength is the sequence of pilots, not this
   one. No skill-wording change is under test here, so the n ≥ 2 rule for wording changes does not apply.

## 9. Artifacts to keep

Per PROTOCOL §8, and per arm: the three stage cards as delivered, the oracle Q&A log, a `stage-N` tagged
commit per stage, the cost log, the loaded-skills/plugins listing, the anonymized X/Y/Z snapshots, the
verbatim OpenSpec command log, the fresh-session transcripts for stages 2 and 3, and the four judge reports
— each finding carrying a reproduction or a `file:line`.

## 10. Status

**Planned. Not run.** [`results.md`](results.md) is a stub until the package above has been executed
end-to-end; it must not be filled in from expectation.
