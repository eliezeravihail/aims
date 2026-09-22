# Phase 2 — protocol notes, frozen before any stage-2 arm runs

Operational detail `../DESIGN.md` leaves open for stages 2 and 3, fixed here before any result exists. Everything
not restated here is as in `../phase1/PROTOCOL-NOTES.md`.

## Arms — nine sessions per stage, every one fresh

| dir | arm | starts stage 2 from | what reaches the stage-2 session |
|---|---|---|---|
| `a1`, `a2`, `a3` | **A — aims, with records** | `w1`, `w2`, `w3` (Phase 1's aims runs) | the code **and** every record its stage 1 filed (`goals.md`, `architecture.md`, `decisions/`, companions, `.aims/`) |
| `b1`, `b2`, `b3` | **B — aims, records withheld** | the same `w1`, `w2`, `w3` | the code only — records stripped (below); `.aims/anchor.py` re-installed, as `/install-on` does |
| `c1`, `c2`, `c3` | **C — unaided** | `w4`, `w5`, `w6` (Phase 1's unaided runs) | the code |

Stage 3 starts each arm from **its own** stage-2 result, the same way (B's stage-2 records are stripped again).
A stage that ends BLOCKED on the floor still goes on — the floor is reported, not a stop.

**Stripping a record (B only).** Removed: `goals.md`, `architecture.md`, `base-dependencies.md`, `dependencies.md`,
`decisions/`, every companion (`<file>.<ext>.md`) and `<dir>.md` folder record, and `.aims/` (then only
`.aims/anchor.py` is put back). Kept: the product's own documentation under `docs/`. In code, a comment line naming
a record is removed, as in Phase 1's anonymization; a mention inside a docstring or string stays and is counted.

**Each tree is committed before its session starts**, with the same neutral message in every arm ("Add
multi-language sites" before stage 2, "Add incremental rebuilds" before stage 3) — so every session starts from a
clean working tree, and nothing but the code (and, in A, the records) tells it what came before. `.venv/` is never
committed.

## The prompt

Identical for all nine, except the one aims line (A, B) and the session-start note (A only):

- The Phase 1 prompt, with the stage's card in place of the stage-1 card, and "A few tests fail before you start,
  for environmental reasons (localization-catalogue tests and `test_draft_docs_with_comments_from_user_guide`)" in
  place of "Six tests fail…" — after stage 1 the exact count can differ by arm.
- **A only — the session-start note.** An installed aims prints a note at the start of every session in a project
  that carries aims records (`templates/hooks/session-start.sh` at the pinned commit). Hooks do not run inside a
  subagent, so A's prompt opens with that hook's output, **verbatim**. B carries no records, so for B the same
  hook prints nothing — and B's prompt opens with nothing. This is aims' own text, not the experimenter's; it is
  what "with records" means for an installed aims.
- The read-time staleness hook cannot be emulated and is not. A's companions were anchored when filed; this is
  disclosed, not corrected.

## The product owner

As in Phase 1: an answer in `../hidden/oracle.md` for the current stage, verbatim; else, if the card answers, the
card's own sentences, verbatim; else *"I don't know — choose a simple, sensible technical approach."* Any question
about later plans: *"Not now — build for today."* No reply to "unless you object". Every exchange logged in
`oracle-log.md`.

**The goal-2 trap (stage 3)** gets the oracle's answer only if a session asks about opening in the reader's
language, detecting the browser language, or how that line relates to the no-detection rule.

## The floor

- Stage 2: `../hidden/probes/stage1_probe.py` (regression) and `stage2_probe.py`.
- Stage 3: `stage1_probe.py` (regression) and `stage3_probe.py` (with the arm's stage-2 tree as its baseline for
  "`mkdocs build` unchanged").
- From Phase 2 on, `stage1_probe.py` ignores `messages.pot` — fixed now, as `../phase1/floor-notes.md` announced.
- Found while validating `stage2_probe.py` on the pinned commit (see its docstring): pristine's own `--dirty` build
  writes "None" for the navigation titles of pages it did not re-render, and a search index of only the rebuilt
  pages. Page HTML is gated exactly, as the card says; the search index and single-language `--dirty` are reported,
  not gated.

The floor enters no verdict.

## Judging

Anonymized exactly as in Phase 1; nine labels drawn with `SystemRandom`, salted; only the SHA-256 committed before
any judge runs; a fresh draw at each stage.

- **Stage 2:** the disjoint-vocabulary judge alone, all nine designs (`../DESIGN.md` §4).
- **Stage 3:** the full panel — ownership, simplicity, disjoint — all nine designs. Each judge's prompt is Phase 1's,
  with "nine" for "six" and the Phase 2 paths.
- If a judge session cannot finish nine designs, it is rerun on two batches (A+B designs; C designs plus one A
  design as a common anchor), with one Step 0 inventory, and that is reported.

Every S3/S4 a verdict rests on is reproduced against the code, blind, before unsealing.

## Verdicts — as `../DESIGN.md` §6 registered them

**Goal 1 — B vs C at stage 3 (primary).** Per judge, with F = the worst of an arm's three grades, M = their mean,
and R(C) = C's range (best − worst):

- **supported** if F(B) > F(C) **and** M(B) − M(C) > R(C);
- **falsified** if M(B) ≤ M(C) **or** F(B) ≤ F(C);
- otherwise **no clear advantage**.

The panel's verdict: if the ownership and simplicity judges agree, that is it; if they differ, the disjoint judge
decides only by agreeing with one; otherwise **no clear advantage**.

**Secondary, reported with the same arithmetic, no separate claim:** B vs C at stage 2 (disjoint judge);
the trajectory of each arm across stages 1–3; **A vs B at stage 3** (records → design; predicted: no meaningful
difference).

**Goal 2 — the non-goal (stage 3).** A session **surfaces** the conflict if it asks the product owner about the
opening-in-the-reader's-language line (or detection), or its reply states that the line conflicts with the rule
that the reader always chooses. Anything else does not surface it — whether it implements detection (recorded from
the code and `stage3_probe.py`'s INFO line) or drops it silently. Supported if A surfaces it in ≥ 2 of 3 and B and
C each in ≤ 1 of 3; **falsified if A's count ≤ B's**; otherwise no clear advantage.

## Cost

About 7 M tokens (`../DESIGN.md` §8): 18 arm sessions, the stage-2 judge, the stage-3 panel.
