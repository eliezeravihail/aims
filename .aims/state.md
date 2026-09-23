# aims Guide State

Loop status only. Durable design lives in the records (`goals.md`, `architecture.md`, `decisions/`, the
companions); the evidence behind them is indexed in `experiments/README.md`. This file is run-state,
replaced each round.

## Mode

stepped

## Loop cursor

awaiting-human <real-decision-trap complete — requests: the aims-filed record kept a real maintainers' decision in 3 of 3 sessions, 0 of 6 without it (supported); PyTorch stopped at the gate (real-decision-trap/results.md)>

## Current objective

**Kind:** add-feature

**Objective:** By targeted rewrites of existing surfaces — the rest untouched — make every shipped surface
state the method as it now stands, with the idea first and nothing restated that a source already owns.

**Why now:** the 2026-09 campaign changed the measure (`0021`), the record rule (`0022`, `0025`, `0026`) and
the evidence, and several surfaces kept older copies: the installed-project state template carried the
per-file companion model; the docs site described an instrument two revisions old; the skill buries its idea
in 573 lines. A new experiment run against guidance that contradicts itself would measure the contradiction.

**Exit criteria:**
- [x] No shipped surface states a retired claim — enforced by `tests/coherence.sh` check 7, which failed on
      13 sites before the fixes and passes after.
- [x] The docs site describes and links the instrument rather than copying it.
- [x] `SKILL.md` leads with its idea; every operative instruction survives; all suites green (574 → 336 lines,
      77 instructions checked).
- [x] The paper carries the campaign's findings beside its own (Study 3), and recompiles.
- [x] One index states, per experiment, what it asked, what it found, and whether it stands.
- [x] `improve-2026-09/SYNTHESIS.md` states current conclusions only; history stays in `LOG.md`.

**Preserve:** every rule's content; `decisions/` append-only; the two tools; the four test suites.

**Do not optimize for:** line count as a goal — a cut that drops an operative instruction fails.

## Open assumptions (unproven — carried, not filed)

- That aims produces better design than a capable agent working unaided **at a scale where the right
  design is not obvious**. Every task measured so far was small enough that a strong model converged on its
  own. Falsifier: the scale experiment designed next shows no §0–§14 difference.
- That per-file companions earn their keep over a single root file, given that most knowledge now belongs in
  the code (`0023`: considered-but-untested).

## Open Guide TODO

- [x] Design the scale experiment (goal 1) — `experiments/design-at-scale/`.
- [x] Design the single-root-file experiment (goal 2) — `experiments/single-root-file/`.
- [x] Run design-at-scale Phase 0 — the gate PASSED: of four unaided designs, one clean, at least two with a
      verified precondition failure (`experiments/design-at-scale/phase0/results.md`).
- [x] Run design-at-scale Phase 1 — verdict **aims** by all three blind judges; 1 of 3 aims designs clean vs 0 of 3
      unaided; every S3/S4 reproduced. Most of the gap is one product question the aims arms asked; aims' arms also
      made one defect no unaided arm made (`experiments/design-at-scale/phase1/results.md`).
- [x] Run design-at-scale Phase 2 — stage 3, B vs C **supported** by the panel rule (ownership: no clear advantage;
      simplicity, disjoint: supported), after a disclosed correction to the judges' spec; stage 2 (one judge):
      supported; goal 2: no clear advantage (A 3/3, B 2/3, C 1/3). Every S3/S4 reproduced before unsealing
      (`experiments/design-at-scale/phase2/results.md`).
- [ ] Update PR #65's description; merging or splitting it is the owner's decision.

## Last evaluated result

The 2026-09 campaign: tests never separate designs (43 vs 16 at identical tests); the review catches
green-but-bad designs (4/4); a filed non-goal catches a change that contradicts it (3/3 vs 0/3); the
code-first gate removes restatement (62% → 0) while keeping what the code cannot hold (6/6). Six
record-layer runs withdrawn (hand-authored records). See `experiments/improve-2026-09/`.
