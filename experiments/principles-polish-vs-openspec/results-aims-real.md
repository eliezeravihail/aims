# Results: aims arm rerun (current aims, real isolation) vs openspec-real

**Run 2026-09-23.** This reruns the aims-single arm under the same conditions as the openspec-real arm
([`results-openspec-real.md`](results-openspec-real.md)): same model, fresh isolated sessions, same oracle
policy. The openspec-real designs are unchanged. Protocol: [`../PROTOCOL.md`](../PROTOCOL.md). This file
reports numbers only and draws no interpretation.

- **Pinned aims:** `477cff9b397f79869f72cf13f32f2f626a3dd2e9`, the commit "Align assessment-form with
  measurement.md (no global cap; S4 is a gate)". Nothing else in aims changed between that commit and the rerun.
- **Model:** `claude-opus-5-5` (configured `--model`) for every arm and judge session. Worker subagents
  inherit it. Per-session `modelUsage` is in each `runs/*/stats.json`.

## Step 0: the instrument, fixed before the rerun

`experiments/judging-rubric/assessment-form.md` was aligned with `skills/aims-guide/references/measurement.md`:
- The graded caps (S2 ≤ 8.5, S3 ≤ 7.5, S4 ≤ 5.0) and the capped grade were removed. The profile now reports the
  grade (weighted average), the worst chapter, (#S3,#S4), and the gate (any S4 ⇒ BLOCKED).
- The worked example was restated: 8.5 capped became 9.63 CLEAR.
- One other copy of the old capped figure was aligned: `docs/measurement.html` showed "blind (rubric 8.5)",
  now 9.63.
- Historical result files that report grades computed under the old rule were not edited:
  `judging-rubric/regrade-results.md`, `cross-experiment-regrade.md`, `plant-mineral-id/results.md`, and the
  per-experiment judge reports.

`tests/coherence.sh` passed.

## Setup

- **Repo per product:** `/home/user/aims-rerun/<P>`, a fresh `git init` containing only `substrate.md` and
  `skills/aims-guide/` at the pin, placed at `.claude/skills/aims-guide/`. Committed.
- **Isolation:** each session ran in a private mount namespace in which:
  - `/home/user` held only that repo;
  - `/tmp` and `~/.claude/{projects,tasks,backups,shell-snapshots}` were empty tmpfs mounts.

  A diagnostic session (`feed-ranking/arms/aims-real/runs/feed-ranking-isolation-test/`) confirmed:
  - `aims-guide` was the only project skill (the harness's own built-in and plugin skills were also present);
  - no CLAUDE.md was loaded;
  - `/home/user/aims` did not exist;
  - a subagent could be spawned.
- **Runner:** [`run-arm-aims-real.sh`](run-arm-aims-real.sh), a copy of `run-arm-openspec-real.sh` with four
  changes:
  - base dir `/home/user/aims-rerun`;
  - `Task`/`Agent` added to `--allowedTools`;
  - the namespace wrapper;
  - one added stats field, `all_models_total_tokens`.

  The same main-loop token accounting is kept (input + cache creation + cache read + output), and
  `--model claude-opus-5-5` is unchanged.
- **Prompt:** the card verbatim, then "follow the aims-guide skill; design only", then an operator note:
  - follow aims-guide including its mandatory review-and-revise round, inside the session;
  - stop before any code;
  - write questions to `QUESTIONS.md` and stop;
  - write the final design to `DESIGN.md`.
- **Stage 2** ran as a new session in the same repo.
- **Revise round:** each product's `.aims/state.md` records the mandatory revise round as done at both stages.
  Every stage ran as a three-Worker panel, then merge, measure, revise round and re-measure.
- **Saved** under `*/arms/aims-real/`:
  - `stage-N/DESIGN.md`, the design that was judged;
  - `stage-N/repo/`, every filed record at tag `stage-N`;
  - the oracle Q&A (`sN-QUESTIONS.md`, `sN-ANSWERS.md`);
  - `RUN-LOG.md`;
  - `runs/*` (prompt, stats, gzipped transcript).

## Oracle

| product | stage 1 | stage 2 |
|---|---|---|
| feed-ranking | 9 questions → answered, re-spawned | 5 questions → answered, re-spawned |
| booking-availability | 4 questions → answered, re-spawned | 4 questions → answered, re-spawned |
| entitlements | none | none |

The answers come only from the hidden spec, for the current stage. A question the openspec-real arm had asked
got its answer word for word. Two oracle phrases were given without their leak words: "all stage 1 needs" and
"ignore cross-zone for now". The logs are in each `RUN-LOG.md`.

## Cost

"Main tokens" uses the same accounting as openspec-real. "All-model tokens" includes Worker subagents.
"Tool calls" counts every `tool_use` in the stream, subagents' included.

| product | stage 1: s / calls / main tok / all-model tok | stage 2: s / calls / main tok / all-model tok | total: s / calls / main tok / all-model tok / USD |
|---|---|---|---|
| feed-ranking | 924 / 76 / 953,513 / 4,417,283 | 1,122 / 103 / 2,036,733 / 8,165,605 | 2,046 / 179 / 2,990,246 / 12,582,888 / 15.72 |
| booking-availability | 1,072 / 48 / 729,919 / 3,544,177 | 1,846 / 116 / 1,942,642 / 9,594,759 | 2,918 / 164 / 2,672,561 / 13,138,936 / 21.10 |
| entitlements | 715 / 67 / 540,072 / 3,982,613 | 832 / 59 / 1,933,402 / 4,302,144 | 1,547 / 126 / 2,473,474 / 8,284,757 / 11.97 |

For reference, openspec-real totals (s / calls / main tok, archive included) were:
- feed-ranking: 427 / 44 / 2,190,697
- booking-availability: 436 / 38 / 1,728,856
- entitlements: 375 / 35 / 1,615,462

## Judging

- **Anonymization:** the same scrub rules as `judging-real`. The openspec-real snapshot = each stage's change
  bundle (proposal, delta specs, design, tasks). The aims-real snapshot = `DESIGN.md` at each tag, with the
  records stripped (PROTOCOL §6). X/Y labels were random per product. The mappings were sealed in
  `judging-aims-real/*/MAPPING-SECRET.md` and opened after all six reports existed.
- **Judges:** two per product with opposite dispositions, **ownership** (invariant-ownership) and
  **simplicity** (YAGNI). The disposition texts are in `judging-aims-real/disp-*.txt`.
  - Each judge was a new session in its own mount namespace; `/home/user` held only its workspace.
  - Step 1 (manipulation check) saw only `blind/`.
  - Step 2 was the same session, resumed, with `rubric/` (at the pin) and `product/` added.
  - A transcript audit found no tool call on a path outside each judge's own workspace.
  - Prompts: [`prompt-1.txt`](judging-aims-real/prompt-1.txt),
    [`prompt-2-template.txt`](judging-aims-real/prompt-2-template.txt). Each judge was required to give a
    reproducing input for every failure it reported.

### Manipulation check

| product | mapping | ownership judge | simplicity judge |
|---|---|---|---|
| feed-ranking | X = aims-real, Y = openspec-real | correct, 97% | correct, 97% |
| booking-availability | X = openspec-real, Y = aims-real | correct, 97% | correct, 97% |
| entitlements | X = openspec-real, Y = aims-real | correct, 97% | correct, 97% |

### Scores (unmasked)

Profile = grade · worst chapter · (#S3,#S4) · gate. Survival = reopened + discarded, stage 1 → stage 2.

| product | judge | D1 aims-real | D1 openspec-real | D1 winner | survival aims / openspec | survival winner | D2 form aims-real | D2 form openspec-real | D2 form winner |
|---|---|---|---|---|---|---|---|---|---|
| feed-ranking | ownership | 9.79 · 7 · (0,0) · CLEAR | 5.92 · 2 · (0,1) · BLOCKED | aims | 4+0 / 3+0 | openspec, narrowly | 9.64 · 7 · (0,0) · CLEAR | 5.80 · 2 · (0,1) · BLOCKED | aims |
| feed-ranking | simplicity | 9.71 · 6 · (0,0) · CLEAR | 6.09 · 2 · (0,1) · BLOCKED | aims | 2+0 / 2+0 | no clear advantage | 9.57 · 4 · (0,0) · CLEAR | 5.78 · 2 · (0,1) · BLOCKED | aims |
| booking-availability | ownership | 10.00 · 10 · (0,0) · CLEAR | 6.82 · 2 · (0,1) · BLOCKED | aims | 2+1 / 1+0 | openspec | 6.86 · 2 · (0,1) · BLOCKED | 6.52 · 2 · (0,1) · BLOCKED | aims, narrowly |
| booking-availability | simplicity | 9.33 · 6 · (0,0) · CLEAR | 9.47 · 7 · (0,0) · CLEAR | no clear advantage | 3+1 / 1+0 | openspec | 6.64 · 2 · (0,1) · BLOCKED | 9.07 · 7 · (0,0) · CLEAR | openspec |
| entitlements | ownership | 9.50 · 7 · (0,0) · CLEAR | 8.74 · 7 · (0,0) · CLEAR | aims | 3+1 / 2+0 | openspec | 9.18 · 7 · (0,0) · CLEAR | 5.71 · 2 · (1,1) · BLOCKED | aims |
| entitlements | simplicity | 9.47 · 6 · (0,0) · CLEAR | 9.33 · 7 · (0,0) · CLEAR | no clear advantage | 3+1 / 3+0 | openspec, narrowly | 9.00 · 6 · (0,0) · CLEAR | 6.36 · 2 · (0,1) · BLOCKED | aims |

### Hidden-oracle traps

| product | trap | aims-real (ownership / simplicity) | openspec-real (ownership / simplicity) |
|---|---|---|---|
| feed-ranking | 1 blocked-as-weight | avoided / avoided | avoided / avoided |
| | 2 diversity-as-penalty | avoided / avoided | avoided / avoided |
| | 3 pipeline ownership | avoided / avoided | avoided / avoided |
| booking-availability | 1 buffer-as-booking | avoided / avoided | avoided / avoided |
| | 2 scattered "bookable" rule | avoided / avoided | avoided, partial breach (fit bound in two policy classes) / avoided (same, S1) |
| | 3 interaction coverage | avoided / **partly failed** (F-B1) | avoided / avoided |
| entitlements | 1 deny-as-absence | avoided / avoided | avoided / avoided |
| | 2 inheritance at call sites | avoided / avoided | avoided / avoided |
| | 3 time / precedence | avoided / avoided | structurally avoided, time predicate wrong at DST fold (F-E1) / avoided |

Both entitlements judges independently reported that the hidden oracle is self-contradictory on specificity. Its
first answer, "most specific wins", conflicts with its third answer and with the card, both of which say "a deny
on the path still wins". Both designs return DENY on the one input that distinguishes the readings, and neither
judge charged a failure for it.

### Output failures reported, with the judges' reproducing inputs

| id | design | stage | judge(s) | severity | input → design output vs correct |
|---|---|---|---|---|---|
| F-F1 | openspec-real | 1, 2 | ownership | §13 S4 | host `decimal.getcontext().prec = 6`; weights 0.5/0.3/0.2; `a.recency=0.1234567`, `b.recency=0.1234568`, other signals 0 → `[a, b]` with tied `0.0617284` vs correct `[b, a]` |
| F-F1′ | openspec-real | 1, 2 | simplicity | §13 S4 | weights recency 1, affinity 1e-17, popularity 0; `b = (0.5, 1e-14, 0)`, `a = (0.5, 0, 0)` → `[a, b]` (b rounds to 0.5 at prec 28) vs correct `[b, a]` |
| F-B1 | aims-real | 2 | both | §13 S4 | hours 09:00–17:00, booking 17:00–18:00, duration 30 min, buffer 15 min, no grid → offers `09:00 … 16:30` (16 starts) vs correct `09:00 … 16:00` (15): the 16:30 slot's buffer `[17:00, 17:15)` overlaps the 17:00 booking |
| F-B2 | openspec-real | 1, 2 | ownership | §13 S4 | `duration = timedelta.max`, hours 09:00–17:00 → `OverflowError` vs correct `[]` (the design's own scenario) |
| F-E1 | openspec-real | 2 | both | §13 S4 | Europe/Berlin, deny window ending `2026-10-25 02:30 fold=1`, `now = 02:45 fold=0` (00:45Z, inside the window): the same-`tzinfo` comparison uses wall time → deny dropped → ALLOW vs correct DENY. The simplicity judge's variant has an allow grant: DENY vs correct ALLOW. |
| F-E2 | openspec-real | 2 | ownership | §4 S2 | `Window(None, None)` grant, no `now` → `EvaluationInstantRequired` vs correct ALLOW |
| F-E3 | openspec-real | 2 | ownership | §7 S3 | role with allow + deny on `(read, doc-42)` → `grants_of` lists the permission while `check` returns DENY |
| F-E4 | aims-real | 1, 2 | ownership | §11 S2 | `if model.decide(...)` with no grants → `Decision.DENY` is truthy, so the branch runs |

**Operator re-check.** I ran only the Python-level facts these reproductions depend on, in CPython 3; this does
not check the judges' reading of the designs. All four held:
- Same-`tzinfo` datetimes compare by wall time: `02:45 fold=0 < 02:30 fold=1` is False, while as UTC instants
  00:45Z < 01:30Z is True.
- `timedelta(hours=9) + timedelta.max` raises `OverflowError`.
- At `prec=6`, `0.5×0.1234567` and `0.5×0.1234568` both give `0.0617284`.
- At `prec=28`, `0.5 + 1e-17×1e-14` equals `0.5`.

Full reports: `judging-aims-real/<product>/{ownership,simplicity}/report.md`.

## Deviations, declared

1. **Operator note** added to "card + line": the question channel, `DESIGN.md` as the output file, the
   in-session revise round, and stop before code. The openspec-real arm got the equivalent note.
2. **Isolation is stronger than in openspec-real.** This arm ran in a mount namespace that hid the aims repo
   and every operator transcript. openspec-real relied on process separation only; its sessions could have
   read those paths, though nothing checked whether they did.
3. **Re-spawn state:** after questions, the first session's `.aims/state.md` stayed in the repo, and the
   re-spawned session saw it. Its `QUESTIONS.md` was removed after it was logged. In openspec-real, the
   question-asking session created no OpenSpec files.
4. **Stage-2 cards were revealed per product** as soon as that product's aims stage 1 closed. The openspec-real
   arm had closed every stage earlier.
5. **Two leak-word removals** in oracle answers ("stage 1", "for now").
6. **No disjoint-vocabulary tie-break judge, no product judge.** PROTOCOL §6 calls for both; only the two
   rubric judges ran.
7. **Tool-call counts** include Worker subagents' calls, so they are not per-agent. The openspec-real arm had
   no subagents.
8. **Judge placement:** two of the six judges wrote `GUESS.md` into `blind/` instead of the workspace root.
   The content was unaffected.
9. **n = 1 per product.**
