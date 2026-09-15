# Judge prompts and criteria

Four readings, four judges, **never merged into one score**. No judge produced any of the designs. Every
load-bearing claim carries a **quotation from the design text** — there is no code to reproduce against, so
a quotation is the only admissible evidence, and a claim without one is struck before the reading is read.

---

## Preparing the blind copies

All three arms have a tell, so all three are stripped identically:

```
from each arm, keep only:  the three architecture documents
strip:                     method names anywhere in the text, directory names,
                           file headers and provenance lines, record/spec/proposal
                           wrappers, commit messages, dates that identify a run
relabel:                   X / Y / Z, in an order the judges are not told
```

The arm's own artifacts — companions, `openspec/specs/`, proposals, task lists — are **not** given to the
Q1 or Q2 judges. They go only to the Q3 judge, whose whole subject they are.

A judge that names a method in its report has not judged blind: discard it and re-cut the copies. Keep the
X/Y/Z → arm mapping in `mapping-SECRET.md`, unopened until all four readings are in.

---

## Q2 — survival (run this first; it is the primary reading)

Do it before Q1, so the taste-based reading cannot colour the countable one.

Per arm, twice — stage-1 → stage-2, and stage-2 → stage-3 — build the table defined in
[`../hidden/spec-and-oracle.md` §3a](../hidden/spec-and-oracle.md): every named component and seam of the
earlier design, classified **survived / extended / reopened / discarded**, each non-survival quoting both
versions.

Then per arm: the **reopened + discarded** count across both transitions.

Two rules that decide most disputes:

- **A rename is not a discard.** Same responsibility, same boundary, new name → *survived*. State the
  rename.
- **"Extended" requires an existing seam.** If the later design adds something at a place the earlier one
  had not named as a seam, that is *reopened*, not extended — the earlier design did not anticipate it.

**Output:** the two tables per arm, the counts, and the single most expensive reopening in each arm, quoted.
No verdict beyond the counts — the counts *are* the reading.

---

## Q1 — architecture (two opposite-disposition judges)

Both read the same three stage-3 designs against
[`design-principles.md`](../../../skills/aims-guide/references/design-principles.md) and
[`review.md`](../../../skills/aims-guide/references/review.md).

- **Judge 1 — invariant ownership.** Is each stated rule owned and enforced in one place? Can it be
  bypassed? Is a boundary one seam or several?
- **Judge 2 — YAGNI / simplicity.** Is any structure here unearned? Would a smaller design have carried the
  same three stages? Is each abstraction paying for itself?

Both answer **S1–S6** from [`../hidden/spec-and-oracle.md` §3b](../hidden/spec-and-oracle.md) for each of
X / Y / Z, quoting, or writing **the design does not say** — which is itself a finding.

Three standing rules:

- **Length is not a merit.** A longer design is not a better one. Say so to the judge explicitly; prose
  volume is the main way a design comparison goes wrong.
- **A removable local blemish must not flip a verdict.**
- **Small is not unearned** — a single stated rule with one owner is small *and* load-bearing.

**Output per judge:** the S1–S6 answers per design with quotations; then one verdict — **X**, **Y**, **Z**,
or **no clear advantage** — and the single structural fact that decides it. No scores, no percentages.

---

## Q3 — continuity (per arm, not blind)

The one reading that cannot be blind: the durable documents are its subject. Inputs — the fresh stage-2 and
stage-3 sessions' transcripts, and the arm's own artifacts.

Per arm, with quoted evidence:

1. Before changing the design, did the session **open a specific document**? Quote the moment.
2. Did it **cite** what it read as a reason for what it then did — or read it and proceed regardless?
3. Does the new design **build on** the earlier conclusion, or restate it from scratch?

**Three outcomes per arm:** *navigated and built on it* · *re-derived the same conclusion independently* ·
*contradicted or discarded the prior conclusion*. For the plain arm the question is whether its own earlier
design sufficed — re-deriving correctly there is a real result **against** both methods, not a failure.

Also run the coverage count of [§3c](../hidden/spec-and-oracle.md): requirements revealed vs. requirements
pinned, per arm.

A session that was told where the seam is has invalidated this reading. Check the prompt as delivered.

---

## Cost (recorder, no verdict)

Per arm, per stage: input/output tokens, turns, wall-clock, model calls, words of design produced, words of
method artifact produced. Report the two method arms against the plain arm as plain multiples. **No quality
judgment appears here** — and note that "words produced" is a cost, not an achievement.

---

## Verifying the judges

- Spot-check three quotations per judge against the design text.
- Confirm no report names a method.
- Confirm the two Q1 judges disagree somewhere. Two identical reports from opposite dispositions means the
  dispositions were not adopted.
- Confirm the Q2 counts were produced before the Q1 verdicts were read.
