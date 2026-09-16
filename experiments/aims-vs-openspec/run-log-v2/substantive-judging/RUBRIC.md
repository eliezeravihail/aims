# Substantive architecture judging — by consequence, not by catalogue

An architecture is good insofar as it (a) absorbs unforeseen change cheaply, (b) carries little
complexity the *problem* did not force, and (c) keeps the blast radius of the next change small. A code
smell matters ONLY insofar as it predicts one of these. A smell that predicts none is cosmetic and is
barred from the verdict. This rubric exists because a taste-based smell hunt let a single removable
decision outrank a structurally leaner design — the error this replaces.

Judge three final designs (blind). Produce four measures, three of them countable.

## M1 — Change absorption (retrospective, already measured)
The survival count: named components/seams reopened or discarded across the two evolutions. Lower better.
(Provided per design; do not recompute — use it as one input.)

## M2 — Accidental complexity (count it)
For each design, count the named components, types, and error classes that the PROBLEM did not force —
machinery introduced to support the design's own choices, not the requirements. Test for "forced": would
*every* correct design of this exact product need it? If a shared/simpler mechanism satisfies every stated
case, the heavier one is accidental. List each accidental item with a one-line justification. Lower total
is better. (Example of the judgment, not a preset answer: a per-market catalogue file plus a
market-mismatch error plus a routing guard is accidental *iff* a single shared catalogue prices every
given case; decide that from the text.)

## M3 — Blast radius of the next change (pre-registered, forward-looking)
These three changes are fixed in advance and none is in the current spec. For each design and each change,
count the NAMED components that must be reopened (responsibility or boundary changes), quoting the seam.
Lower total is better. This is the real test of whether the seams anticipated the future.
  C-next-1: a third market with a **reduced VAT rate on some products** (rate becomes per-line and needs
            product metadata the cart does not carry today).
  C-next-2: a promotion whose **eligibility depends on the customer** (customer id is carried today but
            read by nothing).
  C-next-3: a **second currency**.

## M4 — Fault severity as a Cartesian plane (two continuous axes)
There is no binary gate. Every cited fault is a **point** on two continuous axes, and its **severity
grows monotonically along both** — the further from the origin, the worse:

- **X — Hiddenness (0 → high).** 0 = fully *visible*: an openly-stated design choice, or a wrong number on
  an ordinary input, that a reasonable reader or user meets at once. High = deeply *latent*: correct on
  ordinary inputs, surfaces only under a rare or future condition, so it is discovered late and after
  damage. **The more hidden, the more severe.**
- **Y — Change required to fix (0 → high).** 0 = *additive/focused*: add code or a bounded local edit, no
  rethink. High = *architectural*: the fix reshapes a core seam, moves the ownership of an invariant, or
  rebuilds the spine. **The more it forces, the more severe.**

Severity is the position in that plane. The **origin corner (visible + additive)** is negligible and
**cannot move the ranking**. The **far corner (hidden + architectural)** is the design-failure corner and
can be decisive. Everything between weighs in proportion to how far it sits toward the far corner — a very
hidden but cheap fault, or a very architectural but glaring one, weighs a middling amount; only faults
well into the hidden-and-architectural quadrant may outrank a design that leads the consequence measures.

For every fault: give its (X, Y) placement with the textual evidence for each coordinate, then its
resulting severity (low / moderate / high), then whether that severity is enough — against M1–M3 — to move
the ranking.

Correctness gate (raises X toward the visible-but-real end, or flags a true bug): if a fault produces a
**wrong result** on any input you name, it is a real defect, not a cleanliness point — test each design's
stated cases plus one adversarial input of your own. A modelling/altitude concern whose numbers are
correct everywhere sits low on Y-as-bug and is weighed as cleanliness, placed by its (X, Y) like any
other fault.

## Verdict rule (this is the substance)
Rank primarily on **M1 + M2 + M3** — the three consequence measures. **M4 may only break a tie between
designs that are close on M1–M3, or downgrade a design carrying a PERVASIVE integrity fault.** No single
local decision may invert a design that leads on the consequence measures. If a design leads M1–M3 and its
only integrity faults are local blemishes, it wins — say so explicitly, and name the blemishes you are
correctly declining to rank on.

Output: the four measures per design with counts and quotations; the mandatory local-vs-pervasive
classification for every cited fault; then ONE verdict naming which consequence measures decide it.
