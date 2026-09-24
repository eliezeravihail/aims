# Results — design-principles.md vs. OpenSpec, three products, design-only

> **Superseded.** In this run the OpenSpec arm only imitated the tool's format. The comparison was re-run with
> the real tool, in two rounds: [`results-openspec-real.md`](results-openspec-real.md) (round 1) and
> [`results-aims-real.md`](results-aims-real.md) (round 2). The rounds disagree, and the same OpenSpec designs
> were graded 5.7–9.8 depending on the judge. The readings below are kept as the record of this run.

**Run once, 2026-09-18.** Pins: aims method at this branch's head; both arms and all three judges are
isolated subagents on the same model; design-only, no code. n = 1 per product (strength is the sequence of
three). Deviations declared in [`README.md`](README.md) §5.

## What was measured

Two arms — **aims-single** (the shipped `aims-guide` skill, run as-is, incl. its one mandatory
review-and-revise round) and **OpenSpec** (its own spec-first workflow) — on three products, each scored on
two separate dimensions: **D1** first-round design quality (assessment form on the stage-1 design) and **D2**
change absorption (survival count + form on the stage-2 design, after an unforeseen requirement). Quality and
cost both read.

## Readings

| Product | D1 (first-round) | D2 rubric grade | D2 survival — *rubric-free* (reopened+discarded) | Hard correctness traps |
|---|---|---|---|---|
| **feed-ranking** | **aims 10** vs OpenSpec 8.5 | aims 9.9 vs 8.5 (narrow) | **tie** — aims 0, OpenSpec 0 | both passed all (stage 1 & 2) |
| **booking-availability** | **aims 10** vs OpenSpec 7.5 | **aims 10** vs 7.5 (decisive) | **aims better** — aims ≈1, OpenSpec ≈2 | both passed all |
| **entitlements** | **aims 10** vs OpenSpec 8.5 | aims 9.9 vs 8.5 (narrow) | **tie** — aims ≈2, OpenSpec ≈2 | both passed all |

Each blind judge scored X/Y structure-only against `design-principles.md` + the hidden oracle; sealed
mappings under `judging/*/MAPPING-SECRET.md`; full reports under `judging/*/report.md`.

### D1 — first-round quality: aims wins all three, on the same axis
The gap is always §4 (value objects) and §5/§9 (one owner). aims wrapped domain concepts in named value
objects with a single rule-owner each — `UnitInterval`/`SignalVector` (feed), `TimeOfDay`/`Duration`/
`Interval` as the sole half-open owner (booking), `Role.grants(...)` + typed ids (entitlements) — where
OpenSpec's stage-1 designs carried bare floats / minutes-scalars / positional strings (a §4 S2–S3 finding
each). This is exactly the rubric's stated dominant failure ("too little structure … primitive obsession").

### D2 — change absorption: aims wins the rubric score all three; the rubric-free reading is tie / aims / tie
Both arms **passed every hard correctness trap at both stages** — neither shipped a wrong number. On these
three products OpenSpec was *also* correct; the traps discriminated on **structure**, not on raw correctness.
The one place a rubric-free-ish trap clearly separated them was **booking**: OpenSpec split the new *buffer*
rule across a "normal" occupancy path and a separate trailing filter — a one-owner-per-rule breach (S3) that
appeared *because the rule gained a case under the change* — while aims kept the buffer to one owner (a
symmetric minimum-separation, after its concept-fit review caught the buffer-as-`Booking` substitution). On
feed and entitlements the survival count was a **tie**: both kept every rule owner intact and slotted the
change in at an existing seam.

### Cost (recorder only, no quality verdict)
aims is markedly more expensive: the aims arms averaged ~**140k tokens / 30–40 tool-calls / ~12 min** per
product; the OpenSpec arms ~**55k tokens / 4 tool-calls / ~3 min** — roughly **2.5–3×** tokens and much more
wall-clock, the price of reading the method, filing records, and running the mandatory revise round. Final
design length was **not** proportional to quality (OpenSpec's stage-2 docs were often longer).

## The honest limitations

1. **Rubric bias — the un-removable one.** D1/D2 are scored against aims' *own* `design-principles.md`, and
   all three judges independently flagged that the aims arm's designs **speak the rubric's vocabulary**
   ("subtractive pass", "§7 falsifier", concept-fit), which a rubric-sharing judge can be pulled toward.
   Each judge controlled for it (structural, quoted findings; not crediting vocabulary) — but it is not
   eliminated. The rubric-free cross-check is the **survival count**, and there the result is only
   tie / aims / tie. So the defensible claim is: **aims is at least as good as OpenSpec on change
   absorption on all three, and clearly better on first-round structure; it is decisively better only where
   a structural trap (booking's one-owner buffer) discriminated.**
2. **These products did not break a careful OpenSpec run's correctness.** A stronger falsifier would be a
   product where the cram is *hard to avoid*; here both arms avoided every cram, so the pilot measures
   structural quality more than correctness-under-pressure.
3. **n = 1 per product; blinding is partial** (house styles remain legible); the oracle was non-interactive.

## What the pilot changed in `design-principles.md` (and `review.md`)

The pilot did **not** find the document leading aims to an incorrect design — aims' arms had essentially no
principle-level findings (grades 10 / 10 / 10 at stage 1). It **validated** the document. The one
genuinely new, evidence-backed lesson is about the **concept-fit / value-correct-cram** family: across the
runs it appeared in four distinct shapes — tax-as-adjustment, **buffer-as-booking**, **deny-as-absence**,
**block/diversity-as-weight** — where the document named only one (decomposition-vs-movement). Two minimal
sharpenings, backed by these instances:

- **§4 Concept fit** broadened from the decomposition/movement case to the whole family (a concept modelled
  as a degenerate/synthetic instance of a neighbouring type — entity, effect-as-absence, or filter-as-score
  — each with an inert stand-in as the tell).
- **§5 One owner per rule** gained the change-time clause the booking loss demonstrated: when a rule gains a
  case under a change, absorb it in the one owner; a parallel special-case path silently creates a second
  owner.
- **`review.md`** concept-fit pass extended to ask the general question, not only decomposition-vs-movement.

No re-run "to confirm a fix" was needed: no arm failed, and the change is a *generalization* backed by four
observed instances, not a repair of a regression. The pilot's own stage-2 designs are the standing evidence
that the sharpened wording matches designs aims already produces correctly.
