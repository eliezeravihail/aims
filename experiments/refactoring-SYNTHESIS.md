# Synthesis — validating `add-feature-principles.md`

The add-feature/adaptation experiments (historically "refactoring"; the Kind and doc were renamed per
`../decisions/0017-rename-refactoring-to-add-feature.md`), and what they establish about the shipped
[`add-feature-principles.md`](../skills/aims-guide/references/add-feature-principles.md) and the
`/aims-add-feature` Kind. Read alongside each experiment's own `results.md`.

## The experiments

| # | experiment | codebase | change | reading |
|---|---|---|---|---|
| 1 | `refactoring-principles-validation` | synthetic pricing | per-line tax + allocation (spelled out) | both arms oracle-correct; card over-specified the trap |
| 2 | `refactoring-suite` (3 tasks) | synthetic (calc, state machine, pricing) | add operator / cancel event / discover allocation | both arms correct on all; aims cleaner (one-owner vs a scattered set) |
| 3 | `refactoring-suite-real` | **real** (mahmoud/boltons cacheutils) | add TTL (cross-path: in/get/[] + LRU override) | both 23 tests + 14-oracle; aims tighter (expiry in the node, 31 vs 53 lines) |
| 4 | `refactoring-rot` (3-step sequence) | synthetic plain pricing | 3 successive interacting changes | both correct every step; **aims design trajectory improves, plain stays flat/denser** |
| 5 | `refactoring-crosscut` (capstone) | 4-module ledger | multi-currency (cross-cutting) | both correct + on-grain; **essentially a tie** (aims wins DRY, plain wins one coherence point) |
| 6 | `refactoring-continuity` | same code ± the record | a fresh session adds a refund (re-derivation trap) | both fresh sessions reused the owner and passed 14/14; the record added legibility, **not a different outcome**, at this scale |

## What holds across all five

1. **Correctness parity — with a caveat that matters.** On every task *in this refactoring set* — synthetic
   or real, single-file or cross-cutting — a capable model with **no method** produced a correct adaptation
   that preserved existing behavior. But "parity" is **contingent on no correctness defect appearing**, and
   it is not general: the separate plant→mineral design pilot (`../plant-mineral-id/`) is a case where the
   aims arm shipped a real **S4** — a type model that could not represent a value the spec named ("6.5–7").
   That is a **§4/§1 *design* defect, not an execution slip** (a corrected framing, per review): when a
   design's types cannot represent a required case, calling the result "near parity" is too generous. So the
   honest claim is narrower: **where no correctness defect appears, a strong model is correct without the
   method; the instrument's job is to catch the defect when it does appear — and, judged blind, it caught
   one in the home method.** The tempting follow-up — reword §7 so a stated capability can never be
   YAGNI-cut — was **tested on an unseen product and did not prove necessary** (both arms kept the
   capability; `../s7-yagni-stated-capability/`), so it was **not** folded in: the plant→mineral S4 reads as
   a builder miss under adequate wording, not a documented gap, and the document is left unchanged rather
   than padded off one loss.
2. **The method's measurable edge is structural, and it grows with the sequence.** The clearest signal is
   experiment 4: under the correct measurement — a **before/after design review on the target's grain across
   successive changes** — aims *improves* each step (named single-owners, short functions) while the plain
   arm stays flat and denser (an unnamed 20-line block, a 5-tuple read by a magic index). One change hides
   this; a sequence exposes it. That is the mechanism behind the historical checkout **S4**
   (`../judging-rubric/regrade-results.md`): rot accumulates while every step "works".
3. **Consistency-over-dogma held.** Given a deliberately plain-style base (4, 5), aims did **not** impose
   value objects — it kept the bare-int/bare-string grain and absorbed only the representation change the
   requirement forced. The `decisions/0016` constraint (match the target's grain, no new mess) is doing its
   job: the method did not "improve" the code into inconsistency.

## What the experiments changed in the document

The validation was not a rubber stamp — three sharpenings came out of it, each from a specific run:
- **§4 concept-fit generalized** to the whole value-correct-cram family (from the design pilot's four instances).
- **The before/after-review measure + consistency-over-dogma constraint** (`decisions/0016`), from the user's
  reasoning while validating — the refactoring review grades a *delta on the target*, not an absolute ideal.
- **§6 extended** so an existing reader that now runs on the change's new data shape is re-traced, not left
  under §4 — from the capstone, where aims left a `statement` function incoherent under multi-currency.

## Honest bottom line

`add-feature-principles.md` is **validated and improved**: following it yields correct, behavior-preserving,
on-grain adaptations, and — measured as a trajectory — a cleaner design than no method, without
over-abstraction. It does **not** manufacture a correctness advantage on changes a strong model already
handles; its value is structural discipline and durable records that compound across many changes and hands
— a scale beyond a single session to stage, and the honest frontier for the next round.

The **continuity** experiment (6) closes the loop on aims' second claim with the same honesty: on a small,
readable module a fresh session reconstructs the invariant from the code itself, so the co-located record
adds legibility and confidence but not a different outcome. The record is load-bearing only where the code is
ambiguous or hides a rejected-alternative trap, at a scale where re-deriving is slow and error-prone —
again a scale-and-longevity effect, not a single-session one. Across all six: **correctness parity at every
scale tested; a real, measurable structural/legibility edge that grows with the sequence and the codebase;
and consistency-over-dogma held throughout.**
