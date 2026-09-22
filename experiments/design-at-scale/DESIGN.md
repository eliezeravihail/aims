---
title: "Design at scale — does aims produce better design where the right design is not obvious?"
date: 2026-09-22
status: DESIGNED — not run. Frozen at the start of Phase 0; nothing below changes once a run begins.
---

# The idea, in plain terms

aims claims it makes an agent design better. Every test so far used a task small enough that a strong model
found a good design **without** aims, so the claim was never really tested — both arms converged, and a
convergent task cannot tell two methods apart.

This experiment fixes that in two ways:

1. **A real, sizeable codebase and changes that cut across it** — mkdocs, 7,111 lines in 37 files, with
   three staged changes that each break an assumption the code already makes.
2. **A difficulty gate before the real run.** Unaided agents do stage 1 first. If they all produce a good
   design, the task is too easy, it is rejected, and the budget is not spent. Only a task where unaided
   agents sometimes get the design wrong can show whether aims prevents that.

It measures **goal 1 (design)** and keeps **goal 2 (records)** separate by construction (§3).

# 0. Kind and axis

**Build pilot, goal 1**, on existing code (the aims arm runs as `add-feature`). **Axis: a dimension the
pipeline assumes away.** mkdocs builds one language into one tree of HTML pages. Each stage adds something that
assumption cannot absorb without a design decision:

| stage | change | the assumption it breaks | the tempting shortcut (passes tests) |
|---|---|---|---|
| 1 | multi-language content | one language, one tree | run the whole build once per language, or thread `lang` through every function |
| 2 *(hidden)* | correct incremental rebuilds across languages | a page depends only on its own file | patch `--dirty` with special cases per language |
| 3 *(hidden)* | an offline single-file export per language | output is one HTML file per page | a second build path copied from the first |

A stage-1 design that makes language a first-class dimension absorbs stages 2 and 3; one that loops the build
per language pays for it twice more. That is the difference the rubric should see.

# 1. The codebase, pinned

| | |
|---|---|
| repository | `mkdocs/mkdocs`, BSD-2-Clause |
| commit | `2862536793b3c67d9d83c33e0dd6d50a791928f8` (2025-10-20) |
| size | 7,111 source lines in 37 files; 12,013 test lines |
| suite | `python -m unittest discover -s mkdocs/tests -p '*tests.py' -t .` — 725 tests in ~10 s |
| baseline | 4 failures + 2 errors, all environmental (5 localization-catalogue tests, 1 draft-docs test) — pinned in [`hidden/baseline.md`](hidden/baseline.md) |

Verified on the pinned commit: multi-language **content** is not in core (`localization.py` translates theme
labels only); `--dirty` exists but only skips pages whose own file is unmodified; output is hard-wired to one
HTML file per page (`commands/build.py`, `_build_page`).

**Reserve:** `httpie/cli` at `5b604c37c6c67e18e7c3e9aee6c88a8c22b98345` (BSD-3, 10,630 lines in 86 files;
1,028 tests, 33 failing at baseline, all network- or pip-dependent). Used only if mkdocs fails the gate; its
stage cards are written then, before any of its arms run.

# 2. Phase 0 — the difficulty gate (runs first, cheaply)

**Four unaided agents** do stage 1. Their stage-1 code is scored blind on the §0–§14 form (the disjoint-
vocabulary judge alone suffices here).

**The gate passes if unaided designs actually vary:** at least one of the four carries an S3 or S4 structural
finding, **and** at least one carries none. That is, unaided agents sometimes get this design wrong and
sometimes right — the only condition under which a method can show that it helps.

- **Fails because all four are clean** → the task is convergent. Try the reserve. If the reserve also fails,
  **stop and report it as the result**: *even on a real multi-thousand-line codebase with a cross-cutting
  change, a strong model finds the design unaided.* That would itself answer the question — against the
  need for aims' design method on strong models.
- **Fails because all four are flawed** → the task may be unreasonably hard or the card unclear. Revise the
  card once, re-gate once; a second failure stops the experiment.

**These four gate runs are not reused as the control arm.** The task was selected *because* of their spread,
so reusing them would bias the comparison. The control arm is run fresh.

# 3. The arms — three, so the two goals never mix

| arm | stage 1 | stages 2–3 |
|---|---|---|
| **A — aims** | aims, `add-feature` | a fresh aims session, **with** the records the earlier stages filed |
| **B — aims, records withheld** | *the same stage-1 run as A* | a fresh aims session on the **code only** — every record stripped |
| **C — unaided** | a capable agent, "build it well" | a fresh unaided session on the code |

A and B **share each stage-1 run** and branch after it, so they differ in exactly one thing: whether the
records reach the later sessions. This makes the design paired, and it answers the question the campaign kept
tangling:

- **Goal 1 — does the design method produce better design?** → **B vs C.** Neither carries records forward;
  only the method differs.
- **Do records change the design?** → **A vs B.** Reported, but *not* a goal-2 measurement — the design rubric
  cannot see goal-2 value (`goals.md`).
- **Goal 2 — does knowledge that is not in the code survive?** → its own instrument, §5.

Every stage runs in a **fresh session** in every arm, so all three face the same continuity conditions. Each arm
is rooted where this repository is unreachable (it contains the hidden cards).

**n = 3** stage-1 aims runs (each branching into A and B) and **n = 3** C runs.

# 4. Measuring design (goal 1)

**Floor — a gate that earns nothing.** After each stage: every test green at baseline stays green, and the
stage's hidden acceptance probes pass. A failure marks that arm-stage BLOCKED. Passing earns nothing
(`decisions/0021`).

**The measure — §0–§14 scored from the code** (`skills/aims-guide/references/measurement.md`):

- two **opposite-disposition judges** — one weighting invariant ownership, one weighting simplicity and
  YAGNI — and one **disjoint-vocabulary judge** who scores from code properties and may not credit a
  design's self-description (`experiments/PROTOCOL.md` §6);
- judges see the tree and its diff against the pinned base, **with every record and method trace removed**
  (all `.md` files the arm added, `.aims/`, commit messages) — the records are the treatment, not evidence;
- labels X / Y / Z, mapping sealed in `blind/MAPPING-SECRET.txt` before any judge runs;
- every load-bearing finding carries a `file:line` or a reproduction, and is re-checked before it is believed.

**Primary endpoint: the stage-3 grade** — its per-arm mean **and its floor** (the worst of three). The
campaign's evidence is that aims raises the floor; the floor is therefore reported first, not averaged away.
Secondary: the stage-1 grade (the method's first design, before any stage compounds it) and the trajectory
across stages. Whether a stage reopened code a previous stage built is recorded as **corroboration only** —
it is a gameable proxy (`bp13`).

**Judging load:** the full panel at stages 1 and 3; the disjoint-vocabulary judge alone at stage 2.

# 5. Measuring goal 2 — a non-goal that the code cannot hold

The stage-1 card states a **non-goal**, with its reason: *the reader always chooses the language — no automatic
detection or redirection, for a legal requirement in one market.* In code this is an **absence**: there is
simply no detection logic, and nothing records that its absence is deliberate.

The stage-3 card asks, among the export's requirements, that the offline file *open in the reader's own
language when available* — which requires exactly the detection the non-goal rules out. The card does not
mention the conflict.

**Pass:** the stage-3 session surfaces the conflict — asks the product owner, or states it — before or while
implementing. **Fail:** it implements detection silently. A session can learn of the non-goal in only two ways:
from a record (arm A, if aims filed it) or by asking the product owner (any arm). The product owner answers
from [`hidden/oracle.md`](hidden/oracle.md) and never volunteers it.

This is `bp19`'s finding, re-tested on a real codebase at scale.

# 6. Pre-registered predictions and falsifiers

Fixed now; a run is judged against these and nothing chosen afterwards.

| question | prediction | falsified if |
|---|---|---|
| gate | mkdocs passes — at least one of four unaided stage-1 designs has an S3+ finding | all four are clean (then the convergence result above is reported) |
| **goal 1** (B vs C, stage 3) | B's **floor** is above C's, and B's mean exceeds C's by more than C's own range | B's mean ≤ C's mean, **or** B's floor ≤ C's floor |
| goal 1, first design (B vs C, stage 1) | B's floor above C's | B's floor ≤ C's floor |
| records → design (A vs B, stage 3) | no meaningful difference — design is recoverable from the code | reported either way; not a claim about goal 2 |
| **goal 2** (§5) | A surfaces the conflict in ≥ 2 of 3; B and C in ≤ 1 of 3, and only by asking | A's count ≤ B's |

Anything between "supported" and "falsified" is reported as **no clear advantage**, per `PROTOCOL.md` §7. A
design win does not cancel a floor failure, and neither is averaged into a single score.

# 7. Controls

Same model and version, same reasoning setting, same tools and permissions, same equal budget ceiling per
stage, in every arm. The aims commit the run executes under is pinned in `results.md`. The product owner is
strict and passive (`PROTOCOL.md` §4): answers only from the hidden spec for the current stage, volunteers
nothing, never reveals a later stage, and logs every question and its verbatim answer — the same answer, word
for word, to every arm that asks it. No arm sees another's code, reasoning or output. Judges built nothing.

# 8. Phases, cost, and stop rules

| phase | what runs | ≈ tokens | stop rule |
|---|---|---|---|
| 0 — gate | 4 unaided stage-1 runs + 4 judge runs | ~1 M | gate fails twice → stop and report convergence |
| 1 — first design | 3 aims + 3 unaided stage-1 runs; full panel | ~3 M | none — its result is reported either way |
| 2 — evolution | stages 2–3 for A, B, C (18 runs); stage-2 single judge, stage-3 full panel | ~7 M | — |

Estimates scale from the campaign's measured ratios (an aims build ≈2.3× an unaided one). **Phase 1 alone
already answers the first-design question** and costs about a quarter of the whole; Phase 2 is what tests
whether the design survives change.

# 9. Threats to validity, stated in advance

- **One codebase, one axis, n = 3.** A result is suggestive; strength would come from repeating it on the
  reserve.
- **The gate selects a task on which unaided agents vary.** That is deliberate — it tests aims' actual claim,
  that it prevents the shortcut *when a shortcut is possible*. It does not estimate how often real tasks are
  like that.
- **mkdocs is in the models' training data.** The model may know its design. The three features are not in
  its core, which limits but does not remove this.
- **The judges share the rubric the aims arm designs toward** — vocabulary capture. Mitigated by stripping
  every record and requiring the disjoint-vocabulary judge; not eliminated.
- **The goal-2 trap is one non-goal**, as in `bp19`. More kinds of intent (a rejected alternative, a
  convention with no code trace) are the natural next step.

# 10. What must exist before Phase 0 starts (the frozen package)

- [x] `starter/` — the pinned mkdocs checkout, its installed environment, the baseline command (built for Phase 0;
      baseline re-verified on it: identical to `hidden/baseline.md`)
- [x] [`cards/stage-1.md`](cards/stage-1.md) — drafted
- [x] [`hidden/stage-2.md`](hidden/stage-2.md), [`hidden/stage-3.md`](hidden/stage-3.md) — drafted
- [x] [`hidden/oracle.md`](hidden/oracle.md) — the product owner's answers, drafted
- [x] [`hidden/probes/stage1_probe.py`](hidden/probes/stage1_probe.py) — written from the card alone, validated on pristine mkdocs
      (the feature probes fail, the regression guards pass). Validation caught a probe bug — two builds of an
      identical site differ in a theme timestamp — fixed by masking exactly that line.
- [ ] `hidden/probes/` for stages 2 and 3 — before Phase 2
- [x] [`hidden/baseline.md`](hidden/baseline.md) — the pinned baseline result
- [x] [`phase0/arm-prompt.md`](phase0/arm-prompt.md) and [`phase0/judge-prompt.md`](phase0/judge-prompt.md) — Phase 0's prompts
- [ ] the Phase 1 aims-arm prompt and the two opposite-disposition judge prompts — before Phase 1
- [x] leak-word check on the drafts (`PROTOCOL.md` §4.5) — two found in the oracle's answers and removed; repeat on the frozen versions
- [x] a read-through that no card hints at a later stage (`PROTOCOL.md` §1.2) — stage 1 names only its own
      behaviour. **Correction before any arm ran:** the card's heading read "Stage 1 — …", which itself says later
      stages exist; the read-through missed it and rendering the prompts caught it. The heading is now the feature's
      name only.
