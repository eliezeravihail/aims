# The measurement instrument — one form, everywhere

**All measurement in aims is this one form** — the in-loop review (`SKILL.md` step 5), the standalone
`/aims-review`, and any comparison of designs fill the same form. It does not define correctness; it *reads*
`references/design-principles.md` and turns "does this item hold" into a number. There is exactly one
instrument; what differs is only the projection shown (below).

## The structure — chapters are rows, items are sub-checks

`design-principles.md` is chapters (§0–§14), each a list of items. The scoring maps onto that structure
directly:

- **One row per chapter.** The profile is ~15 rows, not one per item.
- **A chapter's sub-checks are its items.** Each item is a binary, cited yes/no against the Step-0
  inventory: holds / does not. **chapter score = round(10 × items-passed / items-applicable).**
- **Applicability prunes hard.** Most items are N/A for a given artifact (architecture/§10 for a
  single-file utility; §14 with no boundary; §11 runtime on a pure design). N/A items leave the
  denominator; a typical review scores 15–25 applicable items across the chapters, not all of them.

## Step 0 — the fixed inventory (before any scoring)

Pin from the spec / the objective's exit criteria, never from the design, and hold fixed for the whole
measurement: **(R)** the rules/invariants, **(X)** the change-axes (+ one plausible unstated variant),
**(C)** the acceptance cases (or, with no numeric cases, the end-to-end capability checks). Every failed
sub-check cites an R/X/C item or a named seam.

## Severity — read the class from the source

The tier of a **failed item** follows its **correctness class** in `design-principles.md`:

- a **precondition** item failing (all of §1; §5 "one owner"; §0/§5 seam-leak; §11 concurrency-safety under
  concurrency; §14 with a boundary) is **S4** — the code is wrong, not merely less clean;
- a **quality** item failing is **S1–S3** by pervasiveness (cosmetic → local → structural);
- a **conditional** (§13, §14) or **code-leaning** (§12, §11 runtime) item is **N/A** where it does not
  apply.

A chapter's severity is the tier of its worst failed item; that tier sets the chapter's ceiling and weight:

| worst failed item | ceiling | weight |
|---|---|---|
| none | 10 | ×1 |
| S1 cosmetic | 8 | ×1 |
| S2 moderate | 7 | ×2 |
| S3 high | 5 | ×4 |
| S4 severe / correctness | 2 | ×8 |

**§0 (Foundational) carries the heaviest structural weight:** a seam that leaks an implementation, a module
reaching into another's internals, or a missing‑encapsulation failure is S3–S4 and drives the grade down
hard through its weight — never a nit.

## Rules of filling

- **Every item cited** — a pass quotes where it holds; a fail quotes the defect and the R/X/C or seam it
  violates. No citation → not counted.
- **One defect, one item** — a defect is scored under the most specific item; other items reference it,
  never re-deduct. With a long list this is what prevents double-counting.
- **Not eyeballed** — the chapter score is computed from its items, never a holistic guess.

## Aggregation

```
grade         = Σ(chapter_score × weight) / Σ(weight)   ← the whole-list weighted score
worst_chapter = min chapter_score
counts        = (#S3, #S4) across items
gate          = any S4 ⇒ BLOCKED (a correctness precondition fails) · else CLEAR
```

**The grade is the weighted list — there is no global cap that overrides it.** A design score grades the
*design*; the weighting already carries severity (a severe chapter takes a low ceiling *and* an ×8 weight,
so one bad chapter pulls the number down hard on its own). A single local, easily-fixed correctness defect
therefore lowers the grade through its chapter — but it never *caps* the whole design to a near-fail, which
would double-count the same defect and let one fixable item bury an otherwise-excellent design.

The **gate** is reported *beside* the grade, not folded into it: `any S4 ⇒ BLOCKED` means "not shippable
until this precondition item is fixed" — a fact about **shippability**, not a verdict that the design is
weak. A design can be strong (high grade) *and* blocked (one S4 to fix); the fix-list projection names
exactly what to fix. Report the grade, `worst_chapter`, the `(#S3,#S4)` counts, and the gate together —
never a bare number, and never a capped one.

**Comparability.** Applicability is decided by Step 0 (the spec), so **all arms of one product share the
same applicable set** and their grades are directly comparable. Grades across *different* products are not
(different applicable sets) — and are never read as a single verdict on the method.

## Two projections — same filled form, shown two ways

- **Building / in-loop (default):** the **fix-list** — only the failed items, sorted most-severe-first,
  each with its citation and the direction to fix it. **No aggregate score shown** — a device so the Worker
  fixes content, not a number (`decisions/0014`), not a principle. The scores exist underneath.
- **Comparing designs:** the full scored form + the aggregate profile — for ranking arms or tracking a
  design across revisions.

## Building with the same form

The build side runs the same chapters, preconditions first (§1 correctness, §5 one-owner, §0 seams): pin
R/X/C, make every applicable item hold by construction, and self-fill the form before returning. Never
return a design carrying a failed precondition (S4) or an S3 without surfacing it.
