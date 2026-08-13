---
title: "results — instance-segmentation annotator (two-arm blind pilot)"
date: 2026-08-13
---

## What this pilot is

A **build pilot** under [`../PROTOCOL.md`](../PROTOCOL.md): a real, container-run product
(multi-class instance-segmentation annotator) built by two arms across a **staged evolution neither arm
saw in advance**, then judged **blind** by separate judges I did not build with. This replaces an earlier
single-arm, self-judged *demonstration* of the same product — which is exactly the failure the protocol
exists to prevent (a demonstration is not an experiment; the control arm and the separate blind judge are
what make it one).

- **aims arm** — built following the design method, files co-located records; its Stage-2 evolution run by
  a **fresh session** told to navigate the records.
- **clean arm** — an equally capable agent told only "build it well"; no method, no records.

Both arms shared an identical substrate (Python/FastAPI + vanilla-canvas + Docker), identical stage cards
([`cards/stage-1.md`](cards/stage-1.md), [`cards/stage-2.md`](cards/stage-2.md)), and identical
neutrally-worded oracle answers ([`hidden/spec-and-oracle.md`](hidden/spec-and-oracle.md)). The axis under
stress: **the seam between annotation geometry and how the image is presented/stored**, exercised by the
Stage-2 satellite tiling + dataset export.

Blind mapping (revealed post-judgment): **X = clean arm, Y = aims arm.** The judges saw only records-
stripped, anonymized X/Y snapshots and a neutralized design standard.

## The two builds (both independently verified: `pytest` re-run by the operator)

|  | clean arm (X) | aims arm (Y) |
|---|---|---|
| Stage-1 core | polygons in **image-pixel space**, per-image JSON sidecar, Pillow confined | **same** independent choice |
| Stage-1 tests | 33 passed | 31 passed |
| Stage-2 evolution | `tiling.py` (pure) + `coco.py` (format) + `export.py` (orch, streams a **zip**); **0 core modules changed** | `tiling.py` (pure) + `export.py` (COCO); model untouched, **3 core modules extended additively** to preserve named invariants |
| Stage-2 tests | 52 passed (independently re-run) | 66 passed (independently re-run) |
| Records filed | none (README only) | root records + ADR 0002 + 8 anchored companions |

**The Stage-1 convergence is itself a result.** Both arms, independently, chose to store annotations in
original-image pixel space with the model separate from HTTP/canvas. So the "boundary that makes Stage 2
additive" was reached by the clean arm too — and **both** landed Stage 2 without touching the annotation
model. The earlier single-arm demo implied the *method* caused that additivity; the control shows an
equally-capable agent reaches it unaided. That specific claim does **not** survive the control.

## Q1 — direction (is the aims arm's final architecture better?) → **no clear advantage**

Two opposite-disposition design judges read the same blind X/Y. They **split**, and both called their
margins narrow and steelmanned the other side:

- **Invariant-ownership judge → Y (aims), modest margin.** Y funnels its two load-bearing boundaries
  through one seam each: **Pillow lives only in `images.py`** (X leaks `from PIL import Image` into
  `export.py` — two modules now know Pillow), and **path-safety is one gate** in the store (every read/
  write validates the id first). It found a **reproduction** against X: `storage.load_annotation(data,
  "../../secret")` returns an `Annotation` read from *outside* the data dir — the invariant is protected
  only incidentally by Starlette's router, not by X's storage design. X's one real structural win: a
  cleaner **export-format seam** (COCO confined to `coco.py`) vs. Y inlining COCO records in its export
  loop.
- **YAGNI/simplicity judge → X (clean), narrow margin.** Y pays a **distributed serialization tax that
  owns no present rule** — `Point` objects + a `*_stored`/`from_stored` mapping threaded through three
  modules, when Y's on-disk and wire shapes are identical (it decouples nothing that diverges). X keeps
  bare `[x,y]` lists and returns models directly. And X's export evolution touched **zero** core modules
  (zip to a temp dir), where Y reached into the store to add an `export_dir` concept. Steelman for Y:
  fewer modules overall (6 vs 8), COCO assembled inline instead of in a once-used builder class, tiling on
  plain tuples — "if you weight fewest files, Y is simpler and the call flips."

The verdict **flips with the judge's disposition**, and both margins are narrow — the taste-artifact
signal the two-judge design exists to catch. Per PROTOCOL §7, that is reported as **no clear structural
advantage**. The arms made different, defensible trades: the aims arm bought tighter dependency/invariant
ownership at the price of a serialization layer, a heavier export integration, and a weaker format seam;
the clean arm bought a leaner, self-contained export (and a richer frontend — pan/zoom/vertex-editing) at
the price of a diffused Pillow dependency and a path-safety invariant its storage design does not own.

### Verifying the judges (did they measure design, or execution?)

The recurring failure in this method's history is a "design" judge that silently scores *execution* —
does it work, test count, feature richness. So the judges were audited (a separate pass classifying every
load-bearing finding) and one factual claim was re-checked against source:

- **The design verdicts rest on design-quality criteria, not execution.** Every load-bearing finding is a
  genuine design property — dependency confinement, invariant ownership, seam/fork structure, earned
  abstraction, coupling, concept economy. No finding used test-pass/test-count, performance, or "it works"
  as a design signal. The one true feature-richness axis (the clean arm's richer frontend — pan/zoom/
  vertex-edit) was **explicitly identified and deliberately excluded** from the design score by the YAGNI
  judge, which is the correct discipline. The split is a real design disagreement (owned boundaries vs.
  fewer unearned abstractions), not design-vs-execution confusion.
- **But one judge mis-observed a load-bearing fact.** The two judges gave *contradictory* observations
  about the clean arm's Pillow use. Re-checked against source: `clean-arm/app/export.py:32` **and**
  `images.py:13` both `from PIL import Image` (two modules), while the aims arm has it only in
  `images.py:11` (one). So the **ownership judge was correct** and the **YAGNI judge was wrong** to list
  "both confine Pillow" as an equivalence. This does not flip either verdict (the YAGNI judge scored on the
  serialization tax + export self-containment, not on Pillow), but it lowers confidence in the YAGNI
  judge's observation accuracy — and, on the one axis where they conflicted, the evidence favors the aims
  arm. "Verify the judge, don't trust it" earned its place here.

## Q2 — continuity (did the fresh session continue from the records?) → **yes, and blind-corroborated**

This is where the durable-records layer showed a real, measured effect — judged separately from Q1.

The fresh aims Stage-2 session (no memory of Stage 1) **read the records and its design was shaped by
them**: it cited the two confined seams `architecture.md` names ("Pillow confined behind `images`",
"storage format confined behind the store") and **preserved both invariants** — keeping Pillow in one
module (adding `crop_to_file` to `images.py` rather than importing PIL in `export.py`) and routing export
writes through the store's path-safety owner (`export_dir`) rather than inventing a parallel filesystem
path.

The corroboration: the **blind** ownership judge — which never saw the records — independently scored
*exactly those two invariants* as the aims arm's structural wins, and independently found the
path-traversal weakness in the clean arm that the aims arm avoided. So the co-located records measurably
changed what the continuation session preserved, and a blind judge confirmed the preservation was real —
not self-reported. These are invariants legible in the records but **not obvious from the code alone**,
which is the whole point of the layer.

**Honest counterweight:** the same records/method also propagated the serialization layer and the
export-dir concept that the YAGNI judge marked as cost. The records faithfully carried invariants forward;
they did **not** guarantee a uniformly leaner design. Continuity ≠ dominance.

## Product → **no clear advantage**

The black-box product judge found both arms satisfy every Stage-1 and Stage-2 acceptance point and produce
byte-equivalent COCO. Offsetting minors: X has an explicit multi-instance/multi-class reload test and
streams a downloadable zip; Y adds export-name path-safety coverage and a tighter within-bounds clip
assertion. One small gap in Y: no automated test asserts *multiple* instances persist+reload (works live;
coverage asymmetry, not a defect).

## Cost → the treatment's price

| | clean arm | aims arm | delta |
|---|---|---|---|
| output tokens (S1+S2) | ~157.7k | ~223.7k | **+42%** |
| tool uses | 76 | 133 | +75% |
| wall-clock | ~17 min | ~23 min | +38% |

The extra reasoning + record-filing is the treatment; recorded, not equalized.

## Did the aims format documentation integrate correctly? (record-layer fidelity)

Audited separately from the design verdict:

- **Format written correctly.** All 8 companions use `title`/`date`/`hash:` frontmatter + Insights /
  Decisions / Discussions, same-name-as-source; all 8 anchors verified **in sync** (recomputed sha256).
  New files got new companions (`tiling.py.md`, `export.py.md`); on **updated** files (`images.py.md`,
  `store.py.md`) the fresh session **appended** new decisions and re-anchored (append-not-rewrite honored).
  System-level knowledge went to root records (ADR `0002`, `architecture.md` tension, `dependencies.md`);
  pure wiring/markup files got no companion.
- **Reading/continuation worked.** The session navigated to the relevant records and its Stage-2 decisions
  were shaped by them (see Q2).
- **Impurity:** the arm produced `.balash/state.md`, but the aims-guide skill uses `.aims/state.md` — so
  the run was actually steered by the **`balash-guide`** skill (available from the sibling repo), not
  `aims-guide`. Because aims is the port of Balash and they share the identical companion format + method,
  the treatment is faithfully represented and the fidelity finding holds; but the exact skill pin was
  balash-guide, not aims-guide.

## Verdict, plainly

- **Q1 (does the method yield better architecture here): no clear advantage.** A genuine, narrow,
  disposition-dependent split. Neither arm is structurally dominant on this product/axis.
- **Q2 (do the co-located records carry the design forward): yes, blind-corroborated.** The records
  changed what a fresh session preserved, and a blind judge independently credited those exact invariants —
  while also showing the method propagates its costs, not only its wins.
- **Product: no clear advantage. Cost: aims ~+42% tokens.**

The single most honest sentence: on an axis where a competent engineer already reaches the good seam
unaided, the method's measurable value was **not** a better one-shot architecture but the **faithful,
blind-verifiable propagation of specific invariants** to a fresh continuation session — bought at ~40%
more tokens, and not without propagating its own overhead.

## Why there was no gap — read against the prior experiments

Earlier pilots (Balash `experiments/RESULTS.md`, #1–#4/#6/#7) **did** measure a design gap. Their decisive
finding was always the same shape:

> the method won by getting the proportionality right on the **one subtle design decision the feature
> framing glosses over** — the decision the design objective explicitly *names* for the Worker to reason
> about. A plain session, handed the feature, does the feature and moves past that decision.

And the gap **shrank toward zero as that decision became more obvious/intrinsic**: pilot #1 (is a cycle
even possible?) and #2 (what uniqueness do you guarantee?) were clear wins because the plain arm *missed*
a latent judgment; pilot #3 (Sudoku) was the **closest** pilot precisely because uniqueness is *intrinsic
to Sudoku*, so the plain arm didn't miss it and the win narrowed to ownership quality only; pilot #4's gap
came from a late stage that **falsified an implicit assumption** ("rooms are independent").

This pilot reproduces none of the three gap-generating conditions — which is *why* Q1 came back null:

1. **The load-bearing decision was intrinsic, not latent.** "Store annotations in original-image pixel
   space, model decoupled from display" is the *default any competent engineer reaches for* when building
   an image annotator — even more obvious than Sudoku's uniqueness (the closest prior pilot). Both arms
   made it independently at Stage 1. There was no glossed-over judgment for the method to surface, so the
   first-order decision converged and the mechanism that won #1–#3 had nothing to bite on.
2. **Stage 2 falsified no earlier assumption.** Unlike #4's cross-room rule, satellite tiling + export is a
   pure *consumer* of the already-correct pixel model — it broke no hidden Stage-1 assumption, so both arms
   absorbed it additively. The axis I picked exercised a seam both arms had **already gotten right** rather
   than stressing a latent one. (Per `PROTOCOL.md` §0: "if you can't name the axis [that discriminates],
   the pilot won't discriminate." Here the axis was real but its key decision was not gloss-over-able.)
3. **Both arms ran a strong executor.** Pilot #3's lesson is that the method's edge is clearest carrying a
   *weaker* executor (a strong Guide lifted a Sonnet Worker past a plain Sonnet). With a strong clean arm,
   the unaided baseline is already high — that compresses any gap.

What *did* survive is the residue of the same "where should this truth live?" cognition that won the prior
pilots — the aims arm's tighter ownership of Pillow and path-safety — but it stayed **second-order**
(because the first-order truth was already placed correctly by both) and was offset by the method's own
recurring defect, over-build at the seams (here the rule-less serialization layer — the direct analogue of
the "ceremony at the seams" docked in #1–#3). And it showed up most clearly through the **records
(Q2)**, not the one-shot build.

So the honest reading is not "the method doesn't work." It is: **on an axis whose key decision is the
obvious default and whose evolution falsifies nothing, there is no latent judgment to surface, so the
one-shot design gap collapses** — exactly as the prior sequence predicts at its narrow end — and the
method's measurable value narrows to faithful, blind-verified *propagation of invariants* to a fresh
session. To measure a Q1 gap on this product, the pilot would need an axis that hides a decision — e.g. a
late requirement that the *same physical object spans multiple overlapping source images and must keep one
identity*, which would falsify "one annotation document per image" and stress ownership the way #4's
cross-room rule did.

## Honest limits

- **n = 1**, one product, one axis. Suggestive, not a measured effect size. Strength would come from a
  *sequence* of such pilots, not this single unit.
- **The arms are subagents of one session**, not independent humans/harnesses; convergent, not fully
  independent.
- **The Stage-2 aims session was *instructed* to read the records.** In a real install the SessionStart
  hook does this; here it was a prompt, so Q2 tests "given that it reads, does it continue correctly,"
  not "will an unprompted session read."
- **Skill pin impurity** (balash-guide vs aims-guide, above).
- **`docker compose build` could not run live** (no daemon in the sandbox); both apps were verified booting
  under uvicorn, the container's own entrypoint. Live container runs are unverified.
- Judges are subagents. Load-bearing claims were required to carry a reproduction or `file:line`; the
  operator independently re-ran both suites; the design verdicts were audited for execution-drift (clean —
  see "Verifying the judges"); and one contradicted structural claim (Pillow confinement) was re-checked
  against source. That check found a genuine **mis-observation by one judge** — evidence that these judges
  can and do err, so single-judge structural claims should be spot-verified, not trusted.
</content>
