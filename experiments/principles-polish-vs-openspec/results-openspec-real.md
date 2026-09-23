# Results: OpenSpec arm rerun with the real tool

**Run 2026-09-23.** This reruns **only** the OpenSpec arm, using the real OpenSpec CLI and skills. The
aims-single arm is frozen: its designs are the unchanged `*/arms/aims-single/stage-{1,2}.md` from the
2026-09-18 run ([`results.md`](results.md)). Protocol: [`../PROTOCOL.md`](../PROTOCOL.md). This file reports
results only and draws no interpretation.

## Setup

- **Tool:** `npm install -g @fission-ai/openspec@1.13.2`. `openspec --version` → `1.13.2`.
- **Starter:** for each product, a fresh git repo containing only `substrate.md` (the same starter the aims
  arm had), then `openspec init --tools claude --no-animation`, then a commit. `.claude/skills/openspec-*` was
  verified present in each repo: explore, propose, apply-change, archive-change, sync-specs, update-change.
- **Arm sessions:** every stage ran as a new headless `claude -p` process started inside the product repo.
  The OpenSpec skills loaded natively. No aims file, aims skill or aims `CLAUDE.md` was visible. The model was
  the same family as the frozen arms (configured `claude-opus-5-5`).
- **Prompt:** the stage card verbatim + "use OpenSpec for this; design only" + a fixed operator note: explore
  then propose, stop before apply, write product-owner questions to `QUESTIONS.md` and stop. The exact prompts
  and transcripts are under `*/arms/openspec-real/runs/`.
- **Stage flow:** S1 explore+propose → oracle (if asked) → `openspec validate --all` → archive skill (separate
  session) → commit, tag `stage-1` → S2 explore+propose → oracle (if asked) → validate → commit, tag `stage-2`.
  Every `validate --all` passed.
- **Runner:** [`run-arm-openspec-real.sh`](run-arm-openspec-real.sh). Per-product logs are in
  `*/arms/openspec-real/RUN-LOG.md`.

## Oracle

| product | stage 1 | stage 2 |
|---|---|---|
| feed-ranking | no questions | 3 questions (unsatisfiable diversity case, input shape, visibility of excluded items), answered from the hidden spec. A fresh session was re-spawned with the card + the Q&A. The log is in [`feed-ranking/arms/openspec-real/RUN-LOG.md`](feed-ranking/arms/openspec-real/RUN-LOG.md) |
| booking-availability | no questions | no questions |
| entitlements | no questions | no questions |

## Cost of the OpenSpec arm (real tool)

Tokens = input + cache-creation + cache-read + output, so cache reads dominate the figure.

| product | S1 propose: s / tool calls / tokens | archive: s / calls / tokens | S2 propose: s / calls / tokens | total s / calls / tokens |
|---|---|---|---|---|
| feed-ranking | 141 / 18 / 703,747 | 40 / 7 / 368,500 | 45 / 4 / 223,395 (asked) + 201 / 15 / 895,055 | 427 / 44 / 2,190,697 |
| booking-availability | 121 / 12 / 454,556 | 28 / 4 / 195,725 (declined) + 28 / 7 / 350,079 | 259 / 15 / 728,496 | 436 / 38 / 1,728,856 |
| entitlements | 133 / 13 / 577,574 | 34 / 7 / 356,357 | 208 / 15 / 681,531 | 375 / 35 / 1,615,462 |

## Judging

- **Anonymization:** the openspec-real design for a stage = that stage's change bundle (proposal, delta specs,
  design, tasks) concatenated into one file. The frozen aims-single design is used as is. Method names
  (`openspec`, `opsx`, `aims`, `aims-guide`, `.aims/`) were replaced with neutral tokens in both. X/Y labels
  were assigned at random per product. The mappings were sealed in `judging-real/*/MAPPING-SECRET.md` and
  opened only after scoring.
- **Judge:** one new headless session per product, in a directory outside the aims repo that at first held
  only `blind/`. Its transcripts show it read nothing outside that directory. **Step 1 (manipulation
  check):** guess which label is which, with confidence and cues. **Step 2 (same session, resumed):** the
  judge was given the rubric (`assessment-form.md`, `design-principles.md`, `measurement.md`, `review.md`) and
  the product files (the cards, `substrate.md`, the hidden spec + oracle), then asked for the D1 form, the D2
  survival count + form, and the correctness traps. Prompts:
  [`judging-real/prompt-1.txt`](judging-real/prompt-1.txt),
  [`judging-real/prompt-2.txt`](judging-real/prompt-2.txt).

### Manipulation check

| product | mapping | judge's guess | correct | confidence |
|---|---|---|---|---|
| feed-ranking | X = aims-single, Y = openspec-real | X = aims, Y = OpenSpec | yes | 97% |
| booking-availability | X = aims-single, Y = openspec-real | X = aims, Y = OpenSpec | yes | 97% |
| entitlements | X = openspec-real, Y = aims-single | X = OpenSpec, Y = aims | yes | 97% |

The cues the judges cited were OpenSpec's artifact layout and headings (`## ADDED Requirements`,
`#### Scenario`, `SHALL`, proposal/design/tasks) and the aims designs' numbered principle citations (`§4`,
`Step-0`).

### Scores (unmasked)

Grades are the uncapped weighted average per `measurement.md`, as the judges reported them. The form-capped
figure is in parentheses. "Gate" = BLOCKED if any row is S4.

| product | D1 aims-single | D1 openspec-real | D1 winner (judge) | reopened+discarded aims / openspec | D2 survival winner | D2 form aims | D2 form openspec | D2 form winner |
|---|---|---|---|---|---|---|---|---|
| feed-ranking | 6.50, worst 2, BLOCKED (5.0) | 8.69, worst 5, CLEAR (8.5) | no clear advantage | 2+0 / 3+0 | aims, narrowly | 6.50, BLOCKED (5.0) | 8.69, CLEAR (8.5) | openspec, clearly |
| booking-availability | 9.64, worst 7, CLEAR | 9.79, worst 7, CLEAR | no clear advantage | 2+0 / 1+0 | openspec, narrowly | 6.18, worst 2, BLOCKED (5.0) | 9.71, worst 8, CLEAR | openspec, clearly |
| entitlements | 6.86, worst 2, BLOCKED (5.0) | 9.27, worst 7, CLEAR (8.5) | no clear advantage | 2+1 / 3+0 | openspec, narrowly (3 vs 3; reopens internal vs public) | 6.59, worst 2, BLOCKED (5.0) | 9.00, worst 6, CLEAR (8.5) | openspec |

### Correctness traps (from the hidden oracle)

| product | trap | aims-single | openspec-real |
|---|---|---|---|
| feed-ranking | 1 blocked-as-weight | avoided | avoided |
| | 2 diversity-as-penalty | penalty avoided; judge found the sequencer can emit 3-in-a-row on satisfiable input `a1,b1,a2,a3,a4` | avoided (hard limit) |
| | 3 pipeline ownership | avoided from stage 1 | reached at stage 2 via a core output-type change |
| booking-availability | 1 buffer-as-booking | avoided | avoided |
| | 2 scattered "bookable" rule | avoided (notice encoded twice in one owner) | avoided |
| | 3 interaction coverage | mostly; notice × back-to-back re-anchoring missed | avoided |
| entitlements | 1 deny-as-absence | avoided | avoided |
| | 2 inheritance at call sites | avoided | avoided |
| | 3 time/precedence | avoided (inverted deny window unvalidated, row 13) | avoided |

The full reports carry every citation: [`judging-real/feed-ranking/report.md`](judging-real/feed-ranking/report.md),
[`judging-real/booking-availability/report.md`](judging-real/booking-availability/report.md),
[`judging-real/entitlements/report.md`](judging-real/entitlements/report.md).

## Deviations, declared

1. **Operator note in the prompt** beyond "card + line": the non-interactive question channel (`QUESTIONS.md`)
   and "explore, then propose, stop before apply".
2. **Archive in a design-only project:** feed-ranking and entitlements archived with an incomplete-tasks
   warning. The first booking archive session declined (0/10 tasks). A second session, told the project is
   design-only and that the owner confirms, archived it.
3. **Harness false start:** the first stage-1 launch failed before any model call (a path error, and root
   refusing bypass mode). Nothing ran, and it is not counted.
4. **Stage-2 not archived** (the task asked for validate + commit only at stage 2).
5. **One judge per product**, not the two opposite-disposition judges + a disjoint-vocabulary judge of
   PROTOCOL §6. There is no product judge and no re-verification of the judges' reproductions.
6. **Judges disagreed with the instrument:** all three noted that `assessment-form.md`'s graded caps conflict
   with `measurement.md` ("no global cap"). They led with `measurement.md`, and both figures are shown above.
7. **The frozen aims-single designs were the same files judged on 2026-09-18.** The earlier judges saw an
   aims text with only "aims" → "the-method" replaced. This run scrubbed both arms with the same rule set.
8. n = 1 per product.
