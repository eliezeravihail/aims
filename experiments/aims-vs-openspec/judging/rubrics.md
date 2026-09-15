# Judge prompts and rubrics

Four readings, four judges, **never merged into one score** (PROTOCOL §7). No judge is a session that built
any arm (PROTOCOL §6). Every load-bearing claim carries a reproduction (input → wrong output, a failing
test) or a precise `file:line`; a claim without one is struck from the report before the reading is read.

---

## Preparing the blind snapshots

All three arms have a tell, so all three are stripped identically:

```
remove from every arm's snapshot:
  .aims/  *.md companions  goals.md  architecture.md  decisions/
  openspec/  AGENTS.md  CLAUDE.md  .claude/  .github/
  .git/                      # commit messages name the method
keep:
  source, tests, config, any README the product itself needs to run
relabel the three trees X / Y / Z, in an order the judges are not told,
and rename any directory whose name contains a method's name
```

A judge who can name a method in its report has not judged blind: discard that report and re-cut the
snapshots. Record the X/Y/Z → arm mapping in a `mapping-SECRET.md` that is not opened until all four
readings are in.

---

## R1 — design (two opposite-disposition judges)

Both judges read the **same three snapshots** against
[`design-principles.md`](../../../skills/aims-guide/references/design-principles.md) and
[`review.md`](../../../skills/aims-guide/references/review.md). Two dispositions, because a single judge's
verdict is often a taste artifact:

- **Judge 1 — invariant ownership.** Is each stated rule owned and enforced in exactly one place? Can it be
  bypassed? Is a boundary one seam or N?
- **Judge 2 — YAGNI / simplicity.** Is any structure here unearned? Would a smaller thing have carried the
  same evolution? Is the abstraction paying for itself?

**The verdict must turn on a structural property.** The five structural probes in
[`../hidden/spec-and-oracle.md` §3](../hidden/spec-and-oracle.md) are the spine of this reading:

| | Question the judge answers with a `file:line` |
|---|---|
| S1 | To add a fourth promotion kind: how many files change? Does the total calculation change at all? |
| S2 | How many distinct places round money? |
| S3 | Is the explanation derived from the structure that computes the amount, or a second implementation that can disagree? |
| S4 | To add a third market with a third tax model: how many files change? |
| S5 | Is adjustment ordering stated in one place, or implied by control flow in several? |

Two standing refinements (PROTOCOL §6.3): a **removable local blemish must not flip a verdict**, and
**"small is not unearned"** — a one-line funnel or a private field with no setter is small *and*
load-bearing, not ceremony.

**Output per judge:** for each of X / Y / Z, the five structural answers with citations; then one verdict —
**X**, **Y**, **Z**, or **no clear advantage** — and the single structural fact that decides it. No scores,
no percentages, no composite.

---

## R2 — requirement fidelity (black-box judge)

Given: the three stage cards, the hidden final probes, and each arm's stated entry point. **Not** given: the
method label, the snapshots' provenance, or any arm's internal artifacts.

1. **Run** P1–P8 from [`../hidden/spec-and-oracle.md` §3](../hidden/spec-and-oracle.md) against each arm.
   Record pass/fail per probe with the exact input and the exact output.
2. **P1 is the reading that matters most** — every stage-1 and stage-2 behavior re-run *after* stage 3. A
   method that keeps requirements pinned should show here, if it shows anywhere.
3. **Coverage.** For each requirement revealed across the three cards, name the artifact in that arm that
   pins it — a test, a scenario, an assertion — or record **nothing pins it**. Count, per arm: requirements
   revealed / requirements pinned.
4. **Verdict:** **X**, **Y**, **Z**, or **no clear advantage**, on probes and coverage separately.

This reading is scored on **OpenSpec's own standard**, deliberately (README §6).

---

## R3 — continuity (per arm, not blind)

The one reading that is necessarily un-blinded, because the durable layer *is* the subject. Inputs: the
fresh stage-3 session's full transcript and its diff.

Per arm, answer with quoted evidence:

1. Before touching the pricing path, did the session **read a specific durable artifact** — and can you
   quote the moment it did?
2. Did it **cite** what it read as a reason for what it then did, or did it read and proceed regardless?
3. Does the diff **reuse** the composition seam, or reopen it?

**Three outcomes, per arm:** *navigated and built on it* · *re-derived the same conclusion independently* ·
*contradicted or tore open the prior conclusion*. For the plain arm the question is whether the code alone
sufficed — its "no durable layer" is its honest condition, and re-deriving correctly is a real result
**against** both methods, not a failure of the arm.

A session that was *told* where the seam is has invalidated this reading. Check the stage-3 prompt as
delivered.

---

## R4 — cost (recorder, no verdict)

Per arm, per stage: input/output tokens, turns, wall-clock, model calls, runtime dependencies added, lines
of product code, lines of method artifact. Report the aims arm's and the OpenSpec arm's overhead against the
plain arm as plain multiples. **No quality judgment appears in this reading.**

---

## Verify the judge (PROTOCOL §6.4)

Before any reading is believed:

- re-run each arm's suite independently (`pip install -e .`, `pytest -q`) — never take "tests pass" on
  report;
- spot-check three citations per judge by opening the `file:line`;
- confirm no judge report names a method;
- confirm the two R1 judges disagree *somewhere* — two identical reports from opposite dispositions is a
  sign the dispositions were not actually adopted.
