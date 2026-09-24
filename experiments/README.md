# Experiments — what each one asked, what it found, and whether it stands

Every experiment behind aims, in one place. Each row is taken from that experiment's own results file; follow
the link for the evidence. Each experiment's README states exactly what was handed to each arm and what was
measured, so a run is reproducible and its claims checkable. How to run a new one: [`PROTOCOL.md`](PROTOCOL.md).

**Two that reproduce in minutes:**

- **Navigation** — copy [`navigation/product/`](navigation/product/) to a scratch directory, then give a fresh,
  no-history session (e.g. a subagent) the task in [`navigation/README.md`](navigation/README.md). It should open
  only the relevant file's companion; the recorded run read 2 of 8 files and honored a constraint that lived
  only there.
- **Continued development** — take [`continued-development/product-v1/`](continued-development/product-v1/) (a
  small product with its records), hand a fresh session the product plus the continuation task, and compare
  against a session with the records withheld.

aims has **two goals, measured separately** ([`../goals.md`](../goals.md)):

- **Goal 1 — correct design.** Measured by the §0–§14 rubric **scored from the code**. Passing tests is a floor
  that earns nothing ([`../decisions/0021`](../decisions/0021-design-rubric-leads-a-comparison-not-behavioral-proxies.md)).
- **Goal 2 — knowledge that is not in the code.** Measured by whether that knowledge survives and is acted on.

**Status:** **stands** · **null** (tested, no effect — recorded as such) · **superseded** (a later run
replaced its conclusion) · **removed** (the test was invalid; its files are deleted and kept only in git history).

## Where the evidence stands today

- **Measurement first.** The design grades do not yet repeat. In the latest comparison, aims against the real
  OpenSpec tool over two rounds, the rounds pointed in opposite directions. The same unchanged designs were
  graded 5.7 to 9.8 depending on the judge, all nine judges recognized which method produced each design, and
  the principle-free reopen count favoured OpenSpec in 5 of 6 readings
  ([`results-openspec-real.md`](principles-polish-vs-openspec/results-openspec-real.md),
  [`results-aims-real.md`](principles-polish-vs-openspec/results-aims-real.md)). Every Goal-1 rubric reading
  below should be read against that spread.
- **Goal 1.** The rubric separates designs the tests cannot (43 vs 16 at an identical suite). The **review**
  catches green-but-bad designs (4/4). On a *weaker* model aims raises the floor; on a strong one the effect
  is small, because **every task so far was small enough that a strong model converged on a good design
  unaided**. Whether aims produces better design **at a scale where the right design is not obvious** is
  untested — the open question.
- **Goal 2.** A filed **non-goal** catches a change that contradicts it (3/3 vs 0/3) — the one thing a
  record holds that the code cannot. On a **real** decision (requests' maintainers: no timeout on `Session`), the
  record aims filed from their discussion kept it in 3 of 3 sessions; without it, 0 of 6 — aims' process alone did
  not find it. A record does not change the outcome where the pattern is recoverable from the code itself. Six campaign runs were withdrawn (hand-written records).
- **Cost.** ≈1.85–2.34× tokens in the campaign's two measurements; 2.5–3× in the paper's study.

---

## Goal 1 — correct design

| experiment | asked | found | status |
|---|---|---|---|
| [`aims-vs-openspec`](aims-vs-openspec/results.md) (v1) | aims vs OpenSpec vs plain, design-only, checkout pricing over 3 stages | aims won no reading; third under both judges | **superseded** by v4 (`0010`) |
| `aims-vs-openspec` (v3) | same, after the concept-fit pass | the arms could read the ADR naming the fault under test | **removed** — flawed (leak), replaced by v4; in git history at `7a7f71d` |
| [`aims-vs-openspec`](aims-vs-openspec/results-v4.md) (v4) | clean isolated re-run | aims-panel first under both opposite-prior judges — **and ships a real defect** in its tax mechanism | **stands**, with the defect |
| [`aims-upgraded-rerun`](aims-upgraded-rerun/results.md) | the pilot aims lost, re-run on upgraded aims | the judges now agree — on a real structural fault (two structures for one tax concept) and a correctness gap | **stands** — a loss, diagnosed |
| [`aims-single-pass-rerun`](aims-single-pass-rerun/README.md) | single-pass designer on the corrected principles | discovered the discount→line allocation from the requirement itself | **stands** |
| [`single-pass-assessment-rerun`](single-pass-assessment-rerun/README.md) | the same, scored on the assessment form | checkout a three-way tie; aims no longer last | **stands** |
| [`principles-polish-vs-openspec`](principles-polish-vs-openspec/results.md) | design-principles.md vs OpenSpec, 3 fresh products | aims wins first-round on all three; change absorption tie / win / tie | **superseded** — the OpenSpec arm only imitated the tool's format; re-run below |
| [`principles-polish-vs-openspec`](principles-polish-vs-openspec/results-openspec-real.md) (round 1) | the same, OpenSpec arm re-run with the real tool (1.13.2), against the frozen aims designs | form: no clear advantage on D1 in all 3, OpenSpec on D2 in all 3; fewer reopens: aims 1, OpenSpec 2; wrong-output failures found in aims on 3 products, OpenSpec 0 | **contested** — round 2 disagrees |
| [`principles-polish-vs-openspec`](principles-polish-vs-openspec/results-aims-real.md) (round 2) | aims re-run at its current version in stricter isolation; two opposite-disposition judges per product | form: aims 4 of 6 on D1, 5 of 6 on D2; fewer reopens: OpenSpec 5 of 6; the same OpenSpec designs graded 5.7–9.8 by judge; 9 of 9 judges named the methods | **stands as a measurement failure** — the grades depend on the judge |
| [`plant-mineral-id`](plant-mineral-id/results.md) | aims vs OpenSpec, feature-based identifier | **aims lost decisively** (6.63 vs 9.54), the only BLOCKED arm | **stands** — a loss |
| [`s7-yagni-stated-capability`](s7-yagni-stated-capability/results.md) | does a §7 clause fix that loss on an unseen product? | the loss did not reproduce with or without it | **null** — not adopted |
| [`marketplace-change-absorption`](marketplace-change-absorption/results.md) | informal change-absorption probe, furniture → cars | three blind judges: aims > OpenSpec > plain | **stands** — informal |
| [`instance-seg-annotator`](instance-seg-annotator/results.md) | two-arm build pilot, staged evolution | design: **no clear advantage** (verdict flips with the judge) | **stands** (its Q2 is in goal 2) |
| [`iter-plan`](iter-plan/README.md) | revise round vs a long upfront brief | one review-and-revise round is the biggest lever measured (2.0 → 3.5) | **stands** → `0011` |
| [`plan-diversity`](plan-diversity/results.md) | three candidate designs + synthesis vs single pass | synthesized inter-model 38/40 vs single pass 24/40 — n = 1, and the winner leaned on the judge's own model | **stands** — suggestive |
| [`self-redesign-regression`](self-redesign-regression/results.md) | did the self-redesign regress the method? | no; one probe fix was caught blind | **stands** |
| [`refactoring-principles-validation`](refactoring-principles-validation/results.md) | add-feature principles on a synthetic change | both arms correct; the card over-specified the trap | **stands** |
| [`refactoring-suite`](refactoring-suite/results.md) | 3 real-code tasks, aims vs plain | both correct on all; aims kept the one-owner rule where plain scattered it | **stands** |
| [`refactoring-suite-real`](refactoring-suite-real/results.md) | a real library (boltons cache TTL) | both correct; aims tighter (expiry co-located, 31 vs 53 lines) | **stands** |
| [`refactoring-rot`](refactoring-rot/results.md) | 3 successive interacting changes | both correct each step; **aims' design improves, plain's stays flat and denser** | **stands** |
| [`refactoring-crosscut`](refactoring-crosscut/results.md) | multi-currency across a 4-module ledger | essentially a tie | **stands** |

Synthesis of the add-feature runs: [`refactoring-SYNTHESIS.md`](refactoring-SYNTHESIS.md).

## Goal 2 — knowledge that is not in the code

| experiment | asked | found | status |
|---|---|---|---|
| [`navigation`](navigation/results.md) | does a fresh agent reach the knowledge by navigating? | opened exactly 2 of 8 files, found and honored a constraint that lived only in the companion, skipped the distractor | **stands** — navigation on a prepared fixture |
| [`continued-development`](continued-development/results.md) | does a fresh session continue from the records? | a tie on the code; the records arm *knew* the invariant instead of re-deriving it | **stands** — narrow |
| [`instance-seg-annotator`](instance-seg-annotator/results.md) | Q2: did the fresh session continue from the records? | yes, blind-corroborated | **stands** |
| [`refactoring-continuity`](refactoring-continuity/results.md) | the same code with and without its record | both correct; the record added legibility, not a different outcome | **null** at this scale |
| [`real-decision-trap`](real-decision-trap/results.md) | a **real** maintainers' decision, reached on GitHub and absent from code and docs, filed as a record by aims from the maintainers' words: does a later session keep it when a feature request invites the historical wrong turn? | requests (no timeout on `Session`): with the record **3 of 3** kept it — each stopped, cited the record and built the default on the transport adapter; aims without it 0 of 3, unaided 0 of 3, all building `Session.timeout`. PyTorch (sampler re-seeding): stopped at the gate — unaided kept it 3 of 3, the code's own shape leads there | **stands** — one decisive case, n = 3 |

## Designed, not yet run

| experiment | goal | asks | status |
|---|---|---|---|
| [`design-judgment`](design-judgment/README.md) | 1 (its precondition) | can a judgment of design quality pass through language, to or from a model, in a way that is stable, responds to structure rather than surface, and agrees with established design knowledge? Three tests on the judgment itself, no execution proxy: stability (Q1), surface invariance (Q2), minimal pairs (Q3) | **open** — the problem is documented from the existing data; not yet run |
| [`single-root-file`](single-root-file/DESIGN.md) | 2 | one root file of design notes, or records beside the code? The same aims-filed records in both layouts, converted by a script that changes no word | **designed** — needs records from a real aims build |
| [`design-at-scale`](design-at-scale/DESIGN.md) | 1, and 2 separately | does aims produce better design on a real codebase (mkdocs, 7k lines) with changes that cut across it — and only after a gate proves unaided agents sometimes get that design wrong? | **Phase 0 run — the gate passed** ([results](design-at-scale/phase0/results.md)). **Phase 1 run — verdict aims** at stage 1, by all three blind judges; 1 of 3 aims designs clean vs 0 of 3 unaided. Most of the gap is one product question the aims arms asked and the unaided did not; aims' arms also made one defect no unaided arm made ([results](design-at-scale/phase1/results.md)). **Phase 2 run** — stage 3, B vs C: **supported** by the registered panel rule (2 of 3 judges; the ownership judge: no clear advantage), after a disclosed correction removing the goal-2 line from the judges' spec (under the first spec, one judge would have falsified); goal 2: **no clear advantage** (A 3/3, B 2/3, C 1/3 surfaced the conflict) ([results](design-at-scale/phase2/results.md)) |

## The measurement instrument

| item | what it is |
|---|---|
| [`judging-rubric/`](judging-rubric/) | the assessment form and its regrades |
| [`judge-agreement/`](judge-agreement/README.md) | how far the grades repeat across judges, from the 36 existing forms. Same OpenSpec designs, three judges: α 0.11, and the judge explains more grade variance (50%) than the design (27%). Mostly driven by which judge finds a correctness bug; without chapter 13, α 0.49. Within one round the two judges' grades agree (ICC 0.78), but not which chapters fail (α 0.38) or the verdict (5 of 9). |
| [`grade-rule-regrade.md`](grade-rule-regrade.md) | every earlier grade recomputed without the removed global cap, both readings kept; no ranking changed (`0018`) |
| [`PROTOCOL.md`](PROTOCOL.md) | how to run an experiment that discriminates |

---

## The 2026-09 improvement campaign — [`improve-2026-09/`](improve-2026-09/)

Current conclusions: [`SYNTHESIS.md`](improve-2026-09/SYNTHESIS.md) · history: [`LOG.md`](improve-2026-09/LOG.md) ·
every attempt re-checked against the corrected measure: [`REEVALUATION.md`](improve-2026-09/REEVALUATION.md) ·
which record-layer runs are valid: [`AUDIT-record-layer-claims.md`](improve-2026-09/AUDIT-record-layer-claims.md).

**Method changes proposed and tested:**

| run | goal | asked | found | status |
|---|---|---|---|---|
| [`i1`](improve-2026-09/i1-input-space-table/results.md) | 1 | a design-time input-space table | no gain over the shipped §1 | **null** — not adopted |
| [`i2`](improve-2026-09/i2-falsification-review/results.md) | 1 | an adversarial falsification review pass | the shipped review already falsifies | **null** — not adopted |
| [`i3`](improve-2026-09/i3-outcome-first/validation.md) | 1 | lead comparisons with behavioural proxies | shipped as `0019` — then shown to be a regression | **superseded** by `0021` |
| [`i4`](improve-2026-09/i4-table-unstated-corner/results.md) | 1 | the table, on an unstated corner | still no gain | **null** — closed |
| `i5` | 2 | a record-layer trap | — | **removed** — withdrawn (records written by hand); in git history at `7a7f71d` |

**Build pilots:**

| run | goal | asked | found | status |
|---|---|---|---|---|
| [`bp1`](improve-2026-09/bp1-inventory/results.md) | 1 | 3-stage build, aims vs no method | 0 vs 1 reopen; correctness a tie; ≈1.85× tokens | **stands** — modest |
| [`bp2`](improve-2026-09/bp2-inventory-haiku/results.md) | 1 | the same on a cheaper model | reproduces (n = 2); did not compound | **stands** |
| [`bp3`](improve-2026-09/bp3-hint-transfer/results.md) | 1 | is the edge the method, or one principle? | one principle made a plain arm match aims — on a strong model | **stands** |
| [`bp4`](improve-2026-09/bp4-conceptfit-probe/results.md) | 1 | a concept-fit trap | both arms avoided it | **null** |
| [`bp5`](improve-2026-09/bp5-ledger-compounding/results.md) | 1 | does the edge compound over 4 changes? | no — both absorbed all four | **null** on compounding |
| [`bp6`](improve-2026-09/bp6-baserate/results.md) | 1 | how often does a plain build take the shortcut? | 1 of 6 | **stands** |
| [`bp7`](improve-2026-09/bp7-conceptfit-generalize/results.md) | 1 | on a second axis? | 0/3 on a strong model, 2/6 on a weak one — model-dependent | **stands** |
| [`bp8`](improve-2026-09/bp8-lite-baserate/results.md) | 1 | does the principle in the prompt help a weak model? | no — 2/6 both ways | **null** |
| [`bp9`](improve-2026-09/bp9-review-vs-principle/results.md) | 1 | does the review catch what the prompt missed? | **yes, 4/4** — output inspection is the part that matters | **stands** |
| [`bp10`](improve-2026-09/bp10-correctness-baserate/results.md) | 1 | a correctness deficit on clear specs? | 0 bugs in 12 | **null** |
| [`bp11`](improve-2026-09/bp11-interaction-corner/results.md) | 1 | a designed interaction corner? | 0 slips in 6 | **null** |
| [`bp12`](improve-2026-09/bp12-cost/results.md) | — | cost, second datapoint | ≈2.3× tokens, ≈12× wall on a small task | **stands** |
| [`bp13`](improve-2026-09/bp13-design-under-surprise/results.md) | 1 | does design quality show under an unforeseen change? | only on the right change: type-switch 4/4 reopen vs polymorphic 0/2, identical tests | **stands** |
| [`bp14`](improve-2026-09/bp14-design-rubric/results.md) | 1 | does the rubric separate designs the tests cannot? | **43 vs 16** at an identical suite | **stands** |
| `bp15`, `bp15b`, `bp16`, `bp16b`, `bp17` | 2 | record-layer runs | — | **removed** — withdrawn: the evaluator wrote the records by hand, so they tested that construction, not the method; in git history at `7a7f71d` |
| `bp18` | 2 | one root file vs per-file companions | — | **removed** — withdrawn; the question is open (`0023`) and re-designed in [`single-root-file`](single-root-file/DESIGN.md); in git history at `7a7f71d` |
| [`bp19`](improve-2026-09/bp19-aims-filed-records/results.md) | 2 | do aims-filed records help a blind agent? | a filed non-goal caught a contradicting change **3/3 vs 0/3**; the design rubric could not see it | **stands** |
| [`bp21`](improve-2026-09/bp21-code-first-gate/results.md) | 2 | does the code-first gate stop records restating the code? | 62% of a pre-gate companion was restatement; with the gate 8/8 dropped, 6/6 kept, matching a pre-registered prediction | **stands** → `0022` |
| [`bp22`](improve-2026-09/bp22-gate-on-itself/results.md) | 2 | the gate run on aims' own session | 10 of 14 declined as already carried; found four real guidance defects (a fifth claimed defect was wrong) | **stands** |
