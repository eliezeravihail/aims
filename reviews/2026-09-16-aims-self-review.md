---
title: "aims self-review — foundation for the corrected design"
date: 2026-09-16
---

# aims self-review

This is a full review of aims, run *with aims' own review discipline* (measure, don't grade; every
reading carries a `file:line` citation or a reproduction; no scores). It is the **first record of the
corrected-design branch** (`claude/aims-self-redesign`): the measurement that the redesign is directed
from. aims was built without aims; this document is the honest measurement of what that produced,
before the corrected round begins.

**Method.** Four independent reviewers ran in parallel over four axes — the method (skills + commands),
the machinery (the two Python tools + install), the evidence base (the experiments vs. the claims), and
doc/tree coherence. Machinery and evidence findings were then **reproduced by hand** before being relied
on (aims' own rule: a reviewer's reading is confirmed, not trusted). Line numbers are as of commit
`b6f1f3e`.

The review is in two parts. **Part I** is the two mechanisms the redesign treats as its core — the
staged planning with correct objectives, and the execution reviewed at the abstraction level of the
current phase — each asked the two questions: *is it implemented completely?* and *is it correct?*
**Part II** is the system-wide findings that frame them.

---

# Part I — The two core mechanisms (the heart of the corrected design)

## 1. Staged planning with correct objectives

**What it is.** The PLAN phase's opening round runs three advisor planners in parallel, each optimizing
one fixed quality axis in isolation (clean code / correct encapsulation / correct genericity), and a
master planner composes their strengths into one design + Worker handoff
(`skills/aims-guide/references/panel-plan.md:48-63`). This is the "staged" (מדורג) planning.

### Is it correct? — Partly. The staging is sound; the *objective* it emits is not disciplined.

The staging half is genuinely correct and non-trivial:
- **Independence is an invariant, not a hope** (`panel-plan.md:66-68`): sequential passes in one shared
  context are excluded outright, because a later advisor cannot unsee an earlier one.
- **The compose step names its failure modes** (`panel-plan.md:53-63`): winner-picking, union, and
  averaging each fail by name — a real mechanism, not "merge well".
- **It declines honestly** (`panel-plan.md:86`) when no isolation facility exists, rather than faking
  independence.

But the mechanism optimizes toward a good **design**, and then *assembles an objective as an
afterthought*. `panel-plan.md`'s master procedure runs six steps — read, harvest, compose, glue,
subtract — and only at step 6 (`panel-plan.md:110`) does the objective appear at all: *"Assemble the
round's single objective + Worker handoff."* A grep of the entire reference confirms it: **the words
"exit criteria", "adversarial", "falsifier", "hard decision", "Kind", and "objective-selection" never
appear in `panel-plan.md`** (verified — the grep returns nothing). Yet those are precisely what aims
defines as a *correct objective*:
- the objective is a **design outcome**, with the behavior as a constraint, never a feature ticket
  (`SKILL.md:451-456`);
- it carries **adversarially-derived exit criteria** — the edge and break cases named as a bug-hunter
  would, so a minimalist build cannot satisfy it on paper (`SKILL.md:389-399`);
- it puts the **hard decision at its core** — "if the best the objective can say is 'design it well',
  it is not yet an objective" (`SKILL.md:401-404`).

So the staged mechanism guarantees a strong *design* and leaves the *objective* — the thing aims'
entire thesis says is what actually steers the Worker — to a one-line "assemble" with no stated bar.
The mechanism could produce a beautifully merged design behind a mushy objective, and nothing in
`panel-plan.md` would catch it. **This is the sharpest gap in mechanism 1: the staged planner uses
correct *axes* but does not use *correct objectives* — the two are not the same thing, and the
reference never bridges them.**

### Is it complete? — No, on two counts.

1. **The objective-quality discipline reaches the mechanism only in stepped mode, by luck of routing.**
   The command `commands/aims-panel-plan.md:7,19-20` *does* reference `objective-selection.md` and
   require declaring the Kind. But in **auto** mode the panel is convened directly from `SKILL.md:353`
   (step 2) with no command in the path, so the only thing carrying the objective-quality bar is the
   surrounding step-2 prose — not the mechanism. The reference that *owns* the mechanism
   (`panel-plan.md`, per `decisions/0006`) is silent on it. A mechanism whose correctness depends on
   which entry path reached it is not completely specified.

2. **The advisors optimize axes that overlap the review, but nothing connects the two.** The three
   planning axes (`panel-plan.md:33-44`) and the three review lenses (`review-panel.md:25-52`) are
   different partitions of "good", authored separately. `decisions/0005:73-77` even admits the shipped
   axis trio was *swapped in after* the experiment that validated the protocol, "at the cost of somewhat
   less built-in opposition between advisors" — i.e., the very diversity the staging exists to produce
   was knowingly reduced, and never re-measured (see Part II, evidence).

**Verdict on mechanism 1:** the staging is correct and well-built; the "correct objectives" half is
under-specified — the reference emits an objective without the exit-criteria / hard-decision / Kind
discipline that defines a correct one. Incomplete.

## 2. Execution, reviewed at the abstraction level of the current phase

**What it is.** Every objective declares a **Kind — design | implementation | refactoring**
(`review-panel.md:18`), and the review measures the result through the lens for that kind: a `design`
result on whether the structure is right (*not* tests), an `implementation` on correctness and
conformance, a `refactoring` on behavior-preservation (`review-panel.md:25-52`). This *is* "a review
that matches the abstraction level of the current phase" — and it is the single best idea in aims.

### Is it correct? — The idea is; the evidence rule contradicts it at the design level.

The Kind→lens mapping is a real mechanism: it gives the review a typed question it cannot dodge, and
`review-panel.md:53-55` correctly makes a Kind/deliverable mismatch the *first* reading. That part is
right.

But the rule that makes a reading count collides with the design lens. `review-panel.md:57-66`: *"Every
reading carries either a reproduction … or a precise **code citation** — `file:line` … A reading
without a reproduction or a citation is not a measurement — drop it."* Yet the design lens explicitly
covers a deliverable with **no runnable code**: `review-panel.md:30-31`, *"design reasoning and
fit-to-forces — **not** tests (a design objective may have no runnable code)."* On a greenfield first
design — the round aims cares most about (`SKILL.md:92`, the first objective of a new product is exactly
this) — there is no code to reproduce and no `file:line` to cite. Taken literally, every reading must be
dropped, and `review-panel.md:146` then blesses the empty set as "a valid, honest measurement." The
phase-matched review at the *design* abstraction level is told to *measure the shape* and simultaneously
told that only *code-level evidence* counts. The two instructions cannot both hold. (In practice one
cites the design document's own `file:line`; the rule's wording never says a design artifact counts as
a citable surface — so the fix is real but small.)

### Is it complete? — No: a declared Kind has no lens, and the loop can't record a review's own outcome.

1. **The `experiment` Kind has no review lens.** `assets/state-template.md:38-42` defines a *fourth*
   Kind, `experiment`, and points at `../../experiments/PROTOCOL.md` — but `review-panel.md` defines
   lenses for exactly three, and `commands/aims-review.md:8-11` tells the reviewer to "take that kind's
   lens." For `experiment` there is none. (The path is doubly broken — from `assets/`, `../../` resolves
   to `skills/experiments/`, which does not exist; in an installed project no `experiments/` exists at
   all. This is the dogfood-leak class `CLAUDE.md` warns about.)

2. **The review command never records the outcome the loop is designed around.** `modes.md:56` says
   review "parks at `reviewed:awaiting-decision`", but `commands/aims-review.md:19-21` only ever writes
   `ready-to-choose-next` or back toward `plan`/`build` — `reviewed:awaiting-decision` is written by no
   command, and two of the four defined outcomes (`invalidated`, `blocked`, `SKILL.md:504-505`) have no
   cursor value to park at (`modes.md:84-92`). The phase-matched review can reach a conclusion the loop
   has nowhere to store.

**Verdict on mechanism 2:** the phase-matched lens is aims' best idea and is correctly conceived; but
it is incomplete — the design-level evidence rule contradicts the design lens, one declared Kind has no
lens, and the review's own outcomes have no home in the cursor.

---

# Part II — System-wide findings

These frame the two mechanisms and must be fixed alongside them. Ordered by consequence.

## Evidence — the most damaging gap, and it is a documentation gap, not a research one

The experiments were run with unusual honesty (see "What holds up"). The failure is that the **public
surface does not tell the truth the experiments recorded.**

- **The README tells a prospective user the central test was never run.** `README.md:215`: the
  aims-vs-OpenSpec pilot is "**planned, not yet run**." On disk it *was* run: `results.md:7` "This pilot
  was **executed**"; `decisions/0007:43` "**Do not claim a design-quality advantage for aims**"; the
  design reading placed aims **third of three** under both judges (`results.md:14`). README suppresses,
  by omission, the one direct blind test of aims' central claim — and that it came back negative.
- **The newest evidence points at a file that does not exist.** `goals.md:56-57` and
  `results-v3.md:3-4` retire the v3 result as flawed, "superseded by the isolated re-run,
  `results-v4.md`." `results-v4.md` **does not exist** (verified: `ls` fails; git shows it was never
  added). The current headline evidence is self-flagged invalid and its replacement is vapor.
- **The winning v3 run has no artifacts.** The commit that added v3 added exactly one file, a summary
  (`c610330`). No designs, no judge reports, no sealed mapping — so v3 is not an auditable pilot, and
  every v3-derived sentence in `goals.md:44-49` is currently unbacked.
- **The one fully-auditable pilot (`aims-vs-openspec` v1) found no advantage for aims** — third place,
  most structural churn of three arms, a pre-registered falsifier fired, and a plain "design it well"
  agent matched both methods with no machinery (`results.md:14-18,118-124`).

Honest current state: there is **no positive blind evidence in this repo that aims beats no-method on
design quality**; the one clean test found the opposite; the one apparent win (v3) is unbacked and
self-retired to a missing file. The narrow, real payoff the project already claims honestly is the
append-only trail of *why a superseded decision no longer holds* (`decisions/0007:64-79`).

## Machinery — two self-declared invariants are false right now

- **"The hook never blocks; fail-open" is false.** `architecture.md` states the read hook is advisory
  and fail-open. Reproduced: `echo 'null' | python3 knowledge/staleness_hook.py` → `AttributeError`,
  **exit 1**. Three lines (`staleness_hook.py:89,93,94`) sit outside the `try` that begins at `:97`. Any
  change to the hook's input envelope turns every `Read` into a visible error.
- **"Anchor every companion on filing" is violated by the repo itself.** Reproduced with aims' own
  tool: both companions are stale — `anchor.py.md` stamped `d88e8bd5…` vs actual `c85ed064…`;
  `staleness_hook.py.md` stamped `cada8bdb…` vs actual `a73ef226…`. The entire dogfood sample of the
  anchor discipline (n=2) is 100% stale, and no test checks the repo's own companions.
- **The dogfood trap is live inside the shipped tool.** `anchor.py:17` and `knowledge/format.md:61`
  print `python3 knowledge/anchor.py` — a path that does not exist in an installed project (the tool is
  copied to `.aims/`). The guard that exists for exactly this (`tests/install-wiring.sh:25`) scans
  `skills commands templates` but **not `knowledge/`**, the directory holding the copied files.
- **Relative hook paths die silently from a subdirectory** (`templates/settings.json.tmpl:6,14`): both
  hooks fail with exit 0 if Claude launches from anywhere but the repo root — drift-checking off, no
  signal.

## Method — contradictions and unreachable surface

- **"accept" vs "does not accept".** `review.md:35` — the subtractive pass "is mandatory before you
  **accept** a design"; `review-panel.md:141,144` — the review "**does not accept or reject** … no
  accept/reject stamp." Sibling files, opposite verbs.
- **Advertised controls that do not exist.** `"aims next"` is called "the first-class control"
  (`SKILL.md:209`) but no command implements it; an `auto` phase command is listed (`modes.md:57`) with
  no file behind it. Verified.
- **Dead surface.** `assets/record-templates.md` (81 lines) is referenced by nothing (verified grep).
- **The 'never coerce' philosophy vs. the gates actually written.** `SKILL.md:55-66` — "It does **not**
  coerce. There is no enforcement pillar." The method is in fact full of hard gates
  (`SKILL.md:362-370`, `discovery.md:6`, `review-panel.md:114`). The honest framing is "gates on the
  Guide, never on the Worker" — which the text does not say.
- **Restatement the project's own doctrine forbids.** The substrate gate, load-bearing assumptions, "an
  agent optimizes the goal you give it", and the subtractive pass are each stated 3–4 times across
  files (`SKILL.md:343-377` ≈ `discovery.md:103-128` ≈ `design-principles.md:205-225`, etc.), with no
  single owner — the exact shape `design-record.md:42-44` bans in records.

## Docs vs. tree — the append-only trail broke

- **`decisions/0007` is the newest ADR, its headline is overturned, and nothing points forward.** It
  records "no advantage for aims"; `goals.md:44-46` says later runs reversed that; no `decisions/0008`
  supersedes it. A session navigating the ADR trail — the discipline aims sells — inherits a dead
  verdict as current.
- **Mandated root records missing.** No `base-dependencies.md`, no `dependencies.md`, though
  `SKILL.md:83` and every plan command order them filed. aims silently violates its own day-zero rule.
- **The newest feature is invisible.** `/aims-panel-plan` is absent from `README.md`,
  `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, and `SKILL.md`.
- **Stale frontmatter dates** on both root records (`goals.md:3`, `architecture.md:3`), which
  `knowledge/format.md:32` makes half the frontmatter contract.

---

# Part III — What genuinely holds up

Naming this matters as much as the faults; the corrected design must *keep* these.

- **The Kind→lens mapping** (`objective-selection.md:66-82` → `review-panel.md:25-52`) — a typed review
  the reviewer cannot dodge. The heart of mechanism 2, and correct.
- **The concept-fit pass** (`review.md:60-90`) — catching "value-correct, concept-wrong" (a
  decomposition modelled as a movement) *before* code. The sharpest idea in the repo, and the one
  change the experiments show *caused* a real fault to disappear.
- **The floor/ceiling derivation of interface generality** (`design-principles.md:107-147`) —
  non-obvious and operationally checkable via the swap test.
- **Advisor independence as an invariant, with an honest decline** (`panel-plan.md:66-88`) — the one
  place the mechanism refuses to paper over a limitation.
- **The name-derivation anchor rule** — survived every adversarial input tried (empty, binary, unicode,
  spaces, symlink, directory-as-system-record).
- **The research honesty itself** — `decisions/0007:43` records the method's own central claim failing;
  `results.md:14-18` leads with the loss; operator errors are self-reported. This is rare and must not
  be lost in the correction.

---

# Part IV — What the corrected design is directed at

From the measurement above, in priority order:

1. **Make the staged planner emit a *correct objective*, not just a merged design.** Wire the
   objective-selection discipline (design-as-goal, adversarial exit criteria, the hard decision, Kind)
   into `panel-plan.md`'s compose/assemble step, so the mechanism — not the entry path — guarantees it.
2. **Reconcile the phase-matched review's evidence rule with the design lens** (a design artifact is a
   citable surface), and give the `experiment` Kind a lens or remove it; give the review's own outcomes
   a cursor home.
3. **Tell the truth on the public surface** — README, and a `decisions/0008` that supersedes `0007`; or
   run the promised `results-v4.md`. This is a claim made to users and is the most damaging gap.
4. **Restore the two false invariants** — wrap the hook's pre-`try` lines and widen the fail-open guard
   to the input envelope; re-anchor the two companions and add a test that fails when the repo's own
   companions drift; extend `install-wiring.sh` to `knowledge/`.
5. **Resolve the method contradictions** — accept vs. not-accept; delete or implement `aims next`,
   `auto`, and `record-templates.md`; state the "gates on the Guide, not the Worker" framing plainly;
   give each restated rule one owner.

The through-line: aims' *ideas* are strong and several of its mechanisms are genuinely well-built. The
corrected design is not a rewrite of the thesis — it is closing the gap between what aims does and what
aims says, starting with the two mechanisms at its core.
